"""Module for handling automation behaviour"""

from utils.anytype import AnyTypeUtils
from utils.helper import Helper
from utils.logger import logger
from utils.pushover import PushoverUtils


class AnytypeService:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """

    def __init__(self, settings, task_service, space_service):
        self.settings = settings
        self.task = task_service
        self.space = space_service

        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def daily_rollover(self):
        """Daily automation script"""
        dt_tmw_str = self.helper.next_date("1@day")
        if self.settings.config.task_reset:
            logger.info("Running overdue tasks")
            self.task.overdue(dt_tmw_str)
        logger.info("Daily Rollover completed")

    def migrate_spaces(self, migrate_request: dict):
        """Copy types and copy objects of that type to new space"""
        raise NotImplementedError("Broken by data model")
        # # TODO: rework with data model
        # source_name = migrate_request["source_space_name"]
        # target_id = migrate_request["target_space_id"]
        # target_name = migrate_request["target_space_name"]

        # DATA.root[target_name] = {"id": migrate_request["target_space_id"]}

        # return_data = {}

        # if "clear" in migrate_request["stages"]:

        #     self.space.clear_space(target_id)
        #     return_data["clear"] = True

        # if "props" in migrate_request["stages"]:
        #     props_to_create = self.space.sync_spaces(
        #         {
        #             "source_space_name": source_name,
        #             "target_space_name": target_name,
        #         },
        #     )
        #     return_data["props"] = props_to_create[target_name]

        # types_to_create = {}

        # if "types" in migrate_request["stages"]:
        #     types_to_create = self.space.copy_types(
        #         source_name,
        #         target_id,
        #     )
        #     return_data["types"] = types_to_create

        # if "objects" in migrate_request["stages"]:
        #     for obj_type in types_to_create.items():
        #         objects_to_create = self.search(
        #             {
        #                 "search_name": f"Collecting all objects of type {obj_type}",
        #                 "space_name": source_name,
        #                 "types": obj_type["id"],
        #             }
        #         )
        #         return_data["objects"] = self.space.copy_objects(
        #             objects_to_create, source_name, target_id
        #         )

        # return return_data
