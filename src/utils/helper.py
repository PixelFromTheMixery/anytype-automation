"""Module for managing non-specific methods"""

import re

import datetime
import yaml

from models.helper_models import DueDateTime

DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"

PATTERN = r"(\d+)-(day|week|month|quarter|year)(.+)?"


class Helper:

    @staticmethod
    def read_write(path, method, data=None):
        """File interaction central script"""
        with open(path, method, encoding="utf-8") as f:
            if data:
                f.write(yaml.safe_dump(data, sort_keys=False))
            else:
                return yaml.safe_load(f)

    def make_deeplink(self, space_id: str, object_id: str):
        """Builds deeplinks for link purposes"""
        return f"https://object.any.coop/{object_id}?spaceId={space_id}"

    def next_date(self, rate: str):
        """
        Returns formatted string of the next date based on the timescale provided
        n-unit:modifier@time
        Currently supported units:
        days of the week - 1-week:mon,thu@14
        day of the month - 1-month:15
        """
        captured = re.search(PATTERN, rate).groups()

        data_dict: dict = {"number": captured[0], "unit": captured[1]}
        if captured[2]:
            data_dict["extra"]: captured[2]

        dt_next = DueDateTime(**data_dict)

        exit(0)

        return dt_next.strftime(DATETIME_FORMAT)

    def get_today(self, replace=["minute", "hour"], string: bool = False):
        """gets midnight today"""

        now = datetime.datetime.now().replace(microsecond=0, second=0)
        if "minute" in replace:
            now = datetime.datetime.now().replace(minute=0)
        if "hour" in replace:
            now = datetime.datetime.now().replace(hour=0)
        if string:
            return now.strftime(DATETIME_FORMAT)
        return now
