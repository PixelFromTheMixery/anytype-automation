"""Mask Management module"""

from utils.anytype import AnyTypeUtils
from utils.date_tools import get_next_date, get_today, unpack_time
from utils.logger import logger
from utils.pushover import PushoverUtils


RESET = "Reset Count"


class TaskService:
    """For managing"""

    def __init__(self, settings, journal=None):
        self.settings = settings
        self.data = self.settings.data.anytype
        self.space_id = self.settings.config.task_space_id
        self.max_reset = self.settings.config.task_review_threshold
        self.anytype = AnyTypeUtils()
        if settings.config.pushover:
            self.pushover = PushoverUtils()
        if journal:
            self.journal = journal
        self.tmw_str = get_next_date("0-day")

    def set_ready(self):
        return {
            "key": "status",
            "select": self.data["tasks"].props["Status"].options["Ready"].id,
        }

    def recurrent_check(self):
        """Collect tasks for processing"""
        job_list = []
        if self.settings.config.task_reset:
            job_list.append("Shifted tasks")
            logger.info("Running task processing")
            tasks_to_check = self.anytype.get_list_view_objects(
                self.space_id,
                self.data["tasks"].queries["Automation"].id,
                self.data["tasks"].queries["Automation"].Done,
            )

            for task in tasks_to_check:
                next_date = None
                if task.get("Rate") not in ["", None]:
                    next_date = get_next_date(task["Rate"])

                self.task_status_reset(task, next_date)

        if self.settings.config.timetagger:
            job_list.append("Adding id to timers")
            logger.info("Running id injection for timer")
            objs_to_check = self.anytype.get_list_view_objects(
                self.space_id,
                self.data["tasks"].queries["Automation"].id,
                self.data["tasks"].queries["Automation"].Timer,
            )

            for obj in objs_to_check:
                update_data = {
                    "properties": [
                        {
                            "key": "timer",
                            "url": self.settings.config.api_addr
                            + "/timetagger/toggle_timer/"
                            + obj["id"],
                        },
                        self.set_ready(),
                    ]
                }
                self.anytype.update_object(
                    self.space_id, obj["name"], obj["id"], update_data
                )
        if self.settings.config.habit_logs:
            job_list.append("Adding id to habit url")
            logger.info("Running id injection for habit")
            habits_to_check = self.anytype.get_list_view_objects(
                self.space_id,
                self.data["tasks"].queries["Automation"].id,
                self.data["tasks"].queries["Automation"].Habits,
            )

            for habit in habits_to_check:
                update_data = {
                    "properties": [
                        {
                            "key": "url",
                            "url": self.settings.config.api_addr
                            + "/anytype/log_habit/"
                            + habit["id"],
                        },
                        self.set_ready(),
                    ]
                }
                self.anytype.update_object(
                    self.space_id, habit["name"], habit["id"], update_data
                )

        return "Task Check Jobs completed: " + ", ".join(job_list)

    def overdue(self):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            self.space_id,
            self.data["tasks"].queries["Automation"].id,
            self.data["tasks"].queries["Automation"].Overdue,
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"

        for task in tasks_to_check:
            new_due: str
            if "@" in task["Rate"]:
                hour, minute = unpack_time(task["Rate"].split("@")[1])
                new_due = get_today([hour, minute], True)
            else:
                new_due = get_today(string=True)
            data = {"properties": [{"key": "due_date", "date": new_due}]}
            if self.max_reset > 0:
                data = self.max_reset_cap(task, data)

            self.anytype.update_object(self.space_id, task["name"], task["id"], data)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def max_reset_cap(self, task: dict, data: dict):
        new_count = task[RESET] + 1 if RESET in task else 1
        data["properties"].append({"key": "reset_count", "number": new_count})

        if new_count >= self.max_reset:
            if self.settings.journal_space_id != "":
                self.journal.review_overflow(task, self.space_id)

            data["properties"].append(
                {
                    "key": "status",
                    "select": self.data["tasks"].props["Status"].options["Blocked"].id,
                }
            )
            data["properties"][0]["date"] = None
        else:
            data["properties"].append(self.set_ready())

        return data

    def task_status_reset(self, task, next_date):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if next_date is None:
            self.anytype.delete_object(self.space_id, task["name"], task["id"])
        else:
            update_data = {
                "properties": [{"key": "due_date", "date": next_date}, self.set_ready()]
            }
            if task["Status"] == "Skipped" and self.max_reset > 0:
                update_data = self.max_reset_cap(task, update_data)
                new_due: str = ""
                if "@" in task["Rate"]:
                    due_time = task["Rate"].split("@")[1]
                    new_due = get_next_date("1-day@" + due_time)

                update_data["properties"].append(
                    {
                        "key": "due_date",
                        "date": new_due if new_due != "" else self.tmw_str,
                    }
                )
            elif task["Status"] == "Done" and RESET in task:
                update_data["properties"].append(
                    {"key": "due_date", "date": next_date},
                )
                update_data["properties"].append(
                    {"key": "reset_count", "number": 0},
                )

            self.anytype.update_object(
                self.space_id, task["name"], task["id"], update_data
            )

        if self.settings.config.task_logs and task["Status"] == "Done":
            self.journal.log_object(task)
