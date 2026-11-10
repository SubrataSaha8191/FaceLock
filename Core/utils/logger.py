"""Centralized logging configuration for FaceLock."""

import logging
import sys


def get_logger(name: str = "FaceLock", level: int = logging.INFO) -> logging.Logger:
    """Return a formatted logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)
        if sys.stdout is not None:
            handler: logging.Handler = logging.StreamHandler(sys.stdout)
        else:
            # pythonw.exe / windowless launches have no console: log to a file instead of dropping messages.
            try:
                from Core.config.settings import get_default_data_dir
                log_dir = get_default_data_dir()
                log_dir.mkdir(parents=True, exist_ok=True)
                handler = logging.FileHandler(log_dir / "facelock.log", encoding="utf-8")
            except Exception:
                handler = logging.NullHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
