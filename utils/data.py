"""Data singleton based on id page"""

import threading
import yaml

from utils.api_tools import make_call
from utils.config import Config

DATA_ID = "bafyreickhqath2lc5rwayclybimuxhjpuvllbcrfsx3ot2ddeenuz2lr2a"
TEST_DATA_ID = "bafyreidlqnenmanyxemvlw56ahjgwtjzhdrluykrqf4yqmulbkzvjadnwu"

ID_OBJECT_URL = (
    "/v1/spaces/bafyreicbskqmtyxcinkpqr4nininlxmz6yu7qshm3wkbwhcxrfuyqnzhy4.2bx9tjqqte21g"
    "/objects/"
)


class DataManager:
    """Manager for Data Object"""

    data = {}
    lock = threading.Lock()
    url = ID_OBJECT_URL
    url += TEST_DATA_ID if Config.data["local"] else DATA_ID

    @classmethod
    def get(cls):
        """Access the current config, loading if needed."""
        with cls.lock:
            if not cls.data:
                cls.reload(hold_lock=True)
            return cls.data

    @classmethod
    def reload(cls, hold_lock=False):
        """Checks lock before performing reload"""
        if hold_lock:
            return cls.perform_reload()

        with cls.lock:
            return cls.perform_reload()

    @classmethod
    def perform_reload(cls):
        """Reload config from object."""
        markdown = make_call("get", cls.url, "collecting ID Data from Anytype")[
            "object"
        ]["markdown"]

        new_data = yaml.safe_load(markdown.replace("```\n", ""))

        cls.data.clear()
        cls.data.update(new_data)

        return cls.data

    @classmethod
    def update(cls):
        """Save current config to object."""
        new_data = yaml.safe_dump(cls.data, sort_keys=False)
        new_data_formatted = "```yaml\n" + new_data + "```\n"

        make_call(
            "patch",
            cls.url,
            "Update ID Data from Anytype",
            {"markdown": new_data_formatted},
        )

        markdown = make_call("get", cls.url, "collecting ID Data from Anytype")[
            "object"
        ]["markdown"]

        if new_data_formatted.replace("yaml", "") != markdown.replace("\n\n", "\n"):
            raise ValueError
