from __future__ import annotations

import logging

from . import logger
from .config import get_config


def configure_logging(app):
    logger.setLevel(logging.INFO)

    fmt = "[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
    if not app.debug:
        fmt = "%(name)s %(levelname)s in %(pathname)s:%(lineno)s: %(message)s"

    config = get_config()
    if config.testing:
        logger.setLevel(logging.CRITICAL)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(fmt))
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)