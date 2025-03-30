from django import template
import logging

# Настройка логирования
logger = logging.getLogger('chat_logger')

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Получает значение по ключу из словаря"""
    return dictionary.get(key)

@register.filter
def split(value, delimiter):
    """Делит строку по разделителю"""
    return value.split(delimiter)

@register.filter
def price_with_currency(value, currency='USD'):
    """
    Добавляет символ валюты к значению цены
    """
    try:
        logger.debug(f"[TEMPLATE_TAG] Форматирование цены {value} с валютой {currency}")
        currency_symbols = {
            'USD': '$',
            'EUR': '€',
            'RUB': '₽',
            'GBP': '£',
            'JPY': '¥',
        }
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{value}"
    except Exception as e:
        logger.error(f"[TEMPLATE_TAG] Ошибка при форматировании цены: {str(e)}")
        return value

@register.filter
def user_display_name(user):
    """
    Возвращает отображаемое имя пользователя
    """
    try:
        logger.debug(f"[TEMPLATE_TAG] Получение имени пользователя для {user.username if hasattr(user, 'username') else 'неизвестный'}")
        if not user:
            return "Гость"
        return user.get_full_name() or user.username
    except Exception as e:
        logger.error(f"[TEMPLATE_TAG] Ошибка при получении имени пользователя: {str(e)}")
        return "Пользователь"

@register.filter
def time_since(date):
    """
    Возвращает время, прошедшее с указанной даты, в человеко-читаемом формате
    """
    from django.utils import timezone
    from django.utils.timesince import timesince
    
    try:
        logger.debug(f"[TEMPLATE_TAG] Расчет времени с даты {date}")
        if not date:
            return "Неизвестно"
        
        now = timezone.now()
        if date > now:
            logger.warning(f"[TEMPLATE_TAG] Дата в будущем: {date}")
            return "0 минут назад"
            
        return f"{timesince(date, now)} назад"
    except Exception as e:
        logger.error(f"[TEMPLATE_TAG] Ошибка при расчете времени: {str(e)}")
        return "Неизвестно"

@register.simple_tag(takes_context=True)
def is_unread_messages(context, conversation):
    """
    Проверяет, есть ли непрочитанные сообщения в диалоге для текущего пользователя
    """
    try:
        user = context['request'].user
        logger.debug(f"[TEMPLATE_TAG] Проверка непрочитанных сообщений в диалоге ID: {conversation.id} для пользователя {user.username}")
        
        from gameapp.models import Message
        count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=user).count()
        
        logger.debug(f"[TEMPLATE_TAG] Найдено {count} непрочитанных сообщений")
        return count > 0
    except Exception as e:
        logger.error(f"[TEMPLATE_TAG] Ошибка при проверке непрочитанных сообщений: {str(e)}")
        return False

@register.simple_tag(takes_context=True)
def unread_messages_count(context, conversation):
    """
    Возвращает количество непрочитанных сообщений в диалоге для текущего пользователя
    """
    try:
        user = context['request'].user
        logger.debug(f"[TEMPLATE_TAG] Подсчет непрочитанных сообщений в диалоге ID: {conversation.id} для пользователя {user.username}")
        
        from gameapp.models import Message
        count = Message.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=user).count()
        
        logger.debug(f"[TEMPLATE_TAG] Найдено {count} непрочитанных сообщений")
        return count
    except Exception as e:
        logger.error(f"[TEMPLATE_TAG] Ошибка при подсчете непрочитанных сообщений: {str(e)}")
        return 0

@register.filter
def truncate_chars(value, max_length):
    """
    Обрезает строку до указанной длины и добавляет многоточие
    """
    try:
        logger.debug(f"[TEMPLATE_TAG] Обрезка строки до {max_length} символов")
        if len(value) > max_length:
            return value[:max_length] + "..."
        return value
    except Exception as e:
        logger.error(f"[TEMPLATE_TAG] Ошибка при обрезке строки: {str(e)}")
        return value 