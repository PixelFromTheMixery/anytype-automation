"""Notification service for Anytype."""

from utils.anytype import AnyTypeUtils
from utils.config import config
from utils.logger import logger
from utils.pushover import Pushover

class AnytypeNotification:
    """Handles notifications for Anytype."""
    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = Pushover()

    def send_notification(self, message: )