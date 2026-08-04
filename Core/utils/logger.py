"""Centralized logging configuration for FaceLock."""

import logging
import sys


def get_logger(name: str = "FaceLock", level: int = logging.INFO) -> logging.Logger:
    """Return a formatted logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
