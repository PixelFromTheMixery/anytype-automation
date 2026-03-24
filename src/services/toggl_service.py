"""toggl interaction module"""

import datetime
import urllib.parse

from services.anytype.core_service import AnytypeService
from utils.anytype import AnyTypeUtils
from utils.api_tools import make_call
from utils.data import DataManager

from utils.config import Config

DATA = DataManager.get()
TOGGL_WORKSPACE = Config.data["toggl_workspace"]
TOGGL_URL = "https://api.track.toggl.com/api/v9/workspaces/" + TOGGL_WORKSPACE


class TogglService:
    """Toggl class for hosting functions"""

    def __init__(self):
        self.anytype_service = AnytypeService()
        self.anytype_utils = AnyTypeUtils()
        if Config.data["toggl"]:
            self.project_cache = self.collect_projects()

    def start_timer(self, project, task_name):
        """Start a time entry"""
        time_entry_url = TOGGL_URL + "/time_entries"
        project_id = self.project_cache.get(project)
        data = {
            "created_with": "Anytype Automation",
            "description": urllib.parse.unquote(task_name),
            "duration": -1,
            "project_id": project_id,
            "start": datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "workspace_id": int(TOGGL_WORKSPACE),
        }
        make_call(
            "post", time_entry_url, "start time entry for " + task_name, data, "toggl"
        )
        return f"Started {task_name} in {project}"

    def collect_projects(
        self,
    ):
        project_url = TOGGL_URL + "/projects"

        project_map = {}
        project_list = make_call(
            "get", project_url, "collect projects from toggl", None, "toggl"
        )

        for project in project_list:
            project_map[project["name"]] = project["id"]

        return project_map
