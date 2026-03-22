import datetime
from dateutil.relativedelta import relativedelta

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


class Helper:

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
        n@unit:modifier
        Currently supported units:
        days of the week - 1@week:mon,thu
        day of the month - 1@month:15
        """
        n, unit = rate.split("@")
        n = int(n)
        modifier = None
        if ":" in unit:
            unit, modifier = unit.split(":", 1)
            if unit in ["month", "year"]:
                modifier = int(modifier)

        allowed = self.date_eligibility(unit, modifier)

        delta_map = {
            "day": lambda d, n: d + relativedelta(days=n),
            "week": lambda d, n: d + relativedelta(weeks=n),
            "month": lambda d, n, m=None: (
                d + relativedelta(months=n, day=m) if m else d + relativedelta(months=n)
            ),
            "quarter": lambda d, n: d + relativedelta(months=n * 3),
            "year": lambda d, n: d + relativedelta(years=n),
        }
        dt_next = delta_map.get(unit, lambda d, n: d + relativedelta(days=n))(
            self.get_today, n
        )

        while dt_next.weekday() not in allowed:
            dt_next += datetime.timedelta(days=1)

        return dt_next.strftime(DATETIME_FORMAT)

    def get_today(self):
        """gets midnight today"""
        return datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
