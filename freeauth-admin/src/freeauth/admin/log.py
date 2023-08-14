# Copyright (c) 2016-present DecentFoX Studio and the FreeAuth authors.
# FreeAuth is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan
# PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY
# KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from __future__ import annotations

import logging

from freeauth.conf.settings import get_settings

from . import logger


def configure_logging(app):
    logger.setLevel(logging.INFO)

    fmt = "[%(asctime)s] %(levelname)s:%(name)s: %(message)s"
    if not app.debug:
        fmt = "%(name)s %(levelname)s in %(pathname)s:%(lineno)s: %(message)s"

    settings = get_settings()
    if settings.testing:
        logger.setLevel(logging.CRITICAL)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(fmt))
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
