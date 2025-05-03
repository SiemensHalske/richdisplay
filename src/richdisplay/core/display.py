"""
Handles displaying information in a structured format using Rich library.
"""

import logging
import uuid
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
    _log_ctrl: Optional["LogControl"] = None
    _consumer_id: str = ""

    def __init__(self, logger_name: str, log_lvl: Optional[int] = 20):
        """Initializes the Display instance with a specific logger name."""
        self.logger_name = logger_name

        self._consumer_id = uuid.uuid4().hex
        self._log_ctrl = LogControl(self._consumer_id)

        if log_lvl > 0:
            self._log_ctrl.update_log_level(log_lvl)
        else:
            print("Uh-oh... Logging at level 0 are we? Brace yourselves, the logs are coming!")

        self._logger = logging.getLogger(logger_name)
        self.init_display()

    def __del__(self):
        """Destructor to clean up resources."""
        if LogDB._connection:
            LogDB.close_db()

    def set_debug(self) -> Union[int, None]:
        """Sets the debug mode for the logger."""

        try:
            SysContext.push(auth_token=self._token)
            self._debug = SysContext.get_debug()
            self._log_to_db = SysContext.get_log_to_db()
            _log_level = SysContext.get_log_level()

            return _log_level
        except (RuntimeError, PermissionError) as e:
            print(f"Error: Unable to push system context: {e}")
            sys.exit(1)

    def _set_token(self) -> None:
        """Sets the token for the logger."""
        try:
            self._token = self._log_ctrl.request_token(self._consumer_id)
            if self._token == "":
                raise RuntimeError("Empty token received.")
        except (RuntimeError, PermissionError) as e:
            print(f"Error: Unable to push system context: {e}")
            sys.exit(1)

    def init_display(self):
        """Initializes the display settings using the new SysContext push API."""
        # push system context using this instance's token

        self._set_token()

        _log_level = self.set_debug()

        if self._log_to_db:
            LogDB.init_db()

        # Initialize the RichHandler with proper settings
        self._handler = RichHandler(
            show_time=True,  # Show timestamp
            show_level=True,  # Show log level
            show_path=True,  # Hide file path
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
        self._logger.debug(
            "Display initialized with logger '%s'.", self.logger_name)

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
