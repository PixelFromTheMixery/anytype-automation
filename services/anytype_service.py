"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta

from utils.anytype import AnyTypeUtils
from utils.config import Config, Data
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

    def get_setting(self, key, default=None):
        """Safely fetch a config setting without crashing."""
        return Config.get().get(key, default)

    def get_data(self, key):
        """Safely fetch a data value without crashing."""
        return Data._data.get()

    def update_data(self, key, value):
        """Update data and immediately commit to disk."""
        Data._data.get(key, default)
        Data.save()

    def search(self, search_request: dict):
        """
        Searches a specified space according to type and query
        Default to task type
        """
        space_id = self.data["spaces"].get(search_request["space_name"])
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
        space_id = self.get_data(["spaces"][data["space_name"]])
        if data["category"] == "types":
            fetched = self.anytype.get_types(space_id)
        if data["category"] == "templates":

            fetched = self.anytype.get_templates(
                space_id,
                self.get_data(["types"][data["space_name"]][data["type_name"]]),
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
        space_id = self.data["spaces"].get(space_name)
        try:
            query_id = self.data["queries"][query_name]["id"]
        except KeyError:
            raise KeyError(
                "query not found in config, check if space or query name and that query has automation checkbox ticked"
            )
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
            self.data["spaces"]["tasks"],
            self.data["queries"]["automation"]["id"],
            self.data["queries"]["automation"]["overdue"],
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return NO_TASKS

        dt_next = dt_now + datetime.timedelta(days=1)

        if len(tasks_to_check) > 15 and self.data["config"]["pushover"]:
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

            if self.data["config"]["task_review_threshold"] > 0:
                data = self.task_review_cleanup(task, data)
                if task["Reset Count"] > self.data["config"]["task_review_threshold"]:
                    data["properties"].append(
                        {
                            "key": "status",
                            "select": self.data["tags"]["tasks"]["Status"]["Review"],
                        }
                    )
                    tasks_to_review.append(task["name"])

            self.anytype.update_object(
                self.data["spaces"]["tasks"], task["name"], task["id"], data
            )

        if tasks_to_review and self.data["config"]["pushover"]:
            message = "The following tasks have been reset 5 times, please review:"
            for task in tasks_to_review:
                message += "<br>" + task
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def reflection_updates(self, dt_now):
        """Updates dates of completed reflections"""
        objs_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["journal"],
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
                        "select": self.data["tags"]["journal"]["Status"]["Review"],
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
        if self.data["config"]["task_reset"]:
            logger.info("Running overdue tasks")
            self.overdue(dt_now)
        if self.data["reflection_updates"]:
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
                    self.data["spaces"].get(space_name), prop["id"]
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
                    self.data["spaces"][target], data
                )
        return tags

    def scan_spaces(self, scan_data):
        """Scan spaces and update self file"""
        tags = {}
        source_name = scan_data["source_space_name"]
        source_select = self.anytype.get_property_list(
            self.data["spaces"].get(source_name)
        )
        tags = self.update_config_tag_data(tags, source_name, source_select)

        target_name = scan_data["target_space_name"]
        target_select = self.anytype.get_property_list(
            self.data["spaces"].get(target_name)
        )
        tags = self.update_config_tag_data(tags, target_name, target_select, False)

        props_to_create = tags[source_name].keys() - tags[target_name].keys()
        for prop in props_to_create:
            data = {
                "format": tags[source_name][prop]["format"],
                "prop_key": tags[source_name][prop]["key"],
                "prop_name": prop,
            }
            tags[source_name][prop] = self.anytype.add_property(
                self.data["spaces"].get(target_name), data
            )

        tags = self.option_matching(tags, source_name, target_name)

        self.data["tags"] = tags

        self.data = Config.save()

        return None

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
            tag_id = self.anytype.add_tag_to_select_property(
                self.data["spaces"][space_name],
                data["prop_key"],
                data["tag_key"],
                data["value"],
            )
            self.data["tags"][space_name][data["prop_key"]][data["tag_key"]] = tag_id
            self.data = Config.save()

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
                prop_details = self.data["tags"]["journal"][prop]
                prop_data = {"key": prop_details["key"]}
                if prop_details["format"] == "select":
                    prop_data[prop_details["format"]] = prop_details[task[prop]]
                else:
                    prop_data[prop_details["format"]] = task[prop]

                data["properties"].append(prop_data)
        try:
            self.anytype.create_object(
                self.data["spaces"]["journal"], task["name"], data
            )

        except:
            scan_data = {"source_space_name": "tasks", "target_space_name": "journal"}
            self.scan_spaces(scan_data)
            self.anytype.create_object(
                self.data["spaces"]["journal"], task["name"], data
            )

    def task_status_reset(self, task, accepted_props, dt_now):
        """
        Delete tasks that occur once
        Reset tasks that recur
        Update task based on reset count
        """
        if self.data["config"]["task_logs"]:
            self.log_task_in_archive(task, accepted_props)

        if "Rate" not in task or task["Rate"] == "":
            self.anytype.delete_object(
                self.data["spaces"]["tasks"], task["name"], task["id"]
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
                        "select": self.data["tags"]["tasks"]["Status"]["Repeating"][
                            "id"
                        ],
                    },
                ]
            }
            self.anytype.update_object(
                self.data["spaces"]["tasks"], task["name"], task["id"], update_data
            )

    def recurrent_check(self):
        """Collect tasks for processing from completed view"""
        logger.info("Running completed task processing")
        tasks_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["tasks"],
            self.data["queries"]["automation"]["id"],
            self.data["queries"]["automation"]["complete"],
        )
        if not tasks_to_check:
            return NO_TASKS

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        accepted_props = self.data["tags"]["journal"].keys()

        for task in tasks_to_check:

            self.task_status_reset(task, accepted_props, dt_now)

    def test(self):
        """Temp endpoint for testing"""
        data = {
            "space": self.data["spaces"]["journal"],
            "prop": self.data["tags"]["journal"]["AoC"]["id"],
        }
        return self.anytype.get_tags_from_prop(
            self.data["spaces"]["journal"], self.data["tags"]["journal"]["AoC"]["id"]
        )

    def other(self):
        """Temp endpoint for offhand tasks"""
        tasks_to_check = self.anytype.get_list_view_objects(
            self.data["spaces"]["tasks"],
            self.data["queries"]["automation"]["id"],
            self.data["queries"]["automation"]["other"],
        )

        for task in tasks_to_check:
            update_data = {
                "properties": [
                    {
                        "key": "status",
                        "select": self.data["tags"]["tasks"]["status"]["repeating"],
                    },
                ]
            }

            self.anytype.update_object(task["name"], task["id"], update_data)
        return "Completed with no issue"
