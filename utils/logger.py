import logging
from pythonjsonlogger import json

log = logging.getLogger()
log.level = logging.INFO
logger = logging.getLogger()

logHandler = logging.StreamHandler()
formatter = json.JsonFormatter("%(asctime)s [%(levelname)s] %(message)s")

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)