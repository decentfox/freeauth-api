from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def setup_and_teardown():
    orig_env = os.environ.copy()
    os.environ["TESTING"] = "true"

    yield

    os.environ = orig_env
