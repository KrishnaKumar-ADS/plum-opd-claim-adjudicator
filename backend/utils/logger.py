"""Logging configuration."""

import logging
import sys
from backend.config import get_settings


def setup_logger(name: str = "plum_adjudicator") -> logging.Logger:
    """Create and configure a logger instance."""
    settings = get_settings()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Console handler with formatting
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Default application logger
logger = setup_logger()


def get_logger(module_name: str) -> logging.Logger:
    """Get a child logger for a specific module."""
    return setup_logger(f"plum.{module_name}")
