"""
JSONExporter class for exporting logs in JSON format.
"""

from typing import List, Dict, Any, Optional, Union
import json


class JSONExporter:
    """
    Class to export data to JSON format.
    """

    _file_name: str = ""
    _data: List[Dict[str, Any]] = []
    _encoding: str = "utf-8"

    def __init__(self, encoding: str = "utf-8") -> None:
        """
        Initialize the JSONExporter with the specified encoding.

        :param encoding: The encoding to use for the JSON file.
        """
        self._encoding = encoding

    @classmethod
    def set_file_name(cls, file_name: str) -> str:
        """
        Set the file name for the JSON export.

        :param file_name: The desired file name.
        :return: The formatted file name.
        """
        cls._file_name = file_name
        return f"{cls._file_name}.json"

    @classmethod
    def get_file_name(cls) -> str:
        """
        Get the file name for the JSON export.

        :return: The file name.
        """
        return cls._file_name

    @classmethod
    def set_data(cls, data: List[Dict[str, Any]]) -> bool:
        """
        Set the data to be exported to JSON.

        :return: 0 if successful, 1 if no data is available.
        """
        if not data:
            return False
        cls._data = data
        return True

    @classmethod
    def get_data(cls) -> Optional[Union[int, List[Dict[str, Any]]]]:
        """
        Get the data to be exported to JSON.

        :return: The data to be exported.
        """
        if not cls._data:
            return 1
        return cls._data

    @classmethod
    def export(cls) -> Optional[Union[int, str]]:
        """
        Export the data to a JSON file.

        :return: 0 if successful, 1 if no data is available.
        """
        if not cls._data:
            return 1
        try:
            with open(cls._file_name, "w", encoding=cls._encoding) as json_file:
                json.dump(cls._data, json_file, indent=4)
            return 0
        except Exception as e:  # pylint: disable=broad-except
            return str(e)
