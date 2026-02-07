"""
Logging configuration.
"""

import logging
import sys
from typing import Optional


class Logger:
    """Simple logger wrapper."""

    def __init__(self, name: str = "news_scanner", level: int = logging.INFO):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def debug(self, msg: str, *args):
        """Log debug message."""
        self._logger.debug(msg, *args)

    def info(self, msg: str, *args):
        """Log info message."""
        self._logger.info(msg, *args)

    def warning(self, msg: str, *args):
        """Log warning message."""
        self._logger.warning(msg, *args)

    def error(self, msg: str, *args):
        """Log error message."""
        self._logger.error(msg, *args)

    def set_level(self, level: int):
        """Set logging level."""
        self._logger.setLevel(level)
        for handler in self._logger.handlers:
            handler.setLevel(level)

    def enable_debug(self):
        """Enable debug logging."""
        self.set_level(logging.DEBUG)


# Global logger instance
logger = Logger()
