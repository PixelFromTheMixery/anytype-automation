"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta

from utils.anytype import AnyTypeUtils
from utils.config import Config
from utils.logger import logger
from utils.pushover import PushoverUtils


DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"
NO_TASKS = "No tasks to update"


class AnytypeService:
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
        self.data = Config.get()

    def search(self, search_detail, search_request: dict):
        """
        Searches a specified space according to type and query
        Default to task type
        """
        space_id = self.data["spaces"]["main"]
        search_body = {}
        if search_request.get("types") is not None:
            search_body["types"] = search_request["types"]

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
        return self.anytype.search(space_id, search_detail, search_body)

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

    def view_list(self, list_id: str):
        """Formats view objects into consumable objects to add to this object"""
        return self.anytype.get_views_list(list_id)

    def task_review_cleanup(self, task, data):
        """Updates tasks that have been left unattended"""
        if task["Status"] not in ["Blocked", "Review", "Later"]:
            new_count = task["Reset Count"] + 1
        data["properties"].append({"key": "reset_count", "number": new_count})

        return data

    def overdue(self, dt_now):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["main"],
            self.data["queries"]["automation"]["id"],
            self.data["queries"]["automation"]["overdue"],
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

            if self.data["settings"]["task_review_threshold"] > 0:
                data = self.task_review_cleanup(task, data)
                if task["Reset Count"] > self.data["settings"]["task_review_threshold"]:
                    data["properties"].append(
                        {
                            "key": "status",
                            "select": self.data["tags"]["main"]["status"]["review"],
                        }
                    )
                    tasks_to_review.append(task["name"])

            self.anytype.update_object(task["name"], task["id"], data)

        if tasks_to_review and self.data["settings"]["pushover"]:
            message = "The following tasks have been reset 5 times, please review:"
            for task in tasks_to_review:
                message += "<br>" + task
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def reflection_updates(self, dt_now):
        """Updates dates of completed reflections"""
        objs_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["archive"],
            self.data["queries"]["reflections"]["id"],
            self.data["queries"]["reflections"]["update"],
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
                    {
                        "key": "status",
                        "select": self.data["tags"]["archive"]["status"]["review"],
                    },
                    {"key": "rate", "text": new_tag},
                    {"key": "due_date", "date": new_day},
                ]
            }
            self.anytype.update_object(obj["name"], obj["id"], data)

    def daily_rollover(self):
        """Daily automation script"""
        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        logger.info("Running overdue tasks")
        self.overdue(dt_now)
        logger.info("Updating Reflections")
        self.reflection_updates(dt_now)
        logger.info("Daily Rollover completed")

    async def scan_spaces(self, props: list[str] = None):
        """Scan spaces and update self file"""
        pass

    def get_or_create_property(self, space_name, data):
        """Get or create a property in a given space."""
        try:
            return self.data["tags"][space_name][data["prop_key"]]
        except IndexError:
            prop_id = self.anytype.add_property(self.data["spaces"][space_name], data)
            self.data["tags"][space_name][data["prop_key"]]["id"] = prop_id
            self.data = Config.save()

    def get_or_create_tag(self, space_name, data):
        """Get or create a tag for a given property in archive."""
        try:
            return self.data["tags"][space_name][data["prop_key"]][data["tag_key"]]
        except KeyError:
            self.get_or_create_property(
                space_name,
                {
                    "format": data["format"],
                    "key": data["prop_key"],
                    "name": data["prop_name"],
                },
            )
        except IndexError:
            tag_id = self.anytype.add_tag_to_select_property(
                self.data["spaces"][space_name],
                data["prop_key"],
                data["tag_key"],
                data["value"],
            )
            self.data["tags"][space_name][data["prop_key"]][data["tag_key"]] = tag_id
            self.data = Config.save()

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
        # TODO Fix me
        data = {}
        data["type_key"] = "log"
        data["name"] = task["name"]
        props = [
            {"key": "do_d", "text": task["DoD"]},
            {
                "key": "function",
                "select": self.get_or_create_tag("Function", task["Function"]),
            },
            {
                "key": "points",
                "number": task["Points"],
            },
            {
                "key": "day_segment",
                "select": self.get_or_create_tag("Day Segment", task["Day Segment"]),
            },
            {
                "key": "project",
                "select": self.get_or_create_tag("Project", task["Project"][0]["name"]),
            },
        ]

        data["properties"] = props
        self.anytype.create_object(self.data["archive"]["id"], task["name"], data)

    def task_status_reset(self, task, dt_now):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if self.data["settings"]["task_logs"]:
            self.log_task_in_archive(task)

        if "Rate" not in task or task["Rate"] == "":
            self.anytype.delete_object(
                self.data["spaces"]["main"], task["name"], task["id"]
            )
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
                        "select": self.data["tags"]["main"]["status"]["repeating"],
                    },
                ]
            }
            self.anytype.update_object(
                self.data["spaces"]["main"], task["name"], task["id"], update_data
            )

    def recurrent_check(self):
        """Collect tasks for processing from completed view"""
        logger.info("Running completed task processing")
        tasks_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["main"],
            self.data["queries"]["automation"]["id"],
            self.data["queries"]["automation"]["complete"],
        )
        if not tasks_to_check:
            return NO_TASKS

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        for task in tasks_to_check:
            self.task_status_reset(task, dt_now)

    def test(self):
        """Temp endpoint for testing"""
        return self.anytype.test()

    def other(self):
        """Temp endpoint for offhand tasks"""
        tasks_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["main"],
            self.data["queries"]["automation"]["id"],
            self.data["queries"]["automation"]["other"],
        )

        for task in tasks_to_check:
            update_data = {
                "properties": [
                    {
                        "key": "status",
                        "select": self.data["tags"]["main"]["status"]["repeating"],
                    },
                ]
            }

            self.anytype.update_object(task["name"], task["id"], update_data)
        return "Completed with no issue"
