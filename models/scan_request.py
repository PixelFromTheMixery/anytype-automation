from pydantic import BaseModel


class ScanSpacesRequest(BaseModel):
    source_space_name: str
    target_space_name: str
    props: list | None = None
