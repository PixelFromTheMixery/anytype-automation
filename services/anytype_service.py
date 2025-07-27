"""Module for handling automation behaviour"""

import datetime
from dateutil.relativedelta import relativedelta, weekday

from utils.anytype import AnyTypeUtils
from utils.config import config, archive_log, load_archive_logging, save_archive_logging
from utils.logger import logger
from utils.pushover import PushoverUtils


class AnytypeAutomation:
    """
    Anytype Services manages the current tasks:
    - resets task due date to today if overdue (simple)
    - adds task to collection based on project
    """
    def __init__(self):
        self.anytype = AnyTypeUtils()
        self.pushover = PushoverUtils()
        self.converter = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

    def search(self, search_critera: str, obj: bool = True, search_filter: str = ""):
        """Conducts a search with provided data"""
        return self.anytype.search_by_type_and_or_name(
            search_critera, obj, search_filter
        )

    def next_date(self, date: datetime.datetime, timescale: str, freq: int):
        """Returns formatted string of the next date based on the timescale provided"""
        day_int = -1
        if timescale in self.converter:
            day_int = self.converter[timescale]
        dt_next = datetime.datetime
        if timescale == "Day":
            dt_next =  date + relativedelta(days=freq)
        elif timescale == "Week":
            dt_next =  date + relativedelta(weeks=freq)
        elif timescale == "Month":
            dt_next =  date + relativedelta(months=freq)
        elif timescale == "Year":
            dt_next = date + relativedelta(years=freq)
        elif timescale == "Weekday":
            dt_next = date + datetime.timedelta(days=freq)
            while dt_next.weekday() >= 5:
                dt_next += datetime.timedelta(days=freq)
        elif timescale == "Weekend":
            dt_next = date + datetime.timedelta(days=freq)
            while dt_next.weekday() < 5:
                dt_next += datetime.timedelta(days=freq)
        else:
            dt_next = date + relativedelta(days=1)
            dt_next = dt_next + relativedelta(weekday=weekday(day_int)(+freq))

        return dt_next.strftime("%Y-%m-%dT%H:%M:%SZ")

    def view_list(self, list_id: str = config["queries"]["automation"]):
        """Formats view objects into consumable objects to add to this object"""
        return self.anytype.get_views_list(list_id)

    def overdue(self, dt_now):
        """Updates due date to tomorrow at 11pm so it will be 'today' upon viewing"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["overdue"],
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"

        dt_next = dt_now + datetime.timedelta(days=1)

        if len(tasks_to_check) > 15:
            self.pushover.send_message(
                "Loads of tasks incoming",
                f"There are {len(tasks_to_check)} incoming. Please have a gentle day.",
                1,
            )

        tasks_to_review = []
        for task in tasks_to_check:
            data = {"properties": []}

            data["properties"].append(
                {"key": "due_date", "date": dt_next.strftime("%Y-%m-%dT%H:%M:%SZ")}
            )
            if "Reset Count" not in task:
                task["Reset Count"] = 0
            elif task["Status"] != "Blocked":
                task["Reset Count"] = task["Reset Count"] + 1

            if task["Rate"] != "Once" and task["Frequency"] is None:
                task["Frequency"] = 1

            if task["Reset Count"] > 4:
                data["properties"].append(
                    {"key": "status", "select": config["tags"]["status"]["review"]}
                )
                data["properties"].append(
                    {
                        "key": "review_date",
                        "date": dt_now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                )
                tasks_to_review.append(task["name"])
            data["properties"].append(
                {"key": "reset_count", "number": task["Reset Count"]}
            )
            self.anytype.update_object(task["name"], task["id"], data)
        if tasks_to_review:
            message = "The following tasks have been reset 5 times, please review:"
            for task in tasks_to_review:
                message += "<br>" + task
            url = self.pushover.make_deeplink(
                config["queries"]["task_cleanup"], config["spaces"]["main"]
            )
            message += f"<br><a href={url}>Link here</a>"
            self.pushover.send_message("Task reset threshold reached", message, 1)

        return f"{len(tasks_to_check)} tasks with dates updated"

    def set_collections(self):
        """Assigns collection to task based on project"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["aoc"], "full"
        )
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            logger.info("No tasks to update")
            return None
        project = ""
        aoc = ""
        tasks_to_add = []
        for task in tasks_to_check:
            if project != task["Project"][0]["name"]:
                project = task["Project"][0]["name"]
                project_obj = self.anytype.get_object_by_id(
                    task["Project"][0]["id"], "project"
                )
                if aoc != project_obj["AoC"]["name"]:
                    if len(tasks_to_add) != 0:
                        self.anytype.add_to_list(
                            aoc, config["collections"][aoc], tasks_to_add
                        )
                    tasks_to_add = []
                    aoc = project_obj["AoC"]["name"]
            tasks_to_add.append(task["id"])
        self.anytype.add_to_list(aoc, config["collections"][aoc], tasks_to_add)

    def summary_writer(self):
        """Write summery of task"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["summary"]
        )
        # TODO: performance improvement, code duplication, raise exception
        if tasks_to_check is None:
            return "raise exception"
        if len(tasks_to_check) == 0:
            return "No tasks to update"
        for task in tasks_to_check:
            summary = task["Interval"]
            try:
                summary += ", " + "Urgent" if task["Urgent"] else ""
            except KeyError:
                pass
            try:
                summary += ", " + "Important" if task["Important"] else ""
            except KeyError:
                pass
            summary += ", " + task["Function"]
            summary += ", " + task["Day Segment"]
            if task["Rate"] != "Once":
                if task["Frequency"] > 1:
                    task["Rate"] = task["Rate"] + "s"
                summary += ", every " + str(task["Frequency"]) + " " + task["Rate"]
            self.anytype.update_object(
                task["name"],
                task["id"],
                {"properties": [{"key": "summary", "text": summary}]},
            )

    def set_reflection(self, dt_now):
        """Sets review obj for task"""
        objs_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["reflection"]
        )
        for obj in objs_to_check:

            data = {
                "type_key": "reflection",
                "name": obj["name"],
                "template_id": config["templates"]["reflection"],
                "properties": [
                    {"key": "due_date", "date": dt_now.strftime("%Y-%m-%dT%H:%M:%SZ")}
                ],
            }

            if obj["Rate"] != "Once":
                data["properties"].append({"key": "repeating_task", "checkbox": True})

            reflection = self.anytype.create_object(
                config["spaces"]["main"], "reflection", data
            )

            if reflection is None:
                logger.error("Can't find created reflection object")
                break

            data = {}
            data = {
                "properties": [
                    {"key": "reflection", "objects": [reflection["object"]["id"]]}
                ]
            }
            self.anytype.update_object(obj["name"], obj["id"], data)

    def reflection_updates(self, dt_now):
        """Updates dates of completed reflections"""
        objs_to_check = self.anytype.get_list_view_objects(
            config["views"]["reflect"]["to_adjust"],
            list_id=config["queries"]["reflect"],
        )
        for obj in objs_to_check:
            new_tag = obj["Rate"]
            new_day = dt_now

            if obj["Rate"] == "Day":
                new_tag = config["tags"]["rate"]["week"]
                new_day = self.next_date(dt_now, "Week", 1)
            elif obj["Rate"] == "Week":
                new_tag = config["tags"]["rate"]["month"]
                new_day = self.next_date(dt_now, "Month", 1)
            elif obj["Rate"] == "Month":
                new_tag = config["tags"]["rate"]["quarter"]
                new_day = self.next_date(dt_now, "Month", 3)
            elif obj["Rate"] == "Quarter":
                if "Repeating Task" in obj:
                    new_tag = config["tags"]["rate"]["quarter"]
                    new_day = self.next_date(dt_now, "Month", 3)
                else:
                    new_tag = config["tags"]["rate"]["year"]
                    new_day = self.next_date(dt_now, "Year", 1)
            elif "Year" in obj["Rate"]:
                new_day = self.next_date(dt_now, "Year", 1)
            data = {
                "properties": [
                    {"key": "status", "select": config["tags"]["status"]["review"]},
                    {"key": "rate", "select": new_tag},
                    {"key": "due_date", "date": new_day},
                ]
            }
            self.anytype.update_object(obj["name"], obj["id"], data)

    def daily_rollover(self):
        """Daily automation script"""
        logger.info("Running missing collections")
        self.set_collections()
        logger.info("Running writing summaries")
        self.summary_writer()

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        logger.info("Running overdue tasks")
        self.overdue(dt_now)
        logger.info("Setting reflections")
        self.set_reflection(dt_now)
        logger.info("Updating Reflections")
        self.reflection_updates(dt_now)
        logger.info("Daily Rollover completed")

    def get_or_create_archive_tag(self, prop_name, value):
        """Get or create a tag for a given property in archive_log."""
        try:
            return archive_log[prop_name][value]
        except (KeyError, IndexError):
            tag_id = self.anytype.add_option_to_property(
                config["spaces"]["archive"],
                archive_log[prop_name]["id"],
                prop_name,
                value,
            )
            archive_log[prop_name][value] = tag_id
            save_archive_logging(archive_log)
            load_archive_logging()
            return tag_id

    def define_log_object(self, task):
        """Define log object for archival"""
        data = {}
        data["type_key"] = "log"
        data["name"] = task["name"]
        props = [
            {"key": "do_d", "text": task["DoD"]},
            {
                "key": "function",
                "select": self.get_or_create_archive_tag("Function", task["Function"]),
            },
            {
                "key": "interval",
                "select": self.get_or_create_archive_tag("Interval", task["Interval"]),
            },
            {
                "key": "day_segment",
                "select": self.get_or_create_archive_tag(
                    "Day Segment", task["Day Segment"]
                ),
            },
            {
                "key": "project",
                "select": self.get_or_create_archive_tag(
                    "Project", task["Project"][0]["name"]
                ),
            },
        ]
        for link in task["Backlinks"]:
            if link["name"] in [
                "Care",
                "Finance",
                "Home",
                "Management",
                "Self-Dev",
                "Workshop",
            ]:
                props.append(
                    {
                        "key": "ao_c",
                        "text": self.get_or_create_archive_tag("AoC", link["name"]),
                    },
                )
                break

        data["properties"] = props
        return data

    def migrate_tasks(self):
        """Migrate completed tasks that occur once to archive"""
        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["migrate"], "full"
        )
        if not tasks_to_check:
            return "No tasks to update"
        try:
            for task in tasks_to_check:
                data = self.define_log_object(task)
                self.anytype.create_object(
                    config["spaces"]["archive"], task["name"], data
                )
                self.anytype.delete_object(task["name"], task["id"])
        finally:
            self.set_collections()
            tasks_to_check = self.anytype.get_list_view_objects(
                config["views"]["automation"]["migrate"], "full"
            )
            for task in tasks_to_check:
                data = self.define_log_object(task)
                self.anytype.create_object(
                    config["spaces"]["archive"], task["name"], data
                )
                self.anytype.delete_object(task["name"], task["id"])

    def reset_repeating(self):
        """Log and reset repeating tasks"""

        tasks_to_check = self.anytype.get_list_view_objects(
            config["views"]["automation"]["reset"], "full"
        )
        if not tasks_to_check:
            return "No tasks to update"

        dt_now = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        for task in tasks_to_check:
            if "Summary" not in task:
                self.summary_writer()
                self.reset_repeating()
                break

            data = self.define_log_object(task)
            self.anytype.create_object(config["spaces"]["archive"], task["name"], data)
            data = {
                "properties": [
                    {
                        "key": "due_date",
                        "date": self.next_date(
                            dt_now,
                            task["Rate"],
                            task["Frequency"] if "Frequency" in task else 1,
                        ),
                    },
                    {"key": "reset_count", "number": 0},
                    {
                        "key": "status",
                        "select": config["tags"]["status"]["repeating"],
                    },
                ]
            }
            self.anytype.update_object(task["name"], task["id"], data)

    def recurrent_check(self):
        """Recurrent automation script"""
        logger.info("Running completed task migration")
        self.migrate_tasks()
        logger.info("Running repeating task reset")
        self.reset_repeating()

    def test(self):
        """Temp endpoint for testing"""
        return self.anytype.get_tag_from_list(
            config["spaces"]["main"],
            "bafyreiakcjhtb4elqbuqznpjditjaitei2gqxj7jf62qi7qqfptetpybve",
            "bleh",
        )
        return self.anytype.test()
