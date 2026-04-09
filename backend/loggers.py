import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LangChainLogger:
    def __init__(self, level: int):
        self.level = level
        self.level_name = logging.getLevelName(level)
        self.log_messages = []

    def log(self, message, event, **kwargs):
        self.log_messages.append((self.level_name, message, event, kwargs))
        logger.log(self.level, message, **kwargs)


lc_logger = LangChainLogger(level=logging.INFO)


def log_langchain_event(event: Dict):
    lc_logger.log(message="LangChain Event:", event=event)


def log_langchain_event_v2(event: Dict):
    logger.log(
        logging.INFO,
        msg=event.__str__()
    )
