"""Validated config singleton — load once, reuse everywhere.

Usage:
    from config import config  # or get_config()
    config.suggestion_engine.cibil_good_threshold
"""
from functools import lru_cache

from .config_schema import AppConfig, load_config

_config_singleton: AppConfig | None = None


def get_config() -> AppConfig:
    """Return the validated config, loading config.yaml only on first call."""
    global _config_singleton
    if _config_singleton is None:
        _config_singleton = load_config()
    return _config_singleton


def _reset_config_cache() -> None:
    """Test helper: clear the cached singleton so the next get_config() re-reads YAML."""
    global _config_singleton
    _config_singleton = None


# Eagerly validate at import so the app fails fast at startup on bad config.
config: AppConfig = get_config()

__all__ = ["config", "get_config", "AppConfig"]
