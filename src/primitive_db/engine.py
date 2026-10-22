"""The first interactive application check."""

import prompt


def welcome():
    """Handle help and exit in the first interactive version."""
    print("Первая попытка запустить проект!")
    print("help - справочная информация; exit - выйти из программы")
    while True:
        command = prompt.string("Введите команду: ")
        if command == "exit":
            break
        if command == "help":
            print("help - справочная информация; exit - выйти из программы")
        else:
            print(f"Функции {command} нет. Попробуйте снова.")