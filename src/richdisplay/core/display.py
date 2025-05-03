"""
Handles displaying information in a structured format using Rich library.
"""

import logging
import uuid
import sys
from dataclasses import dataclass
from typing import Optional, Union, List
from rich.logging import RichHandler

from richdisplay.state import SysContext
from richdisplay.utils import RichFormatter
from richdisplay.database import LogDB

from .log_control import LogControl

@dataclass
class DisplayState:
    """Represents the state of the display."""

    _valid_entities: List[str] = [
        "debug",
        "log_to_db",
        "log_level",
        "token",
        "consumer_id",
        "log_ctrl",
    ]

    _debug: bool
    _log_to_db: bool
    _log_level: int
    _token: str
    _consumer_id: str
    _log_ctrl: Optional["LogControl"] = None

    def __init__(
        self,
        log_level: int = 20,
        consumer_id: str = "",
        log_ctrl: Optional["LogControl"] = None,
    ):
        self._log_level = log_level
        self._consumer_id = consumer_id
        self._log_ctrl = log_ctrl

        if self._log_ctrl is None:
            self._log_ctrl = LogControl(self._consumer_id)
            self._log_ctrl.update_log_level(self._log_level)
        else:
            self._log_ctrl.update_log_level(self._log_level)

    def _is_parent(self, pid: str) -> bool:
        """Checks if the current instance is the parent of the given PID."""
        if self._log_ctrl:
            try:
                _ = self._log_ctrl.request_token(pid)
                return True
            except (RuntimeError, PermissionError):
                return False
        return False

    def set_entity(self, entity: str, value: Union[str, int], pid: str) -> None:
        """Sets an entity in the DisplayState."""
        if not self._is_parent(pid):
            raise PermissionError(
                f"Permission denied for entity '{entity}' with PID '{pid}'."
            )

        if entity not in self._valid_entities:
            raise ValueError(f"Invalid entity '{entity}' to set.")

        entity = "_"+entity.lower()
        setattr(self, entity, value)

    def request_entity(self, entity: str, pid: str) -> Optional[Union[str, int]]:
        """Requests an entity from the DisplayState."""
        if not self._is_parent(pid):
            raise PermissionError(
                f"Permission denied for entity '{entity}' with PID '{pid}'."
            )

        if entity not in self._valid_entities:
            raise ValueError(f"Invalid entity '{entity}' to request.")

        entity = "_"+entity.lower()
        return getattr(self, entity)


class Display:
    """Handles displaying information in a structured format."""

    _debug: bool = False
    _log_to_db: bool = False
    _handler: RichHandler
    _token: str = ""
    _log_ctrl: Optional["LogControl"] = None
    _consumer_id: str = ""

    _state: Optional[DisplayState] = None

    def __init__(self, logger_name: str, log_lvl: Optional[int] = 20):
        """Initializes the Display instance with a specific logger name."""
        self._consumer_id = uuid.uuid4().hex
        _log_ctrl = LogControl(self._consumer_id)

        self._state = DisplayState(
            consumer_id=self._consumer_id, log_ctrl=_log_ctrl, log_level=log_lvl)
        self.logger_name = logger_name

        if log_lvl > 0:
            _log_ctrl.update_log_level(log_lvl)
        else:
            print(
                "Uh-oh... Logging at level 0 are we? Brace yourselves, the logs are coming!")

        self._logger = logging.getLogger(logger_name)
        self.init_display()

    def __del__(self):
        """Destructor to clean up resources."""
        if LogDB._connection:
            LogDB.close_db()

    def set_debug(self) -> Union[int, None]:
        """Sets the debug mode for the logger."""

        try:
            _token = self._state.request_entity("token", self._consumer_id)
            SysContext.push(auth_token=_token)
            _debug = SysContext.get_debug()
            _log_to_db = SysContext.get_log_to_db()
            _log_level = SysContext.get_log_level()

            self._state.set_entity("debug", _debug, self._consumer_id)
            self._state.set_entity("log_to_db", _log_to_db, self._consumer_id)
            self._state.set_entity("log_level", _log_level, self._consumer_id)

            return _log_level
        except (RuntimeError, PermissionError) as e:
            print(f"Error: Unable to push system context: {e}")
            sys.exit(1)

    def _set_token(self) -> None:
        """Sets the token for the logger."""
        try:
            _log_ctrl = self._state.request_entity(
                "log_ctrl", self._consumer_id)
            _token = _log_ctrl.request_token(self._consumer_id)
            self._state.set_entity("token", _token, self._consumer_id)
            if _token == "":
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
