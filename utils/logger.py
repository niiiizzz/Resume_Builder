"""
Centralized logging configuration for the Resume Builder application.
Import `get_logger(__name__)` in any module to get a properly configured logger.
"""

import logging
import sys


def setup_logging(level: str = "INFO"):
    """Configure root logger with structured formatting."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s | %(message)s"
    logging.basicConfig(
        level=log_level,
        format=fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given module name."""
    return logging.getLogger(name)


# Auto-configure on import
setup_logging()
