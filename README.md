# Примитивная база данных

Автор: Артур Хафизов. Группа: m26-555.

Консольное учебное приложение на Python. Поддерживает управление
таблицами и CRUD операции. Схемы хранятся в db_meta.json, записи -
в отдельных JSON файлах data/<имя_таблицы>.json.

## Требования и установка

Нужны Git, uv и Python 3.12 или новее. uv может скачать Python.
Склонируйте этот репозиторий и перейдите в его корневую папку.

```text
uv sync --locked
uv run database
```

Альтернативный запуск: uv run project или
uv run python -m primitive_db.main.

## Управление таблицами

```text
create_table users name:str age:int is_active:bool
list_tables
info users
```

Поддерживаются int, str и bool. ID:int добавляется автоматически.
Имена таблиц и столбцов чувствительны к регистру; используйте
латинские буквы, цифры после первого символа и подчёркивания.
Поле ID нельзя объявлять вручную или изменять через update.

## CRUD операции

```text
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
delete from users where ID = 1
info users
drop_table users
exit
```

При delete и drop_table программа запрашивает подтверждение.
Введите "y" для выполнения; любой другой ответ отменяет действие.
Все пользовательские поля обязательны. В values не передавайте ID:
он генерируется как максимум существующих ID плюс один.

Строки заключаются в двойные кавычки; числа и true/false - без них.
Кавычки и обратная косая черта внутри строки экранируются по JSON.
В set можно менять несколько полей через запятую:

```text
update users set age = 30, is_active = false where ID = 1
```

where использует равенство. Несколько условий через запятую должны
выполниться одновременно. Полный SQL, JOIN, OR, float и NULL
не поддерживаются. help выводит справку; exit завершает программу.
update и delete требуют where; select без where читает все строки.

## Ошибки и дополнительные возможности

Ожидаемые ошибки обрабатываются декоратором handle_db_errors.
confirm_action подтверждает удаления, log_time измеряет insert
и select. Результаты select кэшируются замыканием; ключ содержит
данные и условие, поэтому изменение данных даёт новый результат.
Кэш не заменяет чтение файлов и ограничен 128 ключами.

Приложение работает с базой в текущей рабочей папке. Запускайте
команду из одной и той же папки, чтобы видеть те же данные.
Используйте один процесс для одной папки. Запись JSON через
временный файл защищает отдельный файл; общей транзакции нет.

## Качество и сборка

```text
uv run ruff check .
uv run ruff format --check .
uv build
```

При установленном make доступны make install, make run,
make lint и make build. Обычные зависимости: prompt и prettytable.
Ruff находится в группе dev. Файлы окружения, базы и dist
не входят в репозиторий.

Для версии 0.2.0 проверка метаданных и установка в PowerShell:

```text
uvx twine check .\dist\primitive_db-0.2.0-py3-none-any.whl
uvx twine check .\dist\primitive_db-0.2.0.tar.gz
uv tool install --force .\dist\primitive_db-0.2.0-py3-none-any.whl
uv tool update-shell
```

После обновления PATH откройте новый терминал и в отдельной папке
выполните database. Команда project также доступна после установки.
Twine проверяет метаданные локально; публикация в PyPI не нужна.
На Linux используйте разделители путей / вместо обратной косой черты.

## Демонстрации

Управление таблицами

[![asciicast][tables-preview]][tables-demo]

[tables-preview]: https://asciinema.org/a/TABLES_RECORD_ID.svg
[tables-demo]: https://asciinema.org/a/TABLES_RECORD_ID

CRUD операции

[![asciicast][crud-preview]][crud-demo]

[crud-preview]: https://asciinema.org/a/CRUD_RECORD_ID.svg
[crud-demo]: https://asciinema.org/a/CRUD_RECORD_ID

Полный цикл и декораторы

[![asciicast][final-preview]][final-demo]

[final-preview]: https://asciinema.org/a/FINAL_RECORD_ID.svg
[final-demo]: https://asciinema.org/a/FINAL_RECORD_ID
