#!/usr/bin/env python
"""
Скрипт для запуска тестов в проекте Django.
Позволяет запускать все тесты или выборочные тесты по указанным модулям.
Использование:
    python test.py             # Запустить все тесты
    python test.py app_name    # Запустить тесты для конкретного приложения
    python test.py app_name.TestClass  # Запустить тесты конкретного класса
    python test.py app_name.TestClass.test_method  # Запустить конкретный тест
"""

import os
import sys
import django
from django.conf import settings

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameproject.settings_local")

# Инициализируем Django
django.setup()

# Импортируем тестовый runner Django
from django.test.runner import DiscoverRunner


def run_tests(test_labels=None):
    """
    Запускает Django тесты с указанными метками.
    
    Args:
        test_labels (list): Список меток для запуска конкретных тестов.
                          None для запуска всех тестов.
                          
    Returns:
        int: Количество неудачных тестов. 0 означает, что все тесты прошли успешно.
    """
    # Если аргументы не переданы, запускаем все тесты
    if not test_labels:
        test_labels = ['gameapp']
        
    # Создаем тестовый runner
    test_runner = DiscoverRunner(
        verbosity=2,            # Уровень детализации вывода
        interactive=True,       # Включаем интерактивный режим
        failfast=False,         # Не останавливать тесты после первой ошибки
    )
    
    print(f"Запуск тестов: {', '.join(test_labels) if test_labels else 'все тесты'}")
    
    # Запускаем тесты и получаем результат
    failures = test_runner.run_tests(test_labels)
    
    # Выводим результаты
    if failures:
        print(f"ОШИБКА: {failures} тестов не прошли.")
    else:
        print("УСПЕХ: Все тесты прошли успешно!")
        
    return failures


if __name__ == "__main__":
    # Получаем аргументы командной строки, кроме самого имени скрипта
    test_args = sys.argv[1:]
    
    # Запускаем тесты с переданными аргументами
    failures = run_tests(test_args)
    
    # Используем количество неудачных тестов как код возврата
    # 0 означает успешное выполнение
    sys.exit(failures) 