from utils.anytype import AnyTypeUtils
from utils.data import DataManager
from utils.helper import Helper
from utils.pushover import PushoverUtils

DATA = DataManager.get()


class JournalService:
    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.helper = Helper()
        self.pushover = PushoverUtils()

    def find_or_create_day_journal(self, dt_hour, dt_day_str, dt_tmw_str):
        """Searches for or creates a journal for the day"""

        date_str = dt_day_str if dt_hour >= 21 else dt_tmw_str

        entry = self.anytype.search(
            DATA["journal"]["id"], "looking for journal object", {"query": date_str}
        )

        if not entry:

            data = {
                "name": date_str,
                "type_key": "entry",
                "template_id": DATA["journal"]["types"]["Entry"]["templates"]["Day"],
            }

            # Matching output of search
            entry = {
                # fmt: off
                date_str: self.anytype.create_object(
                    DATA["journal"]["id"], data
                )["object"]["id"]
            }

        message = ""

        if dt_hour <= 6:
            message = "Good morning! Start your day right with "
        elif dt_hour == 20:
            message = "Good evening! Take a look back on your day with "
        elif dt_hour > 20:
            message = "Good evening! Plan your tomorrow with "
        else:
            message = "Hey, hey, please take a moment to check in with "

        link = f"""<a href={self.helper.make_deeplink(
            DATA["journal"]["id"], entry[date_str]
        )}>this</a>!"""

        self.pushover.send_message("Check in", message + link)

    # def reflection_updates(self, dt_now, date_next):
    #     """Updates dates of completed reflections"""
    #     # TODO: Not in use, refine
    #     objs_to_check = self.anytype.get_list_view_objects(
    #         DATA["journal"]["id"],
    #         DATA["journal"]["queries"]["reflections"]["id"],
    #         DATA["journal"]["queries"]["reflections"]["update"],
    #     )
    #     for obj in objs_to_check:
    #         today_day = dt_now

    #         if "Rate" not in obj or obj["Rate"] == "":
    #             new_tag = "1@day"
    #         elif obj["Rate"] == "1@day":
    #             new_tag = "1@week"
    #         elif obj["Rate"] == "Week":
    #             new_tag = "1@month"
    #         elif obj["Rate"] == "Month":
    #             new_tag = "1@quarter"
    #         elif obj["Rate"] == "Quarter" and "Repeating Task" not in obj:
    #             new_tag = "1@year"

    #         new_day = self.next_date(today_day, new_tag)

    #         data = {
    #             "properties": [
    #                 {
    #                     "key": "status",
    #                     "select": DATA["tags"]["journal"]["Status"]["options"][
    #                         "Review"
    #                     ]["id"],
    #                 },
    #                 {"key": "rate", "text": new_tag},
    #                 {"key": "due_date", "date": new_day},
    #             ]
    #         }
    #         # self.anytype.update_object(obj["name"], obj["id"], data)
