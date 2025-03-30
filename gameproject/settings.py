# Импорт модуля Path для работы с путями к файлам и директориям
from pathlib import Path

# Определение базовой директории проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ для криптографических подписей (используется для cookies, CSRF и т.д.)
# ВНИМАНИЕ: для продакшена нужно заменить на более безопасное значение
SECRET_KEY = "django-insecure-your-secret-key-here"

# Режим отладки (должен быть выключен в продакшене)
DEBUG = True

# Список разрешенных хостов (пустой список разрешает localhost)
ALLOWED_HOSTS = ['*']

# Список установленных приложений Django
INSTALLED_APPS = [
    "django.contrib.admin",  # Административный интерфейс
    "django.contrib.auth",   # Система аутентификации
    "django.contrib.contenttypes",  # Система типов контента
    "django.contrib.sessions",  # Система сессий
    "django.contrib.messages",  # Система сообщений
    "django.contrib.staticfiles",  # Работа со статическими файлами
    "gameapp",  # Наше основное игровое приложение
]

# Список промежуточных слоев (middleware) - обработчики запросов
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # Безопасность
    "django.contrib.sessions.middleware.SessionMiddleware",  # Сессии
    "django.middleware.common.CommonMiddleware",  # Общие настройки
    "django.middleware.csrf.CsrfViewMiddleware",  # Защита от CSRF атак
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Аутентификация
    "django.contrib.messages.middleware.MessageMiddleware",  # Сообщения
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Защита от clickjacking
]

# Конфигурация URL корневого уровня
ROOT_URLCONF = "gameproject.urls"

# Настройки шаблонизатора
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # Используем Django шаблонизатор
        "DIRS": [],  # Дополнительные директории для поиска шаблонов
        "APP_DIRS": True,  # Искать шаблоны в директориях приложений
        "OPTIONS": {
            "context_processors": [  # Процессоры контекста для шаблонов
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "gameapp.context_processors.common_context",  # Наш собственный процессор контекста
            ],
        },
    },
]

# Настройки базы данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Используем SQLite
        'NAME': BASE_DIR / 'db.sqlite3',  # Путь к файлу базы данных
    }
}

# Настройки статических файлов (CSS, JavaScript, изображения)
STATIC_URL = '/static/'  # URL для доступа к статическим файлам
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Директория для сбора статических файлов
STATICFILES_DIRS = [BASE_DIR / 'static']  # Дополнительные директории со статикой

# Настройки медиа-файлов (загружаемые пользователем файлы)
MEDIA_URL = '/media/'  # URL для доступа к медиа-файлам
MEDIA_ROOT = BASE_DIR / 'media'  # Директория для хранения медиа-файлов

# Тип поля для автоинкрементного первичного ключа
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Настройки авторизации
LOGIN_REDIRECT_URL = '/'  # Перенаправление на главную страницу после входа
LOGOUT_REDIRECT_URL = '/'  # Перенаправление на главную страницу после выхода
LOGIN_URL = '/login/'  # URL для страницы входа

# Настройки сессий
SESSION_COOKIE_AGE = 86400  # Время жизни сессии в секундах (1 день)
SESSION_SAVE_EVERY_REQUEST = True  # Сохранять сессию при каждом запросе

# Настройки безопасности
CSRF_COOKIE_SECURE = False  # Отправлять CSRF-токен только по HTTPS
SESSION_COOKIE_SECURE = False  # Отправлять сессионный cookie только по HTTPS
SECURE_BROWSER_XSS_FILTER = True  # Включить XSS-фильтр в браузере
SECURE_CONTENT_TYPE_NOSNIFF = True  # Запретить угадывание типа контента
