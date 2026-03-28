"""toggl interaction module"""

import datetime
import urllib.parse

from fastapi import Depends

from utils.anytype import AnyTypeUtils
from utils.api_tools import make_call

from settings import generate_settings


def get_settings():
    """Generates Settings singleton"""
    return generate_settings()


class TogglService:
    """Toggl class for hosting functions"""

    def __init__(self, settings):
        self.settings = settings
        self.anytype_utils = AnyTypeUtils()
        self.api = "https://api.track.toggl.com/api/v9/workspaces/"

    def start_timer(self, project, task_name, settings=Depends(get_settings)):
        """Start a time entry"""
        time_entry_url = self.api + "/time_entries"
        project_id = settings.data.toggl.projects.get(project)
        data = {
            "created_with": "Anytype Automation",
            "description": urllib.parse.unquote(task_name),
            "duration": -1,
            "project_id": project_id,
            "start": datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "workspace_id": int(self.workspace),
        }
        make_call(
            "post", time_entry_url, "start time entry for " + task_name, data, "toggl"
        )
        return f"Started {task_name} in {project}"

    def collect_projects(
        self,
    ):
        project_url = self.api + self.settings.data.toggle.projects + "/projects"

        project_map = {}
        project_list = make_call(
            "get", project_url, "collect projects from toggl", None, "toggl"
        )

        for project in project_list:
            project_map[project["name"]] = project["id"]

        return project_map

    def check_subscriptions(
        self,
    ):
        pass
