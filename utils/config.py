""" Loads in config file as it is easier to manage than hardcode """

import os
import yaml


def load_config():
    """Loads config object"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


def load_archive_logging():
    """Loads archive metadata"""
    archive_path = os.path.join(os.path.dirname(__file__), "archive_data.yaml")
    with open(archive_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

archive_log = load_archive_logging()

def save_archive_logging(data):
    """Saves archive metadata"""
    archive_path = os.path.join(os.path.dirname(__file__), "archive_data.yaml")
    with open(archive_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
