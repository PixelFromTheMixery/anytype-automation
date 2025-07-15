"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta, weekday

from utils.anytype import AnyTypeUtils
from utils.config import config, archive_log, save_archive_logging

class AnytypeService:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """
    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.converter = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

    def next_date(self, date: datetime.datetime, timescale: str, freq: int):
        """Returns formatted string of the next date based on the timescale provided"""
        if timescale in self.converter:
            timescale = self.converter[timescale]
        dt_next = datetime.datetime
        if timescale == "Day":
            dt_next =  date + relativedelta(days=freq)
        elif timescale == "Week":
            dt_next =  date + relativedelta(weeks=freq)
        elif timescale == "Month":
            dt_next =  date + relativedelta(months=freq)
        elif timescale == "Weekday":
            dt_next = date + datetime.timedelta(days=freq)
            while dt_next.weekday() >= 5:
                dt_next += datetime.timedelta(days=freq)
        elif timescale == "Weekend":
            dt_next = date + datetime.timedelta(days=freq)
            while dt_next.weekday() < 5:
                dt_next += datetime.timedelta(days=freq)
        else:
            dt_next =  date + relativedelta(weekday=weekday(timescale)(+freq))

        return dt_next.strftime("%Y-%m-%dT%H:%M:%SZ")

    def view_list(self):
        """Formats view objects into consumable objects to add to this object"""
        return self.anytype.get_views_list()

    def overdue(self):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["automation_list"]["overdue"]
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"
        # TODO:if length more than 15, check in notification?
        data = {"properties": []}

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        dt_next = dt_now + datetime.timedelta(days=1)

        data["properties"].append(
            {"key": "due_date", "date": dt_next.strftime("%Y-%m-%dT%H:%M:%SZ")}
        )

        # TODO: dynamic new date

        for task in tasks_to_check:

            if task["Reset Count"] is None:
                task["Reset Count"] = 0
            elif task["Status"] != "Blocked":
                task["Reset Count"] = task["Reset Count"] + 1

            if task["Rate"] != "Once" and task["Frequency"] is None:
                task["Frequency"] = 1

            # TODO:if reset count is > 7 set to review?
            data["properties"].append(
                {"key": "reset_count", "number": task["Reset Count"]}
                )

            self.anytype.update_object(task["name"], task["id"], data)
        return f"{len(tasks_to_check)} tasks with dates updated"

    def set_collections(self):
        """Assigns collection to task based on project"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["automation_list"]["aoc"]
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"

        collections_dict = self.anytype.search_by_type(
            "collection"
        )

        project = ""
        aoc = ""
        tasks_to_add = []
        for task in tasks_to_check:
            if project != task["Project"]["value"]["name"]:
                project = task["Project"]["value"]["name"]
                project_obj = self.anytype.get_object_by_id(
                    task["Project"]["value"]["id"]
                )
                if aoc != project_obj["AoC"]["value"]["name"]:
                    if len(tasks_to_add) != 0:
                        self.anytype.add_to_list(aoc, collections_dict[aoc], {"objects": tasks_to_add})
                    tasks_to_add = []
                    aoc = project_obj["AoC"]["value"]["name"]
            tasks_to_add.append(task["id"])
        self.anytype.add_to_list(aoc, collections_dict[aoc], {"objects":tasks_to_add})

    def daily_rollover(self):
        """Daily automation script"""
        self.overdue()
        self.set_collections()

    def define_log_object(self, task):
        """Define log object for archival"""
        data = {}
        data["type_key"] = "log"
        props = [
            {"key": "type", "select": archive_log["Type"][task["Type"]]},
            {"key": "interval", "select": archive_log["Interval"][task["Interval"]]},
            {"key": "day_segment", "select": archive_log["Day Segment"][task["Day Segment"]]},
        ]
        # for link in task["Backlinks"]:
        #     if link["name"] in ["Care", "Finance", "Home", "Management", "Self-Dev", "Workshop"]:
        #         props.append(
        #             {"key": "ao_c", "select": archive_log["AoC"][link["name"]]},
        #         )
        #         break

        # try:
        #     project_name = task["Project"][0]["name"]
        #     props.append({"key": "project", "select": archive_log["Project"][project_name]})
        # except (KeyError, IndexError):
        #     project_name = task.get("Project", [{}])[0].get("name", "")
        #     tag_id = self.anytype.get_tag_from_list(
        #         config["spaces"]["archive"],
        #         archive_log["Project"]["id"],
        #         project_name
        #     )
        #     archive_log["Project"][project_name] = tag_id
        #     save_archive_logging(archive_log)
        #     props.append(
        #         {"key": "project", "select": tag_id}
        #     )

        data["properties"] = props
        return data

    def migrate_tasks(self):
        """Presumably for repeating tasks?"""
        tasks_to_check = self.anytype.get_list_view_objects(config["automation_list"]["migrate"])
        if not tasks_to_check:
            return "No tasks to update"
        for task in tasks_to_check:
            data = self.define_log_object(task)
            self.anytype.create_object(
            config["spaces"]["archive"],
            task["name"], data)
        return "Task status update completed"


""" 
reference for next date function
data["properties"].append(
                {
                    "key": "due_date",
                    "date": self.next_date(dt_now, task["Rate"], task["Frequency"]),
                }
            )
"""
