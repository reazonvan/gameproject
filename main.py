#!/usr/bin/env python
"""
Main entry point script for running the application directly
without the standard Django management commands.
This can be useful for development or specific deployment scenarios.
"""
# Импорт стандартных библиотек Python
import os                  # Для работы с операционной системой и переменными окружения
import sys                 # Для работы с аргументами командной строки и выходом из скрипта
import subprocess
from pathlib import Path
import logging
from django.core.management import execute_from_command_line

# Определяем базовую директорию проекта
BASE_DIR = Path(__file__).resolve().parent

def main():
    """
    Основная функция для запуска сервера приложения.
    В зависимости от режима запускает Django-сервер разработки или Gunicorn для продакшена.
    """
    # Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameproject.settings")
    
    # Режим работы (development или production)
    mode = os.environ.get("APP_MODE", "development")
    
    # Порт для сервера (по умолчанию 8000)
    port = os.environ.get("PORT", "8000")
    
    # Хост для привязки (0.0.0.0 позволит получить доступ с любого IP)
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Количество рабочих процессов для Gunicorn
    workers = os.environ.get("WORKERS", "2")
    
    # Проверяем доступен ли Gunicorn (для режима production)
    gunicorn_available = True
    try:
        # Пробуем импортировать модуль gunicorn
        import gunicorn
    except ImportError:
        gunicorn_available = False
    
    # Запуск в режиме разработки (используем встроенный сервер Django)
    if mode == "development" or not gunicorn_available:
        print("Starting Django development server...")
        from django.core.management import execute_from_command_line
        execute_from_command_line(["manage.py", "runserver", f"{host}:{port}"])
    
    # Запуск в режиме production (используем Gunicorn)
    else:
        print("Starting Gunicorn production server...")
        # Команда для запуска Gunicorn
        cmd = [
            "gunicorn",
            "--bind", f"{host}:{port}",
            "--workers", workers,
            "--timeout", "120",
            "--log-level", "info",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "--forwarded-allow-ips", "*",
            "gameproject.wsgi:application"
        ]
        
        # Запуск Gunicorn как подпроцесса
        subprocess.run(cmd)

def setup_static_files():
    """Настройка статических файлов перед запуском сервера."""
    print("Collecting static files...")
    
    # Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameproject.settings")
    
    # Запускаем команду collectstatic для сбора статических файлов
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "collectstatic", "--noinput"])
    
    print("Static files collected successfully.")

def setup_database():
    """Настройка базы данных перед запуском сервера."""
    print("Setting up database...")
    
    # Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameproject.settings")
    
    # Запускаем миграции для настройки базы данных
    from django.core.management import execute_from_command_line
    execute_from_command_line(["manage.py", "migrate", "--noinput"])
    
    print("Database setup completed.")

# Настройки логирования
def setup_logging():
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Настраиваем форматирование
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчик к корневому логгеру
    root_logger.addHandler(console_handler)
    
    # Настраиваем логгеры Django
    django_logger = logging.getLogger('django')
    django_logger.setLevel(logging.INFO)
    
    # Настраиваем логгер приложения
    app_logger = logging.getLogger('chat_logger')
    app_logger.setLevel(logging.DEBUG)
    
    # Отключаем распространение логов для app_logger, чтобы избежать дублирования
    app_logger.propagate = False
    app_logger.addHandler(console_handler)
    
    # Создаем специальный файловый обработчик для логов чата
    chat_file_handler = logging.FileHandler('chat_debug.log')
    chat_file_handler.setLevel(logging.DEBUG)
    chat_file_handler.setFormatter(formatter)
    app_logger.addHandler(chat_file_handler)
    
    # Логируем начало работы сервера
    logging.info("============================================")
    logging.info("Сервер запущен, логирование настроено")
    logging.info("============================================")

# Точка входа в скрипт - если файл запущен напрямую, а не импортирован
if __name__ == "__main__":
    # Настраиваем логирование
    setup_logging()
    
    logging.info("Запуск Django сервера из main.py")
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gameproject.settings")
    
    # Добавляем дополнительные аргументы для запуска сервера
    args = sys.argv.copy()
    if len(args) == 1:
        args.extend(["runserver", "0.0.0.0:8000"])
        logging.info(f"Запуск сервера с аргументами по умолчанию: {args[1:]}")
    
    # Логируем аргументы запуска
    logging.info(f"Аргументы запуска: {args}")
    
    # Запускаем Django сервер
    try:
        execute_from_command_line(args)
    except Exception as e:
        logging.error(f"Ошибка при запуске сервера: {e}", exc_info=True) 