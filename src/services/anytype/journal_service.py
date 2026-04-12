import json


from utils.anytype import AnyTypeUtils
from utils.helper import Helper
from utils.date_tools import get_today
from utils.logger import logger
from utils.pushover import PushoverUtils


class JournalService:
    def __init__(self, settings):
        self.settings = settings
        self.data = self.settings.data.anytype
        self.space_id = self.settings.config.journal_space_id
        self.task_space = self.settings.config.task_space_id
        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        if settings.config.pushover:
            self.pushover = PushoverUtils()

    def find_or_create_day_journal(self):
        """Searches for or creates a journal for the day"""
        dt_now = get_today()
        date_str = dt_now.strftime(r"%d.%m.%y")

        entry = self.anytype.search(
            self.space_id,
            "looking for journal object",
            {"query": date_str},
        )

        if not entry:

            data = {
                "name": date_str,
                "type_key": "entry",
                "template_id": self.data["journal"].types["Entry"].templates["Day"],
            }

            # Matching output of search
            entry = {
                date_str: self.anytype.create_object(self.space_id, data)["object"][
                    "id"
                ]
            }

        message = ""

        dt_hour = dt_now.hour

        if dt_hour <= 6:
            message = "Good morning! Start your day right with "
        elif dt_hour == 20:
            message = "Good evening! Take a look back on your day with "
        elif dt_hour > 20:
            message = "Good evening! Plan your tomorrow with "
        else:
            message = "Hey, hey, please take a moment to check in with "

        link = f"""<a href={self.helper.make_deeplink(
            self.space_id, entry[date_str]
        )}>this</a>!"""

        self.pushover.send_message("Check in", message + link)

    def log_object(self, obj_dict):
        """
        Define log object for archival
        """
        data = {
            "type_key": "log",
            "name": obj_dict["name"],
            "properties": [
                {
                    "key": "log_type",
                    "select": self.data["journal"]
                    .props["Log Type"]
                    .options[obj_dict["type"]]
                    .id,
                },
                {"key": "logged", "date": get_today(string=True)},
            ],
        }

        metadata_dict = {}
        sorting = self.settings.config.log_props
        for prop in obj_dict:
            if prop not in sorting:
                continue
            try:
                metadata_dict[prop] = obj_dict[prop]
            except KeyError:
                logger.warning("prop not discovered, might not matter")
        sorted_data = {k: metadata_dict[k] for k in sorting}
        data["properties"].append({"key": "metadata", "text": json.dumps(sorted_data)})
        self.anytype.create_object(self.space_id, data)

    def log_habit(self, object_id):
        obj_dict = self.anytype.get_object_by_id(self.task_space, object_id)

        self.log_object(obj_dict)

        new_count = obj_dict["Count"] + 1
        self.anytype.update_object(
            self.task_space,
            obj_dict["name"],
            object_id,
            {"properties": [{"key": "count", "number": new_count}]},
        )

        return {
            "Habit logged": obj_dict["name"],
            "Habit count": "✨" + str(new_count) + "✨",
        }

    def review_overflow(self, task, space_id):
        self.anytype.create_object(
            self.data["journal"].id,
            {
                "template_id": self.data["journal"]
                .types["Prompt"]
                .templates["Task Review"],
                "name": task["name"],
                "type_key": "prompt",
                "properties": [
                    {
                        "key": "url",
                        "url": self.helper.make_deeplink(space_id, task["id"]),
                    }
                ],
            },
        )
