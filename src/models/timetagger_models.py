"""
Model for managing models for working with time tagger
"""

from pydantic import BaseModel


class TimeEntry(BaseModel):
    """
    Data model described for records in time-tagger
    """

    key: str
    ds: str
    t1: float
    t2: float = 0.0 # To start running entry
    mt: float
    st: float = 0.0 # To start running entry
