"""Module for timetaggger integration"""

import time
from ulid import ULID

from models.data import TimetaggerPersistent
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
        if settings.data.timetagger is None:
            self.settings.data.timetagger = TimetaggerPersistent()
            self.settings.data.file_sync()
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

    def changes(self):
        updates_url = self.url + "/updates?since=" + str(self.since)

        update_data = make_call(
            "get", updates_url, "get recent updates", None, "timetagger"
        )

        for record in update_data["records"]:
            if "#task" in record["ds"]:
                self.settings.data.timetagger.running_task = record
            if "#state" in record["ds"]:
                self.settings.data.timetagger.running_state = record
        self.settings.data.file_sync()

        self.since = update_data["server_time"]

    def toggle(self, object_id: str):
        records_url = self.url + "/records"

        self.changes()

        object_data = self.anytype.get_object_by_id(self.space_id, object_id)

        message = ""

        entries_to_update = []
        old_entry = {"ds": ""}

        if (
            object_data["type"] == "Task"
            and self.settings.data.timetagger.running_task is not None
        ):
            old_entry = self.record_builder(
                TimeEntry(**self.settings.data.timetagger.running_task)
            )
            entries_to_update.append(old_entry)
        elif (
            object_data["type"] == "State"
            and self.settings.data.timetagger.running_state is not None
        ):
            old_entry = self.record_builder(
                TimeEntry(**self.settings.data.timetagger.running_state)
            )
            entries_to_update.append(old_entry)

        if object_data["name"] not in old_entry["ds"]:
            new_timer = self.record_builder(object_data)
            message += "Starting " + new_timer["ds"]
            entries_to_update.append(new_timer)
            if object_data["type"] == "Task":
                message += ", recommendation: " + object_data["Focus"]
            self.anytype.update_object(
                self.space_id,
                object_data["name"],
                object_data["id"],
                {
                    "properties": [
                        {"key": "status", "select": self.status_options["Doing"].id}
                    ]
                },
            )

        else:
            message += "Stopping " + old_entry["ds"]
            if "task" in message:
                self.settings.data.timetagger.running_task = None
            else:
                self.settings.data.timetagger.running_state = None
            self.settings.data.file_sync()

            self.anytype.update_object(
                self.space_id,
                object_data["name"],
                object_data["id"],
                {
                    "properties": [
                        {"key": "status", "select": self.status_options["Ready"].id}
                    ]
                },
            )

        make_call(
            "put",
            records_url,
            "start timetagger timer",
            entries_to_update,
            "timetagger",
        )

        return message

    def record_builder(self, entry: TimeEntry | dict):

        now_seconds = time.time()
        now_time = int(now_seconds)

        if isinstance(entry, dict):
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
            timer_data = entry.model_dump()
            timer_data["t2"] = now_time
            timer_data["mt"] = self.since

        timer_data["st"] = 0.0
        TimeEntry(**timer_data)

        return timer_data
