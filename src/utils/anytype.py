"""Utility module for anytype, abstracted for common tasks"""

from utils.api_tools import make_call
from utils.logger import logger


URL = "/v1/spaces/"
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
        search_name,
        search_body: dict,
    ):
        """Returns all objects by type"""
        url = URL + space_id
        url += "/search?limit=999"
        objects = make_call("post", url, f"searching for {search_name}", search_body)

        if objects is not None and objects["data"] is None:
            return "No objects found"

        formatted_objects = {}
        for obj in objects["data"] if objects is not None else []:
            formatted_objects[obj["name"]] = obj["id"]

        return formatted_objects

    def get_types(self, space_id, system_types=None, props: bool = False):
        types_url = URL + space_id
        types_url += "/types"

        types = make_call("get", types_url, "get types from space")
        types_formatted = {}

        system_types = [] if system_types is None else system_types
        for type_obj in types["data"] if types is not None else []:
            if type_obj["name"] in system_types:
                continue
            type_dict = {"id": type_obj["id"], "key": type_obj["key"]}
            if props:
                type_dict["plural_name"] = type_obj["plural_name"]
                type_dict["layout"] = type_obj["layout"]
                type_dict["name"] = type_obj["name"]
                type_dict["icon"] = type_obj["icon"]
                type_dict["properties"] = []
                for prop in type_obj["properties"]:
                    type_dict["properties"].append(
                        {
                            "key": prop["key"],
                            "name": prop["name"],
                            "format": prop["format"],
                        }
                    )
            type_templates = self.get_templates(space_id, type_dict["id"])
            if type_templates is not None:
                type_dict["templates"] = {}
            for template in type_templates["data"]:
                type_dict["templates"][template["name"]] = template["id"]
            types_formatted[type_obj["name"]] = type_dict

        return types_formatted

    def get_templates(
        self,
        space_id,
        type_id,
    ):
        templates_url = URL + space_id
        templates_url += "/types/" + type_id
        templates_url += "/templates"

        templates = make_call("get", templates_url, "get templates from type")

        return templates

    def get_lists(self, space_id, query_type_id):
        list_ids = self.search(space_id, "collect queries", {"types": [query_type_id]})

        query_dict = {}
        for list_id in list_ids:
            query_dict[list_id] = {"id": list_ids[list_id]}
            view_list = self.get_views_list(space_id, list_ids[list_id])
            for view in view_list:
                query_dict[list_id][view["name"]] = view["id"]
        return query_dict

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

    def create_type(self, space_id, type_data: dict):
        """Creates a type with the provided data"""
        type_url = URL + space_id
        type_url += "/types"
        type_dict = type_data.copy()
        del type_dict["id"]

        make_call("post", type_url, f'create type {type_dict["name"]}', type_dict)

    def delete_type(self, space_id, type_data: dict):
        """Creates a type with the provided data"""
        type_url = URL + space_id
        type_url += "/types/" + type_data["id"]

        make_call("delete", type_url, f'delete type {type_data["key"]}')

    def update_type(self, space_id: str, type_id: str, type_name: str, type_data: dict):
        """Patches a type with the provided data"""
        type_url = URL + space_id
        type_url += "/types/" + type_id

        make_call("patch", type_url, f"update type {type_name}", type_data)

    def unpack_object(self, object_obj: dict, sub_objects: bool = True):
        """Pulls out name, id, and properties for use"""
        object_dict = {
            "name": object_obj["name"],
            "id": object_obj["id"],
            "type": object_obj["type"]["name"],
        }
        for prop in object_obj["properties"]:
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

    def get_object_by_id(self, space_id: str, object_id: str, simple: bool = True):
        """Pulls detailed object data by id"""
        object_url = URL + space_id
        object_url += OBJ + object_id

        object_obj = make_call("get", object_url, "get object by id")["object"]

        if object_obj is None:
            return "raise exception"

        object_formatted = None

        if isinstance(object_obj, str):
            return {"Clear me": object_obj["id"]}

        if simple:
            object_formatted = self.unpack_object(object_obj, False)
            return object_formatted

        return object_obj

    def update_object(self, space_id, object_name: str, object_id: str, data: dict):
        """Updates object with provided data"""
        object_url = URL + space_id
        object_url += OBJ + object_id
        return make_call(
            "patch", object_url, f"update object ({object_name}) by id", data
        )

    def create_object(self, space_id: str, data: dict):
        """Creates object with provided data"""
        object_url = URL + space_id
        object_url += "/objects"
        return make_call(
            "post",
            object_url,
            f"create object {data['name']} with {data['type_key']} data",
            data,
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

    def get_property_list(self, space_id, system_props=None):
        """Returns a list of all the properties of a space and their properties"""
        prop_url = URL + space_id
        prop_url += PROPS
        props = make_call("get", prop_url, f"get props from space {space_id}")
        system_props = [] if system_props is None else system_props
        formatted_props = {}
        if props["data"]:
            for prop in props["data"]:
                if prop["name"] in system_props:
                    continue
                formatted_props[prop["name"]] = {
                    "id": prop["id"],
                    "key": prop["key"],
                    "name": prop["name"],
                    "format": prop["format"],
                }
                if prop["format"] in ["select", "multiselect"]:
                    formatted_props[prop["name"]]["options"] = self.get_tags_from_prop(
                        space_id, prop["id"]
                    )
            return formatted_props
        return {}

    def get_tags_from_prop(self, space_id: str, prop_id: str):
        """Returns the tag and name from the provided list"""
        tag_url = URL + space_id
        tag_url += PROPS + prop_id
        tag_url += "/tags"
        tags = make_call("get", tag_url, "get tags from property")
        formatted_tags = {}
        if tags["data"]:
            for tag in tags["data"]:
                formatted_tags[tag["name"]] = {
                    "id": tag["id"],
                    "key": tag["key"],
                    "name": tag["name"],
                    "color": tag["color"],
                }
            return formatted_tags
        return {}

    def add_tag_to_select_property(self, space_id: str, prop_id: str, data: dict):
        """Adds option to provided property"""
        prop_url = URL + space_id
        prop_url += PROPS + prop_id
        prop_url += "/tags"
        new_tag = make_call(
            "post",
            prop_url,
            f"add {data['name']} to property",
            data,
        )
        formatted_tag = {}
        if new_tag["tag"]:
            formatted_tag[new_tag["tag"]["name"]] = {
                "id": new_tag["tag"]["id"],
                "key": new_tag["tag"]["key"],
                "name": new_tag["tag"]["name"],
                "color": new_tag["tag"]["color"],
            }
        return formatted_tag

    def create_property(self, space_id: str, data: dict):
        """Adds property to space"""
        prop_url = URL + space_id
        prop_url += "/properties"
        prop_data = {
            "format": data["format"],
            "key": data["key"],
            "name": data["name"],
        }
        new_prop = make_call(
            "post", prop_url, f"add property '{data['name']}' to space", prop_data
        )
        return new_prop["property"]["id"] if new_prop is not None else None

    def delete_property(self, space_id, prop_dict):
        """Removes property from space"""
        prop_url = URL + space_id
        prop_url += "/properties/" + prop_dict["id"]
        prop_url = make_call("delete", prop_url, f'delete property {prop_dict["name"]}')
