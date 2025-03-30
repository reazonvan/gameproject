# Импорт необходимых модулей Django
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
import logging
from . import views  # Импорт представлений (views) из текущего приложения

# Настройка логирования
logger = logging.getLogger('chat_logger')

# Список URL-маршрутов приложения gameapp
urlpatterns = [
    path('', views.offer_list, name='index'),  # Главная страница сайта (список предложений)
    path('', views.offer_list, name='offer_list'),  # Дублирующий URL для списка предложений (для обратной совместимости)
    path('games/', views.game_catalog, name='game_catalog'),  # Каталог игр
    path('offers/', views.offer_listing, name='offer_listing'),  # Расширенный список предложений с фильтрацией
    path('offer/<int:offer_id>/', views.offer_detail, name='offer_detail'),  # Детальная страница предложения по ID
    path('offers/create/', views.create_offer, name='create_offer'),  # Страница создания нового предложения
    path('login/', views.login_view, name='login'),  # Страница входа в аккаунт
    path('register/', views.register_view, name='register'),  # Страница регистрации нового пользователя
    path('profile/', views.profile_view, name='profile'),  # Личный профиль текущего пользователя
    path('profile/update-avatar/', views.update_avatar, name='update_avatar'),  # Обновление аватара профиля
    path('profile/<str:username>/', views.profile_view, name='user_profile'),  # Профиль пользователя по имени пользователя
    path('chat/', views.chat_view, name='chat'),  # Страница чата для текущего пользователя
    path('chat/start_with_seller/', views.start_chat_with_seller, name='start_chat_with_seller'),  # Начать чат с продавцом
    
    # API-маршруты для работы с сообщениями в беседах
    path('api/conversations/<int:conversation_id>/messages/', views.get_messages, name='get_messages'),  # Получение всех сообщений беседы
    path('api/conversations/<int:conversation_id>/messages/new/', views.get_new_messages, name='get_new_messages'),  # Получение новых сообщений
    path('api/conversations/<int:conversation_id>/messages/send/', views.send_message, name='send_message'),  # Отправка сообщения
    path('api/conversations/<int:conversation_id>/messages/status/', views.get_message_statuses, name='get_message_statuses'),  # Статусы сообщений
    path('api/conversations/<int:conversation_id>/voice-message/', views.send_voice_message, name='send_voice_message'),  # Отправка голосового сообщения
    path('api/conversations/create/', views.create_conversation, name='create_conversation'),  # Создание новой беседы
    
    path('update_online_status/', views.update_online_status_view, name='update_online_status'),  # Обновление статуса онлайн пользователя
    path('api/users/status/', views.get_users_status, name='get_users_status'),  # API для получения статусов пользователей
    path('logout/', views.logout_view, name='logout'),  # Выход из аккаунта
    
    # Маршруты для работы с играми и категориями
    path('games/<slug:slug>/', views.game_detail, name='game_detail'),  # Детальная страница игры по URL-slug
    path('categories/<slug:slug>/', views.game_category, name='game_category'),  # Страница категории игры
    path('categories/<slug:category_slug>/<slug:slug>/', views.game_subcategory, name='game_subcategory'),  # Страница подкатегории игры
    
    # API-маршруты для получения данных о категориях и подкатегориях
    path('api/categories/', views.get_categories, name='get_categories'),  # Получение списка категорий
    path('api/subcategories/', views.get_subcategories, name='get_subcategories'),  # Получение списка подкатегорий
    
    path('notifications/', views.notifications_view, name='notifications'),  # Страница уведомлений пользователя
    
    # API-маршруты для работы с сообщениями и уведомлениями
    path('api/chat/check_new_messages/', views.check_new_messages, name='check_new_messages'),  # Проверка новых сообщений
    path('api/message/<int:message_id>/read/', views.mark_message_read, name='mark_message_read'),  # Отметка сообщения как прочитанного
    path('api/users/online-count/', views.get_online_users_count, name='get_online_users_count'),  # Получение количества пользователей онлайн
]

# Добавление маршрутов для медиа-файлов при режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    logger.debug(f"[URLS] Добавлены URL-маршруты для медиа-файлов: {settings.MEDIA_URL}")

# Логирование всех зарегистрированных URL-маршрутов
if settings.DEBUG:
    logger.info(f"[URLS] Зарегистрировано {len(urlpatterns)} URL-маршрутов")
    
    # Вывод списка URL в лог для отладки
    for pattern in urlpatterns:
        if hasattr(pattern, 'name') and pattern.name:
            logger.debug(f"[URLS] Маршрут: {pattern.pattern} -> {pattern.name}")
        else:
            logger.debug(f"[URLS] Маршрут: {pattern.pattern} (без имени)") 