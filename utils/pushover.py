"""Pushover utilities for sending notifications."""

import os
from dotenv import load_dotenv

from utils.api_tools import make_call

load_dotenv()

class Pushover:
    """Class to handle Overpush notifications."""
    def __init__(self):
        self.url = "https://api.pushover.net/1/messages.json"
        self.data = {
            "token": os.getenv("PUSHOVER_KEY"),
            "user": os.getenv("PUSHOVER_USER"),
            "html": 1
        }

    def send_message(self, title: str, message: str, priority: int = 0):
        """Send a message via Pushover.""" 
        data = self.data.copy()
        data["title"] = title
        data["priority"] = priority
        data["message"] = message

        make_call(
            "post",
            self.url,
            "send message via pushover",
            data
        )
