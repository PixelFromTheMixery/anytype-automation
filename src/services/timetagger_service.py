"""Module for timetaggger integration"""

from models.timetagger_models import TimeEntry

from utils.anytype import AnyTypeUtils
from utils.api_tools import make_call
from utils.logger import logger
from utils.pushover import PushoverUtils


class TimetaggerService:
    """
    Timetagger Services manages the current tasks:
    """

    def __init__(self, settings):
        self.settings = settings

        self.url = self.settings.config.timetagger_url + "/timetagger/api/v2"
        self.anytype = AnyTypeUtils()
        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def toggle(self, object_id):
        test_url = self.url + "/settings"
        return make_call("get", test_url, "get timetagger data", None, "timetagger")
