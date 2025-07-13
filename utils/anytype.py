"""Utility module for anytype, abstracted for common tasks"""

from utils.api_tools import make_call


class AnyTypeUtils:
    """
    Pulls views for automation, refer to anytype service
    Pulls object details in views in views
    Updates tasks with provided data
    """

    def __init__(self):
        self.url = "http://localhost:31009/v1/spaces/"

        self.main_space = (
            "bafyreihydnqhxtkwiv55kqafoxyfk3puf7fm54n6txjo34iafbjujbbo2a.2bx9tjqqte21g/"
        )
        self.archive_space = (
            "bafyreifxsujwztkbi2zrf3yudthopppmhcz36aiyozmbuc323ai6q6347e.2bx9tjqqte21g/"
        )
        self.automation_list = (
            "bafyreibhhlelfjv2kmtomcbgsprj3xjjx4xtw3oqh4qtvwfyquyg4gcbbi/"
        )
        self.me = "_participant_bafyreihydnqhxtkwiv55kqafoxyfk3puf7fm54n6txjo34iafbjujbbo2a_2bx9tjqqte21g_ABDuEvCxWRjgHiuX1XL2384JN95jYnEPYvnmxFYQTg4zfLzW"

    def get_views_list(self):
        """Pull all views(queries) in the automation query object"""
        views_url = self.url + self.main_space
        views_url += "lists/" + self.automation_list
        views_url += "views"

        views = make_call("get", views_url, "get view list from automation query")
        views_formatted = []

        for view in views if views is not None else []:
            views_formatted.append({"name": view["name"], "id": view["id"]})

        return views_formatted

    def get_list_view_objects(self, view_id):
        """Pulls out detailed information of objects in a view (query)"""
        tasks_url = self.url + self.main_space
        tasks_url += "lists/" + self.automation_list
        tasks_url += "views/" + view_id
        tasks_url += "objects"
        main_tasks = make_call("get", tasks_url, "get tasks")

        tasks_to_check = []

        if main_tasks and "data" in main_tasks:
            for task in main_tasks["data"]:
                tasks_to_check.append(self.get_task_by_id(task["id"]))

        return tasks_to_check

    def unpack_object(self, task_object: dict):
        """Pulls out name, id, and properties for use"""
        task_dict = {
            "name": task_object["object"]["name"],
            "id": task_object["object"]["id"],
        }
        for prop in task_object["object"]["properties"]:
            prop_type = prop["format"]
            prop_value = None
            # Basic props that match their type
            if prop_type in ["checkbox", "date", "number", "text", "url"]:
                prop_value = prop[prop_type]

            elif prop_type == "select, multiselect":
                prop_value = prop[prop_type]["name"]

            elif prop_type == "objects":
                if prop[prop_type] is None:
                    continue
                for object_id in prop[prop_type]:
                    if "participant" in object_id:
                        continue
                    else:
                        prop_value = self.get_task_by_id(object_id, True)

            task_dict[prop["name"]] = {
                "type": prop_type,
                "value": prop_value,
            }

        return task_dict

    def get_task_by_id(self, task_id: str, simple: bool = False):
        """Pulls detailed object data"""
        task_url = self.url + self.main_space
        task_url += "objects/" + task_id

        task_obj = make_call("get", task_url, "get task by id")

        if task_obj is None:
            return "raise exception"

        task_formatted = None

        if simple:
            task_formatted = {
                "name": task_obj["object"]["name"],
                "id": task_obj["object"]["id"],
            }
        elif task_obj is not None:
            task_formatted = self.unpack_object(task_obj)
        else:
            return "Task is not none"
        return task_formatted

    def update_task(self, task_name: str, task_id: str, data: dict):
        """Updates tasks with  porvided data"""
        task_url = self.url + self.main_space
        task_url += "objects/" + task_id
        return make_call("patch", task_url, f"update task ({task_name}) by id", data)
