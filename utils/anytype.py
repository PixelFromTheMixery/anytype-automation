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
                task_object = self.get_task_by_id(task)
                if task_object and "object" in task_object:
                    tasks_to_check.append(task_object["object"])

        return tasks_to_check

    def get_task_by_id(self, task: dict):
        """Pulls detailed object data"""
        task_url = self.url + self.main_space
        task_url += "objects/" + task["id"]
        return make_call("get", task_url, f"get task ({task['name']}) by id")

    def update_task(self, task_name: str, task_id: str, data: dict):
        """Updates tasks with  porvided data"""
        task_url = self.url + self.main_space
        task_url += "objects/" + task_id
        return make_call("patch", task_url, f"update task ({task_name}) by id", data)
