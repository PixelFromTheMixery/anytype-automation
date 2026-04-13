import re

import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

DATETIME_FORMAT = r"%Y-%m-%dT%H:%M:%SZ"

PATTERN = r"(\d+)-(day|weekd(?:day|end)?|month|quarter|year)(.+)?"

CONVERTER = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

DELTA_MAP = {
    "day": lambda d, n: d + relativedelta(days=n),
    "week": lambda d, n: d + relativedelta(weeks=n),
    "month": lambda d, n,: d + relativedelta(months=n),
    "quarter": lambda d, n: d + relativedelta(months=n * 3),
    "year": lambda d, n: d + relativedelta(years=n),
}


def get_today(replace=[0, 0], string: bool = False):
    """gets midnight today"""

    now = datetime.now().replace(
        hour=replace[0], minute=replace[1], second=0, microsecond=0
    )
    if string:
        return now.strftime(DATETIME_FORMAT)
    return now


def date_eligibility(unit, modifier=None):
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


def unpack_time(time_str: str, minute: int = 0):
    hour = 0

    if len(time_str) > 2:
        minute = int(time_str[-2:])
        hour = int(time_str[:-2])
    else:
        hour = int(time_str)

    if hour < 0 or hour > 23:
        raise ValueError("Hour must be in 0-23")

    if minute < 0 or minute > 59:
        raise ValueError("Minute must be in 0-59")

    return hour, minute


def validate_modifiers(unit, extra):
    if unit == "week":
        mods = extra.split(",")
        for mod in mods:
            if mod not in CONVERTER:
                raise ValueError(
                    "Week modifier must be a comma separated list from list of: "
                    + CONVERTER.keys()
                )
        return mods
    if unit == "month":
        extra_int = int(extra)
        if -30 >= extra_int >= 30:
            raise ValueError(
                "Month modifier must be within a length of a month. "
                "If you need last day of the month, try '-1'"
            )
    return extra_int


def unpack_extra(extra_str: str, unit: str):

    hour = 0
    minute = 0
    modifiers = []

    possible_extras = extra_str.split(":@")

    for extra in possible_extras:
        if "@" in extra:
            hour, minute = unpack_time(extra.lstrip("@"))
        if ":" in extra:
            modifiers = validate_modifiers(unit, extra.lstrip(":"))

    return modifiers, hour, minute


def process_due_datetime(number, unit, extra):

    hour: int = 0
    minute: int = 0
    modifier: int | list[str]

    if extra is not None:
        modifier, hour, minute = unpack_extra(extra, unit)

    if unit == "month" and modifier:
        dt_now = datetime.now()
        if modifier < 0:
            _, last_day_num = calendar.monthrange(dt_now.year, dt_now.month)
            modifier = modifier + last_day_num
        dt_next: datetime = dt_now + relativedelta(months=number, day=modifier)

    else:
        dt_next: datetime = DELTA_MAP.get(unit, lambda d, n: d + relativedelta(days=n))(
            datetime.now(),
            number,
        )
        allowed = [0, 1, 2, 3, 4, 5, 6]

        while dt_next.weekday() not in allowed:
            dt_next += datetime.timedelta(days=1)

    dt_next = dt_next.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return dt_next


def get_next_date(rate_str: str):
    """
    Returns formatted string of the next date based on the timescale provided
    n-unit:modifier@time
    Currently supported units:
    days of the week - 1-week:mon,thu@14
    day of the month - 1-month:15
    """

    captured = re.search(PATTERN, rate_str).groups()

    number: int = int(captured[0])
    unit: str = captured[1]
    extra: [str] = captured[2] if captured[2] else None

    dt_next = process_due_datetime(number, unit, extra)

    return dt_next.strftime(DATETIME_FORMAT)
