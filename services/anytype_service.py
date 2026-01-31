"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta

from utils.anytype import AnyTypeUtils
from utils.config import Config
from utils.data import DataManager
from utils.helper import make_deeplink
from utils.logger import logger
from utils.pushover import PushoverUtils


DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"
NO_TASKS = "No tasks to update"
DATA = DataManager.get()


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

    def search(self, search_request: dict):
        """
        Searches a specified space according to type and query
        Default to task type
        """
        space_id = DATA["spaces"].get(search_request["space_name"])
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
        return self.anytype.search(space_id, search_request["search_name"], search_body)

    def fetch_data(self, data):
        space_id = DATA["spaces"].get(data["space_name"])
        if data["category"] == "types":
            fetched = self.anytype.get_types(space_id)
        if data["category"] == "templates":

            fetched = self.anytype.get_templates(
                space_id, DATA["types"][data["space_name"]][data["type_name"]]
            )
        return fetched

    def date_eligibility(self, unit, modifier=None):
        """Returns list of eligible values for days of the week"""

        if unit in ["day", "week", "month", "quarter", "year"]:
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

    def view_list(self, space_name: str, query_name: str):
        """Formats view objects into consumable objects to add to this object"""
        space_id = DATA["spaces"].get(space_name)
        try:
            query_id = DATA["queries"][query_name]["id"]
        except KeyError as exc:
            raise KeyError(
                "query not found in config, "
                "check if space or query name and that query has automation checkbox ticked"
            ) from exc
        return self.anytype.get_views_list(space_id, query_id)

    def task_review_cleanup(self, task, data):
        """Updates tasks that have been left unattended"""
        if task["Status"] not in ["Blocked", "Review", "Later"]:
            new_count = task["Reset Count"] + 1
        data["properties"].append({"key": "reset_count", "number": new_count})

        return data

    def overdue(self, dt_now):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            DATA["spaces"]["tasks"],
            DATA["queries"]["automation"]["id"],
            DATA["queries"]["automation"]["overdue"],
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return NO_TASKS

        dt_next = dt_now + datetime.timedelta(days=1)

        tasks_to_review = []

        for task in tasks_to_check:
            data = {"properties": []}

            data["properties"].append(
                {"key": "due_date", "date": dt_next.strftime(DATETIME_FORMAT)}
            )

            if DATA["config"]["task_review_threshold"] > 0:
                data = self.task_review_cleanup(task, data)
                if task["Reset Count"] > DATA["config"]["task_review_threshold"] - 1:
                    self.anytype.create_object(
                        DATA["spaces"]["journal"],
                        {
                            "template_id": DATA["templates"]["journal"]["prompt"][
                                "Task Review"
                            ],
                            "name": task["name"],
                            "type_key": "prompt",
                            "properties": [
                                {
                                    "key": "url",
                                    "url": make_deeplink(
                                        DATA["spaces"]["tasks"], task["id"]
                                    ),
                                }
                            ],
                        },
                    )
                    data["properties"].append(
                        {
                            "key": "status",
                            "select": DATA["tags"]["tasks"]["Status"]["Review"]["id"],
                        }
                    )
                    tasks_to_review.append(task["name"])

            self.anytype.update_object(
                DATA["spaces"]["tasks"], task["name"], task["id"], data
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
            message += make_deeplink(
                DATA["spaces"]["journal"],
                "bafyreifo2ypf4ahoy3iz2azhnmq4naalrdealrnxtnfkaolm2vgjgi4isq",
            )
            message += ">your Journal space.<a/>"
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def reflection_updates(self, dt_now):
        """Updates dates of completed reflections"""
        objs_to_check = self.anytype.get_list_view_objects(
            DATA["spaces"]["journal"],
            DATA["queries"]["reflections"]["id"],
            DATA["queries"]["reflections"]["update"],
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
                        "select": DATA["tags"]["journal"]["Status"]["Review"]["id"],
                    },
                    {"key": "rate", "text": new_tag},
                    {"key": "due_date", "date": new_day},
                ]
            }
            # self.anytype.update_object(obj["name"], obj["id"], data)

    def daily_rollover(self):
        """Daily automation script"""
        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        if Config.data["task_reset"]:
            logger.info("Running overdue tasks")
            self.overdue(dt_now)
        if Config.data["reflection_updates"]:
            logger.info("Updating Reflections")
            self.reflection_updates(dt_now)
        logger.info("Daily Rollover completed")

    def update_config_tag_data(
        self, tags: dict, space_name: str, props: list, source: bool = True
    ):
        """Updates Config file tag data"""
        if space_name not in tags:
            tags[space_name] = {}

        for prop in props:
            if prop["format"] in ["date", "checkbox", "objects"]:
                continue

            tags[space_name][prop["name"]] = {
                "key": prop["key"],
                "id": prop["id"],
                "format": prop["format"],
            }
            if prop["format"] in ["select", "mulit_select"]:
                prop_tags = self.anytype.get_tags_from_prop(
                    DATA["spaces"].get(space_name), prop["id"]
                )
                for tag in prop_tags:
                    if source:
                        tags[space_name][prop["name"]][tag["name"]] = {
                            "id": tag["id"],
                            "key": tag["key"],
                            "color": tag["color"],
                        }
                    else:
                        tags[space_name][prop["name"]][tag["name"]] = tag["id"]
        return tags

    def option_matching(self, tags: dict, source: str, target: str):
        """Ensures that status fields have matching current tags"""
        for tag in tags[source]:
            if tag == "Status" or tags[source][tag]["format"] not in [
                "select",
                "multi_select",
            ]:
                continue
            options_to_create = tags[source][tag].keys() - tags[target][tag].keys()
            for option in options_to_create:
                tag_info = tags[source][tag][option]
                data = {
                    "prop_name": tag,
                    "prop_id": tags[target][tag]["id"],
                    "color": tag_info["color"],
                    "tag_key": tag_info["key"],
                    "tag_name": option,
                }

                tags[target][tag][option] = self.anytype.add_tag_to_select_property(
                    DATA["spaces"][target], data
                )
        return tags

    def scan_spaces(self, scan_data):
        """Scan spaces and update self file"""
        tags = {}
        source_name = scan_data["source_space_name"]
        source_select = self.anytype.get_property_list(DATA["spaces"].get(source_name))
        tags = self.update_config_tag_data(tags, source_name, source_select)

        target_name = scan_data["target_space_name"]
        target_select = self.anytype.get_property_list(DATA["spaces"].get(target_name))
        tags = self.update_config_tag_data(tags, target_name, target_select, False)

        props_to_create = tags[source_name].keys() - tags[target_name].keys()
        for prop in props_to_create:
            data = {
                "format": tags[source_name][prop]["format"],
                "prop_key": tags[source_name][prop]["key"],
                "prop_name": prop,
            }
            tags[source_name][prop] = self.anytype.add_property(
                DATA["spaces"].get(target_name), data
            )

        tags = self.option_matching(tags, source_name, target_name)

        DATA["tags"] = tags

        DataManager().update()

        return None

    def get_or_create_property(self, space_name, data):
        """Get or create a property in a given space."""
        try:
            return DATA["tags"][space_name][data["prop_key"]]
        except IndexError:
            prop_id = self.anytype.add_property(DATA["spaces"][space_name], data)
            DATA["tags"][space_name][data["prop_key"]]["id"] = prop_id
            DataManager().update()

    def get_or_create_tag(self, space_name, data):
        """Get or create a tag for a given property in archive."""
        try:
            return DATA["tags"][space_name][data["prop_key"]][data["tag_key"]]
        except KeyError:
            tag_id = self.anytype.add_tag_to_select_property(
                DATA["spaces"][space_name],
                data["prop_key"],
                data["tag_key"],
                data["value"],
            )
            DATA["tags"][space_name][data["prop_key"]][data["tag_key"]] = tag_id
            DataManager().update()

            return tag_id

    def log_task_in_archive(self, task, accepted_props):
        """
        Define log object for archival
        """
        data = {
            "type_key": "log",
            "name": task["name"],
            "properties": [],
        }
        for prop in task:
            if prop in accepted_props:
                prop_details = DATA["tags"]["journal"][prop]
                prop_data = {"key": prop_details["key"]}
                if prop_details["format"] == "select":
                    prop_data[prop_details["format"]] = prop_details[task[prop]]
                else:
                    prop_data[prop_details["format"]] = task[prop]

                data["properties"].append(prop_data)
        try:
            self.anytype.create_object(DATA["spaces"]["journal"], data)

        except Exception:
            scan_data = {"source_space_name": "tasks", "target_space_name": "journal"}
            self.scan_spaces(scan_data)
            self.anytype.create_object(DATA["spaces"]["journal"], data)

    def task_status_reset(self, task, accepted_props, dt_now):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if Config.data["task_logs"]:
            self.log_task_in_archive(task, accepted_props)

        if "Rate" not in task or task["Rate"] == "":
            self.anytype.delete_object(
                DATA["spaces"]["tasks"], task["name"], task["id"]
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
                        "select": DATA["tags"]["tasks"]["Status"]["Repeating"]["id"],
                    },
                ]
            }
            self.anytype.update_object(
                DATA["spaces"]["tasks"], task["name"], task["id"], update_data
            )

    def recurrent_check(self):
        """Collect tasks for processing from completed view"""
        logger.info("Running completed task processing")
        tasks_to_check = self.anytype.get_list_view_objects(
            DATA["spaces"]["tasks"],
            DATA["queries"]["automation"]["id"],
            DATA["queries"]["automation"]["complete"],
        )
        if not tasks_to_check:
            return NO_TASKS

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        accepted_props = DATA["tags"]["journal"].keys()

        for task in tasks_to_check:

            self.task_status_reset(task, accepted_props, dt_now)

    def find_or_create_day_journal(self):
        """Searches for or creates a journal for the day"""

        dt_now = datetime.datetime.now()

        date_str = ""

        if dt_now.hour >= 21:
            dt_now.day += 1

        date_str = dt_now.strftime(r"%d.%m.%y")

        entry = self.anytype.search(
            DATA["spaces"]["journal"], "looking for journal object", {"query": date_str}
        )

        if not entry:

            data = {
                "name": date_str,
                "type_key": "entry",
                "template_id": DATA["templates"]["journal"]["entry"]["Day"],
            }

            # Matching output of search
            entry = {
                date_str: self.anytype.create_object(DATA["spaces"]["journal"], data)[
                    "object"
                ]["id"]
            }

        message = ""

        if dt_now.hour <= 6:
            message = "Good morning! Start your day right with "
        elif dt_now.hour == 20:
            message = "Good evening! Take a look back on your day with "
        elif dt_now.hour > 20:
            message = "Good evening! Plan your tomorrow with "
        else:
            message = "Hey, hey, please take a moment to check in with "

        link = f"<a href={make_deeplink(DATA["spaces"]["journal"], entry[date_str], False)}>this</a>!"

        self.pushover.send_message("Check in", message + link)

    def test(self):
        """Temp endpoint for testing"""
        return self.anytype.get_tags_from_prop(
            DATA["spaces"]["journal"], DATA["tags"]["journal"]["AoC"]["id"]
        )

    def other(self):
        """Temp endpoint for offhand tasks"""
        tasks_to_check = self.anytype.get_list_view_objects(
            DATA["spaces"]["tasks"],
            DATA["queries"]["automation"]["id"],
            DATA["queries"]["automation"]["other"],
        )

        for task in tasks_to_check:
            update_data = {
                "properties": [
                    {
                        "key": "status",
                        "select": DATA["tags"]["tasks"]["status"]["repeating"]["id"],
                    },
                ]
            }

            self.anytype.update_object(task["name"], task["id"], update_data)
        return "Completed with no issue"
