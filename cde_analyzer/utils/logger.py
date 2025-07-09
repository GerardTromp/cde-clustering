import logging
from typing import Any, Type, List, Optional, Dict, Union


def configure_logging(verbosity: int, logfile: Union[str, None]):
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    handlers = [logging.StreamHandler()]
    if logfile:
        handlers = [logging.FileHandler(logfile, mode="a", encoding="utf-8")]
        # handlers.append(logfile)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_if_verbose(message: str, level: int = 2):
    """
    Custom logging that logs or discards based
    on global verbosity.
    Avoids so many conditionals.
    """
    from utils.analyzer_state import get_verbosity

    if get_verbosity() >= level:
        logging.info(message)
