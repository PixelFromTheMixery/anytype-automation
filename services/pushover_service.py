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

        data = {"type_key": type_name, "name": date_str + suffix}

        if template != "":
            data["template_id"] = config["templates"]["ritual"][template]

        new_obj = self.anytype.create_object(space_id, type_name, data)
        obj_url = self.pushover.make_deeplink(
            new_obj["object"]["id"], config["spaces"]["archive"]
        )

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
        task_segments = config["views"]["task_by_day"]

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
            task_segments[segment], "simple", config["queries"]["task_by_day"]
        )
        if len(tasks) == 0:
            return None
        message = f"You have {str(len(tasks))} recommended task"
        if len(tasks) > 1:
            message += "s"
        message += "<br>"
        link = self.pushover.make_deeplink(
            config["queries"]["task_by_day"], config["spaces"]["archive"]
        )

        message += f"<a href='{link}'>Here's the link.<a/> And here is the list:"
        for task in tasks:
            message += f"<p>{task['name']}</p>"
        message += f"<a href='{link}'>Here's the link again.<a/>😉"

        self.pushover.send_message(title, message)

    def pushover_test(self):
        """Testing notification service"""
        link = "https://object.any.coop/bafyreihpmajq4tyclweganwy4djfwl4cvh3kcj6pzbw7ereivnaay4be5u?spaceId=bafyreifxsujwztkbi2zrf3yudthopppmhcz36aiyozmbuc323ai6q6347e.2bx9tjqqte21g"
        # link = "https://object.any.coop/bafyreigwthrmmn6mhvwdcjhi2g4z2zvb2t4aj763xaaxubyg4ljjmmx6se?spaceId=bafyreihydnqhxtkwiv55kqafoxyfk3puf7fm54n6txjo34iafbjujbbo2a.2bx9tjqqte21g"
        title = "Pushover Test"
        message = "This is a test message from Anytype Automation."
        message += f"<a href= '{link}'>Link to Anytype object</a>"
        self.pushover.send_message(title, message)
