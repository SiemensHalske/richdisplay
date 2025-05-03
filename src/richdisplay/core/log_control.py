"""
LogControl class for managing logging operations.
"""

import argparse
import logging
import sys
from typing import Optional, Union
from rich.console import Console

from richdisplay.database import LogDB
from richdisplay.database.log_query import LogQuery
from richdisplay.exporters import CSVExporter, JSONExporter
from richdisplay.state import AuthManager, ArgsContext, SysContext


class LogControl:
    """Handles the logging control and management."""

    _instance: Optional["LogControl"] = None  # Singleton instance
    _commands = [
        [["--clear", "-c"], "Clear the database.", bool, False, True],
        [["--db_path", "-dbp"], "Set the database path.", str, "logs.db", False],
        [["--db", "-db"], "Enable database logging.", bool, False, False],
        [["--debug", "-d"], "Enable debug mode.", bool, False, False],
        [["--get-logs", "-gl"], "Get logs from the database.", int, 0, True],
        [["--log-level", "-ll"], "Set the log level.", int, 10, True],
        [["--export", "-e"], "Export logs to a file.", str, "", True],
    ]

    _console: Console
    _bail_out = False
    _initialized: bool = False  # Flag to check if the class is initialized
    _logdb: LogDB = None  # Instance of the LogDB class
    _token: str = ""
    _authorized_consumers = []  # List of authorized consumers

    def __new__(cls, *args, **kwargs):
        """Ensures that only one instance of the class exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._console = Console()
            cls._instance._console.print(
                "LogControl created.", style="bold green")
            cls._instance._initialize()  # Perform initialization during creation
        if args:
            cls._instance._authorize(consumer=args[0])  # Authorize the consumer if provided
        return cls._instance

    def _initialize(self):
        """Initializes the LogControl instance. Called only once."""
        # generate and store a token for this instance
        self._token = AuthManager.generate_token()

        if self._logdb is None:
            self._logdb = LogDB.init_db()
        if not self._initialized:
            self._console.print(
                "Initializing LogControl...", style="bold green")
            # parse CLI arguments and push to ArgsContext
            self.parse()

            self._initialized = True  # Prevent reinitialization
            self._console.print(
                "LogControl initialized successfully.", style="bold green")

            # get the log level from ArgsContext
            log_level = ArgsContext.get().log_level

            # push new system context instead of contextmanager
            SysContext.push(
                auth_token=self._token,
                debug=True if log_level == logging.DEBUG else False,
                log_to_db=True,
                log_level=log_level,
            )

            # execute CLI commands under args context
            self.execute_commands()
    def __init__(self, consumer: Optional[str] = None):
        """Prevent duplicate initialization."""
        if consumer:
            self._authorize(consumer=consumer)

    def _exit(self, return_code=0):
        """Exits the program."""
        sys.exit(return_code)

    @property
    def bail_out(self) -> bool:
        """Checks if the program should exit."""
        return self._bail_out

    @bail_out.setter
    def bail_out(self, value: bool):
        """Sets the bail_out flag."""
        self._bail_out = value
    
    def _authorize(self, consumer: str) -> Optional[Union[bool, str]]:
        """Authorizes the consumer to access the token."""
        if consumer not in self._authorized_consumers:
            self._authorized_consumers.append(consumer)
            return True
        return False
    
    def _is_authorized(self, consumer: str) -> bool:
        """Checks if the consumer is authorized to access the token."""
        return consumer in self._authorized_consumers
    
    def request_token(self, consumer: str) -> str:
        if not self._is_authorized(consumer):
            raise PermissionError(f"{consumer} not allowed to access token.")
        return self._token

    @staticmethod
    def is_initialized() -> bool:
        """Checks if the LogControl instance is initialized."""
        return LogControl._instance is not None

    @staticmethod
    def get_instance() -> "LogControl":
        """Returns the singleton instance of LogControl."""
        if LogControl._instance is None:
            LogControl._instance = LogControl()
        return LogControl._instance

    def update_log_level(self, log_level: int) -> None:
        """Updates the log level in the ArgsContext."""
        ArgsContext.push(
            auth_token=self._token,
            log_level=log_level
        )
        SysContext.push(
            auth_token=self._token,
            debug=True if log_level == logging.DEBUG else False,
            log_to_db=True,
            log_level=log_level,
        )

    def parse(self) -> None:
        """Parses CLI arguments and pushes them into ArgsContext."""
        parser = argparse.ArgumentParser(description="LogControl CLI")
        for cmd in self._commands:
            parser.add_argument(*cmd[0], help=cmd[1],
                                type=cmd[2], default=cmd[3])
        args = parser.parse_args()

        # Push parsed CLI flags into ArgsContext
        ArgsContext.push(
            auth_token=self._token,
            clear=args.clear,
            debug=args.debug,
            db=args.db,
            db_path=args.db_path,
            log_to_db=args.db,
            get_logs=args.get_logs,
            export=args.export,
            log_level=args.log_level
        )

    def execute_commands(self):
        """Executes commands based on parsed arguments using ArgsContext."""
        # retrieve parsed CLI values from ArgsContext
        args = ArgsContext.get()

        if args.debug:
            self._console.print("Debug mode enabled.", style="bold yellow")
            self._console.print("Executing commands...", style="bold yellow")

        if args.clear:
            self._console.print("Clearing the database...", style="bold red")
            LogDB.clear_db()
            self._console.print("Database cleared.", style="bold green")
            self._exit()

        if args.log_to_db:
            self._console.print(
                f"Logging to database at {args.db_path}.", style="bold blue")

        if args.get_logs > 0:
            self._console.print(
                f"Fetching logs with level {args.get_logs}.", style="bold cyan")
            log_query = LogQuery(self._logdb)
            logs = log_query.get_logs_by_level(args.get_logs)
            ret = log_query.display_logs(logs, args.get_logs)
            if ret == 1:
                self._console.print(
                    "Error fetching logs. Please check the log level.", style="bold red")
                self._exit(1)
            self._exit(0)

        if args.export:
            self._console.print(
                f"Exporting logs to {args.export}.", style="bold green")
            file_name = f"logs.{args.export}"
            self.export_logs(args.export, file_name)
            self._exit()

        # ArgsContext.pop() moved to Display.__del__ for proper lifecycle management

    def export_logs(self, export_to="json", file_name="logs.json"):
        """Exports logs to a specified format (JSON or CSV)."""

        if export_to == "json":
            exporter = JSONExporter(self._logdb)
        elif export_to == "csv":
            exporter = CSVExporter(self._logdb)
        else:
            self._console.print(
                f"Unsupported export format: {export_to}.", style="bold red")
            return

        exporter.set_file_name(file_name)
        ret = exporter.export()
        if ret == 1:
            self._console.print(
                "Error exporting logs. Please check the file name.", style="bold red")
            return

        self._console.print(
            f"Logs exported successfully to {file_name}.", style="bold green")
