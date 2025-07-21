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
            "html": 1
        }

    def send_message(self, title: str, message: str, priority: int = 0, timestamp=None):
        """Send a message via Pushover.""" 
        data = self.data.copy()
        data["title"] = title
        data["priority"] = priority
        data["message"] = message
        if priority == 2:
            data["sound"] = "siren"
            data["retry"] = 30
            data["expire"] = 300
        if timestamp is not None:
            data["timestamp"] = timestamp
        make_call(
            "post",
            self.url,
            "send message via pushover",
            data
        )
