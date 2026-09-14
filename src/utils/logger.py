"""Central structured logging: INFO normal flow, WARNING recoverable, ERROR failures."""
import logging
import os

_configured = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger with a single shared handler (no duplicate logs)."""
    global _configured
    logger = logging.getLogger(name)
    if not _configured:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"))
        root = logging.getLogger()
        root.setLevel(getattr(logging, level, logging.INFO))
        root.addHandler(handler)
        _configured = True
    return logger
