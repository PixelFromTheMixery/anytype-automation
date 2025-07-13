from utils.api_tools import make_call_with_retry
from utils.logger import logger

import json

# bafyreibhhlelfjv2kmtomcbgsprj3xjjx4xtw3oqh4qtvwfyquyg4gcbbi #automation list

class AnyTypeUtils:
    def __init__(self):
        self.url = "http://localhost:31009/v1/spaces/"
        self.main_space_id = "bafyreihydnqhxtkwiv55kqafoxyfk3puf7fm54n6txjo34iafbjujbbo2a.2bx9tjqqte21g/"
        self.archive_space_id="bafyreifxsujwztkbi2zrf3yudthopppmhcz36aiyozmbuc323ai6q6347e.2bx9tjqqte21g/"
        self.automation_list_id="bafyreibhhlelfjv2kmtomcbgsprj3xjjx4xtw3oqh4qtvwfyquyg4gcbbi/"

    def get_views_list(self):
        views_url = self.url + self.main_space_id
        views_url += "lists/" + self. automation_list_id
        views_url += "views"

        return make_call_with_retry("get", views_url, "get view list from automation query")

    def get_list_view_objects(self, view_id):
        tasks_url = self.url + self.main_space_id
        tasks_url += "lists/" + self.automation_list_id
        tasks_url += "views/" + view_id
        tasks_url += "objects"
        main_tasks = make_call_with_retry("get", tasks_url, "get tasks")

        tasks_to_check = []

        if main_tasks and "data" in main_tasks:
            for task in main_tasks["data"]:
                tasks_to_check.append({"id": task["id"], "name": task["name"]})
            return tasks_to_check
        else:
            return []

    def get_task_by_id(self, task: dict):
        task_url = self.url + self.main_space_id
        task_url += "objects/" + task["id"]
        return make_call_with_retry("get", task_url, f"get task ({task['name']}) by id")

    def update_task(self, task_name: str, task_id: str, data: dict):
        task_url = self.url + self.main_space_id
        task_url += "objects/" + task_id
        return make_call_with_retry("patch", task_url, f"update task ({task_name}) by id", data)
