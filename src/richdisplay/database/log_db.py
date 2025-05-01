"""
Handles logging messages to SQLite database.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Union


class LogDB:
    """Handles logging messages to SQLite."""

    _db_path = "logs.db"
    _connection = None

    @classmethod
    def clear_db(cls):
        """Clears the SQLite database."""
        if cls._connection:
            cls._connection.close()
            cls._connection = None
        try:
            os.remove(cls._db_path)
        except FileNotFoundError:
            pass

    @classmethod
    def init_db(cls) -> Optional[Union[int, str]]:
        """Initializes the SQLite database and creates the table if it doesn't exist."""
        try:
            cls._connection = sqlite3.connect(cls._db_path)
            cursor = cls._connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS log_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            cls._connection.commit()
            return 0
        except sqlite3.Error as e:
            return e

    @classmethod
    def log_to_db(cls, level: str, message: str) -> Optional[Union[int, str]]:
        """Logs a message to the SQLite database."""
        if cls._connection is None:
            return 1

        timestamp = datetime.utcnow().isoformat()
        try:
            cursor = cls._connection.cursor()
            cursor.execute("""
                INSERT INTO log_messages (level, message, timestamp)
                VALUES (?, ?, ?)
            """, (level, message, timestamp))
            cls._connection.commit()
            return 0
        except sqlite3.Error as e:
            return e

    @classmethod
    def fetch_all_logs(cls) -> Optional[Union[int, list[dict]]]:
        """Fetches all logs from the SQLite database."""
        if cls._connection is None:
            return 1

        try:
            cursor = cls._connection.cursor()
            cursor.execute("SELECT * FROM log_messages")
            rows = cursor.fetchall()
            logs = [
                {"id": row[0], "level": row[1],
                    "message": row[2], "timestamp": row[3]}
                for row in rows
            ]
            return logs
        except sqlite3.Error as e:
            return e

    @classmethod
    def fetch_logs_by_level(cls, level: str) -> Optional[Union[int, list[dict]]]:
        """Fetches logs by level from the SQLite database."""
        if cls._connection is None:
            return 1

        try:
            cursor = cls._connection.cursor()
            cursor.execute(
                "SELECT * FROM log_messages WHERE level = ?", (level,))
            rows = cursor.fetchall()
            logs = [
                {"id": row[0], "level": row[1],
                    "message": row[2], "timestamp": row[3]}
                for row in rows
            ]
            return logs
        except sqlite3.Error as e:
            return e

    @classmethod
    def close_db(cls) -> None:
        """Closes the SQLite database connection."""
        if cls._connection:
            cls._connection.close()
            cls._connection = None
