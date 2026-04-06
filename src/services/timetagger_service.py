"""Module for timetaggger integration"""

import time
from ulid import ULID

from models.data import ActiveTimer
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
        if settings.data.timetagger is None:
            self.settings.data.timetagger = {}
            self.settings.data.file_sync()
        self.data = self.settings.data.timetagger
        self.since = int(time.time())
        self.url = self.settings.config.timetagger_url + "/timetagger/api/v2"
        self.space_id = self.settings.config.task_space_id
        self.anytype = AnyTypeUtils()
        self.status_options = (
            self.settings.data.anytype["tasks"].props["Status"].options
        )

        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def generate_key(self):
        return str(ULID())

    def fetch_anytype_object(self, object_id: str):
        return self.anytype.get_object_by_id(self.space_id, object_id)

    def update_object(self, object_data, option_name: str):
        self.anytype.update_object(
            self.space_id,
            object_data["name"],
            object_data["id"],
            {
                "properties": [
                    {"key": "status", "select": self.status_options[option_name].id}
                ]
            },
        )

    def toggle(self, object_id: str):
        logger.info("Preparing timer update data")

        object_data = self.fetch_anytype_object(object_id)

        object_type = object_data["type"].lower()

        active = self.data.get(object_type)

        entries_to_update = []

        message: dict = {}

        new_target: bool = True
        logger.info("Stopping current timer")
        if active is not None and active.anytype is not None:
            new_target = object_data["name"] != active.anytype["name"]
            self.update_object(active.anytype, "Ready")
            stopped_timer = self.record_builder(active.entry, False)
            entries_to_update.append(stopped_timer)
            message["⏹️Stopping"] = stopped_timer["ds"]
            self.data[object_type] = ActiveTimer()

        logger.info("Creating new timer:" + str(new_target))
        if new_target:
            self.update_object(object_data, "Doing")
            new_timer = self.record_builder(object_data, True)
            entries_to_update.append(new_timer)
            self.data[object_type] = ActiveTimer(anytype=object_data, entry=new_timer)
            message["▶️Starting"] = new_timer["ds"]

        self.settings.data.file_sync()

        records_url = self.url + "/records"
        make_call(
            "put",
            records_url,
            "updating timetagger timer",
            entries_to_update,
            "timetagger",
        )
        logger.info("Response candy")

        message["🔁Running"] = {
            object_type: self.data[object_type].anytype["name"]
            for object_type in self.data
            if self.data[object_type] and self.data[object_type].anytype
        }
        if object_type == "task" and new_target:
            message["🧠Recommended Stimuli"] = object_data["Focus"]

        return message

    def record_builder(self, entry: dict, start: bool):

        now_seconds = time.time()
        now_time = int(now_seconds)

        if start:
            tags = [
                entry["AoC"].lower(),
                entry["Project"].lower(),
                entry["type"].lower(),
            ]

            timer_data = {
                "ds": entry["name"] + " #" + " #".join(tags),
                "t1": now_time,
                "t2": now_time,
                "mt": now_time,
                "key": self.generate_key(),
            }
        else:
            timer_data = entry
            timer_data["t2"] = now_time
            timer_data["mt"] = now_time

        timer_data["st"] = 0.0
        TimeEntry(**timer_data)

        return timer_data
