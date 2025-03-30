# Импорт модуля администратора Django для доступа к административной панели
from django.contrib import admin
# Импорт функций для определения URL маршрутов и включения маршрутов из других приложений
from django.urls import path, include
# Импорт настроек проекта для доступа к DEBUG, MEDIA_ROOT и т.д.
from django.conf import settings
# Импорт функции для обслуживания статических файлов во время разработки
from django.conf.urls.static import static
# Импорт представления для отображения домашней страницы
from gameapp.views import offer_list

# Список URL-шаблонов проекта
urlpatterns = [
    path('admin/', admin.site.urls),  # URL для административной панели Django (обычно /admin/)
    path('', include('gameapp.urls')),  # Перенаправление корневого URL на маршруты из gameapp.urls
    path('accounts/', include('django.contrib.auth.urls')),  # Встроенные URL для авторизации (логин, регистрация и т.д.)
]

# Добавление URL для обслуживания статических и медиа-файлов во время разработки
# В продакшене эти файлы должны обслуживаться веб-сервером, а не Django
if settings.DEBUG:  # Проверка, что проект в режиме отладки
    # Добавление URL для статических файлов
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Добавление URL для медиа-файлов (загруженных пользователями)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# В производственной среде статические файлы должны обслуживаться веб-сервером, а не Django
else:
    # Но для разработки и демонстрации мы все равно добавляем путь для медиа-файлов
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)