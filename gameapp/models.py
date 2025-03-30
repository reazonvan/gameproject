from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Q
from django.utils.text import slugify
import logging

# Настройка логирования
logger = logging.getLogger('chat_logger')


class Game(models.Model):
    """Модель для представления игр в системе"""
    title = models.CharField(max_length=100)  # Название игры
    description = models.TextField(blank=True)  # Описание игры
    release_date = models.DateField(null=True, blank=True)  # Дата выпуска игры
    developer = models.CharField(max_length=100, blank=True, null=True)  # Разработчик игры
    publisher = models.CharField(max_length=100, blank=True, null=True)  # Издатель игры
    image = models.ImageField(upload_to='game_images/', null=True, blank=True)  # Обложка игры
    slug = models.SlugField(unique=True, null=True, blank=True)  # URL-совместимый идентификатор
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания записи
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления

    def __str__(self):
        return self.title
        
    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения для автоматического создания slug"""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        """Получение абсолютного URL для доступа к странице игры"""
        return reverse('game_detail', args=[self.slug])


class GameCategory(models.Model):
    """Модель для категорий игровых предметов"""
    name = models.CharField(max_length=100)  # Название категории
    description = models.TextField(blank=True)  # Описание категории
    icon = models.ImageField(upload_to='category_icons/', null=True, blank=True)  # Иконка категории
    order = models.PositiveIntegerField(default=0)  # Порядок отображения
    slug = models.SlugField(unique=True, null=True, blank=True)  # URL-совместимый идентификатор
    is_active = models.BooleanField(default=True)  # Активна ли категория
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания категории
    # Связь с игрой
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='categories', null=True)  # Игра, к которой относится категория

    class Meta:
        """Метаданные модели"""
        ordering = ['order', 'name']  # Порядок сортировки
        verbose_name = 'Категория игры'  # Название в единственном числе
        verbose_name_plural = 'Категории игр'  # Название во множественном числе
        # Уникальное сочетание игры и слага
        unique_together = ['game', 'slug']  # Предотвращает дублирование категорий внутри одной игры

    def __str__(self):
        """Строковое представление объекта"""
        if self.game:
            return f"{self.game.title} - {self.name}"
        return self.name
        
    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения для автоматического создания slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        """Получение абсолютного URL для доступа к странице категории"""
        if self.game:
            return reverse('game_category', args=[self.game.slug, self.slug])
        return reverse('game_category', args=[self.slug])


class GameSubcategory(models.Model):
    """Модель для подкатегорий игровых предметов"""
    category = models.ForeignKey(GameCategory, on_delete=models.CASCADE, related_name='subcategories')  # Родительская категория
    name = models.CharField(max_length=100)  # Название подкатегории
    description = models.TextField(blank=True)  # Описание подкатегории
    icon = models.ImageField(upload_to='subcategory_icons/', null=True, blank=True)  # Иконка подкатегории
    order = models.PositiveIntegerField(default=0)  # Порядок отображения
    slug = models.SlugField(null=True, blank=True)  # URL-совместимый идентификатор
    is_active = models.BooleanField(default=True)  # Активна ли подкатегория
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания подкатегории

    class Meta:
        """Метаданные модели"""
        ordering = ['category', 'order', 'name']  # Порядок сортировки
        verbose_name = 'Подкатегория игры'  # Название в единственном числе
        verbose_name_plural = 'Подкатегории игр'  # Название во множественном числе
        unique_together = ['category', 'slug']  # Предотвращает дублирование подкатегорий внутри одной категории

    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.category.name} - {self.name}"
        
    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения для автоматического создания slug"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        """Получение абсолютного URL для доступа к странице подкатегории"""
        return reverse('game_subcategory', args=[self.category.slug, self.slug])


class Server(models.Model):
    """Модель для игровых серверов"""
    game = models.ForeignKey(Game, on_delete=models.CASCADE)  # Игра, к которой относится сервер
    name = models.CharField(max_length=50)  # Название сервера
    region = models.CharField(max_length=50)  # Регион сервера

    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.game.title} - {self.name}"


class Offer(models.Model):
    """Модель для предложений о продаже игровых предметов"""
    # Выбор качества предмета
    ITEM_QUALITY_CHOICES = [
        ('common', 'Обычный'),
        ('uncommon', 'Необычный'),
        ('rare', 'Редкий'),
        ('epic', 'Эпический'),
        ('legendary', 'Легендарный'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE)  # Продавец (пользователь)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)  # Игра
    server = models.ForeignKey(Server, on_delete=models.CASCADE)  # Сервер
    category = models.ForeignKey(GameCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers')  # Категория предмета
    subcategory = models.ForeignKey(GameSubcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers')  # Подкатегория
    item_name = models.CharField(max_length=100)  # Название предмета
    description = models.TextField()  # Описание предложения
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена (до 10 цифр, 2 после запятой)
    amount = models.PositiveIntegerField(default=1)  # Количество предметов
    quality = models.CharField(max_length=20, choices=ITEM_QUALITY_CHOICES, default='common')  # Качество предмета
    is_tradable = models.BooleanField(default=True)  # Можно ли обменять предмет
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания предложения
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления

    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.item_name} ({self.game.title})"
    
    def get_absolute_url(self):
        """Получение абсолютного URL для доступа к странице предложения"""
        return reverse('offer_detail', args=[self.id])


class Item(models.Model):
    """Модель для игровых предметов"""
    name = models.CharField(max_length=100)  # Название предмета
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='items')  # Игра, к которой относится предмет
    category = models.ForeignKey(GameCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')  # Категория предмета
    subcategory = models.ForeignKey(GameSubcategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')  # Подкатегория предмета
    description = models.TextField(blank=True)  # Описание предмета
    image = models.ImageField(upload_to='item_images/', null=True, blank=True)  # Изображение предмета
    quality = models.CharField(max_length=20, choices=Offer.ITEM_QUALITY_CHOICES, default='common')  # Качество предмета
    is_tradable = models.BooleanField(default=True)  # Можно ли обменять предмет
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания записи
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления
    
    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.name} ({self.game.title})"
    
    def get_absolute_url(self):
        """Получение абсолютного URL для доступа к странице предмета"""
        return reverse('item_detail', args=[self.id])


class UserProfile(models.Model):
    """Модель профиля пользователя с расширенными данными и статистикой"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Связь один-к-одному с моделью User Django
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # Аватар пользователя
    online_status = models.BooleanField(default=False)  # Статус онлайн (в сети/не в сети)
    last_online = models.DateTimeField(default=timezone.now)  # Время последнего посещения
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, help_text="Формат: +7XXXXXXXXXX")  # Номер телефона
    
    # Дополнительные поля для статистики пользователя
    registration_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP-адрес при регистрации")  # IP при регистрации
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, help_text="IP-адрес последнего входа")  # IP последнего входа
    total_logins = models.PositiveIntegerField(default=0, help_text="Общее количество входов в систему")  # Счетчик входов
    total_time_online = models.DurationField(null=True, blank=True, help_text="Общее время онлайн")  # Общее время в системе
    last_session_start = models.DateTimeField(null=True, blank=True, help_text="Начало последней сессии")  # Начало текущей сессии
    
    # Настройки безопасности
    failed_login_attempts = models.PositiveSmallIntegerField(default=0, help_text="Количество неудачных попыток входа")  # Счетчик неудачных входов
    account_locked_until = models.DateTimeField(null=True, blank=True, help_text="Аккаунт заблокирован до")  # Время окончания блокировки
    two_factor_enabled = models.BooleanField(default=False, help_text="Включена ли двухфакторная аутентификация")  # Статус 2FA
    is_verified = models.BooleanField(default=False, help_text="Подтвержден ли аккаунт продавца")  # Верификация продавца
    verified_date = models.DateTimeField(null=True, blank=True, help_text="Дата верификации аккаунта")  # Дата верификации
    
    # Дополнительные персональные данные
    bio = models.TextField(blank=True, help_text="Краткая информация о пользователе")  # Биография пользователя
    location = models.CharField(max_length=100, blank=True, help_text="Город/страна пользователя")  # Местоположение
    
    # Статистика активности
    offers_count = models.PositiveIntegerField(default=0, help_text="Количество созданных предложений")  # Кол-во предложений
    purchases_count = models.PositiveIntegerField(default=0, help_text="Количество совершенных покупок")  # Кол-во покупок
    sales_count = models.PositiveIntegerField(default=0, help_text="Количество совершенных продаж")  # Кол-во продаж
    deals_count = models.PositiveIntegerField(default=0, help_text="Общее количество завершенных сделок (устаревшее)")  # Общее кол-во сделок
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Рейтинг пользователя")  # Рейтинг
    activity_log = models.JSONField(default=dict, blank=True, null=True, help_text="Журнал активности пользователя по дням")  # JSON с активностями
    
    def update_online_status(self):
        """Обновляет статус онлайн пользователя и подсчитывает время в сети"""
        logger.debug(f"[MODEL] Обновление статуса online для пользователя {self.user.username} (ID: {self.user.id})")
        now = timezone.now()
        
        # Проверяем, не установлена ли дата в будущем
        if self.last_online > now:
            # Если дата в будущем, исправляем её
            logger.warning(f"[MODEL] Обнаружена дата в будущем для пользователя {self.user.username} (ID: {self.user.id})")
            self.last_online = now
            
        # Предыдущий статус для логирования
        previous_status = self.online_status
        
        # Время отсутствия активности в секундах
        inactive_time = (now - self.last_online).total_seconds()
        
        # Пользователь считается в сети, если был активен в последние 5 минут
        if inactive_time < 300:  # 5 минут = 300 секунд
            # Если пользователь был не в сети, а теперь в сети - обновляем время начала сессии
            if not self.online_status and not self.last_session_start:
                logger.info(f"[MODEL] Пользователь {self.user.username} (ID: {self.user.id}) перешел в онлайн")
                self.last_session_start = now
            
            # Устанавливаем статус "в сети"
            if not self.online_status:
                logger.info(f"[MODEL] Изменен статус пользователя {self.user.username} (ID: {self.user.id}): offline -> online")
            self.online_status = True
        else:
            # Если пользователь был в сети, а теперь не в сети - обновляем общее время онлайн
            if self.online_status and self.last_session_start:
                session_duration = now - self.last_session_start
                logger.info(f"[MODEL] Завершена сессия пользователя {self.user.username} (ID: {self.user.id}), продолжительность: {session_duration}")
                
                if self.total_time_online:
                    self.total_time_online += session_duration
                else:
                    self.total_time_online = session_duration
                self.last_session_start = None
            
            # Устанавливаем статус "не в сети"
            if self.online_status:
                logger.info(f"[MODEL] Изменен статус пользователя {self.user.username} (ID: {self.user.id}): online -> offline")
            self.online_status = False
        
        # Обновляем время последнего визита только при запросе heartbeat
        # или когда статус изменился с offline на online
        if previous_status != self.online_status or not previous_status:
            self.last_online = now
            self.save(update_fields=['online_status', 'last_online', 'last_session_start', 'total_time_online'])
            logger.debug(f"[MODEL] Статус пользователя {self.user.username} сохранен: online={self.online_status}, last_online={self.last_online}")
        else:
            # Для оптимизации производительности при регулярных обновлениях
            # сохраняем только статус онлайн (без обновления last_online)
            self.save(update_fields=['online_status'])
            logger.debug(f"[MODEL] Обновлен только статус online для пользователя {self.user.username}")
    
    def update_login_stats(self, ip_address=None):
        """Обновляет статистику входов пользователя"""
        logger.info(f"[MODEL] Обновление статистики входа для пользователя {self.user.username} (ID: {self.user.id}), IP: {ip_address}")
        self.total_logins += 1
        self.last_login_ip = ip_address
        self.save()
        logger.debug(f"[MODEL] Статистика входа обновлена для {self.user.username}: всего входов = {self.total_logins}")
    
    def reset_failed_login_attempts(self):
        """Сбрасывает счетчик неудачных попыток входа"""
        logger.info(f"[MODEL] Сброс счетчика неудачных попыток входа для пользователя {self.user.username} (ID: {self.user.id})")
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()
    
    def increment_failed_login(self):
        """Увеличивает счетчик неудачных попыток входа"""
        logger.info(f"[MODEL] Увеличение счетчика неудачных попыток входа для пользователя {self.user.username} (ID: {self.user.id})")
        self.failed_login_attempts += 1
        
        # Если превышено максимальное количество попыток - блокируем аккаунт на время
        if self.failed_login_attempts >= 5:
            lock_until = timezone.now() + timezone.timedelta(minutes=30)
            logger.warning(f"[MODEL] Аккаунт пользователя {self.user.username} (ID: {self.user.id}) заблокирован до {lock_until}")
            self.account_locked_until = lock_until
        
        self.save()
        logger.debug(f"[MODEL] Счетчик неудачных попыток обновлен: {self.failed_login_attempts}")
    
    def is_account_locked(self):
        """Проверяет, заблокирован ли аккаунт"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            logger.info(f"[MODEL] Аккаунт пользователя {self.user.username} (ID: {self.user.id}) заблокирован до {self.account_locked_until}")
            return True
        elif self.account_locked_until:
            # Если время блокировки истекло, сбрасываем блокировку
            logger.info(f"[MODEL] Блокировка аккаунта для пользователя {self.user.username} (ID: {self.user.id}) снята (истек срок)")
            self.account_locked_until = None
            self.save()
        return False

    def __str__(self):
        """Строковое представление объекта"""
        return self.user.username

    # Метод для получения профиля с исправленной датой
    @classmethod
    def get_profile_with_corrected_date(cls, user):
        """Получает профиль пользователя и исправляет дату, если она в будущем"""
        logger.debug(f"[MODEL] Получение профиля с проверкой даты для пользователя {user.username} (ID: {user.id})")
        profile, created = cls.objects.get_or_create(user=user)
        
        if created:
            logger.info(f"[MODEL] Создан новый профиль для пользователя {user.username} (ID: {user.id})")
            
        now = timezone.now()
        
        # Проверяем, не в будущем ли дата
        if profile.last_online > now:
            logger.warning(f"[MODEL] Исправлена дата last_online из будущего для пользователя {user.username} (ID: {user.id})")
            profile.last_online = now
            profile.save(update_fields=['last_online'])
            
        return profile


class Review(models.Model):
    """Модель отзывов на предложения"""
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)  # Связь с предложением
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)  # Автор отзыва
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])  # Рейтинг от 1 до 5
    comment = models.TextField(blank=True)  # Текстовый комментарий
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания отзыва

    def __str__(self):
        """Строковое представление объекта"""
        return f"Review by {self.reviewer.username} for {self.offer.item_name}"


class Conversation(models.Model):
    """Модель беседы между двумя пользователями"""
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_conversations')  # Инициатор беседы
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_conversations')  # Получатель сообщений
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания беседы
    updated_at = models.DateTimeField(auto_now=True)  # Дата последнего обновления
    
    class Meta:
        """Метаданные модели"""
        unique_together = ('initiator', 'receiver')  # Уникальная комбинация участников
        ordering = ['-updated_at']  # Сортировка по дате обновления (новые сверху)
    
    def __str__(self):
        """Строковое представление объекта"""
        return f"Беседа между {self.initiator.username} и {self.receiver.username}"
    
    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения с логированием"""
        is_new = self.pk is None
        if is_new:
            logger.info(f"[MODEL:CONVERSATION] Создание новой беседы между {self.initiator.username} и {self.receiver.username}")
        else:
            logger.debug(f"[MODEL:CONVERSATION] Обновление беседы ID: {self.id} между {self.initiator.username} и {self.receiver.username}")
            
        super().save(*args, **kwargs)
        
        if is_new:
            logger.info(f"[MODEL:CONVERSATION] Создана новая беседа ID: {self.id}")
    
    @staticmethod
    def get_or_create_conversation(user1, user2):
        """
        Получает существующую беседу между двумя пользователями или создает новую.
        Возвращает объект беседы.
        """
        logger.debug(f"[MODEL:CONVERSATION] Запрос на получение/создание беседы между {user1.username} и {user2.username}")
        
        # Проверяем, существует ли уже беседа между этими пользователями
        conversation = Conversation.objects.filter(
            (Q(initiator=user1) & Q(receiver=user2)) |
            (Q(initiator=user2) & Q(receiver=user1))
        ).first()
        
        if conversation:
            logger.debug(f"[MODEL:CONVERSATION] Найдена существующая беседа ID: {conversation.id} между {user1.username} и {user2.username}")
            return conversation
        
        # Если беседы нет, создаем новую
        conversation = Conversation.objects.create(
            initiator=user1,
            receiver=user2
        )
        
        logger.info(f"[MODEL:CONVERSATION] Создана новая беседа ID: {conversation.id} между {user1.username} и {user2.username}")
        return conversation
    
    def get_last_message(self):
        """
        Получает последнее сообщение в беседе.
        Возвращает объект Message или None, если сообщений нет.
        """
        logger.debug(f"[MODEL:CONVERSATION] Запрос последнего сообщения для беседы ID: {self.id}")
        
        last_message = self.messages.order_by('-created_at').first()
        
        if last_message:
            logger.debug(f"[MODEL:CONVERSATION] Найдено последнее сообщение ID: {last_message.id} в беседе ID: {self.id}")
        else:
            logger.debug(f"[MODEL:CONVERSATION] В беседе ID: {self.id} нет сообщений")
            
        return last_message
    
    def get_unread_count(self, user):
        """
        Получает количество непрочитанных сообщений для указанного пользователя.
        Возвращает целое число.
        """
        logger.debug(f"[MODEL:CONVERSATION] Запрос количества непрочитанных сообщений для пользователя {user.username} в беседе ID: {self.id}")
        
        # Определяем другого участника беседы
        other_user = self.receiver if self.initiator == user else self.initiator
        
        # Считаем непрочитанные сообщения от другого участника
        unread_count = self.messages.filter(sender=other_user, is_read=False).count()
        
        logger.debug(f"[MODEL:CONVERSATION] В беседе ID: {self.id} найдено {unread_count} непрочитанных сообщений для пользователя {user.username}")
        return unread_count
    
    def mark_all_messages_as_read(self, user):
        """
        Отмечает все сообщения в беседе как прочитанные для указанного пользователя.
        Возвращает количество отмеченных сообщений.
        """
        logger.debug(f"[MODEL:CONVERSATION] Запрос на отметку всех сообщений как прочитанных для пользователя {user.username} в беседе ID: {self.id}")
        
        # Определяем другого участника беседы
        other_user = self.receiver if self.initiator == user else self.initiator
        
        # Отмечаем сообщения от другого участника как прочитанные
        unread_messages = self.messages.filter(sender=other_user, is_read=False)
        count = unread_messages.count()
        
        if count > 0:
            unread_messages.update(is_read=True)
            logger.info(f"[MODEL:CONVERSATION] Отмечено {count} сообщений как прочитанных для пользователя {user.username} в беседе ID: {self.id}")
        else:
            logger.debug(f"[MODEL:CONVERSATION] Нет непрочитанных сообщений для отметки в беседе ID: {self.id}")
            
        return count


