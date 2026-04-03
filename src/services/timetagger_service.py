"""Module for timetaggger integration"""

from models.timetagger_models import TimeEntry

from utils.anytype import AnyTypeUtils
from utils.helper import Helper
from utils.logger import logger
from utils.pushover import PushoverUtils

class TimetaggerService:
    """
    Timetagger Services manages the current tasks:
    """
    def __init__(self, settings):
        self.settings = settings

        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        if settings.config.pushover():
            self.pushover = PushoverUtils()

    def toggle(self, object_id):
        pass
