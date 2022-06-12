"""Stream type classes for tap-jira."""
import orjson
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Iterable
from memoization import cached

import jira
from singer_sdk import typing as th  # JSON Schema typing helpers

from tap_jira.client import JiraStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class UsersStream(JiraStream):
    """User stream."""

    name = "users"
    primary_keys = ["accountId"]
    replication_key = None
    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("key", th.StringType),
        th.Property(
            "self",
            th.StringType,
            description="The URL this record was sourced from",
        ),
        th.Property("accountId", th.StringType),
        th.Property("accountType", th.StringType),
        th.Property("emailAddress", th.StringType),
        th.Property("displayName", th.StringType),
        th.Property("active", th.BooleanType),
        th.Property("timeZone", th.StringType),
        th.Property("locale", th.StringType),
        th.Property(
            "groups",
            th.ObjectType(
                th.Property("size", th.IntegerType),
                th.Property(
                    "items",
                    th.ArrayType(
                        th.ObjectType(
                            th.Property("name", th.StringType),
                            th.Property("self", th.StringType),
                            th.Property("groupId", th.StringType),
                        )
                    ),
                ),
            ),
        ),
    ).to_dict()

    def get_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Return a generator of row-type dictionary objects."""
        offset = 0
        page_size = 100
        while records := self.conn.search_users(
            query=".*", startAt=offset, maxResults=page_size
        ):
            for record in records:
                yield self.conn.user(record.accountId, expand="groups").raw
            offset += page_size


class IssuesStream(JiraStream):
    """Issue stream. Schema dynamically generated from the JIRA API."""

    name = "issues"
    primary_keys = ["issueId"]
    replication_key = "updated"

    @property
    @cached
    def schema(self) -> dict:
        """Dynamically detect the json schema for the stream.
        This is evaluated prior to any records being retrieved.
        """
        j = jira.JIRA(
            server=self.config.get("api_url", "https://jira.atlassian.com"),
            basic_auth=(self.config["username"], self.config["password"]),
        )
        properties: List[th.Property] = []
        properties.extend(
            [
                th.Property("issueId", th.StringType),
                th.Property(
                    "key",
                    th.StringType,
                    description="Jira issue key",
                ),
            ]
        )
        for field in j.fields():
            if field["key"] == "updated":
                properties.append(th.Property("updated", th.DateTimeType))
                continue
            properties.append(
                th.Property(field["key"], th.StringType, description=field["name"])
            )
        return th.PropertiesList(*properties).to_dict()

    def get_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Return a generator of row-type dictionary objects."""
        offset = 0
        page_size = 100
        while records := self.conn.search_issues(
            jql_str="updated >= '{}' order by updated asc".format(self.start_date),
            startAt=offset,
            maxResults=page_size,
        ):
            for record in records:
                yield {
                    **{
                        k: orjson.dumps(v).decode("utf-8")
                        for k, v in record.raw["fields"].items()
                        if v
                    },
                    "issueId": record.id,
                    "key": record.key,
                }
            offset += page_size


class ProjectsStream(JiraStream):
    """Project stream."""

    name = "projects"
    primary_keys = ["projectId"]
    replication_key = None
    schema = th.PropertiesList(
        th.Property("name", th.StringType),
        th.Property("key", th.StringType),
        th.Property(
            "self",
            th.StringType,
            description="The URL this record was sourced from",
        ),
        th.Property("projectId", th.StringType),
        th.Property(
            "projectCategory",
            th.ObjectType(
                th.Property("name", th.StringType),
                th.Property("self", th.StringType),
                th.Property("description", th.StringType),
                th.Property("id", th.StringType),
            ),
        ),
        th.Property("projectTypeKey", th.StringType),
        th.Property("simplified", th.BooleanType),
        th.Property("classic", th.StringType),
        th.Property("archived", th.BooleanType),
        th.Property("archivedDate", th.DateTimeType),
        th.Property(
            "archivedBy",
            th.ObjectType(
                th.Property("displayName", th.StringType),
                th.Property("self", th.StringType),
                th.Property("active", th.BooleanType),
                th.Property("accountId", th.StringType),
            ),
        ),
    ).to_dict()

    def get_records(self, context: Optional[dict]) -> Iterable[dict]:
        """Return a generator of row-type dictionary objects."""
        for record in self.conn.projects():
            stage = record.raw
            stage["projectId"] = stage.pop("id")
            yield stage
