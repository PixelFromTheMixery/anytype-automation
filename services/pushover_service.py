"""Notification service for Anytype."""

import datetime

from utils.anytype import AnyTypeUtils
from utils.config import Config

from utils.pushover import PushoverUtils


class PushoverService:
    """Handles notifications for Anytype."""

    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = PushoverUtils()

    def create_object_and_notify(
        self,
        type_name: str,
        template: str,
        suffix: str,
        target_space: str,
    ):
        """Create objects and link via pushover"""
        dt_now = datetime.datetime.now()
        date_str = dt_now.strftime("%d/%m/%y")

        space_id = Config.data["spaces"][target_space]

        data = {"type_key": type_name, "name": date_str + suffix}

        new_obj = self.anytype.create_object(space_id, type_name, data)
        obj_url = self.pushover.make_deeplink(
            new_obj["object"]["id"], space_id
        )

        title = ""
        if type_name == "entry":
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
        task_segments = Config.data["queries"]["task_by_day"]

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

        tasks = self.anytype.get_list_view_objects(
            task_segments[segment], "simple", Config["queries"]["task_by_day"]
        )
        if len(tasks) == 0:
            return None
        message = f"You have {str(len(tasks))} recommended task"
        if len(tasks) > 1:
            message += "s"
        message += "<br>"
        link = self.pushover.make_deeplink(
            Config.data["queries"]["task_by_day"], Config.data["spaces"]["journal"]
        )

        message += f"<a href='{link}'>Here's the link.<a/> And here is the list:"
        for task in tasks:
            message += f"<p>{task['name']}</p>"
        message += f"<a href='{link}'>Here's the link again.<a/>😉"

        self.pushover.send_message(title, message)

    def pushover_test(self, test_option:int = 0):
        """Testing notification service"""
        link = "https://object.any.coop/bafyreihpmajq4tyclweganwy4djfwl4cvh3kcj6pzbw7ereivnaay4be5u?spaceId=bafyreifxsujwztkbi2zrf3yudthopppmhcz36aiyozmbuc323ai6q6347e.2bx9tjqqte21g"
        
        url = "https://api.pushover.net/1/messages.json"

        if test_option == 0:
            title = "Pushover Test"
            message = "This is a test message from Anytype Automation."
            message += f"<a href= '{link}'>Link to Anytype object</a>"
        self.pushover.send_message(title, message)
