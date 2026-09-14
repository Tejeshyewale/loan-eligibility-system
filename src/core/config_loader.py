"""Thin re-export so core modules have a stable import path.

Preferred: `from config import config, get_config`
Also works: `from src.core.config_loader import config, get_config`
Both return the SAME singleton (loaded once, reused everywhere).
"""
from config import AppConfig, config, get_config

__all__ = ["AppConfig", "config", "get_config"]
