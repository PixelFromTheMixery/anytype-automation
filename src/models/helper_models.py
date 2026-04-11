from typing import Any, Optional

from datetime import datetime
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, field_validator, model_validator

WEEKDAY_SHORT = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

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
    "month": lambda d, n, m=None: (
        d + relativedelta(months=n, day=m) if m else d + relativedelta(months=n)
    ),
    "quarter": lambda d, n: d + relativedelta(months=n * 3),
    "year": lambda d, n: d + relativedelta(years=n),
}


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


class DueDateTime(BaseModel):
    number: str
    unit: str
    extra: Optional[str] = None

    @field_validator("number", mode="after")
    @classmethod
    def convert_number(cls, value: str):
        return int(value)

    @model_validator(mode="after")
    @classmethod
    def possible_modifiers(cls, data: Any):

        # values = (
        #     data["modifier"].split(",")
        #     if "," in data["modifier"]
        #     else [data["modifier"]]
        # )
        # if data["unit"] == "week":
        #     for value in values:
        #         if value not in WEEKDAY_SHORT:
        #             raise ValueError(
        #                 f"{value} not suitable for week, use one of {WEEKDAY_SHORT}"
        #             )
        # if data["unit"] == "month":
        #     for value in values:
        #         int_value = int(value)
        #         if int_value > 31 or int_value < 1:
        #             raise ValueError(f"{value} not suitable for month, must be 1-31")

        # allowed = date_eligibility(data["unit"], data["modifier"])

        dt_next = DELTA_MAP.get(data.unit, lambda d, n: d + relativedelta(days=n))(
            datetime.now(), data.number
        )

        # while dt_next.weekday() not in allowed:
        #    dt_next += datetime.timedelta(days=1)

        # hour = int(value[0, 1])
        # if hour < 0 or hour > 23:
        #     raise ValueError("Hour must be in 0-23")
        # if len(value) > 2:
        #     minute = int(value[2, 3])
        #     if minute < 0 or minute > 59:
        #         raise ValueError("Minute must be in 0-59")

        # return hour, minute if minute else None

        exit()
        # due_datetime = datetime.strptime()

        return
