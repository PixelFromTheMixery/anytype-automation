"""Module for handling automation behaviour"""

from utils.anytype import AnyTypeUtils
from utils.logger import logger
from utils.pushover import PushoverUtils


class AnytypeService:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """

    def __init__(self, settings, space_service, journal=None):
        self.settings = settings
        self.space = space_service
        if journal:
            self.journal = journal

        self.anytype = AnyTypeUtils()
        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def daily_rollover(self):
        """Daily automation script"""
        if self.settings.config.task_reset:
            logger.info("Running overdue tasks")
            self.task.overdue()
        logger.info("Daily Rollover completed")
