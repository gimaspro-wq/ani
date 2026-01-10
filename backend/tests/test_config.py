import importlib
import sys

import pytest


def _reload_config():
    sys.modules.pop("app.core.config", None)
    return importlib.import_module("app.core.config")


def test_missing_required_env_vars_raise_runtime_error(monkeypatch):
    for key in ["DATABASE_URL", "SECRET_KEY", "INTERNAL_TOKEN", "REDIS_URL"]:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        _reload_config()

    message = str(excinfo.value)
    assert "Missing required environment variables" in message
    for key in ["DATABASE_URL", "SECRET_KEY", "INTERNAL_TOKEN", "REDIS_URL"]:
        assert key in message


def test_settings_load_when_env_present(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/dbname")
    monkeypatch.setenv("SECRET_KEY", "TEST_SECRET_KEY_OVERRIDE_FOR_URL_NORMALIZE_32")
    monkeypatch.setenv("INTERNAL_TOKEN", "TEST_INTERNAL_TOKEN_OVERRIDE_FOR_URL_NORMALIZE")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    config = _reload_config()

    assert config.settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/dbname"
    assert config.settings.SECRET_KEY == "TEST_SECRET_KEY_OVERRIDE_FOR_URL_NORMALIZE_32"
    assert config.settings.INTERNAL_TOKEN == "TEST_INTERNAL_TOKEN_OVERRIDE_FOR_URL_NORMALIZE"
    assert config.settings.REDIS_URL == "redis://localhost:6379/0"

    settings = config.Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/dbname",
        SECRET_KEY="TEST_SECRET_KEY_OVERRIDE_FOR_URL_NORMALIZE_32",
        INTERNAL_TOKEN="TEST_INTERNAL_TOKEN_OVERRIDE_FOR_URL_NORMALIZE",
        REDIS_URL="redis://localhost:6379/0",
    )

    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/dbname"

    url = "postgresql+asyncpg://user:pass@localhost:5432/dbname"
    settings_async = config.Settings(
        DATABASE_URL=url,
        SECRET_KEY="TEST_SECRET_KEY_OVERRIDE_FOR_URL_NORMALIZE_32",
        INTERNAL_TOKEN="TEST_INTERNAL_TOKEN_OVERRIDE_FOR_URL_NORMALIZE",
        REDIS_URL="redis://localhost:6379/0",
    )

    assert settings_async.DATABASE_URL == url
