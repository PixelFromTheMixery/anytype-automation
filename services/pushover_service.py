"""Notification service for Anytype."""
import datetime

from utils.anytype import AnyTypeUtils
from utils.config import config

# from utils.logger import logger
from utils.pushover import PushoverUtils


class Pushover:
    """Handles notifications for Anytype."""

    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = PushoverUtils()

    def make_deeplink(self, object_id, space_id: str = config["spaces"]["main"]):
        """Builds deeplinks for link purposes"""
        return f"anytype://object?objectId={object_id}&spaceId={space_id}"

    def create_object_and_notify(
        self,
        type_name: str,
        template: str,
        suffix: str = "",
        space_id: str = config["spaces"]["archive"],
    ):
        """For rituals or day plan or other template based objects"""
        dt_now = datetime.datetime.now()
        date_str = dt_now.strftime("%d/%m/%y")

        data = {
            "type_key" : type_name,
            "name" : date_str + suffix
        }

        if template != "":
            data["template_id"] = config["templates"]["ritual"][template]

        new_obj = self.anytype.create_object(space_id, type_name, data)
        obj_url = self.make_deeplink(new_obj["object"]["id"], config["spaces"]["archive"])

        title = ""
        if type_name == "ritual":
            title = f"{template.capitalize()} Routine"
        elif type_name == "planning_log":
            title = "Daily Planning"

        message = f"<a href={obj_url}>Follow me!</a>"

        self.pushover.send_message(title, message)

    def task_notify(self):
        """Task reminder"""
        dt_now = datetime.datetime.now()
        hour = dt_now.hour
        segment = ""
        task_segments = config["query"]["Task by Day"]

        if hour == 6:
            segment = "morning"
        elif hour == 10:
            segment = "noon"
        elif hour == 14:
            segment = "afternoon"
        elif hour == 18:
            segment = "evening"
        else:
            return None

        title = f"Good {segment}!"

        tasks = self.anytype.get_list_view_objects(task_segments[segment], task_segments["id"], "simple")
        if len(tasks) == 0:
            return None
        message = f"You have {str(len(tasks))} recommended task"
        if len(tasks) > 1:
            message += "s"
        message += "<br>"
        link = self.make_deeplink(task_segments["id"])

        message += f"<a href='{link}'>Here's the link.<a/> And here is the list:"
        for task in tasks:
            message += f"<p>{task['name']}</p>"
        message += f"<a href='{link}'>Here's the link again.<a/>😉"

        self.pushover.send_message(title, message)
