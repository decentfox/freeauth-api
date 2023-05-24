def pytest_addoption(parser):
    parser.addoption(
        "--reset-db",
        action="store_true",
        default=False,
        help=(
            "By default, the test database is created only if does not "
            "exist. Set this flag to force re-creation of database."
        ),
    )
