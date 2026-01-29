from pydantic import BaseModel, ConfigDict


class DataRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    space_name: str
    category: str
