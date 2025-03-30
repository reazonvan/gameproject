# Импорт класса Path для корректной работы с путями файловой системы независимо от ОС
from pathlib import Path
# Импорт модуля для работы с операционной системой и её переменными окружения
import os

# Базовые настройки из основного файла settings.py
# Определение базовой директории проекта - путь к родительской директории текущего файла
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ для подписи сессий, CSRF и т.д. (в продакшене должен быть надежно защищен)
# ВНИМАНИЕ: В реальном приложении ключ не должен храниться в коде
SECRET_KEY = "django-insecure-your-secret-key-here"

# Режим отладки - включает подробные сообщения об ошибках и другие отладочные функции
# В продакшене должен быть выключен (False) из соображений безопасности
DEBUG = True

# Список разрешенных хостов (доменов), с которых может быть доступно приложение
# Пустой список при DEBUG=True разрешает доступ только с localhost
ALLOWED_HOSTS = []

# Список установленных Django-приложений
INSTALLED_APPS = [
    "django.contrib.admin",         # Административная панель Django
    "django.contrib.auth",          # Система аутентификации и авторизации
    "django.contrib.contenttypes",  # Система типов контента (для polymorphic relationships)
    "django.contrib.sessions",      # Работа с сессиями пользователей
    "django.contrib.messages",      # Система сообщений и уведомлений
    "django.contrib.staticfiles",   # Работа со статическими файлами (CSS, JavaScript)
    "gameapp",                      # Основное приложение проекта
]

# Список middleware - компонентов, обрабатывающих запросы/ответы
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",           # Безопасность (HTTPS, заголовки и т.д.)
    "django.contrib.sessions.middleware.SessionMiddleware",    # Обработка сессий пользователей
    "django.middleware.common.CommonMiddleware",               # Общие настройки (URL нормализация и т.д.)
    "django.middleware.csrf.CsrfViewMiddleware",               # Защита от CSRF-атак
    "django.contrib.auth.middleware.AuthenticationMiddleware", # Аутентификация пользователей
    "django.contrib.messages.middleware.MessageMiddleware",    # Обработка сообщений и уведомлений
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Защита от clickjacking-атак
    "gameapp.online_status_middleware.OnlineStatusMiddleware", # Пользовательский middleware для отслеживания онлайн-статуса
]

# Корневая конфигурация URL для проекта
ROOT_URLCONF = "gameproject.urls"

# Настройки системы шаблонов Django
TEMPLATES = [
    {  # Словарь с настройками для движка шаблонов
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # Используем стандартный движок шаблонов Django
        "DIRS": [],  # Список дополнительных директорий для поиска шаблонов (пустой - ищем только в приложениях)
        "APP_DIRS": True,  # Искать шаблоны в директориях templates внутри приложений
        "OPTIONS": {  # Дополнительные опции для движка шаблонов
            "context_processors": [  # Список процессоров контекста - добавляют переменные в контекст всех шаблонов
                "django.template.context_processors.debug",             # Добавляет переменную debug и sql_queries
                "django.template.context_processors.request",           # Добавляет объект request в контекст
                "django.contrib.auth.context_processors.auth",          # Добавляет user и perms для проверки прав
                "django.contrib.messages.context_processors.messages",  # Добавляет сообщения и уведомления
                "gameapp.context_processors.common_context",            # Пользовательский процессор из gameapp
            ],
        },
    },
]

# Использование SQLite вместо PostgreSQL для локальной разработки
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Драйвер SQLite для Django
        'NAME': BASE_DIR / 'db.sqlite3',         # Путь к файлу базы данных
    }
}

# Настройки статических файлов (CSS, JavaScript, изображения)
STATIC_URL = '/static/'               # URL-префикс для статических файлов
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Директория для сбора статических файлов при деплое
STATICFILES_DIRS = [BASE_DIR / 'static']  # Дополнительные директории со статическими файлами

# Настройки медиа-файлов (загружаемые пользователями файлы)
MEDIA_URL = '/media/'                 # URL-префикс для медиа-файлов
MEDIA_ROOT = BASE_DIR / 'media'       # Директория для хранения медиа-файлов

# Тип поля автоинкрементного первичного ключа по умолчанию (BigAutoField вместо AutoField)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Настройки авторизации
LOGIN_REDIRECT_URL = '/'  # Перенаправление на главную страницу после входа
LOGOUT_REDIRECT_URL = '/'  # Перенаправление на главную страницу после выхода 