"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta, weekday

from utils.anytype import AnyTypeUtils
from utils.config import config, archive_log, load_archive_logging, save_archive_logging
from utils.logger import logger
from utils.pushover import PushoverUtils


DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NO_TASKS = "No tasks to update"


class AnytypeAutomation:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """

    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = PushoverUtils()
        self.converter = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }

    def search(self, search_detail, search_request: dict):
        search_body = {"types": search_request["types"]}

        if search_request.get("query") is not None:
            search_body["query"] = search_request["query"]

        """
        This is just not working at the moment
        if search_request.get("filters") is not None:
            search_body["filters"] = {"operator": "and", "conditions": []}
            search_body["filters"]["conditions"].append(
                {"checkbox": True, "condition": "nempty", "property_key": "urgent"},
            )

                    for condition in search_request["filters"]:
                        search_body["filters"]["conditions"].append(
                            {
                                "condition": "nempty",
                                **condition,
                            }
                        )
        """
        return self.anytype.search(search_detail, search_body)

    def date_eligibility(self, unit, modifier=None):
        """Returns list of eligible values for days of the week"""

        if unit in ["month", "quarter", "year"]:
            allowed = [0, 1, 2, 3, 4, 5, 6]
        elif unit == "week" and modifier:
            allowed = [self.converter[d] for d in modifier.split(",")]
        elif unit == "weekday":
            allowed = [0, 1, 2, 3, 4]
        elif unit == "weekend":
            allowed = [5, 6]
        else:
            allowed = [self.converter.get(unit)]

        return allowed

    def next_date(self, date: datetime.datetime, rate: str):
        """
        Returns formatted string of the next date based on the timescale provided
        n@unit:modifier
        Currently supported units:
        days of the week - 1@week:mon,thu
        day of the month - 1@month:15
        """
        n, unit = rate.split("@")
        n = int(n)
        modifier = None
        if ":" in unit:
            unit, modifier = unit.split(":", 1)
            if unit in ["month", "year"]:
                modifier = int(modifier)

        allowed = self.date_eligibility(unit, modifier)

        delta_map = {
            "day": lambda d, n: d + relativedelta(days=n),
            "week": lambda d, n: d + relativedelta(weeks=n),
            "month": lambda d, n, m=None: (
                d + relativedelta(months=n, day=m) if m else d + relativedelta(months=n)
            ),
            "quarter": lambda d, n: d + relativedelta(months=n * 3),
            "year": lambda d, n: d + relativedelta(years=n),
        }
        dt_next = delta_map.get(unit, lambda d, n: d + relativedelta(days=n))(date, n)

        while dt_next.weekday() not in allowed:
            dt_next += datetime.timedelta(days=1)

        return dt_next.strftime(DATETIME_FORMAT)

    def view_list(self, list_id: str = config["queries"]["automation"]):
        """Formats view objects into consumable objects to add to this object"""
        return self.anytype.get_views_list(list_id)

    def task_review_cleanup(self, task, data):
        """Updates tasks that have been left unattended"""

        if "Reset Count" not in task:
            task["Reset Count"] = 0
        elif task["Status"] not in ["Blocked", "Review"]:
            task["Reset Count"] = task["Reset Count"] + 1
        data["properties"].append({"key": "reset_count", "number": task["Reset Count"]})
        return data

    def overdue(self, dt_now):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["overdue"],
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return NO_TASKS

        dt_next = dt_now + datetime.timedelta(days=1)

        if len(tasks_to_check) > 15:
            self.pushover.send_message(
                "Loads of tasks incoming",
                f"There are {len(tasks_to_check)} incoming. Please have a gentle day.",
                1,
            )

        tasks_to_review = []

        for task in tasks_to_check:
            data = {"properties": []}

            data["properties"].append(
                {"key": "due_date", "date": dt_next.strftime(DATETIME_FORMAT)}
            )

            if config["settings"]["review_threshold"] > 0:
                data = self.task_review_cleanup(task, data)
                if task["Reset Count"] > config["settings"]["review_threshold"]:
                    data["properties"].append(
                        {"key": "status", "select": config["tags"]["status"]["review"]}
                    )
                    tasks_to_review.append(task["name"])

            self.anytype.update_object(task["name"], task["id"], data)

        if tasks_to_review:
            message = "The following tasks have been reset 5 times, please review:"
            for task in tasks_to_review:
                message += "<br>" + task
            url = self.pushover.make_deeplink(
                config["queries"]["task_cleanup"], config["spaces"]["main"]
            )
            message += f"<br><a href={url}>Link here</a>"
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def set_collections(self):
        """Assigns collection to task based on project"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["aoc"], "full"
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            logger.info(NO_TASKS)
            return None

        for task in tasks_to_check:
            aoc = config["AoC"].get(task["Project"][0]["name"][-3:])
            self.anytype.add_to_list(aoc, config["collections"][aoc], [task["id"]])

    def set_reflection(self, dt_now):
        """Sets review obj for task"""
        objs_to_check = self.anytype.get_list_view_objects(
            config["views"]["reflect_prop"]["placeholder"],
            "full",
            config["queries"]["reflect_prop"],
        )
        for obj in objs_to_check:
            data = {
                "type_key": "reflection",
                "name": obj["name"],
                "properties": [
                    {"key": "due_date", "date": dt_now.strftime(DATETIME_FORMAT)}
                ],
            }

            if "Project" in obj and obj["Project"][0]["name"] == "Cleaning":
                data["template_id"] = config["templates"]["reflection"]["cleaning"]
            else:
                data["template_id"] = config["templates"]["reflection"]["regular"]

            if "Rate" in obj and obj["Rate"] != "":
                data["properties"].append({"key": "repeating_task", "checkbox": True})

            reflection = self.anytype.create_object(
                config["spaces"]["main"], "reflection", data
            )

            if reflection is None:
                logger.error("Can't find created reflection object")
                break

            data = {}
            data = {
                "properties": [
                    {"key": "reflection", "objects": [reflection["object"]["id"]]}
                ]
            }
            self.anytype.update_object(obj["name"], obj["id"], data)

    def reflection_updates(self, dt_now):
        """Updates dates of completed reflections"""
        objs_to_check = self.anytype.get_list_view_objects(
            config["views"]["reflect_object"]["to_adjust"],
            list_id=config["queries"]["reflect_object"],
        )
        for obj in objs_to_check:
            today_day = dt_now

            if "Rate" not in obj or obj["Rate"] == "":
                new_tag = "1@day"
            elif obj["Rate"] == "1@day":
                new_tag = "1@week"
            elif obj["Rate"] == "Week":
                new_tag = "1@month"
            elif obj["Rate"] == "Month":
                new_tag = "1@quarter"
            elif obj["Rate"] == "Quarter" and "Repeating Task" not in obj:
                new_tag = "1@year"

            new_day = self.next_date(today_day, new_tag)

            data = {
                "properties": [
                    {"key": "status", "select": config["tags"]["status"]["review"]},
                    {"key": "rate", "text": new_tag},
                    {"key": "due_date", "date": new_day},
                ]
            }
            self.anytype.update_object(obj["name"], obj["id"], data)

    def daily_rollover(self):
        """Daily automation script"""
        logger.info("Running missing collections")
        self.set_collections()

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        logger.info("Running overdue tasks")
        self.overdue(dt_now)
        logger.info("Setting reflections")
        self.set_reflection(dt_now)
        logger.info("Updating Reflections")
        self.reflection_updates(dt_now)
        logger.info("Daily Rollover completed")

    def get_or_create_archive_tag(self, prop_name, value):
        """Get or create a tag for a given property in archive_log."""
        try:
            return archive_log[prop_name][value]
        except (KeyError, IndexError):
            tag_id = self.anytype.add_option_to_property(
                config["spaces"]["archive"],
                archive_log[prop_name]["id"],
                prop_name,
                value,
            )
            archive_log[prop_name][value] = tag_id
            save_archive_logging(archive_log)
            load_archive_logging()
            return tag_id

    def log_task_in_archive(self, task):
        """
        Define log object for archival
        Currently supported properties:
        - Defintion of Done (Text)
        - Function (Select)
        - Points (Number)
        - Day Segment (Select)
        - Project (Select)
        - Area of Concern (Select)

        """
        data = {}
        data["type_key"] = "log"
        data["name"] = task["name"]
        props = [
            {"key": "do_d", "text": task["DoD"]},
            {
                "key": "function",
                "select": self.get_or_create_archive_tag("Function", task["Function"]),
            },
            {
                "key": "points",
                "number": task["Points"],
            },
            {
                "key": "day_segment",
                "select": self.get_or_create_archive_tag(
                    "Day Segment", task["Day Segment"]
                ),
            },
            {
                "key": "project",
                "select": self.get_or_create_archive_tag(
                    "Project", task["Project"][0]["name"]
                ),
            },
        ]

        data["properties"] = props
        self.anytype.create_object(config["spaces"]["archive"], task["name"], data)

    def task_status_reset(self, task, dt_now):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if config["settings"]["archive"]:
            self.log_task_in_archive(task)

        if "Rate" not in task or task["Rate"] == "":
            if task["Reflection"][0]["name"] != "Placeholder":
                self.anytype.delete_object(
                    "Reflection for " + task["name"], task["Reflection"][0]["id"]
                )
            self.anytype.delete_object(task["name"], task["id"])
        else:
            update_data = {
                "properties": [
                    {
                        "key": "due_date",
                        "date": self.next_date(
                            dt_now,
                            task["Rate"],
                        ),
                    },
                    {"key": "reset_count", "number": 0},
                    {
                        "key": "status",
                        "select": config["tags"]["status"]["repeating"],
                    },
                ]
            }
            self.anytype.update_object(task["name"], task["id"], update_data)

    def recurrent_check(self):
        """Collect tasks for processing from completed view"""
        logger.info("Running completed task processing")
        max_retries = 2
        for _ in range(max_retries):
            tasks_to_check = self.anytype.get_list_view_objects(
                config["views"]["automation"]["complete"], "full"
            )
            if not tasks_to_check:
                return NO_TASKS

            dt_now = datetime.datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            for task in tasks_to_check:
                try:
                    [
                        link["name"]
                        for link in task["Backlinks"]
                        if link
                        in [
                            "Care",
                            "Finance",
                            "Home",
                            "Management",
                            "Workshop",
                        ]
                    ]
                except TypeError:
                    self.set_collections()
                self.task_status_reset(task, dt_now)
                break
            else:
                return "Failed to heal after retries"

    def test(self):
        """Temp endpoint for testing"""
        return self.anytype.test()

    def other(self):
        """Temp endpoint for offhand tasks"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["all"],
            list_id=config["queries"]["automation"],
        )

        for task in tasks_to_check:
            update_data = {
                "properties": [
                    {"key": "status", "select": config["tags"]["status"]["repeating"]},
                ]
            }

            self.anytype.update_object(task["name"], task["id"], update_data)
        return "Completed with no issue"
