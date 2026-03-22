from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator, TypeAdapter


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


class ReferenceData(BaseModel):
    """converts top level keys into entries. E.g. tasks, journal..."""

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_extra_spaces(self) -> "ReferenceData":
        space_adapter = TypeAdapter(SpaceData)

        if self.__pydantic_extra__:
            validated_extra = {}
            for key, value in self.__pydantic_extra__.items():
                validated_extra[key] = space_adapter.validate_python(value)

            self.__dict__.update(validated_extra)
            self.__pydantic_extra__.update(validated_extra)

        return self

    def __getitem__(self, item: str) -> SpaceData:
        """Allows ref['tasks'] syntax"""
        if self.__pydantic_extra__ and item in self.__pydantic_extra__:
            return self.__pydantic_extra__[item]
        return getattr(self, item)
