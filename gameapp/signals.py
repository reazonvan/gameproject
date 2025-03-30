from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from gameapp.models import UserProfile
import logging
import socket
import json

# Настройка логирования
logger = logging.getLogger('chat_logger')

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Сигнал для создания или обновления профиля пользователя при изменении модели User.
    """
    if created:
        # Если создан новый пользователь, создаем для него профиль
        logger.info(f"[SIGNAL:USER_CREATE] Создание нового профиля для пользователя {instance.username} (ID: {instance.id})")
        profile = UserProfile.objects.create(user=instance)
        logger.debug(f"[SIGNAL:USER_CREATE] Профиль создан успешно, ID: {profile.id}, online_status: {profile.online_status}, last_online: {profile.last_online}")
    else:
        # Если пользователь обновлен, убеждаемся, что у него есть профиль
        try:
            # Проверяем наличие профиля
            profile = instance.userprofile
            logger.debug(f"[SIGNAL:USER_UPDATE] Обновление пользователя {instance.username} (ID: {instance.id}), профиль существует (ID: {profile.id})")
        except UserProfile.DoesNotExist:
            logger.warning(f"[SIGNAL:USER_UPDATE] Профиль не найден для существующего пользователя {instance.username} (ID: {instance.id}), создаем новый")
            profile = UserProfile.objects.create(user=instance)
            logger.info(f"[SIGNAL:USER_UPDATE] Профиль создан успешно, ID: {profile.id}, online_status: {profile.online_status}, last_online: {profile.last_online}")

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Обработчик события входа пользователя в систему.
    """
    logger.info(f"[SIGNAL:LOGIN] Пользователь {user.username} (ID: {user.id}) вошел в систему")
    
    # Логируем информацию о запросе
    try:
        user_agent = request.META.get('HTTP_USER_AGENT', 'Не определено')
        request_method = request.method
        logger.debug(f"[SIGNAL:LOGIN] Дополнительная информация о входе: метод={request_method}, user-agent={user_agent}")
    except Exception as e:
        logger.warning(f"[SIGNAL:LOGIN] Не удалось получить информацию о запросе: {str(e)}")
    
    # Обновляем статус пользователя
    try:
        # Получаем или создаем профиль
        if hasattr(user, 'userprofile'):
            profile = user.userprofile
            logger.debug(f"[SIGNAL:LOGIN] Найден профиль пользователя {user.username} (ID профиля: {profile.id})")
        else:
            logger.warning(f"[SIGNAL:LOGIN] У пользователя {user.username} нет профиля, создаем новый")
            profile = UserProfile.objects.create(user=user)
            logger.info(f"[SIGNAL:LOGIN] Создан новый профиль (ID: {profile.id}) для пользователя {user.username}")
        
        # Сохраняем предыдущие значения для логирования изменений
        prev_status = profile.online_status
        prev_last_online = profile.last_online
        prev_total_logins = profile.total_logins
        
        # Обновляем статус
        profile.update_online_status()
        
        # Обновляем статистику входов
        client_ip = get_client_ip(request)
        logger.debug(f"[SIGNAL:LOGIN] IP адрес входа для {user.username}: {client_ip}")
        
        # Проверяем и логируем географическое расположение IP-адреса (если возможно)
        try:
            hostname = socket.gethostbyaddr(client_ip)[0]
            logger.debug(f"[SIGNAL:LOGIN] Hostname для IP {client_ip}: {hostname}")
        except (socket.herror, socket.gaierror):
            logger.debug(f"[SIGNAL:LOGIN] Не удалось определить hostname для IP {client_ip}")
            
        profile.update_login_stats(ip_address=client_ip)
        
        # Сбрасываем счетчик неудачных попыток
        if profile.failed_login_attempts > 0:
            logger.info(f"[SIGNAL:LOGIN] Сброс счетчика неудачных попыток для {user.username} (было: {profile.failed_login_attempts})")
            profile.reset_failed_login_attempts()
            
        # Логируем изменения в профиле
        changes = []
        if prev_status != profile.online_status:
            changes.append(f"online_status: {prev_status} -> {profile.online_status}")
        if prev_last_online != profile.last_online:
            changes.append(f"last_online: {prev_last_online} -> {profile.last_online}")
        if prev_total_logins != profile.total_logins:
            changes.append(f"total_logins: {prev_total_logins} -> {profile.total_logins}")
            
        if changes:
            logger.info(f"[SIGNAL:LOGIN] Изменения в профиле {user.username}: {', '.join(changes)}")
            
        # Записываем активность
        details = {
            'ip': client_ip,
            'user_agent': user_agent,
            'method': request_method
        }
        record_user_activity(user, 'login', details=details)
        
    except Exception as e:
        logger.error(f"[SIGNAL:LOGIN] Ошибка при обработке входа пользователя {user.username}: {str(e)}", exc_info=True)

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Обработчик события выхода пользователя из системы.
    """
    if user and user.is_authenticated:
        logger.info(f"[SIGNAL:LOGOUT] Пользователь {user.username} (ID: {user.id}) вышел из системы")
        
        try:
            # Логируем информацию о запросе
            try:
                user_agent = request.META.get('HTTP_USER_AGENT', 'Не определено')
                request_method = request.method
                logger.debug(f"[SIGNAL:LOGOUT] Дополнительная информация о выходе: метод={request_method}, user-agent={user_agent}")
            except Exception as e:
                logger.warning(f"[SIGNAL:LOGOUT] Не удалось получить информацию о запросе: {str(e)}")
                
            # Обновляем статус пользователя
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                
                # Сохраняем предыдущие значения для логирования
                prev_status = profile.online_status
                prev_session_start = profile.last_session_start
                prev_total_time = profile.total_time_online
                
                # Если пользователь был онлайн, записываем время сессии
                if profile.online_status and profile.last_session_start:
                    session_duration = timezone.now() - profile.last_session_start
                    session_seconds = session_duration.total_seconds()
                    
                    logger.info(f"[SIGNAL:LOGOUT] Завершение сессии пользователя {user.username}, продолжительность: {int(session_seconds // 3600)}ч {int((session_seconds % 3600) // 60)}мин {int(session_seconds % 60)}с")
                    
                    if profile.total_time_online:
                        profile.total_time_online += session_duration
                    else:
                        profile.total_time_online = session_duration
                
                # Устанавливаем статус оффлайн
                profile.online_status = False
                profile.last_session_start = None
                profile.save()
                
                # Логируем изменения
                changes = []
                if prev_status != profile.online_status:
                    changes.append(f"online_status: {prev_status} -> {profile.online_status}")
                if prev_session_start != profile.last_session_start:
                    changes.append(f"last_session_start: {prev_session_start} -> {profile.last_session_start}")
                if prev_total_time != profile.total_time_online:
                    # Форматируем общее время в часы:минуты:секунды
                    total_seconds = profile.total_time_online.total_seconds()
                    formatted_time = f"{int(total_seconds // 3600)}ч {int((total_seconds % 3600) // 60)}мин"
                    changes.append(f"total_time_online: {formatted_time}")
                
                if changes:
                    logger.info(f"[SIGNAL:LOGOUT] Изменения в профиле {user.username}: {', '.join(changes)}")
                
                # Записываем активность
                details = {
                    'ip': get_client_ip(request),
                    'session_duration': int(session_seconds) if profile.online_status and profile.last_session_start else None
                }
                record_user_activity(user, 'logout', details=details)
            
        except Exception as e:
            logger.error(f"[SIGNAL:LOGOUT] Ошибка при обработке выхода пользователя {user.username}: {str(e)}", exc_info=True)

@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """
    Обработчик события неудачной попытки входа.
    """
    username = credentials.get('username', None)
    logger.warning(f"[SIGNAL:LOGIN_FAILED] Неудачная попытка входа для пользователя {username}")
    
    # Логируем информацию о запросе
    try:
        if request:
            user_agent = request.META.get('HTTP_USER_AGENT', 'Не определено')
            ip = get_client_ip(request)
            logger.debug(f"[SIGNAL:LOGIN_FAILED] Дополнительная информация: IP={ip}, user-agent={user_agent}")
    except Exception as e:
        logger.warning(f"[SIGNAL:LOGIN_FAILED] Не удалось получить информацию о запросе: {str(e)}")
    
    if username:
        try:
            # Пытаемся найти пользователя
            user = User.objects.filter(username=username).first()
            
            if user:
                # Если пользователь существует, увеличиваем счетчик неудачных попыток
                logger.debug(f"[SIGNAL:LOGIN_FAILED] Увеличение счетчика неудачных попыток для пользователя {username}")
                
                if hasattr(user, 'userprofile'):
                    profile = user.userprofile
                    prev_attempts = profile.failed_login_attempts
                    prev_locked = profile.account_locked_until
                    
                    profile.increment_failed_login()
                    
                    # Логируем изменения
                    changes = []
                    if prev_attempts != profile.failed_login_attempts:
                        changes.append(f"failed_login_attempts: {prev_attempts} -> {profile.failed_login_attempts}")
                    if prev_locked != profile.account_locked_until and profile.account_locked_until:
                        changes.append(f"account_locked_until: {profile.account_locked_until}")
                    
                    if changes:
                        logger.info(f"[SIGNAL:LOGIN_FAILED] Изменения в профиле {username}: {', '.join(changes)}")
                    
                    if profile.is_account_locked():
                        locktime = profile.account_locked_until - timezone.now()
                        locktime_minutes = int(locktime.total_seconds() // 60)
                        logger.warning(f"[SIGNAL:LOGIN_FAILED] Аккаунт пользователя {username} заблокирован на {locktime_minutes} минут (до {profile.account_locked_until})")
                
                # Записываем активность
                client_ip = get_client_ip(request) if request else None
                record_user_activity(user, 'login_failed', details={'ip': client_ip})
            else:
                logger.info(f"[SIGNAL:LOGIN_FAILED] Попытка входа с несуществующим пользователем: {username}")
        
        except Exception as e:
            logger.error(f"[SIGNAL:LOGIN_FAILED] Ошибка при обработке неудачной попытки входа: {str(e)}", exc_info=True)

def get_client_ip(request):
    """
    Получает IP-адрес клиента из запроса.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
        logger.debug(f"[SIGNAL:IP] Получен IP из X-Forwarded-For: {ip}")
    else:
        ip = request.META.get('REMOTE_ADDR')
        logger.debug(f"[SIGNAL:IP] Получен IP из REMOTE_ADDR: {ip}")
    return ip

def record_user_activity(user, activity_type, details=None, related_object_id=None, related_object_type=None):
    """
    Записывает активность пользователя в журнал.
    """
    from .models import UserActivity
    
    try:
        if not details:
            details = {}
            
        logger.debug(f"[SIGNAL:ACTIVITY] Запись активности '{activity_type}' для пользователя {user.username}")
        
        # Добавляем временную метку
        details['timestamp'] = timezone.now().isoformat()
        
        # Создаем запись активности
        activity = UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            details=details,
            related_object_id=related_object_id,
            related_object_type=related_object_type
        )
        
        # Детализированное логирование для активностей, связанных с чатом
        if activity_type in ['message_sent', 'message_read', 'conversation_created']:
            details_str = json.dumps(details, ensure_ascii=False)
            logger.info(f"[SIGNAL:ACTIVITY:CHAT] {user.username} - {activity_type}: {details_str}")
        else:
            logger.debug(f"[SIGNAL:ACTIVITY] Создана запись активности ID: {activity.id} для пользователя {user.username}, тип: {activity_type}")
        
    except Exception as e:
        logger.error(f"[SIGNAL:ACTIVITY] Ошибка при записи активности пользователя {user.username}: {str(e)}", exc_info=True)