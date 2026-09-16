import pytest
from pathlib import Path

from app.config import get_settings


def test_production_rejects_wildcard_cors(monkeypatch):
    monkeypatch.setenv("PHAGEX_ENVIRONMENT", "production")
    monkeypatch.setenv("PHAGEX_ALLOWED_ORIGINS", "*")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="Wildcard CORS"):
        get_settings()
    get_settings.cache_clear()


def test_production_accepts_exact_origin(monkeypatch):
    monkeypatch.setenv("PHAGEX_ENVIRONMENT", "production")
    monkeypatch.setenv("PHAGEX_ALLOWED_ORIGINS", "https://phagex.example")
    monkeypatch.setenv("PHAGEX_API_KEY", "a-production-key-with-24-chars")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.allowed_origins == ("https://phagex.example",)
    assert settings.is_production
    get_settings.cache_clear()


def test_production_requires_long_api_key(monkeypatch):
    monkeypatch.setenv("PHAGEX_ENVIRONMENT", "production")
    monkeypatch.setenv("PHAGEX_ALLOWED_ORIGINS", "https://phagex.example")
    monkeypatch.setenv("PHAGEX_API_KEY", "short")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="at least 24"):
        get_settings()
    get_settings.cache_clear()


def test_relative_embedding_cache_is_resolved_from_backend_root(monkeypatch):
    monkeypatch.setenv("PHAGEX_EMBEDDING_CACHE", "work/test-embeddings.sqlite3")
    get_settings.cache_clear()
    assert get_settings().embedding_cache == Path(__file__).resolve().parents[1] / "work/test-embeddings.sqlite3"
    get_settings.cache_clear()
