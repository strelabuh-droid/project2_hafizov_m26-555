"""Shared settings for the database application."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
ENCODING = "utf-8"
JSON_INDENT = 2
TEMP_SUFFIX = ".tmp"
VALID_TYPES = ("int", "str", "bool")
TYPE_OBJECTS = {"int": int, "str": str, "bool": bool}
ID_COLUMN = "ID"
FIRST_ID = 1
CACHE_MAX_ENTRIES = 128
PUNCTUATION = "(),="
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"}
RESERVED_NAMES.update(f"COM{number}" for number in range(1, 10))
RESERVED_NAMES.update(f"LPT{number}" for number in range(1, 10))