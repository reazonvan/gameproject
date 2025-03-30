# Импорт базового класса конфигурации приложения Django
from django.apps import AppConfig
import logging
from django.db.models.signals import post_migrate

# Настройка логирования
logger = logging.getLogger('chat_logger')

class GameappConfig(AppConfig):
    """Класс конфигурации Django-приложения GameApp"""
    default_auto_field = 'django.db.models.BigAutoField'  # Тип поля для автоинкрементного первичного ключа
    name = 'gameapp'  # Имя приложения
    verbose_name = 'Игровая платформа'

    def ready(self):
        """
        Запускается при инициализации приложения
        """
        try:
            logger.info("[APP] Инициализация приложения gameapp")
            
            # Импортируем модуль сигналов для его регистрации
            import gameapp.signals
            logger.debug("[APP] Сигналы успешно зарегистрированы")
            
            # Другие настройки, которые нужно выполнить при инициализации (без обращения к БД)
            self.setup_initial_settings()
            logger.debug("[APP] Начальные настройки применены")
            
            # Регистрируем обработчик сигнала post_migrate для создания групп
            post_migrate.connect(self.create_user_groups_handler, sender=self)
            logger.debug("[APP] Зарегистрирован обработчик для создания групп после миграции")
            
        except Exception as e:
            logger.error(f"[APP] Ошибка при инициализации приложения: {str(e)}")
    
    def setup_initial_settings(self):
        """
        Применение начальных настроек приложения (без обращения к БД)
        """
        try:
            # Здесь размещаем только настройки, не требующие обращения к БД
            logger.debug("[APP] Начальные настройки приложения завершены")
            
        except Exception as e:
            logger.error(f"[APP] Ошибка при установке начальных настроек: {str(e)}")
            
    def create_user_groups_handler(self, sender, **kwargs):
        """
        Обработчик сигнала post_migrate для создания групп пользователей
        """
        try:
            logger.info("[APP] Запуск создания групп пользователей после миграции")
            self.create_user_groups()
        except Exception as e:
            logger.error(f"[APP] Ошибка при создании групп пользователей после миграции: {str(e)}")
            
    def create_user_groups(self):
        """
        Создание групп пользователей, если они отсутствуют
        """
        try:
            from django.contrib.auth.models import Group
            
            # Список групп, которые должны существовать
            groups = ['Администраторы', 'Модераторы', 'Продавцы', 'Покупатели']
            
            # Создаем группы, если они не существуют
            for group_name in groups:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    logger.info(f"[APP] Создана группа пользователей: {group_name}")
            
        except Exception as e:
            logger.error(f"[APP] Ошибка при создании групп пользователей: {str(e)}") 