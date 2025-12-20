"""Utility module for anytype, abstracted for common tasks"""

from utils.api_tools import make_call
from utils.config import config
from utils.logger import logger


class AnyTypeUtils:
    """
    Pulls views for automation, refer to anytype service
    Pulls object details in views in views
    Updates tasks with provided data
    """

    def test(self):
        """Play area for momentary tasks"""
        url = "http://localhost:31009/v1/spaces/"
        url += config["spaces"]["main"]
        url += "/types"
        return make_call("get", url, "getting test data")

        # url += "tags"
        list_id = config["query"]["Task by Day"]["id"]
        view_id = config["query"]["Task by Day"]["evening"]
        return self.get_list_view_objects(
            view_id,
            list_id,
        )
        return self.search_by_type_and_or_name("Task by Day", False)
        # return make_call("post", url, "getting automation list objects", payload)
        return self.search_by_type_and_or_name("collection")

    def search(
        self,
        search_detail: str,
        search_body: dict,
        unpack_level: str = "simple",
        space_id: str = config["spaces"]["main"],
    ):
        """Returns all objects by type"""
        url = "http://localhost:31009/v1/spaces/"
        url += space_id
        url += "/search"
        objects = make_call("post", url, f"searching for {search_detail}", search_body)

        if objects is not None and objects["data"] is None:
            return "No objects found"

        formatted_objects = {}
        for obj in objects["data"] if objects is not None else []:
            formatted_objects[obj["name"]] = obj["id"]

        return formatted_objects

    def get_views_list(self, list_id: str = config["queries"]["automation"]):
        """Pull all views(queries) in the automation query object"""
        views_url = config["url"] + config["spaces"]["main"]
        views_url += "/lists/" + list_id
        views_url += "/views"

        views = make_call("get", views_url, "get view list from automation query")
        views_formatted = []

        for view in views["data"] if views is not None else []:
            views_formatted.append({"name": view["name"], "id": view["id"]})

        return views_formatted

    def add_to_list(self, list_name: str, list_id: str, list_items: list):
        """Add list items to object"""
        lists_url = config["url"] + config["spaces"]["main"]
        lists_url += "/lists/" + list_id
        lists_url += "/objects"
        if list_items is not None:
            make_call(
                "post",
                lists_url,
                f"add {len(list_items)} items to {list_name}",
                {"objects": list_items},
            )

    def get_list_view_objects(
        self,
        view_id: str,
        unpack_level: str = "most",
        list_id: str = config["queries"]["automation"],
    ):
        """Pulls out detailed information of objects in a view (query)"""
        obj_url = config["url"] + config["spaces"]["main"]
        obj_url += "/lists/" + list_id
        obj_url += "/views/" + view_id
        obj_url += "/objects"
        main_obj = make_call("get", obj_url, "get obj")

        objs_to_check = []

        if main_obj and "data" in main_obj:
            logger.info(f"Found {len(main_obj["data"])} objects")

            for obj in main_obj["data"]:
                objs_to_check.append(self.get_object_by_id(obj["id"], unpack_level))

        return objs_to_check

    def unpack_full_object(self, object_obj: dict, sub_objects: bool = True):
        """Pulls out name, id, and properties for use"""
        object_dict = {
            "name": object_obj["object"]["name"],
            "id": object_obj["object"]["id"],
        }
        for prop in object_obj["object"]["properties"]:
            prop_type = prop["format"]
            prop_value = None
            # Basic props that match their type
            if prop_type in ["checkbox", "date", "number", "text", "url"]:
                prop_value = prop[prop_type]

            elif prop_type in ["select", "multiselect"]:
                prop_value = prop[prop_type]["name"]

            elif prop_type == "objects" and sub_objects is True:
                if prop[prop_type] is None:
                    prop_value = prop[prop_type]
                elif prop["name"] in [
                    "Links",
                    "Parent Task",
                    "Created by",
                    "Last modified by",
                ]:
                    continue
                else:
                    links = []
                    for object_id in prop[prop_type]:
                        result = self.get_object_by_id(object_id, "simple")
                        if "Clear me" not in result:
                            links.append(result)
                        else:
                            self.update_object(
                                object_obj["object"]["name"],
                                object_obj["object"]["id"],
                                {"properties": [{"key": prop_type, "objects": None}]},
                            )
                    prop_value = links
            object_dict[prop["name"]] = prop_value

        return object_dict

    def get_object_by_id(self, object_id: str, unpack_level: str = "most"):
        """Pulls detailed object data by id"""
        object_url = config["url"] + config["spaces"]["main"]
        object_url += "/objects/" + object_id

        object_obj = make_call("get", object_url, f"get {unpack_level} object by id")

        if object_obj is None:
            return "raise exception"

        object_formatted = None

        if isinstance(object_obj, str):
            return {"Clear me": object_obj}

        if unpack_level == "simple":
            object_formatted = {
                "name": object_obj["object"]["name"],
                "id": object_obj["object"]["id"],
            }
        elif unpack_level == "project":
            object_formatted = {
                "name": object_obj["object"]["name"],
                "id": object_obj["object"]["id"],
                "AoC": config["AoC"].get(object_obj["object"]["name"][-3:]),
            }
        elif unpack_level == "most":
            object_formatted = self.unpack_full_object(object_obj, False)
        elif object_obj is not None:
            object_formatted = self.unpack_full_object(object_obj)
        else:
            return "object is None"

        return object_formatted

    def update_object(self, object_name: str, object_id: str, data: dict):
        """Updates object with provided data"""
        object_url = config["url"] + config["spaces"]["main"]
        object_url += "/objects/" + object_id
        return make_call(
            "patch", object_url, f"update object ({object_name}) by id", data
        )

    def create_object(self, space_id: str, type_name: str, data: dict):
        """Creates object with provided data"""
        object_url = config["url"] + space_id
        object_url += "/objects"
        return make_call(
            "post", object_url, f"create object with {type_name} data", data
        )

    def delete_object(self, object_name: str, object_id: str):
        """Deletes object by id"""
        object_url = config["url"] + config["spaces"]["main"]
        object_url += "/objects/" + object_id
        return make_call(
            "delete",
            object_url,
            f"delete object ({object_name}) by id",
        )

    def get_tag_from_list(self, space_id: str, prop_id: str, tag_name: str):
        """Returns the tag and name from the provided list"""
        tag_url = config["url"] + space_id
        tag_url += "/properties/" + prop_id
        tag_url += "/tags"
        tags = make_call("get", tag_url, "get tags from property")
        tags = tags["data"] if tags is not None else []
        for tag in tags:
            if tag["name"] == tag_name:
                return tag["id"]

    def add_option_to_property(
        self, space_id: str, prop_id: str, prop_name: str, option_name: str
    ):
        """Adds option to provided property"""
        prop_url = config["url"] + space_id
        prop_url += "/properties/" + prop_id
        prop_url += "/tags"
        data = {"color": "grey", "name": option_name}
        new_tag = make_call(
            "post", prop_url, f"add {option_name} to {prop_name} property", data
        )
        return new_tag["tag"]["id"] if new_tag is not None else None
