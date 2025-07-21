"""Notification service for Anytype."""

from utils.anytype import AnyTypeUtils
# from utils.config import config
# from utils.logger import logger
from utils.pushover import PushoverUtils


class AnytypeAlert:
    """Handles notifications for Anytype."""
    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = PushoverUtils()

    def create_object_and_notify(self):
        pass
