"""Pushover utilities for sending notifications."""

import os
from dotenv import load_dotenv

from utils.api_tools import make_call

load_dotenv()


class PushoverUtils:
    """Class to handle Overpush notifications."""

    def __init__(self):
        self.url = "https://api.pushover.net/1/messages.json"
        self.data = {
            "token": os.getenv("PUSHOVER_KEY"),
            "user": os.getenv("PUSHOVER_USER"),
            "html": 1,
        }

    def make_deeplink(self, object_id, space_id: str):
        """Builds deeplinks for link purposes"""
        return f"https://object.any.coop/{object_id}?spaceId={space_id}"

    def send_message(self, title: str, message: str, priority: int = 0, timestamp=None):
        """Send a message via Pushover."""
        data = self.data.copy()
        data["title"] = title
        data["priority"] = priority
        data["message"] = message
        data["ttl"] = 86400
        if priority == 2:
            data["sound"] = "siren"
            data["retry"] = 30
            data["expire"] = 300
        if timestamp is not None:
            data["timestamp"] = timestamp
        # fmt: off
        make_call(
            "post",
            self.url,
            "send message via pushover",
            data
        )
