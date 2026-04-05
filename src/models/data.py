"""Data model for local caching"""

from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field

from utils.helper import Helper


class QueryData(BaseModel):
    """Query object reference"""

    id: str
    model_config = ConfigDict(extra="allow")


class TypeData(BaseModel):
    """Basic types reference with optional templates"""

    id: str
    key: str
    templates: Optional[Dict[str, str]] = None


class OptionData(BaseModel):
    """Options on a select or multi_select property"""

    id: str
    key: str
    name: str
    color: str


class PropData(BaseModel):
    """Basic prop data with options"""

    id: str
    key: str
    name: str
    format: str
    options: Optional[Dict[str, OptionData]] = None


class SpaceData(BaseModel):
    """Basic data expected in a space reference"""

    id: str

    queries: Dict[str, QueryData] = Field(default_factory=dict)
    types: Dict[str, TypeData] = Field(default_factory=dict)
    props: Dict[str, PropData] = Field(default_factory=dict)


class TimetaggerPersistent(BaseModel):
    """Basic persistent data across reloads"""

    running_state: Optional[dict] = None
    state_dict: Optional[str] = None
    running_task: Optional[dict] = None
    task_dict: Optional[str] = None


class ReferenceData(BaseModel):
    """Top-level keys map to Dict[str, SpaceData]. E.g. tasks, journal..."""

    anytype: Dict[str, SpaceData] = {}
    timetagger: Optional[TimetaggerPersistent] = None

    def file_sync(self):
        """Writes model to local file for reference"""
        Helper.read_write("data/data.yaml", "w", self.model_dump())
