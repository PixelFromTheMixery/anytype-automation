"""Module for managing non-specific methods"""

import yaml


class Helper:

    @staticmethod
    def read_write(path, method, data=None):
        """File interaction central script"""
        with open(path, method, encoding="utf-8") as f:
            if data:
                f.write(yaml.safe_dump(data, sort_keys=False))
            else:
                return yaml.safe_load(f)

    def make_deeplink(self, space_id: str, object_id: str):
        """Builds deeplinks for link purposes"""
        return f"https://object.any.coop/{object_id}?spaceId={space_id}"
