from django.utils import timezone
import logging
import time

# Настройка логирования
logger = logging.getLogger('chat_logger')

class OnlineStatusMiddleware:
    """
    Middleware для отслеживания статуса онлайн пользователей.
    Проверяет и обновляет статус пользователя при каждом запросе.
    """
    def __init__(self, get_response):
        logger.debug("[MIDDLEWARE] Инициализация OnlineStatusMiddleware")
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        request_path = request.path
        
        is_chat_related = any(path in request_path for path in ['/chat/', '/api/messages/', '/api/conversations/'])
        
        log_level = logging.DEBUG
        if is_chat_related:
            log_level = logging.INFO
        
        logger.log(log_level, f"[MIDDLEWARE:OnlineStatus] Вызов middleware для запроса {request_path} от {'аутентифицированного пользователя' if request.user.is_authenticated else 'анонимного пользователя'}")
        
        if request.user.is_authenticated:
            try:
                # Проверяем и обновляем статус онлайн
                if hasattr(request.user, 'userprofile'):
                    profile = request.user.userprofile
                    
                    # Сохраняем предыдущее состояние для логирования
                    previous_status = profile.online_status
                    previous_last_online = profile.last_online
                    previous_session_start = profile.last_session_start
                    
                    # Обновляем статус и время
                    now = timezone.now()
                    profile.last_online = now
                    
                    # Устанавливаем статус онлайн
                    if not profile.online_status:
                        logger.info(f"[MIDDLEWARE:OnlineStatus] Изменение статуса для {request.user.username}: offline -> online")
                        profile.online_status = True
                    
                    # Начинаем новую сессию, если это первый визит или предыдущая сессия завершена
                    if not profile.last_session_start:
                        logger.info(f"[MIDDLEWARE:OnlineStatus] Начало новой сессии для пользователя {request.user.username}")
                        profile.last_session_start = now
                    
                    # Подсчитываем время сессии для логирования
                    if profile.last_session_start:
                        session_duration = now - profile.last_session_start
                        session_duration_seconds = session_duration.total_seconds()
                        
                        # Логируем длительные сессии (более часа) для мониторинга
                        if session_duration_seconds > 3600:  # 1 час в секундах
                            logger.info(f"[MIDDLEWARE:OnlineStatus] Длительная сессия пользователя {request.user.username}: {int(session_duration_seconds // 3600)} ч {int((session_duration_seconds % 3600) // 60)} мин")
                    
                    # Сохраняем изменения в базе данных
                    fields_to_update = ['last_online', 'online_status']
                    if profile.last_session_start != previous_session_start:
                        fields_to_update.append('last_session_start')
                    
                    profile.save(update_fields=fields_to_update)
                    
                    # Подробное логирование изменений
                    changes = []
                    if previous_status != profile.online_status:
                        changes.append(f"online_status: {previous_status} -> {profile.online_status}")
                    if previous_last_online != profile.last_online:
                        time_diff = (profile.last_online - previous_last_online).total_seconds()
                        changes.append(f"last_online обновлено (+{time_diff:.1f}с)")
                    if previous_session_start != profile.last_session_start and profile.last_session_start:
                        changes.append(f"last_session_start: {profile.last_session_start}")
                    
                    if changes and is_chat_related:
                        logger.info(f"[MIDDLEWARE:OnlineStatus] Обновлен профиль пользователя {request.user.username}: {', '.join(changes)}")
                    elif changes:
                        logger.debug(f"[MIDDLEWARE:OnlineStatus] Обновлен профиль пользователя {request.user.username}: {', '.join(changes)}")
                        
                else:
                    logger.warning(f"[MIDDLEWARE:OnlineStatus] У пользователя {request.user.username} отсутствует профиль")
            except Exception as e:
                logger.error(f"[MIDDLEWARE:OnlineStatus] Ошибка при обработке статуса пользователя {request.user.username}: {str(e)}", exc_info=True)
        
        # Вызываем следующий middleware в цепочке
        response = self.get_response(request)
        
        # Логируем время выполнения для долгих запросов
        elapsed_time = time.time() - start_time
        if elapsed_time > 1.0:  # Логируем запросы длительностью более 1 секунды
            logger.warning(f"[MIDDLEWARE:OnlineStatus] Долгий запрос {request_path}: {elapsed_time:.2f}с")
        elif is_chat_related and elapsed_time > 0.5:  # Логируем чат-запросы длительностью более 0.5 секунды
            logger.info(f"[MIDDLEWARE:OnlineStatus] Запрос чата {request_path} выполнен за {elapsed_time:.2f}с")
        elif is_chat_related:
            logger.debug(f"[MIDDLEWARE:OnlineStatus] Запрос чата {request_path} выполнен за {elapsed_time:.2f}с")
        
        return response 