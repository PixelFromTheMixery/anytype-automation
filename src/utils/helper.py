"""Module for managing non-specific methods"""

import datetime
from dateutil.relativedelta import relativedelta
import re

import yaml


DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"

CONVERTER = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

PATTERN = r"(\d)-(day|week|month|quarter|year)(:?(?:mon|tue|wed|thu|fri|sat|sun|\d+]))?(@\d{1,4})?"

DELTA_MAP = {
    "day": lambda d, n: d + relativedelta(days=n),
    "week": lambda d, n: d + relativedelta(weeks=n),
    "month": lambda d, n, m=None: (
        d + relativedelta(months=n, day=m) if m else d + relativedelta(months=n)
    ),
    "quarter": lambda d, n: d + relativedelta(months=n * 3),
    "year": lambda d, n: d + relativedelta(years=n),
}

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

    def date_eligibility(self, unit, modifier=None):
        """Returns list of eligible values for days of the week"""

        if unit in ["day", "week", "month", "quarter", "year"]:
            allowed = [0, 1, 2, 3, 4, 5, 6]
        elif unit == "week" and modifier:
            allowed = [CONVERTER[d] for d in modifier.split(",")]
        elif unit == "weekday":
            allowed = [0, 1, 2, 3, 4]
        elif unit == "weekend":
            allowed = [5, 6]
        else:
            allowed = [CONVERTER.get(unit)]

        return allowed

    def next_date(self, rate: str):
        """
        Returns formatted string of the next date based on the timescale provided
        n-unit:modifier@time
        Currently supported units:
        days of the week - 1-week:mon,thu@14
        day of the month - 1-month:15
        """

        captured = re.search(PATTERN, rate).groups()
        n = captured[0]
        unit = captured[1]
        

        exit(0)
        allowed = self.date_eligibility(unit, modifier)


        dt_next = DELTA_MAP.get(unit, lambda d, n: d + relativedelta(days=n))(
            self.get_today(), n
        )

        while dt_next.weekday() not in allowed:
            dt_next += datetime.timedelta(days=1)

        return dt_next.strftime(DATETIME_FORMAT)

    def get_today(self, midnight=True):
        """gets midnight today"""
        now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)

        if midnight:
            now = now.replace(hour=0)

        return now
