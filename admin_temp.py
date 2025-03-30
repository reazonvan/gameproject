# Импорт модуля администратора Django
from django.contrib import admin
# Импорт моделей приложения, которые будут зарегистрированы в административной панели
from .models import (
    Game, Server, Offer, UserProfile, Review,
    Conversation, Message, MessageImage, MessageReaction,
    UserActivity, GameCategory, GameSubcategory,
    FilterGroup, FilterOption, FilterValue
)

# Регистрация модели Game с настройками отображения
@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')  # Поля, отображаемые в списке игр
    search_fields = ('title',)  # Поля для поиска

# Регистрация модели Server с настройками отображения
@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'region')  # Поля, отображаемые в списке серверов
    list_filter = ('game', 'region')  # Фильтры для списка
    search_fields = ('name', 'game__title')  # Поля для поиска, включая связанную модель Game

# Регистрация модели UserProfile с настройками отображения
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # Поля, отображаемые в списке профилей
    list_display = ('user', 'phone_number', 'online_status', 'last_online', 'total_logins', 'offers_count', 'deals_count', 'rating')
    search_fields = ('user__username', 'phone_number', 'location')  # Поля для поиска
    list_filter = ('online_status',)  # Фильтр по статусу онлайн
    # Группировка полей в разделы для удобного редактирования
    fieldsets = (
        ('Основная информация', {  # Раздел основной информации
            'fields': ('user', 'avatar', 'phone_number', 'bio', 'location')
        }),
        ('Статус', {  # Раздел статуса пользователя
            'fields': ('online_status', 'last_online', 'last_session_start')
        }),
        ('Статистика', {  # Раздел статистики пользователя
            'fields': ('registration_ip', 'last_login_ip', 'total_logins', 'total_time_online',
                      'offers_count', 'deals_count', 'rating')
        }),
        ('Безопасность', {  # Раздел безопасности
            'fields': ('failed_login_attempts', 'account_locked_until')
        }),
    )

# Регистрация модели Offer с настройками отображения
@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    # Поля, отображаемые в списке предложений
    list_display = ('item_name', 'game', 'server', 'seller', 'price', 'quality', 'created_at')
    list_filter = ('game', 'server', 'quality', 'is_tradable')  # Фильтры для списка
    search_fields = ('item_name', 'description', 'seller__username')  # Поля для поиска
    date_hierarchy = 'created_at'  # Иерархия дат для навигации по датам создания

# Регистрация модели Review с настройками отображения
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('offer', 'reviewer', 'rating', 'created_at')  # Поля, отображаемые в списке отзывов
    list_filter = ('rating',)  # Фильтр по рейтингу
    search_fields = ('comment', 'reviewer__username', 'offer__item_name')  # Поля для поиска

# Регистрация модели Conversation с настройками отображения
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'initiator', 'receiver', 'created_at', 'updated_at')  # Поля, отображаемые в списке бесед
    search_fields = ('initiator__username', 'receiver__username')  # Поля для поиска
    date_hierarchy = 'created_at'  # Иерархия дат для навигации

# Регистрация модели Message с настройками отображения
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'short_content', 'created_at', 'is_read']  # Поля, отображаемые в списке сообщений
    list_filter = ['is_read', 'created_at']  # Фильтры для списка
    search_fields = ['sender__username', 'recipient__username', 'content']  # Поля для поиска
    date_hierarchy = 'created_at'  # Иерархия дат для навигации
    
    # Метод для отображения укороченного содержания сообщения
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Содержание'  # Подпись для столбца

# Регистрация модели MessageImage с настройками отображения
@admin.register(MessageImage)
class MessageImageAdmin(admin.ModelAdmin):
    list_display = ('message', 'created_at')  # Поля, отображаемые в списке изображений сообщений
    date_hierarchy = 'created_at'  # Иерархия дат для навигации

# Регистрация модели MessageReaction с настройками отображения
@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'emoji', 'created_at')  # Поля, отображаемые в списке реакций
    list_filter = ('emoji',)  # Фильтр по эмодзи
    search_fields = ('user__username',)  # Поля для поиска

# Определение класса администратора для модели GameCategory
class GameCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'slug', 'order', 'is_active', 'created_at')  # Поля, отображаемые в списке категорий
    list_filter = ('game', 'is_active')  # Фильтры для списка
    search_fields = ('name', 'description')  # Поля для поиска
    prepopulated_fields = {'slug': ('name',)}  # Автоматическое заполнение slug из name
    ordering = ('game', 'order', 'name')  # Порядок сортировки
    
# Определение класса администратора для модели GameSubcategory
class GameSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'order', 'is_active', 'created_at')  # Поля, отображаемые в списке подкатегорий
    list_filter = ('category', 'category__game', 'is_active')  # Фильтры для списка, включая вложенные связи
    search_fields = ('name', 'description')  # Поля для поиска
    prepopulated_fields = {'slug': ('name',)}  # Автоматическое заполнение slug из name
    ordering = ('category', 'order', 'name')  # Порядок сортировки

# Простая регистрация модели UserActivity без дополнительных настроек
admin.site.register(UserActivity)
# Регистрация модели GameCategory с использованием класса GameCategoryAdmin
admin.site.register(GameCategory, GameCategoryAdmin)
# Регистрация модели GameSubcategory с использованием класса GameSubcategoryAdmin
admin.site.register(GameSubcategory, GameSubcategoryAdmin)

# Определение встроенного класса для отображения опций фильтра внутри группы фильтров
class FilterOptionInline(admin.TabularInline):
    model = FilterOption  # Используемая модель
    extra = 1  # Количество дополнительных пустых форм

# Определение класса администратора для модели FilterGroup
class FilterGroupAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'category', 'filter_type', 'order', 'is_active')  # Поля, отображаемые в списке групп фильтров
    list_filter = ('category', 'filter_type', 'is_active')  # Фильтры для списка
    search_fields = ('name', 'display_name')  # Поля для поиска
    inlines = [FilterOptionInline]  # Встроенные модели (опции фильтра внутри группы)
    
# Определение класса администратора для модели FilterOption
class FilterOptionAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'filter_group', 'order', 'is_active')  # Поля, отображаемые в списке опций фильтров
    list_filter = ('filter_group', 'is_active')  # Фильтры для списка
    search_fields = ('name', 'display_name')  # Поля для поиска
    
# Определение класса администратора для модели FilterValue
class FilterValueAdmin(admin.ModelAdmin):
    list_display = ('offer', 'filter_option', 'value')  # Поля, отображаемые в списке значений фильтров
    list_filter = ('filter_option__filter_group', 'filter_option')  # Фильтры для списка, включая вложенные связи
    search_fields = ('offer__item_name', 'value')  # Поля для поиска

# Регистрация модели FilterGroup с использованием класса FilterGroupAdmin
admin.site.register(FilterGroup, FilterGroupAdmin)
# Регистрация модели FilterOption с использованием класса FilterOptionAdmin
admin.site.register(FilterOption, FilterOptionAdmin)
# Регистрация модели FilterValue с использованием класса FilterValueAdmin
admin.site.register(FilterValue, FilterValueAdmin)
