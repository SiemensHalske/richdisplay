"""
Handles logging messages to SQLite database.
"""

import os
import sqlite3
import psycopg2
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union, Any


@dataclass
class BaseConnector:
    """Represents a base connector; not DB specific."""

    _connection = None

    def __init__(self, connection: Any):
        if connection:
            self._connection = connection
        else:
            raise ValueError("Connection cannot be None")

    def get_cursor(self):
        """Returns the cursor for the connection."""
        raise NotImplementedError("Subclasses must implement this method")

    def close_connection(self):
        """Closes the connection."""
        raise NotImplementedError("Subclasses must implement this method")

    def commit(self):
        """Commits the changes to the connection."""
        raise NotImplementedError("Subclasses must implement this method")

    def rollback(self):
        """Rolls back the changes to the connection."""
        raise NotImplementedError("Subclasses must implement this method")


@dataclass
class SQLiteConnector(BaseConnector):
    """Represents a SQLite connector."""

    _db_path: str = None

    def __init__(self, connection: Any = None, db_path: str = None):
        if not connection:
            _connection = sqlite3.connect(db_path)
        else:
            _connection = connection
        super().__init__(connection=_connection)
        self._db_path = db_path

    def close_connection(self):
        """Closes the SQLite connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        else:
            raise ValueError("Connection is already closed or None")
        self._db_path = None

    def get_cursor(self):
        """Returns the cursor for the SQLite connection."""
        if self._connection:
            return self._connection.cursor()
        raise ValueError("Connection is already closed or None")

    def commit(self):
        """Commits the changes to the SQLite connection."""
        if self._connection:
            self._connection.commit()
        else:
            raise ValueError("Connection is already closed or None")

    def rollback(self):
        """Rolls back the changes to the SQLite connection."""
        if self._connection:
            self._connection.rollback()
        else:
            raise ValueError("Connection is already closed or None")


@dataclass
class PostgresConnector(BaseConnector):
    """Represents a PostgreSQL connector."""
    # Placeholder for PostgreSQL connection logic

    _db_host: str = None
    _db_port: int = None
    _db_name: str = None
    _db_user: str = None
    _db_password: str = None

    def __init__(self, connection: Any = None, 
                    db_host: str = None, db_port: int = None,
                    db_name: str = None, db_user: str = None,
                    db_password: str = None):
        self._db_host = db_host
        self._db_port = db_port
        self._db_name = db_name
        self._db_user = db_user
        self._db_password = db_password
        if connection:
            super().__init__(connection=connection)
        else:
            # Establish a new PostgreSQL connection here
            try:
                _connection = psycopg2.connect(
                    host=self._db_host,
                    port=self._db_port,
                    dbname=self._db_name,
                    user=self._db_user,
                    password=self._db_password
                )
                super().__init__(connection=_connection)
            except psycopg2.Error as e:
                raise ValueError(f"Failed to connect to PostgreSQL: {e}") from e

    def get_cursor(self):
        """Returns the cursor for the PostgreSQL connection."""
        if self._connection:
            return self._connection.cursor()
        raise ValueError("Connection is already closed or None")

    def close_connection(self):
        """Closes the PostgreSQL connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        else:
            raise ValueError("Connection is already closed or None")

    def commit(self):
        """Commits the changes to the PostgreSQL connection."""
        if self._connection:
            self._connection.commit()
        else:
            raise ValueError("Connection is already closed or None")

    def rollback(self):
        """Rolls back the changes to the PostgreSQL connection."""
        if self._connection:
            self._connection.rollback()
        else:
            raise ValueError("Connection is already closed or None")


@dataclass
class LogQuery:
    """Represents a log query"""
    _query: str
    _params: Optional[dict] = None

    def __init__(self, query: str, params: Optional[dict] = None):
        self._query = query
        self._params = params if params else {}
        self._params = {k: v for k, v in self._params.items() if v is not None}

    def __str__(self) -> str:
        """Returns the string representation of the query."""
        return self._query

    def __repr__(self) -> str:
        """Returns the string representation of the query."""
        return self.__str__()

    def __hash__(self) -> int:
        """Returns the hash of the query."""
        return hash((self._query, tuple(sorted(self._params.items()))))

    def execute_no_return(self, connection: SQLiteConnector) -> Optional[Union[int, str]]:
        """Executes the query on the given connection."""
        try:
            cursor = connection.get_cursor()
            cursor.execute(self._query, tuple(self._params.values()))
            connection.commit()
            return 0
        except sqlite3.Error as e:
            return e

    def execute(self, connection: SQLiteConnector) -> Optional[Union[int, list[tuple]]]:
        """Executes the query on the given connection and returns the result."""
        try:
            cursor = connection.get_cursor()
            cursor.execute(self._query, tuple(self._params.values()))
            return cursor.fetchall()
        except sqlite3.Error as e:
            return e


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
            cls._connection = SQLiteConnector(db_path=cls._db_path)

            query_string = """
                CREATE TABLE IF NOT EXISTS log_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """
            params = {}
            _query = LogQuery(query_string, params)
            ack = _query.execute_no_return(cls._connection)

            if ack != 0:
                return ack
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
            query_string = """
                INSERT INTO log_messages (level, message, timestamp)
                VALUES (?, ?, ?)
            """
            params = {
                "level": level,
                "message": message,
                "timestamp": timestamp
            }
            _query = LogQuery(query_string, params)
            ack = _query.execute_no_return(cls._connection)
            if ack != 0:
                return ack
            return 0
        except sqlite3.Error as e:
            return e

    @classmethod
    def fetch_all_logs(cls) -> Optional[Union[int, list[dict]]]:
        """Fetches all logs from the SQLite database."""
        if cls._connection is None:
            return 1

        try:
            query_string = "SELECT * FROM log_messages"
            params = {}
            _query = LogQuery(query_string, params)
            rows = _query.execute(cls._connection)
            if isinstance(rows, int):
                return rows
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
            query_string = "SELECT * FROM log_messages WHERE level = ?"
            params = {"level": level}
            _query = LogQuery(query_string, params)
            rows = _query.execute(cls._connection)
            if isinstance(rows, int):
                return rows
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
