from typing import Optional
from pydantic import BaseModel, ConfigDict


class FilterCondition(BaseModel):
    property_key: str
    model_config = ConfigDict(extra="allow")


class SearchRequest(BaseModel):
    space: str
    types: Optional[list[str]] = None
    query: Optional[str] = None
    filters: Optional[list[FilterCondition]] = None
