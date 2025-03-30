from django.utils import timezone
from .models import UserProfile, UserActivity
from django.shortcuts import redirect
from datetime import timedelta
import logging

# Настройка логирования
logger = logging.getLogger('chat_logger')

class RequestMiddleware:
    """Middleware для обработки всех запросов и отслеживания активности пользователей."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Устанавливаем текущее время
        now = timezone.now()
        
        # Если пользователь авторизован, обновляем статистику
        if request.user.is_authenticated:
            logger.debug(f"[MIDDLEWARE] Обработка запроса для аутентифицированного пользователя {request.user.username} (ID: {request.user.id})")
            try:
                # Обновляем время последней активности
                if hasattr(request.user, 'userprofile'):
                    profile = request.user.userprofile
                    
                    # Записываем IP-адрес
                    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                    if x_forwarded_for:
                        ip = x_forwarded_for.split(',')[0]
                    else:
                        ip = request.META.get('REMOTE_ADDR')
                    
                    # Обновляем последний IP
                    profile.last_login_ip = ip
                    
                    # Если статус пользователя не онлайн, записываем активность "вход"
                    if not profile.online_status:
                        try:
                            UserActivity.objects.create(
                                user=request.user,
                                activity_type='login',
                                details={'ip': ip}
                            )
                        except Exception:
                            # Игнорируем ошибки создания активности
                            pass
                    
                    profile.save(update_fields=['last_login_ip'])
            except Exception:
                # Игнорируем любые ошибки при обновлении профиля
                pass
        
        # Обрабатываем запрос
        response = self.get_response(request)
        
        return response


class ActiveUserMiddleware:
    """
    Middleware для отслеживания активных пользователей и обработки статуса онлайн.
    """
    def __init__(self, get_response):
        logger.debug("[MIDDLEWARE] Инициализация ActiveUserMiddleware")
        self.get_response = get_response
    
    def __call__(self, request):
        # Код выполняется перед view
        if request.user.is_authenticated:
            logger.debug(f"[MIDDLEWARE] Обработка запроса для аутентифицированного пользователя {request.user.username} (ID: {request.user.id})")
            
            # Определяем, нужно ли обновлять статус
            # Не обновляем для AJAX запросов, чтобы не переопределять действия API
            if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                try:
                    profile = request.user.userprofile
                    # Проверяем, прошло ли достаточно времени с момента последнего обновления
                    last_activity = getattr(request, 'last_activity_time', None)
                    now = timezone.now()
                    
                    if not last_activity or (now - last_activity).seconds > 60:  # Обновляем раз в минуту
                        logger.debug(f"[MIDDLEWARE] Обновление времени активности для {request.user.username}")
                        request.last_activity_time = now
                        
                        # Обновляем статус online и last_online
                        if not profile.online_status:
                            logger.info(f"[MIDDLEWARE] Установка статуса online=True для {request.user.username}")
                            profile.online_status = True
                            profile.save(update_fields=['online_status'])
                            
                        # Обновляем время последнего посещения
                        profile.last_online = now
                        profile.save(update_fields=['last_online'])
                    
                except Exception as e:
                    logger.error(f"[MIDDLEWARE] Ошибка при обновлении активности пользователя {request.user.username}: {str(e)}")
        else:
            logger.debug("[MIDDLEWARE] Обработка запроса для анонимного пользователя")
        
        # Вызываем следующий middleware в цепочке
        response = self.get_response(request)
        
        # Код выполняется после view
        return response


class InactiveUserMiddleware:
    """
    Middleware для регулярной проверки и обновления статуса неактивных пользователей.
    """
    def __init__(self, get_response):
        logger.debug("[MIDDLEWARE] Инициализация InactiveUserMiddleware")
        self.get_response = get_response
        self.last_cleanup = timezone.now()
    
    def __call__(self, request):
        # Проверяем, не пора ли обновить статусы неактивных пользователей
        now = timezone.now()
        if (now - self.last_cleanup).seconds > 300:  # Каждые 5 минут
            logger.info("[MIDDLEWARE] Запуск задачи по обновлению статусов неактивных пользователей")
            self.last_cleanup = now
            self.update_inactive_users()
        
        # Вызываем следующий middleware в цепочке
        response = self.get_response(request)
        
        return response
    
    def update_inactive_users(self):
        """Обновляет статус пользователей, которые не были в сети более 5 минут"""
        from .models import UserProfile
        
        # Получаем пользователей, которые помечены как online, но не были активны более 5 минут
        try:
            threshold = timezone.now() - timedelta(minutes=5)
            
            # Получаем профили пользователей, которые онлайн, но не активны
            online_profiles = UserProfile.objects.filter(
                online_status=True,
                last_online__lt=threshold
            )
            
            count = online_profiles.count()
            if count > 0:
                logger.info(f"[MIDDLEWARE] Найдено {count} неактивных пользователей с online_status=True")
                
                # Обновляем статусы
                for profile in online_profiles:
                    logger.info(f"[MIDDLEWARE] Обновление статуса для неактивного пользователя {profile.user.username} (ID: {profile.user.id})")
                    
                    # Рассчитываем продолжительность сессии
                    if profile.last_session_start:
                        session_duration = profile.last_online - profile.last_session_start
                        logger.debug(f"[MIDDLEWARE] Пользователь {profile.user.username} был в сети {session_duration}")
                        
                        # Обновляем общее время онлайн
                        if profile.total_time_online:
                            profile.total_time_online += session_duration
                        else:
                            profile.total_time_online = session_duration
                        
                        profile.last_session_start = None
                    
                    # Устанавливаем статус оффлайн
                    profile.online_status = False
                    profile.save()
                    logger.info(f"[MIDDLEWARE] Пользователь {profile.user.username} (ID: {profile.user.id}) помечен как оффлайн")
            
        except Exception as e:
            logger.error(f"[MIDDLEWARE] Ошибка при обновлении статусов неактивных пользователей: {str(e)}")


class SessionTimerMiddleware:
    """
    Middleware для отслеживания времени начала сессии и общего времени онлайн
    """
    def __init__(self, get_response):
        logger.debug("[MIDDLEWARE] Инициализация SessionTimerMiddleware")
        self.get_response = get_response
    
    def __call__(self, request):
        # Код перед view
        if request.user.is_authenticated:
            logger.debug(f"[MIDDLEWARE] Проверка сессии для пользователя {request.user.username} (ID: {request.user.id})")
            
            try:
                profile = request.user.userprofile
                
                # Проверяем, есть ли запись о начале сессии
                if not profile.last_session_start:
                    logger.info(f"[MIDDLEWARE] Установка времени начала сессии для пользователя {request.user.username}")
                    profile.last_session_start = timezone.now()
                    profile.save(update_fields=['last_session_start'])
                
            except Exception as e:
                logger.error(f"[MIDDLEWARE] Ошибка при обработке сессии пользователя {request.user.username}: {str(e)}")
        
        # Вызываем следующий middleware
        response = self.get_response(request)
        
        # Код после view
        return response
