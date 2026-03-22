from utils.anytype import AnyTypeUtils
from utils.data import DataManager
from utils.helper import Helper
from utils.logger import logger

DATA = DataManager.get()

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


class SpaceService:

    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.helper = Helper()

    def option_matching(self, props: dict, source: str, target: str):
        """Ensures that select and multiselect fields have matching current options"""
        # TODO: Refine
        for prop in props[source]:
            if props[source][prop]["format"] not in [
                "select",
                "multi_select",
            ]:
                continue

            if props[target][prop]["options"] == []:
                options_to_create = props[source][prop]["options"].keys()
            else:
                options_to_create = list(
                    props[source][prop]["options"].keys()
                    - props[target][prop]["options"].keys()
                )
            for option in options_to_create:
                tag_info = props[source][prop]["options"][option]
                data = {
                    "color": tag_info["color"],
                    "key": tag_info["key"],
                    "name": option,
                }

                props[target][prop]["options"][option] = (
                    self.anytype.add_tag_to_select_property(
                        DATA[target], props[target][prop]["id"], data
                    )
                )
        return props

    def scan_space(self, space_name):
        """
        Scans a space and collect:
        - custom (+ Query,) types and their templates
        - properties and their options
        """
        data_types = [t for t in DEFAULT_TYPES if t != "Query"]
        DATA[space_name]["types"] = self.anytype.get_types(
            DATA[space_name]["id"], system_types=data_types
        )
        DATA[space_name]["queries"] = self.anytype.get_lists(
            DATA[space_name]["id"], DATA[space_name]["types"]["Query"]["id"]
        )
        DATA[space_name]["props"] = self.anytype.get_property_list(
            DATA[space_name]["id"], system_props=DEFAULT_PROPS
        )
        DataManager.update()
        return DATA[space_name]

    # TODO: Update to dictionary access if appropriate, rework for new reference structure
    def sync_spaces(self, sync_data):
        """Syncs spaces and update self file"""
        source_name = sync_data["source_space_name"]
        source_id = DATA[source_name]["id"]
        source_props = self.anytype.get_property_list(source_id)

        target_name = sync_data["target_space_name"]
        target_id = DATA[target_name]["id"]
        target_props = self.anytype.get_property_list(target_id)

        props_to_create = list(source_props.keys() - target_props.keys())
        for prop in props_to_create:
            data = {
                "format": source_props[prop]["format"],
                "key": source_props[prop]["key"],
                "name": prop,
            }
            self.anytype.create_property(target_id, data)

        DATA[source_name]["props"] = self.anytype.get_property_list(source_id)
        DATA[target_name]["props"] = self.anytype.get_property_list(target_id)

        DataManager().update()

        # TODO: defunct
        # self.option_matching(DATA["tags"], source_name, target_name)

        DataManager().update()

        return DATA

    def clear_space(self, target_id):
        """Removes basic types and props, Status and Due Date prop must be removed manually"""
        clear_types = self.anytype.get_types(target_id, DEFAULT_TYPES)
        for type_obj in clear_types.items():
            self.anytype.delete_type(target_id, type_obj)
        clear_props = self.anytype.get_property_list(target_id)
        for prop in clear_props:
            if clear_props[prop]["name"] not in DEFAULT_PROPS:
                self.anytype.delete_property(target_id, clear_props[prop])
            if clear_props[prop]["name"] == "Status":
                self.anytype.delete_property(target_id, clear_props[prop])

    def copy_types(self, source_id, target_id):
        """Copy types from one space to another and adds corresponding props"""
        source_types = self.anytype.get_types(source_id, DEFAULT_TYPES)

        created_types = {}
        for type_obj in source_types.items():
            type_copy = type_obj.copy()
            type_copy.pop("id", None)
            try:
                self.anytype.create_type(target_id, type_copy)
                created_types[type_obj] = source_types[type_obj]
            except:
                logger.error("")
        return created_types

    def copy_objects(self, objects_to_create, source_name, target_id):
        objects_created = []

        for object_name in objects_to_create:
            object_dict = self.anytype.get_object_by_id(
                DATA[source_name]["id"], objects_to_create[object_name], False
            )["object"]
            obj_data = {
                "name": object_dict["name"],
                "type_key": object_dict["type"]["key"],
                "properties": [],
                "body": object_dict["markdown"],
            }
            for prop in object_dict["properties"]:

                if prop["name"] in DEFAULT_PROPS or prop["format"] == "date":
                    continue
                prop_data = {
                    "key": prop["key"],
                }

                if prop["format"] == "select":
                    prop_data[prop["format"]] = prop[prop["format"]]["key"]
                else:
                    prop_data[prop["format"]] = prop[prop["format"]]

                obj_data["properties"].append(prop_data)

            self.anytype.create_object(target_id, obj_data)
            objects_created.append(object_dict["name"])
        return objects_created

    def get_or_create_property(self, space_name, data):
        """Get or create a property in a given space."""
        try:
            return DATA[space_name]["props"][data["prop_name"]]
        except IndexError:
            prop_id = self.anytype.create_property(DATA[space_name]["id"], data)
            DATA[space_name]["props"][data["prop_name"]]["id"] = prop_id
            DataManager().update()

    # def get_or_create_tag(self, space_name, data):
    #     """Get or create a tag for a given property in archive."""
    #     # TODO: ???
    #     try:
    #         return DATA["tags"][space_name][data["prop_key"]][data["tag_key"]]
    #     except KeyError:
    #         tag_id = self.anytype.add_tag_to_select_property(
    #             DATA[space_name],
    #             data["prop_key"],
    #             data["tag_key"],
    #             data["value"],
    #         )
    #         DATA["tags"][space_name][data["prop_key"]][data["tag_key"]] = tag_id
    #         DataManager().update()

    #         return tag_id
