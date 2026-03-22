"""Module for handling automation behaviour"""

import datetime

from services.anytype.task_service import TaskService
from services.anytype.space_service import SpaceService

from utils.anytype import AnyTypeUtils
from utils.config import Config
from utils.data import DataManager
from utils.helper import Helper
from utils.logger import logger
from utils.pushover import PushoverUtils


DATA = DataManager.get()


class AnytypeService:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """

    def __init__(self):
        self.task = TaskService()
        self.space = SpaceService()

        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        self.pushover = PushoverUtils()

    def search(self, search_request: dict):
        """
        Searches a specified space according to type and query
        Default to task type
        """
        space_id = DATA[search_request["space_name"]["id"]]
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

    def fetch_data(self, data, props: bool = False):
        """Fetch object based on data"""
        # TODO: ???
        space_id = DATA[data["space_name"]]["id"]
        fetched = {}
        if data["category"] == "types":
            fetched = self.anytype.get_types(space_id, props)
        if data["category"] == "templates":

            fetched = self.anytype.get_templates(
                space_id,
                DATA[data["space_name"]]["types"][data["type_name"]],
            )
        return fetched

    def view_list(self, space_name: str, query_name: str):
        """Formats view objects into consumable objects to add to this object"""
        space_id = DATA[space_name]["id"]
        try:
            query_id = DATA[space_name]["queries"][query_name]
        except KeyError as exc:
            raise KeyError("query not found in local data, ") from exc
        return self.anytype.get_views_list(space_id, query_id)

    def daily_rollover(self):
        """Daily automation script"""
        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        dt_next = dt_now + datetime.timedelta(days=1)
        if Config.data.get("task_reset"):
            logger.info("Running overdue tasks")
            self.task.overdue(dt_now)
        logger.info("Daily Rollover completed")

    def recurrent_check(self):
        """Collect tasks for processing from completed view"""
        logger.info("Running completed task processing")
        tasks_to_check = self.anytype.get_list_view_objects(
            DATA["tasks"].id,
            DATA["tasks"].queries["Automation"].id,
            DATA["tasks"].queries["Automation"].Done,
        )
        if not tasks_to_check:
            return "No tasks to update"

        for task in tasks_to_check:
            next_date = (
                self.helper.next_date(
                    task["Rate"],
                ),
            )

            self.task.task_status_reset(task, next_date)
        return "Completed"

    def migrate_spaces(self, migrate_request: dict):
        """Copy types and copy objects of that type to new space"""
        source_name = migrate_request["source_space_name"]
        target_id = migrate_request["target_space_id"]
        target_name = migrate_request["target_space_name"]

        DATA[target_name] = {"id": migrate_request["target_space_id"]}

        return_data = {}

        if "clear" in migrate_request["stages"]:

            self.space.clear_space(target_id)
            return_data["clear"] = True

        if "props" in migrate_request["stages"]:
            props_to_create = self.space.sync_spaces(
                {
                    "source_space_name": source_name,
                    "target_space_name": target_name,
                },
            )
            return_data["props"] = props_to_create[target_name]

        types_to_create = {}

        if "types" in migrate_request["stages"]:
            types_to_create = self.space.copy_types(
                source_name,
                target_id,
            )
            return_data["types"] = types_to_create

        if "objects" in migrate_request["stages"]:
            for obj_type in types_to_create.items():
                objects_to_create = self.search(
                    {
                        "search_name": f"Collecting all objects of type {obj_type}",
                        "space_name": source_name,
                        "types": obj_type["id"],
                    }
                )
                return_data["objects"] = self.space.copy_objects(
                    objects_to_create, source_name, target_id
                )

        return return_data
