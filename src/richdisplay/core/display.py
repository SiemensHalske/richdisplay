"""
Handles displaying information in a structured format using Rich library.
"""

import logging
import sys
from typing import Optional, Union
from rich.logging import RichHandler

from richdisplay.state import SysContext
from richdisplay.utils import RichFormatter
from richdisplay.database import LogDB

from .log_control import LogControl


class Display:
    """Handles displaying information in a structured format."""

    _debug: bool = False
    _log_to_db: bool = False
    _handler: RichHandler
    _token: str = ""
    _log_ctrl: Optional["LogControl"] = LogControl()

    def __init__(self, logger_name: str):
        """Initializes the Display instance with a specific logger name."""
        self.logger_name = logger_name
        self._logger = logging.getLogger(logger_name)
        self.init_display()

    def __del__(self):
        """Destructor to clean up resources."""
        if LogDB._connection:
            LogDB.close_db()

    def init_display(self):
        """Initializes the display settings using the new SysContext push API."""
        # push system context using this instance's token

        self._log_ctrl.bail_out = True
        self._token = self._log_ctrl.token
        if self._token == "":
            print("Error: Unable to generate token for SysContext.")
            sys.exit(1)

        try:
            SysContext.push(auth_token=self._token)
            self._debug = SysContext.get_debug()
            self._log_to_db = SysContext.get_log_to_db()
            _log_level = SysContext.get_log_level()
        except (RuntimeError, PermissionError) as e:
            print(f"Error: Unable to push system context: {e}")
            sys.exit(1)
        if self._log_to_db:
            LogDB.init_db()

        # Initialize the RichHandler with proper settings
        self._handler = RichHandler(
            show_time=True,  # Show timestamp
            show_level=True,  # Show log level
            show_path=False,  # Hide file path
            markup=True,  # Enable Rich markup
        )

        # Set the logging level for the handler
        self._handler.setLevel(_log_level)

        # Configure the logging format globally
        custom_formatter = RichFormatter()
        self._handler.setFormatter(custom_formatter)
        # Add the handler to the logger
        if not self._logger.handlers:
            self._logger.addHandler(self._handler)
        self._logger.setLevel(_log_level)
        self._logger.propagate = False  # Prevent propagation to root logger
        self._logger.debug("Display initialized with logger '%s'.", self.logger_name)


    def _validate_return(self, ret: Optional[Union[int, str]]) -> None:
        """Checks the return value of a database operation."""
        if isinstance(ret, int):
            if ret == 1:
                self._logger.error(
                    "Database not initialized. Call init_db() first.")
                return
            if ret == 0:
                return
            self._logger.error("Unknown error occurred.")
            return
        if isinstance(ret, str):
            self._logger.error("Error: %s", ret)

    def log_to_db(self, level: str, message: str) -> None:
        """
        Logs a message to the database.

        :param level: The log level (e.g., INFO, DEBUG, ERROR).
        :type level: str
        :param message: The log message to save.
        :type message: str
        :return: None
        """
        ret = LogDB.log_to_db(level, message)
        self._validate_return(ret)

    def info(self, message: str) -> None:
        """Logs an info message and saves it to the database."""
        self._logger.info(message)
        if self._log_to_db:
            self.log_to_db("INFO", message)

    def debug(self, message: str) -> None:
        """Logs a debug message and saves it to the database."""
        self._logger.debug(message)
        if self._log_to_db:
            self.log_to_db("DEBUG", message)

    def error(self, message: str) -> None:
        """Logs an error message and saves it to the database."""
        self._logger.error(message)
        if self._log_to_db:
            self.log_to_db("ERROR", message)

    def warning(self, message: str) -> None:
        """Logs a warning message and saves it to the database."""
        self._logger.warning(message)
        if self._log_to_db:
            self.log_to_db("WARNING", message)

    def critical(self, message: str) -> None:
        """Logs a critical message and saves it to the database."""
        self._logger.critical(message)
        if self._log_to_db:
            self.log_to_db("CRITICAL", message)