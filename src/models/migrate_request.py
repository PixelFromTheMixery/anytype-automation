from pydantic import BaseModel


class MigrateRequest(BaseModel):
    source_space_name: str
    target_space_name: str
    target_space_id: str
    stages: list[str]
