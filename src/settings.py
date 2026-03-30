"""Settings for API"""

from functools import lru_cache
from typing import Annotated

from pydantic import BaseModel, Field

from models.data import ReferenceData
from utils.helper import Helper

helper = Helper()


class ConfigSettings(BaseModel):
    """App configuration"""

    # General
    local: Annotated[
        bool,
        Field(
            description="Flag for development mode, turns off scheduler and notifications",
        ),
    ] = True

    api_addr: Annotated[
        str,
        Field(
            description="Web address at which API is running, for inner use URL generation",
        ),
    ]

    # Task Management
    task_space_id: Annotated[
        str,
        Field(
            description="Anytype space id for task management",
        ),
    ]

    task_reset: Annotated[
        bool,
        Field(
            description="Flag for resetting tasks with a Rate variable",
        ),
    ] = False
    # Task Review
    task_logs: Annotated[
        bool,
        Field(
            description="If task gets logged in journal space",
        ),
    ] = False

    task_log_props: Annotated[
        list[str],
        Field(
            description=(
                "List of Props to put into a metadata dictionary "
                "for simple but flexible task logging"
            ),
        ),
    ]

    task_review_threshold: Annotated[
        int,
        Field(
            description=(
                "Number of says to reset a task before a prompt is generated. "
                "0 is the off switch"
            ),
        ),
    ] = 0

    # Pushover
    pushover: Annotated[
        bool,
        Field(
            description="Flag for pushover notifications",
        ),
    ] = False

    pushover_journal_hours: Annotated[
        list[str],
        Field(
            description="Which hours to send notifications",
        ),
    ] = []


class Settings(BaseModel):
    """The Top-Level Singleton Registry"""

    config: ConfigSettings = Field(default_factory=ConfigSettings)
    data: ReferenceData = Field(default_factory=ReferenceData)


@lru_cache
def generate_settings() -> Settings:
    """Constructor for the weird data sources"""
    try:
        config_yaml = helper.read_write("config.yaml", "r")
    except FileNotFoundError as exc:
        raise FileNotFoundError("config.yaml required") from exc
    try:
        data_yaml = helper.read_write("data/data.yaml", "r")
    except FileNotFoundError:
        print("Reference data file requires generation")
        data_yaml = {}

    return Settings(
        config=ConfigSettings(**config_yaml),
        data=ReferenceData(**data_yaml),
    )
