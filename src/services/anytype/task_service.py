"""Mask Management module"""

from utils.anytype import AnyTypeUtils
from utils.helper import Helper
from utils.logger import logger
from utils.pushover import PushoverUtils


RESET = "Reset Count"


class TaskService:
    """For managing"""

    def __init__(self, settings, journal=None):
        self.settings = settings
        self.data = self.settings.data.anytype
        self.space_id = self.settings.config.task_space_id
        self.anytype = AnyTypeUtils()
        if settings.config.pushover:
            self.pushover = PushoverUtils()
        if journal:
            self.journal = journal
        self.helper = Helper()

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
                    next_date = self.helper.next_date(task["Rate"])

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

    def overdue(self, dt_next_str):
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

        tasks_to_review = []

        for task in tasks_to_check:
            data = {"properties": []}

            data["properties"].append({"key": "due_date", "date": dt_next_str})

            if self.settings.config.task_review_threshold > 0:
                data = self.task_review_cleanup(task, data)

            if task[RESET] > self.settings.config.task_review_threshold - 1:
                self.review_overflow(task)
                data["properties"].append(
                    {
                        "key": "status",
                        "select": self.data["tasks"]
                        .props["Status"]
                        .options["Review"]
                        .id,
                    }
                )
                tasks_to_review.append(task["name"])

            self.anytype.update_object(self.space_id, task["name"], task["id"], data)

        if (
            len(tasks_to_check) - len(tasks_to_review) > 15
            and self.settings.config.pushover
        ):
            self.pushover.send_message(
                "Loads of tasks incoming",
                f"There are {len(tasks_to_check)} incoming. Please have a gentle day.",
                1,
            )

        if tasks_to_review and self.settings.config.pushover:
            message = (
                f"{len(tasks_to_review)} tasks have been reset 5 times. Please review "
            )
            message += "<a href="
            message += self.helper.make_deeplink(
                self.data["journal"].id,
                "bafyreigcem27rencgalo2mtmkvxaet5cdrq6yagyin32cjpyy4ttkufcde",
            )
            message += ">your Journal space.<a/>"
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    # TODO: Move this to journal service?
    def review_overflow(
        self,
        task,
    ):
        self.anytype.create_object(
            self.data["journal"].id,
            {
                "template_id": self.data["journal"]
                .types["Prompt"]
                .templates["Task Review"],
                "name": task["name"],
                "type_key": "prompt",
                "properties": [
                    {
                        "key": "url",
                        "url": self.helper.make_deeplink(self.space_id, task["id"]),
                    }
                ],
            },
        )

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
        if next_date is None:
            self.anytype.delete_object(self.space_id, task["name"], task["id"])
        else:
            update_data = {
                "properties": [
                    {"key": "due_date", "date": next_date},
                    {
                        "key": "status",
                        "select": self.data["tasks"]
                        .props["Status"]
                        .options["Repeating"]
                        .id,
                    },
                ]
            }
            if task["Status"] == "Skipped":
                if task[RESET] > self.settings.config.task_review_threshold - 1:
                    self.review_overflow(task)
                    update_data["properties"].append(
                        {
                            "key": "status",
                            "select": self.data["tasks"]
                            .props["Status"]
                            .options["Review"]
                            .id,
                        }
                    )

                update_data["properties"].append(
                    {
                        "key": "reset_count",
                        "number": (
                            0 if task["Status"] == "Done" else task["Reset Count"] + 1
                        ),
                    }
                )

            self.anytype.update_object(
                self.space_id, task["name"], task["id"], update_data
            )

        if self.settings.config.task_logs and task["Status"] == "Done":
            self.journal.log_object(task)
