"""Reusable error handling, confirmation, timing and a cache closure."""

import time

from primitive_db.constants import CACHE_MAX_ENTRIES


def _preserve_description(wrapper, func):
    """Retain the original function name and documentation on its wrapper."""
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def handle_db_errors(func):
    """Report expected database errors and signal failure with None."""

    def wrapper(*args, **kwargs):
        """Call the function or print an understandable error."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: {error.args[0]}")
        except ValueError as error:
            print(f"Ошибка: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлом: {error}")
        return None

    return _preserve_description(wrapper, func)


def confirm_action(action_name):
    """Create a decorator which proceeds only after an explicit y answer."""

    def decorator(func):
        """Attach the requested confirmation to one function."""

        def wrapper(*args, **kwargs):
            """Ask before calling the original function."""
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')
            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return _preserve_description(wrapper, func)

    return decorator


def log_time(func):
    """Print elapsed monotonic time even if the operation raises an error."""

    def wrapper(*args, **kwargs):
        """Measure only the wrapped operation."""
        start = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - start
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")

    return _preserve_description(wrapper, func)


def create_cacher():
    """Return a function retaining its cache between calls."""
    cache = {}

    def cache_result(key, value_func):
        """Reuse a result or calculate it once for a new key."""
        if key not in cache:
            if len(cache) >= CACHE_MAX_ENTRIES:
                cache.clear()
            cache[key] = value_func()
        return cache[key]

    return cache_result