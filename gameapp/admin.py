from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
import csv
from datetime import datetime
import logging
from .models import (
    Game, Server, Offer, UserProfile, Review,
    Conversation, Message, MessageImage, MessageReaction,
    UserActivity, GameCategory, GameSubcategory,
    FilterGroup, FilterOption, FilterValue,
    Item, Notification
)

# Настройка логирования
logger = logging.getLogger('chat_logger')

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил игру: {obj.title}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал игру: {obj.title}")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил игру: {obj.title}")
        super().delete_model(request, obj)

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'region')
    list_filter = ('game', 'region')
    search_fields = ('name', 'game__title')
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил сервер: {obj.name} (игра: {obj.game.title})")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал сервер: {obj.name} (игра: {obj.game.title})")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил сервер: {obj.name} (игра: {obj.game.title})")
        super().delete_model(request, obj)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_online', 'online_status')
    readonly_fields = ('last_online', 'online_status', 'last_session_start', 'total_time_online')
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'bio', 'avatar')
        }),
        ('Статус онлайн', {
            'fields': ('last_online', 'online_status', 'last_session_start', 'total_time_online')
        }),
        ('Безопасность', {
            'fields': ('failed_login_attempts', 'account_locked_until', 'total_logins')
        }),
    )
    
    actions = ['reset_failed_login_attempts', 'unlock_accounts', 'export_profiles_csv']
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил профиль пользователя {obj.user.username}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал профиль пользователя {obj.user.username}")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил профиль пользователя {obj.user.username}")
        super().delete_model(request, obj)
    
    def reset_failed_login_attempts(self, request, queryset):
        """Сброс счетчика неудачных попыток входа"""
        count = queryset.count()
        usernames = list(queryset.values_list('user__username', flat=True))
        
        for profile in queryset:
            profile.failed_login_attempts = 0
            profile.account_locked_until = None
            profile.save()
        
        logger.info(f"[ADMIN] Администратор {request.user.username} сбросил счетчик неудачных попыток входа для {count} профилей: {', '.join(usernames)}")
        self.message_user(request, f"Сброшены счетчики неудачных попыток входа для {count} пользователей.")
    
    reset_failed_login_attempts.short_description = "Сбросить счетчик неудачных попыток входа"
    
    def unlock_accounts(self, request, queryset):
        """Разблокировка заблокированных аккаунтов"""
        locked_accounts = queryset.filter(account_locked_until__gt=timezone.now())
        count = locked_accounts.count()
        usernames = list(locked_accounts.values_list('user__username', flat=True))
        
        for profile in locked_accounts:
            profile.account_locked_until = None
            profile.save()
        
        logger.info(f"[ADMIN] Администратор {request.user.username} разблокировал {count} аккаунтов: {', '.join(usernames)}")
        self.message_user(request, f"Разблокировано {count} аккаунтов.")
    
    unlock_accounts.short_description = "Разблокировать аккаунты"
    
    def export_profiles_csv(self, request, queryset):
        """Экспорт профилей в CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=user_profiles_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Online Status', 'Last Online', 'Total Logins', 'Failed Login Attempts'])
        
        for profile in queryset:
            writer.writerow([
                profile.user.username,
                profile.user.email,
                profile.online_status,
                profile.last_online,
                profile.total_logins,
                profile.failed_login_attempts
            ])
        
        logger.info(f"[ADMIN] Администратор {request.user.username} экспортировал {queryset.count()} профилей в CSV")
        return response
    
    export_profiles_csv.short_description = "Экспорт выбранных профилей в CSV"

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'seller', 'game', 'server', 'price', 'created_at')
    list_filter = ('game', 'server')
    search_fields = ('item_name', 'description', 'seller__username')
    date_hierarchy = 'created_at'
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил предложение: {obj.item_name} (продавец: {obj.seller.username})")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал предложение: {obj.item_name}")
            if not obj.seller:
                obj.seller = request.user
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил предложение: {obj.item_name} (продавец: {obj.seller.username})")
        super().delete_model(request, obj)
    
    actions = ['activate_offers', 'deactivate_offers']
    
    def activate_offers(self, request, queryset):
        """Активация предложений"""
        count = queryset.update(is_active=True)
        logger.info(f"[ADMIN] Администратор {request.user.username} активировал {count} предложений")
        self.message_user(request, f"Активировано {count} предложений.")
    
    activate_offers.short_description = "Активировать выбранные предложения"
    
    def deactivate_offers(self, request, queryset):
        """Деактивация предложений"""
        count = queryset.update(is_active=False)
        logger.info(f"[ADMIN] Администратор {request.user.username} деактивировал {count} предложений")
        self.message_user(request, f"Деактивировано {count} предложений.")
    
    deactivate_offers.short_description = "Деактивировать выбранные предложения"

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('reviewer', 'offer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer__username', 'offer__item_name', 'comment')
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил отзыв от {obj.reviewer.username} о {obj.offer.item_name}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал отзыв от {obj.reviewer.username} о {obj.offer.item_name}")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил отзыв от {obj.reviewer.username} о {obj.offer.item_name}")
        super().delete_model(request, obj)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username', 'recipient__username')
    readonly_fields = ('sender', 'recipient', 'created_at')
    
    def get_content_preview(self, obj):
        """Получение превью содержимого сообщения"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    
    get_content_preview.short_description = "Содержимое"
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} изменил сообщение ID: {obj.id}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал новое сообщение")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил сообщение ID: {obj.id} от {obj.sender.username}")
        super().delete_model(request, obj)
    
    def has_add_permission(self, request):
        """Запрет на создание сообщений через админку"""
        return False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('initiator', 'receiver', 'created_at')
    search_fields = ('initiator__username', 'receiver__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил диалог ID: {obj.id} между {obj.initiator.username} и {obj.receiver.username}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал диалог между {obj.initiator.username} и {obj.receiver.username}")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил диалог ID: {obj.id} между {obj.initiator.username} и {obj.receiver.username}")
        super().delete_model(request, obj)

@admin.register(MessageImage)
class MessageImageAdmin(admin.ModelAdmin):
    list_display = ('message', 'image', 'created_at')
    list_filter = ('created_at',)
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил изображение сообщения ID: {obj.id}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} добавил изображение к сообщению")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил изображение сообщения ID: {obj.id}")
        super().delete_model(request, obj)

