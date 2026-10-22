"""Read and write JSON files without mixing in command handling."""

import json
import os

from primitive_db.constants import (
    DATA_DIR,
    ENCODING,
    JSON_INDENT,
    RESERVED_NAMES,
    TEMP_SUFFIX,
)


def validate_name(name):
    """Reject names that cannot safely be used as table or column names."""
    if not name.isidentifier() or name.upper() in RESERVED_NAMES:
        raise ValueError(f"Недопустимое имя: {name}")


def _load_json(filepath, default):
    """Return a default only when a file is absent, never when it is damaged."""
    try:
        with open(filepath, encoding=ENCODING) as file:
            return json.load(file)
    except FileNotFoundError:
        return default


def _save_json(filepath, data):
    """Write a temporary file and replace the previous version after success."""
    temporary_path = filepath + TEMP_SUFFIX
    with open(temporary_path, "w", encoding=ENCODING) as file:
        json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)
    os.replace(temporary_path, filepath)


def load_metadata(filepath):
    """Load the dictionary of table schemas, or an empty dictionary."""
    metadata = _load_json(filepath, {})
    if not isinstance(metadata, dict):
        raise ValueError("Метаданные должны быть JSON объектом")
    return metadata


def save_metadata(filepath, data):
    """Save the dictionary of table schemas."""
    _save_json(filepath, data)


def _table_path(table_name):
    """Build a path inside the data directory from a checked name."""
    validate_name(table_name)
    return os.path.join(DATA_DIR, table_name + ".json")


def load_table_data(table_name):
    """Load a list of rows, or an empty list for a missing file."""
    data = _load_json(_table_path(table_name), [])
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise ValueError("Данные таблицы должны быть списком объектов")
    return data


def save_table_data(table_name, data):
    """Create the data directory if necessary and save a table."""
    filepath = _table_path(table_name)
    os.makedirs(DATA_DIR, exist_ok=True)
    _save_json(filepath, data)


def remove_table_data(table_name):
    """Remove a table file if it exists."""
    filepath = _table_path(table_name)
    if os.path.exists(filepath):
        os.remove(filepath)