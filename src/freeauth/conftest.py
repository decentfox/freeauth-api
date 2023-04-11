import pytest


@pytest.fixture
def edgedb_client(request):
    print(request.config.getoption("--reset-db"))
