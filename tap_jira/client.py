"""REST client handling, including JiraStream base class."""
from datetime import datetime, date
from pathlib import Path
from typing import Union

import jira
from singer_sdk.streams import Stream
from singer_sdk.tap_base import Tap


class JiraStream(Stream):
    """Jira stream class."""

    def __init__(self, tap: Tap):
        super().__init__(tap)
        self.conn = jira.JIRA(
            server=self.config.get("api_url", "https://jira.atlassian.com"),
            basic_auth=(self.config["username"], self.config["password"]),
        )
        parsed_date: Union[str, date] = self.config.get("start_date", "1970-01-01")
        if isinstance(parsed_date, str):
            self.start_date = datetime.strptime(parsed_date[:10], "%Y-%m-%d").date()
        else:
            self.start_date = parsed_date
