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
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

    def search(self, search_critera: str, obj: bool = True, search_filter: str = ""):
        """Conducts a search with provided data"""
        return self.anytype.search_by_type_and_or_name(
            search_critera, obj, search_filter
        )

    def next_date(self, date: datetime.datetime, timescale: str, freq: int):
        """Returns formatted string of the next date based on the timescale provided"""
        day_int = -1
        if timescale in self.converter:
            day_int = self.converter[timescale]
        dt_next = datetime.datetime
        if timescale == "Day":
            dt_next =  date + relativedelta(days=freq)
        elif timescale == "Week":
            dt_next =  date + relativedelta(weeks=freq)
        elif timescale == "Month":
            dt_next =  date + relativedelta(months=freq)
        elif timescale == "Year":
            dt_next = date + relativedelta(years=freq)
        elif timescale == "Weekday":
            dt_next = date + datetime.timedelta(days=freq)
            while dt_next.weekday() >= 5:
                dt_next += datetime.timedelta(days=freq)
        elif timescale == "Weekend":
            dt_next = date + datetime.timedelta(days=freq)
            while dt_next.weekday() < 5:
                dt_next += datetime.timedelta(days=freq)
        else:
            dt_next = date + relativedelta(days=1)
            dt_next = dt_next + relativedelta(weekday=weekday(day_int)(+freq))

        return dt_next.strftime(DATETIME_FORMAT)

    def view_list(self, list_id: str = config["queries"]["automation"]):
        """Formats view objects into consumable objects to add to this object"""
        return self.anytype.get_views_list(list_id)

    def task_review_cleanup(self, task, data):
        """Updates tasks that have been left unattended"""
        
        if "Reset Count" not in task:
            task["Reset Count"] = 0
        elif task["Status"] != "Blocked":
            task["Reset Count"] = task["Reset Count"] + 1

        if task["Rate"] != "Once" and "Frequency" not in task.keys():
            task["Frequency"] = 1

        data["properties"].append(
            {"key": "reset_count", "number": task["Reset Count"]}
        )
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
            config["views"]["reflect"]["placeholder"], "full"
        )
        for obj in objs_to_check:
            data = {
                "type_key": "reflection",
                "name": obj["name"],
                "properties": [
                    {"key": "due_date", "date": dt_now.strftime(DATETIME_FORMAT)}
                ],
            }

            if obj["Project"][0]["name"] == "Cleaning":
                data["template_id"] = config["templates"]["reflection"]["cleaning"]
            else:
                data["template_id"] = config["templates"]["reflection"]["regular"]

            if obj["Rate"] != "Once":
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
            config["views"]["reflect"]["to_adjust"],
            list_id=config["queries"]["reflect"],
        )
        for obj in objs_to_check:
            new_tag = obj["Rate"]
            new_day = dt_now

            if obj["Rate"] == "Day":
                new_tag = config["tags"]["rate"]["week"]
                new_day = self.next_date(dt_now, "Week", 1)
            elif obj["Rate"] == "Week":
                new_tag = config["tags"]["rate"]["month"]
                new_day = self.next_date(dt_now, "Month", 1)
            elif obj["Rate"] == "Month":
                new_tag = config["tags"]["rate"]["quarter"]
                new_day = self.next_date(dt_now, "Month", 3)
            elif obj["Rate"] == "Quarter":
                if "Repeating Task" in obj:
                    new_tag = config["tags"]["rate"]["quarter"]
                    new_day = self.next_date(dt_now, "Month", 3)
                else:
                    new_tag = config["tags"]["rate"]["year"]
                    new_day = self.next_date(dt_now, "Year", 1)
            elif "Year" in obj["Rate"]:
                new_day = self.next_date(dt_now, "Year", 1)
            data = {
                "properties": [
                    {"key": "status", "select": config["tags"]["status"]["review"]},
                    {"key": "rate", "select": new_tag},
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
        self.anytype.create_object(
            config["spaces"]["archive"], task["name"], data
        )


    def task_status_reset(self, task, dt_now):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if config["settings"]["archive"]:
            self.log_task_in_archive(task)

        if task.get("Rate") == "Once":
            self.anytype.delete_object(task["name"], task["id"])
        else:
            update_data = {
                "properties": [
                    {
                        "key": "due_date",
                        "date": self.next_date(
                            dt_now,
                            task["Rate"],
                            task.get("Frequency", 1),
                        ),
                    },
                    {"key": "reset_count", "number": 0},
                    {
                        "key": "status",
                        "select": config["tags"]["status"]["repeating"],
                    },
                ]
            }
            self.anytype.update_object(
                task["name"], task["id"], update_data
            )



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
                # TODO Check if this is still needed
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

        return "Completed with no issue"
