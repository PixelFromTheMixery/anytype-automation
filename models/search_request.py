from typing import Optional
from pydantic import BaseModel, ConfigDict


class FilterCondition(BaseModel):
    property_key: str
    model_config = ConfigDict(extra="allow")


class SearchRequest(BaseModel):
    types: Optional[list[str]] = ["task"]
    query: Optional[str] = None
    filters: Optional[list[FilterCondition]] = None
