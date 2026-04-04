"""Module for timetaggger integration"""

import time
from ulid import ULID

from models.timetagger_models import TimeEntry

from utils.anytype import AnyTypeUtils
from utils.api_tools import make_call
from utils.pushover import PushoverUtils


class TimetaggerService:
    """
    Timetagger Services manages the current tasks:
    """

    def __init__(self, settings):
        self.settings = settings

        self.url = self.settings.config.timetagger_url + "/timetagger/api/v2"
        self.space_id = self.settings.config.task_space_id
        self.anytype = AnyTypeUtils()
        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def generate_key(self):
        return str(ULID())

    def current(self):
        timer_url = self.url + ""

    def toggle(self, object_id: str):
        records_url = self.url + "/records"

        object_data = self.anytype.get_object_by_id(self.space_id, object_id)

        timer_data = self.record_builder(object_data)

        make_call(
            "put", records_url, "start timetagger timer", timer_data, "timetagger"
        )

        return timer_data["ds"]

    def record_builder(
        self, object_data: dict, start_time: float = None, end_time: float = None
    ):

        tags = [
            object_data["AoC"].lower(),
            object_data["Project"].lower(),
            object_data["type"].lower(),
        ]

        now_time = int(time.time())

        timer_data = {
            "ds": object_data["name"] + " #" + " #".join(tags),
            "t1": start_time if start_time else now_time,
            "t2": end_time if end_time else now_time,
            "mt": now_time,
            "st": 0.0,
            "key": self.generate_key(),
        }

        TimeEntry(**timer_data)

        return timer_data
