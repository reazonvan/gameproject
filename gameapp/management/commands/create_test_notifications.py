from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from gameapp.models import Notification
import random
import datetime
import logging

# Настройка логирования
logger = logging.getLogger('chat_logger')

class Command(BaseCommand):
    help = 'Создает тестовые уведомления для пользователей'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=str, help='Список юзернеймов через запятую, для которых создать уведомления')
        parser.add_argument('--count', type=int, default=5, help='Количество уведомлений для каждого пользователя')
        parser.add_argument('--clear', action='store_true', help='Очистить существующие уведомления')

    def handle(self, *args, **options):
        # Получаем параметры команды
        users_str = options.get('users')
        count = options.get('count', 5)
        clear = options.get('clear', False)
        
        logger.info(f"[COMMAND] Запуск команды create_test_notifications с параметрами: users={users_str}, count={count}, clear={clear}")
        
        # Проверяем, что количество уведомлений положительное
        if count <= 0:
            logger.error(f"[COMMAND] Количество уведомлений должно быть положительным: {count}")
            self.stderr.write(self.style.ERROR('Количество уведомлений должно быть положительным'))
            return

        try:
            # Определяем пользователей, для которых создавать уведомления
            if users_str:
                # Получаем пользователей по указанным юзернеймам
                usernames = [username.strip() for username in users_str.split(',')]
                users = User.objects.filter(username__in=usernames)
                logger.info(f"[COMMAND] Найдено {users.count()} пользователей из {len(usernames)} указанных")
                
                if users.count() == 0:
                    logger.warning(f"[COMMAND] Не найдено ни одного пользователя из указанных: {users_str}")
                    self.stderr.write(self.style.WARNING('Не найдено ни одного пользователя'))
                    return
            else:
                # Берем всех пользователей
                users = User.objects.all()
                logger.info(f"[COMMAND] Будут созданы уведомления для всех пользователей ({users.count()})")

            # Очищаем существующие уведомления, если требуется
            if clear:
                deleted_count = Notification.objects.filter(user__in=users).delete()[0]
                logger.info(f"[COMMAND] Удалено {deleted_count} существующих уведомлений")
                self.stdout.write(self.style.SUCCESS(f'Удалено {deleted_count} существующих уведомлений'))
            
            # Примеры типов уведомлений
            notification_types = ['message', 'offer', 'system', 'success', 'warning', 'error']
            
            # Примеры заголовков уведомлений
            notification_titles = {
                'message': ['Новое сообщение', 'Вам написали', 'Непрочитанное сообщение'],
                'offer': ['Новое предложение', 'Обновлено предложение', 'Предложение принято'],
                'system': ['Обновление системы', 'Технические работы', 'Новые возможности'],
                'success': ['Операция успешна', 'Платеж получен', 'Сделка завершена'],
                'warning': ['Внимание', 'Срок истекает', 'Требуется подтверждение'],
                'error': ['Ошибка', 'Платеж отклонен', 'Сделка отменена']
            }
            
            # Примеры содержимого уведомлений
            notification_contents = {
                'message': ['Пользователь {} отправил вам сообщение', 'У вас непрочитанное сообщение от {}', 'Вам пришло новое сообщение в чате'],
                'offer': ['По вашему предложению поступило встречное предложение', 'Ваше предложение было обновлено', 'Ваше предложение было принято пользователем {}'],
                'system': ['Система обновлена до версии 2.0', 'Сегодня с 22:00 до 23:00 будут проводиться технические работы', 'Добавлены новые функции в профиль'],
                'success': ['Ваша операция успешно выполнена', 'Платеж на сумму {} успешно получен', 'Сделка с пользователем {} успешно завершена'],
                'warning': ['Срок действия вашего предложения истекает через 3 дня', 'Требуется подтверждение email', 'Обновите информацию в профиле'],
                'error': ['Произошла ошибка при обработке запроса', 'Платеж отклонен банком', 'Сделка была отменена пользователем {}']
            }
            
            # Создаем указанное количество уведомлений для каждого пользователя
            total_created = 0
            for user in users:
                logger.info(f"[COMMAND] Создание {count} тестовых уведомлений для пользователя {user.username}")
                created_for_user = 0
                
                for i in range(count):
                    try:
                        # Выбираем случайный тип уведомления
                        notification_type = random.choice(notification_types)
                        
                        # Выбираем случайный заголовок для данного типа
                        title = random.choice(notification_titles[notification_type])
                        
                        # Выбираем случайное содержимое для данного типа
                        content_template = random.choice(notification_contents[notification_type])
                        
                        # Форматируем содержимое, если нужно
                        if '{}' in content_template:
                            # Получаем случайного пользователя, отличного от текущего
                            other_users = User.objects.exclude(id=user.id)
                            if other_users.exists():
                                random_user = random.choice(other_users)
                                content = content_template.format(random_user.username)
                            else:
                                content = content_template.format('Система')
                        else:
                            content = content_template
                        
                        # Определяем, будет ли уведомление прочитано
                        is_read = random.choice([True, False])
                        
                        # Создаем случайную дату в пределах последних 30 дней
                        days_ago = random.randint(0, 30)
                        created_at = timezone.now() - datetime.timedelta(days=days_ago)
                        
                        # Создаем уведомление
                        notification = Notification.objects.create(
                            user=user,
                            title=title,
                            content=content,
                            notification_type=notification_type,
                            is_read=is_read,
                            created_at=created_at
                        )
                        
                        logger.debug(f"[COMMAND] Создано уведомление ID: {notification.id} для {user.username}, тип: {notification_type}")
                        created_for_user += 1
                        total_created += 1
                        
                    except Exception as e:
                        logger.error(f"[COMMAND] Ошибка при создании уведомления для {user.username}: {str(e)}")
                
                self.stdout.write(f'Создано {created_for_user} уведомлений для пользователя {user.username}')
            
            logger.info(f"[COMMAND] Всего создано {total_created} тестовых уведомлений")
            self.stdout.write(self.style.SUCCESS(f'Всего создано {total_created} тестовых уведомлений'))
        
        except Exception as e:
            logger.error(f"[COMMAND] Ошибка при выполнении команды: {str(e)}")
            self.stderr.write(self.style.ERROR(f'Ошибка: {str(e)}')) 