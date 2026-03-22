"""toggl interaction module"""

from anytype_service import AnytypeService
from utils.anytype import AnyTypeUtils

from utils.config import Config


class TogglService:
    """Toggl class for hosting functions"""

    def __init__(self):
        self.anytype_service = AnytypeService()
        self.anytype_utils = AnyTypeUtils()

    def add_url(self):
        pass