class Message(models.Model):
    """Модель для сообщений чата между пользователями"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')  # Отправитель
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)  # Получатель
    conversation = models.ForeignKey('Conversation', on_delete=models.CASCADE, related_name='messages', null=True, blank=True)  # Связь с беседой
    content = models.TextField(blank=True, null=True)  # Текст сообщения
    is_read = models.BooleanField(default=False)  # Прочитано ли сообщение
    created_at = models.DateTimeField(default=timezone.now)  # Дата отправки
    is_deleted = models.BooleanField(default=False)  # Удалено ли сообщение
    
    # Сохраняем старые поля для обратной совместимости с миграцией
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Устаревшее поле времени
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)  # Прикрепленный файл
    voice = models.FileField(upload_to='voice_messages/', blank=True, null=True)  # Голосовое сообщение
    voice_duration = models.IntegerField(blank=True, null=True)  # Длительность голосового сообщения в секундах
    
    class Meta:
        """Метаданные модели"""
        ordering = ['-created_at']  # Сортировка по дате создания (новые сверху)
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
    
    def __str__(self):
        """Строковое представление объекта"""
        if self.recipient:
            return f"От {self.sender} к {self.recipient}: {self.content[:30] if self.content else 'Нет содержания'}"
        elif self.conversation:
            return f"От {self.sender} в {self.conversation}: {self.content[:30] if self.content else 'Нет содержания'}"
        return f"Сообщение от {self.sender.username}"
    
    def mark_as_read(self):
        """Отмечает сообщение как прочитанное"""
        if not self.is_read:
            logger.info(f"[MODEL:MESSAGE] Отметка сообщения ID: {self.id} как прочитанного. Отправитель: {self.sender.username}, Получатель: {self.recipient.username if self.recipient else 'Нет'}")
            old_status = self.is_read
            self.is_read = True
            self.save(update_fields=['is_read'])
            logger.debug(f"[MODEL:MESSAGE] Сообщение ID: {self.id} статус прочтения изменен: {old_status} -> {self.is_read}")
            return True
        logger.debug(f"[MODEL:MESSAGE] Сообщение ID: {self.id} уже отмечено как прочитанное")
        return False
    
    def soft_delete(self):
        """Мягкое удаление сообщения (помечает как удаленное)"""
        logger.info(f"[MODEL:MESSAGE] Мягкое удаление сообщения ID: {self.id} от пользователя {self.sender.username}")
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])
        logger.debug(f"[MODEL:MESSAGE] Сообщение ID: {self.id} помечено как удаленное")
        return True
    
    def has_attachments(self):
        """Проверяет, есть ли у сообщения вложения"""
        has_file = bool(self.file)
        has_voice = bool(self.voice)
        has_images = self.images.exists()
        
        logger.debug(f"[MODEL:MESSAGE] Проверка вложений сообщения ID: {self.id}: файл={has_file}, голос={has_voice}, изображения={has_images}")
        return has_file or has_voice or has_images
    
    def save(self, *args, **kwargs):
        """Переопределенный метод сохранения с логированием"""
        is_new = self.pk is None
        
        if is_new:
            recipient_info = f"к {self.recipient.username}" if self.recipient else f"в беседу {self.conversation.id}" if self.conversation else "без получателя"
            logger.info(f"[MODEL:MESSAGE] Создание нового сообщения от {self.sender.username} {recipient_info}")
            
            # Логируем содержимое и вложения
            log_content = f"Содержание: {self.content[:50]}{'...' if len(self.content or '') > 50 else ''}"
            log_attachments = []
            if self.file:
                log_attachments.append(f"файл: {self.file.name}")
            if self.voice:
                log_attachments.append(f"голос: {self.voice.name} ({self.voice_duration or 0}с)")
                
            if log_attachments:
                log_content += f", вложения: {', '.join(log_attachments)}"
                
            logger.debug(f"[MODEL:MESSAGE] {log_content}")
        else:
            # Для обновления сообщаем только об изменении конкретных полей
            update_fields = kwargs.get('update_fields', [])
            if update_fields:
                logger.debug(f"[MODEL:MESSAGE] Обновление сообщения ID: {self.id}, поля: {update_fields}")
            else:
                logger.debug(f"[MODEL:MESSAGE] Обновление сообщения ID: {self.id}")
            
        super().save(*args, **kwargs)
        
        if is_new:
            logger.info(f"[MODEL:MESSAGE] Создано новое сообщение ID: {self.id}")


class MessageImage(models.Model):
    """Модель изображения в сообщении"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='images')  # Связь с сообщением
    image = models.ImageField(upload_to='chat_images/')  # Изображение
    created_at = models.DateTimeField(default=timezone.now)  # Дата создания
    
    def __str__(self):
        """Строковое представление объекта"""
        return f"Изображение для сообщения {self.message.id}"


