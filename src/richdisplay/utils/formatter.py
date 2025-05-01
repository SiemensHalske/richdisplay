"""
Custom Formatter for logging with rich library.
"""

import logging


class RichFormatter(logging.Formatter):
    """Custom Formatter to add color to the logger name."""

    _format_string = "%(asctime)s - %(name)s - %(module)s:%(lineno)d - %(message)s"

    def format(self, record):
        # Rich-Markup für den logger name hinzufügen
        record.name = f"[bold blue]{record.name}[/]"

        formatter = logging.Formatter(self._format_string)
        formatted_record = formatter.format(record)

        return formatted_record
