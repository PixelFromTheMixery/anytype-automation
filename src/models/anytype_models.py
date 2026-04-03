from typing import Optional

from pydantic import BaseModel


class SpaceEditRequest(BaseModel):
    source_space_name: str
    source_space_id: str
    target_space_name: str
    target_space_id: str
    stages: Optional[list[str]] = None
    delete_task_types: bool = True
    props: Optional[list | None] = None
    clear: bool = False
