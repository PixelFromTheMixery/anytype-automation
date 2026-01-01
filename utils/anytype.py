"""Utility module for anytype, abstracted for common tasks"""

from utils.api_tools import make_call
from utils.logger import logger

URL = "http://localhost:31009/v1/spaces/"
OBJ = "/objects/"
PROPS = "/properties/"


class AnyTypeUtils:
    """
    Pulls views for automation, refer to anytype service
    Pulls object details in views in views
    Updates tasks with provided data
    """

    def test(self, data):
        """Play area for momentary tasks"""
        test = self.get_tags_from_prop(data["space"], data["prop"])
        return test

    def search(
        self,
        space_id,
        search_detail: str,
        search_body: dict,
    ):
        """Returns all objects by type"""
        url = URL + space_id
        url += "/search"
        objects = make_call("post", url, f"searching for {search_detail}", search_body)

        if objects is not None and objects["data"] is None:
            return "No objects found"

        formatted_objects = {}
        for obj in objects["data"] if objects is not None else []:
            formatted_objects[obj["name"]] = obj["id"]

        return formatted_objects

    def get_views_list(
        self,
        space_id: str,
        list_id: str,
    ):
        """Pull all views in a query object"""
        views_url = URL + space_id
        views_url += "/lists/" + list_id
        views_url += "/views"

        views = make_call("get", views_url, "get view list for query")
        views_formatted = []

        for view in views["data"] if views is not None else []:
            views_formatted.append({"name": view["name"], "id": view["id"]})

        return views_formatted

    def get_list_view_objects(
        self,
        space_id: str,
        list_id: str,
        view_id: str,
    ):
        """Pulls out detailed information of objects in a view (query)"""
        obj_url = URL + space_id
        obj_url += "/lists/" + list_id
        obj_url += "/views/" + view_id
        obj_url += "/objects"
        main_obj = make_call("get", obj_url, "get obj")

        objs_to_check = []

        if main_obj and "data" in main_obj:
            logger.info(f"Found {len(main_obj['data'])} objects")

            for obj in main_obj["data"]:
                objs_to_check.append(self.get_object_by_id(space_id, obj["id"]))

        return objs_to_check

    def unpack_object(self, object_obj: dict, sub_objects: bool = True):
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
                continue
            object_dict[prop["name"]] = prop_value

        return object_dict

    def get_object_by_id(self, space_id: str, object_id: str):
        """Pulls detailed object data by id"""
        object_url = URL + space_id
        object_url += OBJ + object_id

        object_obj = make_call("get", object_url, "get object by id")

        if object_obj is None:
            return "raise exception"

        object_formatted = None

        if isinstance(object_obj, str):
            return {"Clear me": object_obj}

        object_formatted = self.unpack_object(object_obj, False)
        return object_formatted

    def update_object(self, space_id, object_name: str, object_id: str, data: dict):
        """Updates object with provided data"""
        object_url = URL + space_id
        object_url += OBJ + object_id
        return make_call(
            "patch", object_url, f"update object ({object_name}) by id", data
        )

    def create_object(self, space_id: str, type_name: str, data: dict):
        """Creates object with provided data"""
        object_url = URL + space_id
        object_url += "/objects"
        return make_call(
            "post", object_url, f"create object with {type_name} data", data
        )

    def delete_object(self, space_id, object_name: str, object_id: str):
        """Deletes object by id"""
        object_url = URL + space_id
        object_url += OBJ + object_id
        return make_call(
            "delete",
            object_url,
            f"delete object ({object_name}) by id",
        )

    def get_property_list(self, space_id):
        """Returns a list of all the properties of a space and their properties"""
        prop_url = URL + space_id
        prop_url += PROPS
        props = make_call("get", prop_url, f"get props from space {space_id}")
        return props["data"] if props is not None else []

    def get_tags_from_prop(self, space_id: str, prop_id: str):
        """Returns the tag and name from the provided list"""
        tag_url = URL + space_id
        tag_url += PROPS + prop_id
        tag_url += "/tags"
        tags = make_call("get", tag_url, "get tags from property")
        return tags["data"] if tags is not None else []

    def add_tag_to_select_property(self, space_id: str, data: dict):
        """Adds option to provided property"""
        prop_url = URL + space_id
        prop_url += PROPS + data["prop_id"]
        prop_url += "/tags"
        tag_data = {
            "color": "grey" if "color" not in data else data["color"],
            "key": data["tag_key"],
            "name": data["tag_name"],
        }
        new_tag = make_call(
            "post",
            prop_url,
            f"add {data['tag_name']} to {data['prop_name']} property",
            tag_data,
        )
        return new_tag["tag"]["id"] if new_tag is not None else None

    def add_property(self, space_id: str, data: dict):
        """Adds property to space"""
        prop_url = URL + space_id
        prop_url += "/properties"
        prop_data = {
            "format": data["format"],
            "key": data["prop_key"],
            "name": data["prop_name"],
        }
        new_prop = make_call(
            "post", prop_url, f"add property '{data['prop_name']}' to space", prop_data
        )
        return new_prop["property"]["id"] if new_prop is not None else None
