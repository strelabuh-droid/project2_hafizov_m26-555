"""The application loop connecting parsing, core functions and storage."""

import prompt
from prettytable import PrettyTable

from primitive_db import core
from primitive_db.constants import ID_COLUMN, META_FILE
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Describe the supported command syntax."""
    print("\n***Процесс работы с таблицей***")
    print("create_table <таблица> <столбец:тип> ...")
    print("list_tables | drop_table <таблица> | info <таблица>")
    print("insert into <таблица> values (<значение>, ...)")
    print("select from <таблица> [where <столбец> = <значение>]")
    print("update <таблица> set <столбец> = <значение> where <столбец> = <значение>")
    print("delete from <таблица> where <столбец> = <значение>")
    print('Типы: int, str, bool. Строки: "текст". Логические: true, false.')
    print("help — справка | exit — выход\n")


def welcome():
    """Print a greeting and the available commands."""
    print("***База данных***")
    print_help()


def _show_rows(schema, rows):
    """Print all columns in schema order, including when there are no rows."""
    table = PrettyTable()
    names = [column["name"] for column in schema]
    table.field_names = names
    for row in rows:
        table.add_row([row[name] for name in names])
    print(table)


def _describe_columns(schema):
    """Convert a schema into the form ID:int, name:str."""
    return ", ".join(f"{column['name']}:{column['type']}" for column in schema)


def _show_changed_rows(before, after, table_name):
    """Report each updated row or explain that no values changed."""
    changed = [new for old, new in zip(before, after) if old != new]
    for row in changed:
        print(
            f'Запись с ID={row[ID_COLUMN]} в таблице "{table_name}" успешно обновлена.'
        )
    if not changed:
        print("Изменённых записей нет.")


def _execute_crud(metadata, command):
    """Load rows, validate clauses, execute CRUD and save successful changes."""
    name = command["table"]
    operation = command["command"]
    schema = core.get_schema(metadata, name)
    if operation == "insert":
        result = core.insert(metadata, name, command["values"])
        if result is not None:
            save_table_data(name, result)
            print(
                f"Запись с ID={result[-1][ID_COLUMN]} успешно добавлена "
                f'в таблицу "{name}".'
            )
        return
    data = load_table_data(name)
    if operation == "info":
        print(f"Таблица: {name}")
        print(f"Столбцы: {_describe_columns(schema)}")
        print(f"Количество записей: {len(data)}")
        return
    where_clause = command["where"]
    if where_clause is not None:
        core.validate_clause(metadata, name, where_clause)
    if operation == "select":
        result = core.select(data, where_clause)
        if result is not None:
            _show_rows(schema, result)
    elif operation == "update":
        core.validate_clause(metadata, name, command["set"], allow_id=False)
        result = core.update(data, command["set"], where_clause)
        if result is not None:
            save_table_data(name, result)
            _show_changed_rows(data, result, name)
    elif operation == "delete":
        result = core.delete(data, where_clause)
        if result is not None:
            save_table_data(name, result)
            remaining_ids = {row[ID_COLUMN] for row in result}
            for row in data:
                if row[ID_COLUMN] not in remaining_ids:
                    print(
                        f"Запись с ID={row[ID_COLUMN]} успешно удалена "
                        f'из таблицы "{name}".'
                    )
            if len(data) == len(result):
                print("Подходящие записи не найдены.")


@handle_db_errors
def execute_command(text):
    """Handle one command and return exit only when the user requests it."""
    command = parse_command(text)
    operation = command["command"]
    if operation in ("empty", "exit"):
        return operation
    if operation == "help":
        print_help()
        return None
    metadata = load_metadata(META_FILE)
    if operation == "list_tables":
        names = core.list_tables(metadata)
        if names is not None:
            print("\n".join(f"- {name}" for name in names) or "Таблиц пока нет.")
    elif operation == "create_table":
        name = command["table"]
        result = core.create_table(metadata, name, command["columns"])
        if result is not None:
            save_table_data(name, [])
            save_metadata(META_FILE, result)
            print(
                f'Таблица "{name}" успешно создана со столбцами: '
                f"{_describe_columns(result[name])}"
            )
    elif operation == "drop_table":
        name = command["table"]
        core.get_schema(metadata, name)
        result = core.drop_table(metadata, name)
        if result is not None:
            save_metadata(META_FILE, result)
            print(f'Таблица "{name}" успешно удалена.')
    else:
        _execute_crud(metadata, command)
    return None


def run():
    """Read commands repeatedly and exit cleanly on EOF or keyboard interrupt."""
    welcome()
    while True:
        try:
            text = prompt.string("Введите команду: ")
            if execute_command(text) == "exit":
                break
        except (EOFError, KeyboardInterrupt):
            print("\nВыход из программы.")
            break
