"""
Log Query Module
"""

from typing import Optional, Union, List

from rich.console import Console
from rich.table import Table

from richdisplay.database import LogDB


class LogQuery:
    """
    Class for querying logs from the database.
    """

    _lvl_mappping = {
        10: {
            "name": "DEBUG",
            "description": "Debug level logs.",
            "func": "get_debug_logs",
        },
        20: {
            "name": "INFO",
            "description": "Info level logs.",
            "func": "get_info_logs",
        },
        30: {
            "name": "ERROR",
            "description": "Error level logs.",
            "func": "get_error_logs",
        },
        40: {
            "name": "WARNING",
            "description": "Warning level logs.",
            "func": "get_warning_logs",
        },
        50: {
            "name": "CRITICAL",
            "description": "Critical level logs.",
            "func": "get_critical_logs",
        }
    }

    def __init__(self, db: LogDB):
        """Initialize with a database instance."""
        self._db = db

    def get_logs(self, limit: int = 10) -> List[dict]:
        """Retrieve logs from the database with an optional limit."""

        logs = self._db.fetch_all_logs()
        if isinstance(logs, list):
            return logs[:limit]
        return []

    def get_logs_by_level(self, level: int) -> Optional[Union[int, list[dict]]]:
        """
        Retrieve logs by level from the database.

        :param level: The log level to filter by.
        :return: A list of logs matching the specified level.
        """
        if level not in self._lvl_mappping:
            return 1

        level: str = ""
        if level in self._lvl_mappping:
            level = self._lvl_mappping[level]["name"]
        else:
            return 1

        return self._db.fetch_logs_by_level(level)

    def display_logs(self, logs: Optional[Union[int, list[dict]]], level: str) -> Optional[Union[int, str]]:
        """Displays logs in a formatted table."""
        if isinstance(logs, int):
            return 1

        _console = Console()
        if logs:
            table = Table(title=f"Log Messages - {level.capitalize()}")
            table.add_column("ID", justify="right")
            table.add_column("Level", style="cyan")
            table.add_column("Message", style="magenta")
            table.add_column("Timestamp", style="green")

            for log in logs:
                table.add_row(
                    str(log["id"]),
                    log["level"],
                    log["message"],
                    log["timestamp"]
                )

            _console.print(table)
            return 0
        _console.print(
            f"No logs found for level: {level}", style="bold yellow")
        return "no_logs"
