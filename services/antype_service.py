"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta

from utils.anytype import AnyTypeUtils


class AnytypeService:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)

    """
    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.overdue = "7b42e161-589d-4eaa-a57b-4e1c6226830f/"
        self.reset = "8a872d64-7ed4-417e-824c-745d19604849/"
        self.migrate = "3806f1d1-c2b5-4077-8c89-ebc83baff141/"
        self.summary = "48899c65-8da0-4c28-9fc1-b2a8811f523e/"

    def unpack_props(self, props:list, relevant_props: list):
        """Reads object to pull out properties"""
        prop_dict = {
            idx: prop
            for idx, prop in enumerate(props)
            if prop["name"] in relevant_props
        }
        print(prop_dict)

        return prop_dict

    def view_list(self):
        """Formats view objects into consumable objects to add to this object"""
        return self.anytype.get_views_list()

    def daily_rollover(self):
        """Daily automation script"""
        tasks_to_check = self.anytype.get_list_view_objects(self.overdue)
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"

        # if length more than 15, check in notification?

        data = {"properties": []}

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        dt_tomorrow = dt_now + relativedelta(days=1)
        dt_tmw_str = dt_tomorrow.strftime('%Y-%m-%dT%H:%M:%SZ')

        # due date tomorrow (runs at 11 so will be "today")
        data["properties"].append({"key": "due_date", "date": dt_tmw_str})

        for task in tasks_to_check:
            # if reset count is > 7 set to review?
            data["properties"].append(
                {"key": "reset_count", "number": task["Reset Count"]["value"] + 1}
            )

            self.anytype.update_task(task["name"], task["id"], data)
        return f"{len(tasks_to_check)} tasks with dates moved to tomorrow"

    def task_status_reset(self):
        """Presumably for repeating tasks?"""
        tasks_to_check = self.anytype.get_list_view_objects("eep")
        tasks_detailed = []
        if not tasks_to_check:
            return "No tasks to update"
        for task in tasks_to_check:
            tasks_detailed.append(self.anytype.get_task_by_id(task))
        for task in tasks_detailed:
            relevant_props = {prop["name"]:prop for prop in task["properties"] if prop["name"] in ["Rate", "Freqency"]}
            print(relevant_props)
        return "Task status update completed"
