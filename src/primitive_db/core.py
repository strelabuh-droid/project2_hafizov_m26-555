"""Table management, validation and CRUD functions."""

import json

from primitive_db.constants import FIRST_ID, ID_COLUMN, TYPE_OBJECTS, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data, remove_table_data, validate_name

_select_cache = create_cacher()


def get_schema(metadata, table_name):
    """Return a table schema or raise a meaningful missing table error."""
    if table_name not in metadata:
        raise KeyError(f'Таблица "{table_name}" не существует.')
    return metadata[table_name]


def validate_clause(metadata, table_name, clause, allow_id=True):
    """Check column existence and exact value types before a CRUD operation."""
    schema = get_schema(metadata, table_name)
    types = {column["name"]: column["type"] for column in schema}
    for name, value in clause.items():
        if name not in types:
            raise KeyError(f'Столбец "{name}" не найден.')
        if name == ID_COLUMN and not allow_id:
            raise ValueError("Изменять ID нельзя")
        if type(value) is not TYPE_OBJECTS[types[name]]:
            raise ValueError(f"Для {name} нужен тип {types[name]}")
    return clause


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Validate column specifications and add an automatic ID column."""
    validate_name(table_name)
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    if not columns:
        raise ValueError("Укажите хотя бы один столбец")
    schema = [{"name": ID_COLUMN, "type": "int"}]
    names = {ID_COLUMN.casefold()}
    for specification in columns:
        parts = specification.split(":")
        if len(parts) != 2:
            raise ValueError(f"Ожидается столбец:тип, получено {specification}")
        name, data_type = parts
        validate_name(name)
        if name.casefold() in names:
            raise ValueError(f"Повторный или служебный столбец: {name}")
        if data_type not in VALID_TYPES:
            raise ValueError(f"Неизвестный тип: {data_type}")
        schema.append({"name": name, "type": data_type})
        names.add(name.casefold())
    metadata[table_name] = schema
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Delete both the table file and its schema after confirmation."""
    get_schema(metadata, table_name)
    remove_table_data(table_name)
    del metadata[table_name]
    return metadata


@handle_db_errors
def list_tables(metadata):
    """Return table names in a predictable order."""
    return sorted(metadata)


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Validate all required values and append one row with a generated ID."""
    schema = get_schema(metadata, table_name)
    user_columns = schema[1:]
    if len(values) != len(user_columns):
        raise ValueError(f"Ожидается значений: {len(user_columns)}")
    row = {column["name"]: value for column, value in zip(user_columns, values)}
    validate_clause(metadata, table_name, row, allow_id=False)
    data = load_table_data(table_name)
    next_id = max((record[ID_COLUMN] for record in data), default=0) + FIRST_ID
    row = {ID_COLUMN: next_id, **row}
    data.append(row)
    return data


def _matches(row, where_clause):
    """Require equality for every field in a nonempty condition."""
    return where_clause is None or all(
        row[name] == value for name, value in where_clause.items()
    )


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Cache results by the actual data and condition and return row copies."""
    key = json.dumps([table_data, where_clause], sort_keys=True, ensure_ascii=False)

    def calculate():
        """Filter the current snapshot only when the key is new."""
        return [row.copy() for row in table_data if _matches(row, where_clause)]

    rows = _select_cache(key, calculate)
    return [row.copy() for row in rows]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Return new rows with changes applied to every matching record."""
    if not where_clause or not set_clause:
        raise ValueError("Для update нужны set и where")
    if ID_COLUMN in set_clause:
        raise ValueError("Изменять ID нельзя")
    result = []
    for row in table_data:
        new_row = row.copy()
        if _matches(row, where_clause):
            for name, value in set_clause.items():
                if name not in row:
                    raise KeyError(f'Столбец "{name}" не найден.')
                if type(value) is not type(row[name]):
                    raise ValueError(f"Неверный тип для {name}")
            new_row.update(set_clause)
        result.append(new_row)
    return result


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Return the rows which do not match the required condition."""
    if not where_clause:
        raise ValueError("Для delete нужно условие where")
    return [row.copy() for row in table_data if not _matches(row, where_clause)]
