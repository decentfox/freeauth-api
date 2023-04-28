from __future__ import annotations

from . import LoginSettings


def get_setting_keys():
    return [
        x
        for x in vars(LoginSettings).keys()
        if not callable(getattr(LoginSettings, x)) and not x.startswith("_")
    ]
