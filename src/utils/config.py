"""Loads in config file as it is easier to manage than hardcode"""

import yaml


class Config:
    """data based on configuration yaml"""

    data = None
    with open("config.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
