"""
Class to export data to CSV format.
"""

import csv
from typing import List, Dict, Optional, Union, Any


class CSVExporter:
    """
    Class to export data to CSV format.
    """

    _file_name: str = ""
    _data: List[Dict[str, Any]] = []
    _encoding: str = "utf-8"

    def __init__(self, encoding: str = "utf-8") -> None:
        """
        Initialize the CSVExporter with the specified encoding.

        :param encoding: The encoding to use for the CSV file.
        """
        self._encoding = encoding

    @classmethod
    def set_file_name(cls, file_name: str) -> str:
        """
        Set the file name for the CSV export.

        :param file_name: The desired file name.
        :return: The formatted file name.
        """

        cls._file_name = file_name
        return f"{cls._file_name}.csv"

    @classmethod
    def get_file_name(cls) -> str:
        """
        Get the file name for the CSV export.

        :return: The file name.
        """
        return cls._file_name

    @classmethod
    def set_data(cls, data: List[Dict[str, Any]]) -> bool:
        """
        Set the data to be exported to CSV.

        :return: 0 if successful, 1 if no data is available.
        """
        if not data:
            return False
        cls._data = data
        return True

    @classmethod
    def get_data(cls) -> Optional[Union[int, List[Dict[str, Any]]]]:
        """
        Get the data to be exported to CSV.

        :return: The data to be exported.
        """
        if not cls._data:
            return 1
        return cls._data

    @classmethod
    def export(cls, file_name: str = None) -> Optional[Union[int, str]]:
        """
        Export the data to a CSV file.

        :param file_name: The name of the CSV file.
        :return: 0 if successful, 1 if no data is available.
        """
        if not cls._data:
            return 1
        if file_name is None:
            file_name = cls._file_name
        with open(file_name, mode="w", encoding=cls._encoding) as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=cls._data[0].keys())
            writer.writeheader()
            writer.writerows(cls._data)
        return 0