@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'emoji', 'created_at')
    list_filter = ('emoji', 'created_at')
    search_fields = ('user__username',)
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил реакцию ID: {obj.id}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал реакцию")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил реакцию ID: {obj.id}")
        super().delete_model(request, obj)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'details')
    readonly_fields = ('user', 'activity_type', 'timestamp', 'details')
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил запись активности пользователя {obj.user.username} (ID: {obj.id})")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал запись активности пользователя {obj.user.username}")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил запись активности пользователя {obj.user.username} (ID: {obj.id})")
        super().delete_model(request, obj)
    
    def has_add_permission(self, request):
        """Запрет на создание записей активности через админку"""
        return False

@admin.register(GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил категорию игры: {obj.name}")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал категорию игры: {obj.name}")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил категорию игры: {obj.name}")
        super().delete_model(request, obj)

@admin.register(GameSubcategory)
class GameSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    
    def save_model(self, request, obj, form, change):
        """Логируем сохранение модели в админке"""
        if change:
            logger.info(f"[ADMIN] Администратор {request.user.username} обновил подкатегорию игры: {obj.name} (категория: {obj.category.name})")
        else:
            logger.info(f"[ADMIN] Администратор {request.user.username} создал подкатегорию игры: {obj.name} (категория: {obj.category.name})")
        
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Логируем удаление модели в админке"""
        logger.warning(f"[ADMIN] Администратор {request.user.username} удалил подкатегорию игры: {obj.name} (категория: {obj.category.name})")
        super().delete_model(request, obj)

# Регистрация моделей фильтров
admin.site.register(FilterGroup)
admin.site.register(FilterOption)
admin.site.register(FilterValue)