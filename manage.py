#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
# Стандартный скрипт для управления Django-проектом

# Импорт необходимых модулей
import os      # Для работы с переменными окружения и файловой системой
import sys     # Для работы с аргументами командной строки и выходом из скрипта

def main():
    """Основная функция для выполнения административных задач Django."""
    # Устанавливаем переменную окружения для модуля настроек Django
    # Если переменная не установлена, используем gameproject.settings по умолчанию
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameproject.settings")
    try:
        # Пытаемся импортировать функцию для выполнения команд из Django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # В случае ошибки импорта Django выдаем подробное сообщение
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Запускаем команду Django с аргументами командной строки
    execute_from_command_line(sys.argv)

# Если скрипт запущен напрямую (не импортирован как модуль)
if __name__ == "__main__":
    main()  # Вызываем основную функцию