class MessageReaction(models.Model):
    """Модель реакции на сообщение (эмодзи)"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')  # Связь с сообщением
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Пользователь, оставивший реакцию
    emoji = models.CharField(max_length=10)  # Эмодзи в Unicode
    created_at = models.DateTimeField(default=timezone.now)  # Дата создания
    
    class Meta:
        """Метаданные модели"""
        unique_together = ('message', 'user', 'emoji')  # Уникальное сочетание сообщения, пользователя и эмодзи
    
    def __str__(self):
        """Строковое представление объекта"""
        return f"Реакция {self.emoji} от {self.user.username}"


class UserActivity(models.Model):
    """Модель для хранения активности пользователя"""
    ACTIVITY_TYPES = [
        ('login', 'Вход в систему'),
        ('offer_create', 'Создание предложения'),
        ('offer_update', 'Обновление предложения'),
        ('offer_delete', 'Удаление предложения'),
        ('review', 'Оставлен отзыв'),
        ('deal', 'Завершена сделка'),
        ('profile_update', 'Обновление профиля'),
        ('message', 'Отправлено сообщение'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')  # Пользователь
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)  # Тип активности
    timestamp = models.DateTimeField(auto_now_add=True)  # Время активности
    details = models.JSONField(blank=True, null=True)  # Дополнительные данные в JSON
    related_object_id = models.PositiveIntegerField(blank=True, null=True)  # ID связанного объекта
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # Тип связанного объекта
    
    class Meta:
        """Метаданные модели"""
        ordering = ['-timestamp']  # Сортировка по времени (новые сверху)
        verbose_name = 'Активность пользователя'
        verbose_name_plural = 'Активности пользователей'
    
    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.get_activity_type_display()} - {self.user.username} ({self.timestamp.strftime('%d.%m.%Y %H:%M')})"


# Модели для фильтров
class FilterGroup(models.Model):
    """Группа фильтров (например, Тип, Раритетность, Качество)"""
    category = models.ForeignKey(GameCategory, on_delete=models.CASCADE, related_name='filter_groups')  # Связь с категорией
    name = models.CharField(max_length=100)  # Техническое название
    display_name = models.CharField(max_length=100)  # Отображаемое название
    order = models.PositiveSmallIntegerField(default=0)  # Порядок отображения
    filter_type = models.CharField(max_length=20, choices=[
        ('select', 'Выпадающий список'),
        ('checkbox', 'Флажки'),
        ('radio', 'Переключатели'),
        ('range', 'Диапазон'),
    ], default='select')  # Тип элемента фильтрации
    is_active = models.BooleanField(default=True)  # Активен ли фильтр
    
    class Meta:
        """Метаданные модели"""
        ordering = ['category', 'order']  # Сортировка
        verbose_name = 'Группа фильтров'
        verbose_name_plural = 'Группы фильтров'
        
    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.category.name} - {self.display_name}"


class FilterOption(models.Model):
    """Опция фильтра (например, 'Ножи', 'Перчатки' для фильтра Тип)"""
    filter_group = models.ForeignKey(FilterGroup, on_delete=models.CASCADE, related_name='options')  # Связь с группой фильтров
    name = models.CharField(max_length=100)  # Техническое название
    display_name = models.CharField(max_length=100)  # Отображаемое название
    order = models.PositiveSmallIntegerField(default=0)  # Порядок отображения
    is_active = models.BooleanField(default=True)  # Активна ли опция
    
    class Meta:
        """Метаданные модели"""
        ordering = ['filter_group', 'order']  # Сортировка
        verbose_name = 'Опция фильтра'
        verbose_name_plural = 'Опции фильтров'
        
    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.filter_group.display_name} - {self.display_name}"


class FilterValue(models.Model):
    """Значение фильтра для конкретного предложения"""
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='filter_values')  # Связь с предложением
    filter_option = models.ForeignKey(FilterOption, on_delete=models.CASCADE)  # Связь с опцией фильтра
    value = models.CharField(max_length=255, blank=True)  # Значение фильтра
    
    class Meta:
        """Метаданные модели"""
        unique_together = ['offer', 'filter_option']  # Уникальное сочетание предложения и опции
        verbose_name = 'Значение фильтра'
        verbose_name_plural = 'Значения фильтров'
        
    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.offer.item_name} - {self.filter_option.display_name}: {self.value}"


class OfferImage(models.Model):
    """Модель для хранения изображений объявлений"""
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='images')  # Связь с предложением
    image = models.ImageField(upload_to='offer_images/')  # Изображение
    order = models.PositiveSmallIntegerField(default=0)  # Порядок отображения
    created_at = models.DateTimeField(default=timezone.now)  # Дата создания
    
    class Meta:
        """Метаданные модели"""
        ordering = ['offer', 'order']  # Сортировка
        verbose_name = 'Изображение объявления'
        verbose_name_plural = 'Изображения объявлений'
        
    def __str__(self):
        """Строковое представление объекта"""
        return f"Изображение {self.order} для {self.offer.item_name}"


class Notification(models.Model):
    """Модель для хранения уведомлений пользователей"""
    
    TYPE_CHOICES = (
        ('offer_accepted', 'Предложение принято'),
        ('payment', 'Оплата'),
        ('message', 'Сообщение'),
        ('bonus', 'Бонус'),
        ('system', 'Системное'),
    )
    
    ICON_CLASSES = {
        'offer_accepted': 'bg-primary fas fa-tags',
        'payment': 'bg-success fas fa-coins',
        'message': 'bg-warning fas fa-comments',
        'bonus': 'bg-info fas fa-gift',
        'system': 'bg-secondary fas fa-bell',
    }
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')  # Получатель уведомления
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)  # Тип уведомления
    title = models.CharField(max_length=255)  # Заголовок уведомления
    content = models.TextField(blank=True, null=True)  # Содержание уведомления
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    is_read = models.BooleanField(default=False)  # Прочитано ли уведомление
    related_object_id = models.IntegerField(blank=True, null=True)  # ID связанного объекта
    related_object_type = models.CharField(max_length=50, blank=True, null=True)  # Тип связанного объекта
    link = models.CharField(max_length=255, blank=True, null=True)  # Ссылка для перехода
    
    class Meta:
        """Метаданные модели"""
        ordering = ['-created_at']  # Сортировка по дате создания (новые сверху)
        
    def __str__(self):
        """Строковое представление объекта"""
        return f"{self.notification_type}: {self.title} ({self.user.username})"
    
    def get_icon_class(self):
        """Возвращает класс иконки для уведомления"""
        return self.ICON_CLASSES.get(self.notification_type, 'bg-secondary fas fa-bell')
        
    def mark_as_read(self):
        """Отмечает уведомление как прочитанное"""
        self.is_read = True
        self.save(update_fields=['is_read'])
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Отмечает все уведомления пользователя как прочитанные"""
        cls.objects.filter(user=user, is_read=False).update(is_read=True)
    
    @staticmethod
    def create_notification(user, notification_type, title, content=None, related_object_id=None, 
                           related_object_type=None, link=None):
        """Создает новое уведомление"""
        return Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            content=content,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            link=link
        )