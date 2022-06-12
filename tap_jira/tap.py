"""Jira tap class."""

from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_jira.streams import (
    JiraStream,
    ProjectsStream,
    IssuesStream,
    UsersStream,
)

STREAM_TYPES = [
    ProjectsStream,
    IssuesStream,
    UsersStream,
]


class TapJira(Tap):
    """Jira tap class."""

    name = "tap-jira"

    # TODO: Update this section with the actual config values you expect:
    config_jsonschema = th.PropertiesList(
        th.Property(
            "base_url",
            th.StringType,
            default="https://jira.atlassian.com",
            description="The url for your JIRA instance",
        ),
        th.Property(
            "username",
            th.StringType,
            required=True,
            description="JIRA user to authenticate with",
        ),
        th.Property(
            "password",
            th.StringType,
            required=True,
            description="Jira user API token",
        ),
        th.Property(
            "start_date",
            th.DateType,
            description="The earliest record date to sync for Issues",
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]
