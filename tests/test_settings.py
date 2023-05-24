import os

from freeauth.conf.settings import get_settings


def test_get_settings_with_environ():
    os.environ["EDGEDB_DATABASE"] = "testdb"
    os.environ["DEBUG"] = "true"

    get_settings.cache_clear()
    settings = get_settings()

    assert settings.edgedb_database == "testdb"
    assert settings.debug is True


def test_get_settings_from_env_file():
    with open(".env", "w") as f:
        f.write("FOO=bar\nDEBUG=false\nEDGEDB_DATABASE=freeauth")

    get_settings.cache_clear()
    settings = get_settings()
    os.remove(f.name)

    assert settings.edgedb_database == "freeauth"
    assert settings.debug is False
    assert os.environ["EDGEDB_DATABASE"] == settings.edgedb_database
