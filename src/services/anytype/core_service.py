"""Module for handling automation behaviour"""

from utils.anytype import AnyTypeUtils
from utils.helper import Helper
from utils.logger import logger
from utils.pushover import PushoverUtils


class AnytypeService:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """

    def __init__(self, settings, task_service, space_service):
        self.settings = settings
        self.task = task_service
        self.space = space_service

        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def daily_rollover(self):
        """Daily automation script"""
        dt_tmw_str = self.helper.next_date("1@day")
        if self.settings.config.task_reset:
            logger.info("Running overdue tasks")
            self.task.overdue(dt_tmw_str)
        logger.info("Daily Rollover completed")
