# Импорт необходимых модулей Django
from django.utils import timezone
from django.db import connection
from django.db.models import Q, Count
from .models import Message, Conversation, UserProfile, Notification
import logging

# Настройка логирования
logger = logging.getLogger('chat_logger')

def common_context(request):
    """
    Добавляет общие переменные контекста для всех шаблонов
    
    Параметры:
        request: объект HTTP-запроса
        
    Возвращает:
        словарь с переменными контекста, доступными всем шаблонам
    """
    today = timezone.now().date()  # Текущая дата
    yesterday = today - timezone.timedelta(days=1)  # Вчерашняя дата
    
    # Проверяем существование таблицы уведомлений в базе данных
    # (это может потребоваться при первом запуске, когда миграции ещё не применены)
    notifications_table_exists = False
    try:
        cursor = connection.cursor()  # Получаем курсор для выполнения SQL-запроса
        try:
            cursor.execute("SELECT 1 FROM gameapp_notification LIMIT 1")  # Пробуем выполнить запрос к таблице
            notifications_table_exists = True  # Если запрос успешен, таблица существует
        except Exception:
            notifications_table_exists = False  # При ошибке таблица не существует
        finally:
            cursor.close()  # Закрываем курсор
    except Exception:
        # В случае любых других ошибок при работе с соединением
        notifications_table_exists = False
    
    # Возвращаем словарь с контекстными переменными
    return {
        'today': today,  # Текущая дата
        'yesterday': yesterday,  # Вчерашняя дата
        'notifications_table_exists': notifications_table_exists,  # Флаг существования таблицы уведомлений
    } 

def unread_messages_count(request):
    """
    Контекстный процессор для получения количества непрочитанных сообщений
    в чате для текущего пользователя.
    """
    context = {'unread_messages_count': 0}
    
    if request.user.is_authenticated:
        try:
            logger.debug(f"[CONTEXT] Подсчет непрочитанных сообщений для пользователя {request.user.username}")
            
            # Получаем беседы, в которых участвует пользователь
            conversations = Conversation.objects.filter(
                Q(user1=request.user) | Q(user2=request.user)
            )
            
            # Получаем количество непрочитанных сообщений
            unread_count = Message.objects.filter(
                conversation__in=conversations, 
                is_read=False
            ).exclude(sender=request.user).count()
            
            context['unread_messages_count'] = unread_count
            
            logger.debug(f"[CONTEXT] Найдено {unread_count} непрочитанных сообщений для пользователя {request.user.username}")
        except Exception as e:
            logger.error(f"[CONTEXT] Ошибка при подсчете непрочитанных сообщений: {str(e)}")
    
    return context

def user_profile(request):
    """
    Контекстный процессор для получения профиля пользователя.
    """
    context = {'user_profile': None}
    
    if request.user.is_authenticated:
        try:
            logger.debug(f"[CONTEXT] Получение профиля для пользователя {request.user.username}")
            
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            if created:
                logger.info(f"[CONTEXT] Создан новый профиль для пользователя {request.user.username}")
            
            context['user_profile'] = profile
            
            logger.debug(f"[CONTEXT] Профиль пользователя {request.user.username} загружен в контекст")
        except Exception as e:
            logger.error(f"[CONTEXT] Ошибка при получении профиля пользователя: {str(e)}")
    
    return context

def notifications_processor(request):
    """
    Контекстный процессор для получения уведомлений пользователя.
    """
    context = {
        'notifications': [],
        'unread_notifications_count': 0
    }
    
    if request.user.is_authenticated:
        try:
            logger.debug(f"[CONTEXT] Получение уведомлений для пользователя {request.user.username}")
            
            # Получаем последние 5 уведомлений
            notifications = Notification.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
            
            # Получаем количество непрочитанных уведомлений
            unread_count = Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
            
            context['notifications'] = notifications
            context['unread_notifications_count'] = unread_count
            
            logger.debug(f"[CONTEXT] Загружено {len(notifications)} уведомлений, непрочитанных: {unread_count}")
        except Exception as e:
            logger.error(f"[CONTEXT] Ошибка при получении уведомлений: {str(e)}")
    
    return context

def active_section(request):
    """
    Контекстный процессор для определения активного раздела сайта.
    """
    context = {'active_section': None}
    
    try:
        logger.debug(f"[CONTEXT] Определение активного раздела для URL: {request.path}")
        
        # Определяем активный раздел на основе URL
        if '/chat/' in request.path:
            context['active_section'] = 'chat'
        elif '/profile/' in request.path:
            context['active_section'] = 'profile'
        elif '/games/' in request.path:
            context['active_section'] = 'games'
        elif '/offers/' in request.path:
            context['active_section'] = 'offers'
        else:
            context['active_section'] = 'home'
        
        logger.debug(f"[CONTEXT] Определен активный раздел: {context['active_section']}")
    except Exception as e:
        logger.error(f"[CONTEXT] Ошибка при определении активного раздела: {str(e)}")
    
    return context

def debug_mode(request):
    """
    Контекстный процессор для определения режима отладки.
    """
    from django.conf import settings
    
    context = {'debug': settings.DEBUG}
    
    if settings.DEBUG:
        logger.debug(f"[CONTEXT] Приложение работает в режиме отладки")
    
    return context 