from pydantic import BaseModel


class SpaceSyncRequest(BaseModel):
    source_space_name: str
    target_space_name: str
    props: list | None = None
    clear: bool = False
