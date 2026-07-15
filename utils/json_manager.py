"""
Bangkok Airways PTFS Bot - JSON Manager

Safe JSON file read/write operations with automatic file creation.
All data storage uses JSON files (no SQLite).
"""

import json
import os
from typing import Any


def ensure_file_exists(filepath: str, default_data: Any = None) -> None:
    """
    Create a JSON file with default data if it does not exist.

    Args:
        filepath: Path to the JSON file.
        default_data: Data to write if file is missing (default: empty list).
    """
    if default_data is None:
        default_data = []

    # Ensure parent directory exists
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(default_data, file, indent=4, ensure_ascii=False)


def read_json(filepath: str, default_data: Any = None) -> Any:
    """
    Safely read a JSON file. Creates file with default data if missing.

    Args:
        filepath: Path to the JSON file.
        default_data: Default data if file is missing.

    Returns:
        Parsed JSON data.
    """
    ensure_file_exists(filepath, default_data)

    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError):
        # If file is corrupted, reset to default
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(default_data or [], file, indent=4, ensure_ascii=False)
        return default_data or []


def write_json(filepath: str, data: Any) -> None:
    """
    Safely write data to a JSON file with atomic-like operation.

    Args:
        filepath: Path to the JSON file.
        data: Data to serialize and write.
    """
    ensure_file_exists(filepath, data)

    # Write to a temporary file first, then rename for safety
    temp_path = filepath + '.tmp'
    try:
        with open(temp_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        # Atomic replace on most systems
        os.replace(temp_path, filepath)
    except OSError as error:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise error
