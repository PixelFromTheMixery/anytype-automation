"""Mask Management module"""

import json
import urllib.parse

from utils.anytype import AnyTypeUtils
from utils.config import Config
from utils.data import DataManager
from utils.helper import Helper
from utils.logger import logger
from utils.pushover import PushoverUtils

DATA = DataManager.get()
RESET = "Reset Count"


class TaskService:
    """For managing"""

    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = PushoverUtils()
        self.helper = Helper()

    def recurrent_check(self):
        """Collect tasks for processing"""
        job_list = []
        if Config.data["task_reset"]:
            job_list.append("Complete Tasks")
            logger.info("Running task processing")
            tasks_to_check = self.anytype.get_list_view_objects(
                DATA.root["tasks"].id,
                DATA.root["tasks"].queries["Automation"].id,
                DATA.root["tasks"].queries["Automation"].Done,
            )

            for task in tasks_to_check:

                next_date = (
                    self.helper.next_date(task["Rate"])
                    if "Rate" in task.keys()
                    else None
                )

                self.task_status_reset(task, next_date)
        if Config.data["toggl"]:
            job_list.append("Toggle URL")
            new_tasks = self.anytype.get_list_view_objects(
                DATA.root["tasks"].id,
                DATA.root["tasks"].queries["Automation"].id,
                DATA.root["tasks"].queries["Automation"].New,
            )

            for task in new_tasks:
                build_url = Config.data["api_addr"] + urllib.parse.quote(
                    "/toggl/" + f"{task["Mission"]}/{task["name"]}/" + "start_timer"
                )
                data = {
                    "properties": [
                        {
                            "key": "status",
                            "select": DATA.root["tasks"]
                            .props["Status"]
                            .options["Ready"]
                            .id,
                        },
                        {"key": "timer", "url": build_url},
                    ]
                }
                self.anytype.update_object(
                    DATA.root["tasks"].id, task["name"], task["id"], data
                )

        return "Task Check Jobs completed: " + ", ".join(job_list)

    def overdue(self, dt_next_str):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            DATA.root["tasks"].id,
            DATA.root["tasks"].queries["Automation"].id,
            DATA.root["tasks"].queries["Automation"].Overdue,
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"

        tasks_to_review = []

        for task in tasks_to_check:
            data = {"properties": []}

            data["properties"].append({"key": "due_date", "date": dt_next_str})

            if Config.data["task_review_threshold"] > 0:
                data = self.task_review_cleanup(task, data)

                if task[RESET] > Config.data["task_review_threshold"] - 1:
                    self.anytype.create_object(
                        DATA.root["journal"].id,
                        {
                            # fmt: off
                            "template_id": DATA.root[
                                "journal"].types["Prompt"].templates["Task Review"
                            ],
                            "name": task["name"],
                            "type_key": "prompt",
                            "properties": [
                                {
                                    "key": "url",
                                    "url": self.helper.make_deeplink(
                                        DATA.root["tasks"].id, task["id"]
                                    ),
                                }
                            ],
                        },
                    )
                    data["properties"].append(
                        {
                            "key": "status",
                            # fmt: off
                            "select": DATA.root["tasks"].props["Status"].options["Review"].id,
                        }
                    )
                    tasks_to_review.append(task["name"])

            self.anytype.update_object(
                DATA.root["tasks"].id, task["name"], task["id"], data
            )

        if len(tasks_to_check) - len(tasks_to_review) > 15 and Config.data["pushover"]:
            self.pushover.send_message(
                "Loads of tasks incoming",
                f"There are {len(tasks_to_check)} incoming. Please have a gentle day.",
                1,
            )

        if tasks_to_review and Config.data["pushover"]:
            message = (
                f"{len(tasks_to_review)} tasks have been reset 5 times. Please review "
            )
            message += "<a href="
            message += self.helper.make_deeplink(
                DATA.root["journal"].id,
                "bafyreigcem27rencgalo2mtmkvxaet5cdrq6yagyin32cjpyy4ttkufcde",
            )
            message += ">your Journal space.<a/>"
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def log_task_in_archive(self, task):
        """
        Define log object for archival
        """
        data = {
            "type_key": "log",
            "name": task["name"],
            "properties": [],
        }

        metadata_dict = {}
        sorting = Config.data["task_log_props"]
        for prop in task:
            if prop not in sorting:
                continue
            metadata_dict[prop] = task[prop]
        sorted_data = {k: metadata_dict[k] for k in sorting}
        data["properties"].append({"key": "metadata", "text": json.dumps(sorted_data)})
        self.anytype.create_object(DATA.root["journal"].id, data)

    def task_review_cleanup(self, task, data):
        """Updates tasks that have been left unattended"""
        new_count = 0
        if RESET not in task.keys():
            task[RESET] = 0
        if task["Status"] not in ["Blocked", "Review", "Later"]:
            new_count = task[RESET] + 1
        data["properties"].append({"key": "reset_count", "number": new_count})

        return data

    def task_status_reset(self, task, next_date):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if Config.data["task_logs"]:
            self.log_task_in_archive(task)

        if next_date is None:
            self.anytype.delete_object(DATA.root["tasks"].id, task["name"], task["id"])
        else:
            update_data = {
                "properties": [
                    {"key": "due_date", "date": next_date},
                    {"key": "reset_count", "number": 0},
                    {
                        "key": "status",
                        # fmt: off
                        "select": DATA.root["tasks"].props["Status"].options["Repeating"].id,
                    },
                ]
            }
            self.anytype.update_object(
                DATA.root["tasks"].id, task["name"], task["id"], update_data
            )
