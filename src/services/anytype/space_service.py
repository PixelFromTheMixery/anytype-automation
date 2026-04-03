"""Service for managing Anytype Spaces"""

from requests.exceptions import HTTPError

from models.data import SpaceData
from models.anytype_models import SpaceEditRequest

from utils.anytype import AnyTypeUtils
from utils.helper import Helper
from utils.logger import logger


DEFAULT_PROPS = [
    "Added date",
    "Backlinks",
    "Created by",
    "Creation date",
    "Description",
    "Done",
    "File extension",
    "Height",
    "Import Type",
    "Last message date",
    "Last modified by",
    "Last modified date",
    "Last opened date",
    "Links",
    "Object type",
    "Origin",
    "Size",
    "Source",
    "Source object",
    "Width",
]

DEFAULT_TYPES = [
    "Audio",
    "Bookmark",
    "Chat",
    "Collection",
    "File",
    "Image",
    "Page",
    "Query",
    "Space member",
    "Template",
    "Video",
]

STARTER_TYPES = ["Task", "Project", "Note"]


class SpaceService:

    def __init__(self, settings):
        self.settings = settings
        self.data = settings.data.anytype
        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        if self.data == {}:
            self.scan_space("tasks", settings.config.task_space_id)

    def scan_space(self, space_name, space_id):
        """
        Scans a space and collect:
        - custom (+ Query,) types and their templates
        - properties and their options
        """

        anytype_ref = {"id": space_id}
        data_types = [t for t in DEFAULT_TYPES if t != "Query"]
        anytype_ref["types"] = self.anytype.get_types(space_id, system_types=data_types)
        anytype_ref["queries"] = self.anytype.get_lists(
            space_id, anytype_ref["types"]["Query"]["id"]
        )

        anytype_ref["props"] = self.anytype.get_property_list(
            space_id, system_props=DEFAULT_PROPS
        )
        self.settings.data.anytype[space_name] = SpaceData(**anytype_ref)

        self.settings.data.file_sync()

    def migrate_spaces(self, request: SpaceEditRequest):
        """Copy types and copy objects of that type to new space"""

        return_data = {}
        target_space = request.target_space_name

        if "clear" in request.stages:
            return_data["cleared"] = self.clear_space(
                request.target_space_id, request.delete_task_types
            )

        return_data = self.sync_spaces(request, return_data)

        if "objects" in request.stages:
            return_data["objects"] = self.copy_objects(
                request.source_space_id, request.target_space_id, return_data
            )

        return return_data

    def clear_space(self, target_id, delete_task_types):
        """Removes basic types and props, Status and Due Date prop must be removed manually"""
        types_to_clear = self.anytype.get_types(
            target_id,
            (DEFAULT_TYPES + STARTER_TYPES if delete_task_types else DEFAULT_TYPES),
        )
        for type_obj in types_to_clear.values():
            self.anytype.delete_type(target_id, type_obj)
        props_to_clear = self.anytype.get_property_list(
            target_id,
            (DEFAULT_PROPS + ["Status", "Due date"]),
        )
        for prop in props_to_clear.values():
            if prop["name"] not in DEFAULT_PROPS:
                self.anytype.delete_property(target_id, prop)

        if not types_to_clear and not props_to_clear:
            return "Nothing to clear"
        return "Cleared everything but starter types (safetynet)"

    def sync_spaces(
        self, request: SpaceEditRequest, return_data: dict, reload_data: bool = False
    ):
        """Syncs spaces and update self file"""

        source_space_id = request.source_space_id
        target_space_id = request.target_space_id

        if "props" in request.stages:
            return_data["props"] = self.sync_props(source_space_id, target_space_id)
        if "types" in request.stages:
            return_data["types"] = self.sync_types(
                source_space_id,
                target_space_id,
            )
        if reload_data:
            self.scan_space(SpaceEditRequest.target_space_name, target_space_id)

        return return_data

    def sync_props(self, source_space_id, target_space_id):

        source_props = self.anytype.get_property_list(source_space_id)

        target_props = self.anytype.get_property_list(target_space_id)

        source_keys = {val["key"] for val in source_props.values()}
        target_keys = {val["key"] for val in target_props.values()}

        missing_internal_keys = source_keys - target_keys

        props_to_create = [
            val for val in source_props.values() if val["key"] in missing_internal_keys
        ]

        created_props = {}

        for prop in props_to_create:
            data = {
                "format": prop["format"],
                "key": prop["key"],
                "name": prop["name"],
            }
            try:
                new_prop_id = self.anytype.create_property(target_space_id, data)
                if prop["format"] in ["select", "multiselect"]:
                    self.option_matching(target_space_id, prop, new_prop_id)
                created_props[prop["name"]] = new_prop_id

            except HTTPError as err:
                if "already exists" in err.response:
                    logger.info("Prop seems to exist, continuing")

        if "status" in source_keys:
            self.option_matching(
                target_space_id,
                source_props["Status"],
                target_props["Status"],
            )

        return created_props

    def option_matching(self, space_id, prop: dict, target_prop_data: dict | str):
        if isinstance(target_prop_data, str):
            for option in prop["options"].values():
                self.anytype.add_tag_to_select_property(
                    space_id, target_prop_data, option
                )
        else:
            for option_name, option in prop["options"].items():
                if option_name not in target_prop_data["options"].keys():
                    self.anytype.add_tag_to_select_property(
                        space_id, target_prop_data["id"], option
                    )
            #     if props[target][prop]["options"] == []:
            #         options_to_create = props[source][prop]["options"].keys()
            #     else:
            #         options_to_create = list(
            #             props[source][prop]["options"].keys()
            #             - props[target][prop]["options"].keys()
            #         )
            #     for option in options_to_create:
            #         tag_info = props[source][prop]["options"][option]
            #         data = {
            #             "color": tag_info["color"],
            #             "key": tag_info["key"],
            #             "name": option,
            #         }

            #         props[target][prop]["options"][option] = (
            #             self.anytype.add_tag_to_select_property(
            #                 DATA.root[target], props[target][prop]["id"], data
            #             )
            #         )
            # return props

            # def copy_types(self, source_id, target_id):
            #     """Copy types from one space to another and adds corresponding props"""
            #     source_types = self.anytype.get_types(source_id, DEFAULT_TYPES)

            #     created_types = {}
            #     for type_obj in source_types.items():
            #         type_copy = type_obj.copy()
            #         type_copy.pop("id", None)
            #         try:
            #             self.anytype.create_type(target_id, type_copy)
            #             created_types[type_obj] = source_types[type_obj]
            #         except:
            #             logger.error("")
            #     return created_types

            # def copy_objects(self, objects_to_create, source_name, target_id):
            #     objects_created = []

            #

    def sync_types(self, source_space_id, target_space_id):
        source_types = self.anytype.get_types(source_space_id, DEFAULT_TYPES, True)
        target_types = self.anytype.get_types(target_space_id, DEFAULT_TYPES, True)

        types_modified = {"Created": [], "Modified": [], "Unable": []}

        create_types = [
            any_type for any_type in source_types if any_type not in target_types.keys()
        ]

        for any_type in create_types:
            source_data = source_types[any_type]
            if source_data["layout"] not in ["basic", "profile", "action", "note"]:
                types_modified["Unable"].append(any_type)
                continue
            self.anytype.create_type(target_space_id, source_data)
            types_modified["Created"].append(any_type)

        for any_type in STARTER_TYPES:
            if any_type in source_types and any_type in target_types:
                type_data = source_types[any_type]
                data = {
                    "icon": type_data["icon"],
                    "properties": type_data["properties"],
                }
                self.anytype.update_type(
                    target_space_id, target_types[any_type]["id"], any_type, data
                )
                types_modified["Modified"].append(any_type)
        return types_modified

    def copy_objects(self, source_space_id, target_space_id, return_data: dict):

        source_types = self.anytype.get_types(source_space_id, DEFAULT_TYPES, True)
        target_types = self.anytype.get_types(target_space_id, DEFAULT_TYPES, True)

        objects_created = []
        for type_name, type_data in source_types.items():
            logger.info(f"Creating objects for {type_name}")
            if type_name not in target_types.keys():
                continue
            objects = self.anytype.search(
                source_space_id,
                f"collecting all objects of type: {type_name}",
                {"types": [type_data["id"]]},
            )
            for object_name, object_id in objects.items():
                logger.info(f"Creating objects for {object_name}")
                object_dict = self.anytype.get_object_by_id(
                    source_space_id, object_id, False
                )["object"]
                obj_data = {
                    "name": object_dict["name"],
                    "type_key": (
                        "project" if type_data["key"] == "mission" else type_data["key"]
                    ),
                    "properties": [],
                    "body": object_dict["markdown"],
                }
                for prop in object_dict["properties"]:
                    if prop["name"] in DEFAULT_PROPS or prop["name"] == "Mission":
                        continue
                    prop_data = {
                        "key": prop["key"],
                    }

                    if prop["format"] == "select":
                        prop_data[prop["format"]] = prop[prop["format"]]["key"]
                    else:
                        prop_data[prop["format"]] = prop[prop["format"]]

                    obj_data["properties"].append(prop_data)

                self.anytype.create_object(target_space_id, obj_data)
                objects_created.append(object_name)

        return objects_created
