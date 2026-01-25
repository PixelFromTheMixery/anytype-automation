"""Loads in config file as it is easier to manage than hardcode"""

import yaml

CONFIG_PATH = "utils/config.yaml"


class Config:
    path
    _data = None

    @classmethod
    def get(cls):
        """Access the current config, loading if needed."""
        if cls._data is None:
            cls.reload()
        return cls._data

    @classmethod
    def reload(cls):
        """Reload config from disk."""
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cls._data = yaml.safe_load(f)
        return cls._data

    @classmethod
    def save(cls):
        """Save current config to disk."""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(cls._data, f)
        return cls.reload()


class Config(YamlManager):
    _path = "yaml/config.yaml"
    _data = None


class Data(YamlManager):
    _path = "yaml/data.yaml"
    _data = None
