from typing import Any, Optional

from pydantic import BaseModel, field_validator, model_validator

WEEKDAY_SHORT = [
    "mon"
]

class DueDateTime(BaseModel):
    number: int
    unit: str
    modifier: Optional[str|int]
    due_time: Optional[str]S

    @model_validator(mode="after")
    @classmethod
    def possible_modifiers(cls, data: Any):
        if data["unit"] == "week":
            if data["modifier"] not in []
        pass

    @field_validator("unit", mode="after")
    @classmethod
    def possible_units(cls, value: str)
        if value not in [""]

        return value