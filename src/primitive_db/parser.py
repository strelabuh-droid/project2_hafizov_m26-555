"""Parse the small database language, retaining quoted string values."""

import json
import shlex

from primitive_db.constants import PUNCTUATION


def _plain_tokens(text):
    """Split the part outside double quotes into words and punctuation."""
    lexer = shlex.shlex(text, posix=True, punctuation_chars=PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    result = []
    for token in lexer:
        if all(character in PUNCTUATION for character in token):
            result.extend(token)
        else:
            result.append(token)
    return result


def tokenize(text):
    """Keep JSON strings whole, including spaces, commas and escaped quotes."""
    tokens = []
    start = 0
    position = 0
    while position < len(text):
        if text[position] != '"':
            position += 1
            continue
        tokens.extend(_plain_tokens(text[start:position]))
        end = position + 1
        while end < len(text):
            if text[end] == "\\":
                end += 2
            elif text[end] == '"':
                break
            else:
                end += 1
        if end >= len(text):
            raise ValueError("Не закрыты двойные кавычки")
        tokens.append(text[position : end + 1])
        position = end + 1
        start = position
    tokens.extend(_plain_tokens(text[start:]))
    return tokens


def parse_value(token):
    """Convert a literal into exactly int, str or bool without executing code."""
    if token.lower() in ("true", "false"):
        return token.lower() == "true"
    try:
        value = json.loads(token)
    except json.JSONDecodeError as error:
        raise ValueError(f"Некорректное значение: {token}") from error
    if type(value) not in (int, str, bool):
        raise ValueError("Допустимы только int, str и bool")
    return value


def parse_values(tokens):
    """Parse comma separated literals without allowing empty values."""
    if not tokens or len(tokens) % 2 == 0:
        raise ValueError("Ожидаются значения через запятую")
    values = []
    for index, token in enumerate(tokens):
        if index % 2 == 0:
            values.append(parse_value(token))
        elif token != ",":
            raise ValueError("Между значениями нужна запятая")
    return values


def parse_clause(tokens, start):
    """Read column = value pairs and return a dictionary and the next index."""
    clause = {}
    position = start
    while True:
        if position + 2 >= len(tokens) or tokens[position + 1] != "=":
            raise ValueError("Ожидается условие столбец = значение")
        column = tokens[position]
        if column in clause:
            raise ValueError(f"Столбец {column} указан повторно")
        clause[column] = parse_value(tokens[position + 2])
        position += 3
        if position >= len(tokens) or tokens[position] != ",":
            return clause, position
        position += 1


def parse_command(text):
    """Turn one complete command into a dictionary for the engine."""
    tokens = tokenize(text)
    if not tokens:
        return {"command": "empty"}
    lower = [token.lower() for token in tokens]
    command = lower[0]
    result = {"command": command}
    if command in ("help", "exit", "list_tables") and len(tokens) == 1:
        return result
    if command in ("drop_table", "info") and len(tokens) == 2:
        return {**result, "table": tokens[1]}
    if command == "create_table" and len(tokens) >= 3:
        return {**result, "table": tokens[1], "columns": tokens[2:]}
    if command == "insert" and len(tokens) >= 7:
        if lower[1] == "into" and lower[3] == "values":
            if tokens[4] == "(" and tokens[-1] == ")":
                return {
                    **result,
                    "table": tokens[2],
                    "values": parse_values(tokens[5:-1]),
                }
    if command == "select" and len(tokens) >= 3 and lower[1] == "from":
        result.update(table=tokens[2], where=None)
        if len(tokens) == 3:
            return result
        if lower[3] == "where":
            result["where"], end = parse_clause(tokens, 4)
            if end == len(tokens):
                return result
    if command == "update" and len(tokens) >= 10 and lower[2] == "set":
        set_clause, end = parse_clause(tokens, 3)
        if end < len(tokens) and lower[end] == "where":
            where_clause, end = parse_clause(tokens, end + 1)
            if end == len(tokens):
                return {
                    **result,
                    "table": tokens[1],
                    "set": set_clause,
                    "where": where_clause,
                }
    if command == "delete" and len(tokens) >= 7:
        if lower[1] == "from" and lower[3] == "where":
            where_clause, end = parse_clause(tokens, 4)
            if end == len(tokens):
                return {**result, "table": tokens[2], "where": where_clause}
    known = {
        "help",
        "exit",
        "list_tables",
        "drop_table",
        "info",
        "create_table",
        "insert",
        "select",
        "update",
        "delete",
    }
    if command not in known:
        raise ValueError(f"Функции {tokens[0]} нет. Попробуйте снова.")
    raise ValueError("Неверный синтаксис команды. Введите help")
