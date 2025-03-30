from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import Game, GameCategory, Server, Offer, UserProfile, Item, FilterGroup, FilterOption, FilterValue
import logging

# Настройка логирования
logger = logging.getLogger('chat_logger')

class UserRegisterForm(UserCreationForm):
    """Форма для регистрации новых пользователей"""
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_username(self):
        """Проверка уникальности имени пользователя"""
        username = self.cleaned_data.get('username')
        logger.debug(f"[FORM] Проверка уникальности имени пользователя: {username}")
        
        if User.objects.filter(username=username).exists():
            logger.warning(f"[FORM] Попытка регистрации с существующим именем пользователя: {username}")
            raise forms.ValidationError("Пользователь с таким именем уже существует")
        
        return username
    
    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        logger.debug(f"[FORM] Проверка уникальности email: {email}")
        
        if User.objects.filter(email=email).exists():
            logger.warning(f"[FORM] Попытка регистрации с существующим email: {email}")
            raise forms.ValidationError("Пользователь с таким email уже существует")
        
        return email
    
    def save(self, commit=True):
        """Сохранение нового пользователя"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            logger.info(f"[FORM] Создание нового пользователя: {user.username}, email: {user.email}")
            user.save()
            
            # Профиль пользователя создается через сигнал
            logger.debug(f"[FORM] Пользователь успешно сохранен, профиль будет создан через сигнал")
        else:
            logger.debug(f"[FORM] Создание нового пользователя без сохранения: {user.username}")
            
        return user


class LoginForm(forms.Form):
    """Форма для входа пользователей"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        
        logger.debug(f"[FORM] Валидация формы входа для пользователя: {username}")
        
        # Дополнительная валидация может быть добавлена здесь
        return cleaned_data


class GameForm(forms.ModelForm):
    """Форма для создания и редактирования игр"""
    class Meta:
        model = Game
        fields = ['title', 'description', 'developer', 'publisher', 'image', 'release_date']
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        
        logger.debug(f"[FORM] Валидация формы игры: {title}")
        return cleaned_data
    
    def save(self, commit=True):
        """Сохранение игры"""
        game = super().save(commit=False)
        
        if commit:
            action = 'Обновление' if game.pk else 'Создание'
            logger.info(f"[FORM] {action} игры: {game.title}")
            game.save()
        
        return game


class GameCategoryForm(forms.ModelForm):
    """Форма для создания и редактирования категорий игр"""
    class Meta:
        model = GameCategory
        fields = ['name', 'description', 'icon', 'order', 'is_active', 'game']
    
    def clean_name(self):
        """Проверка уникальности имени категории"""
        name = self.cleaned_data.get('name')
        logger.debug(f"[FORM] Проверка уникальности имени категории: {name}")
        
        # Если это не редактирование существующей категории
        if self.instance.pk is None or self.instance.name != name:
            if GameCategory.objects.filter(name=name).exists():
                logger.warning(f"[FORM] Попытка создания категории с существующим именем: {name}")
                raise forms.ValidationError("Категория с таким именем уже существует")
        
        return name
    
    def save(self, commit=True):
        """Сохранение категории игры"""
        category = super().save(commit=False)
        
        if commit:
            action = 'Обновление' if category.pk else 'Создание'
            logger.info(f"[FORM] {action} категории игры: {category.name}")
            category.save()
        
        return category


class ServerForm(forms.ModelForm):
    """Форма для создания и редактирования серверов"""
    class Meta:
        model = Server
        fields = ['name', 'game', 'region']
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        game = cleaned_data.get('game')
        
        logger.debug(f"[FORM] Валидация формы сервера: {name} для игры {game}")
        
        # Проверка уникальности имени сервера для игры
        if name and game and (self.instance.pk is None or self.instance.name != name or self.instance.game != game):
            if Server.objects.filter(name=name, game=game).exists():
                logger.warning(f"[FORM] Попытка создания сервера с существующим именем для игры: {name} - {game}")
                raise forms.ValidationError("Сервер с таким именем уже существует для этой игры")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Сохранение сервера"""
        server = super().save(commit=False)
        
        if commit:
            action = 'Обновление' if server.pk else 'Создание'
            logger.info(f"[FORM] {action} сервера: {server.name} для игры {server.game}")
            server.save()
        
        return server


class OfferForm(forms.ModelForm):
    """
    Форма для создания и редактирования предложений (объявлений)
    с динамическими полями фильтрации для разных категорий
    """
    class Meta:
        """Метаданные формы"""
        model = Offer  # Модель, для которой создается форма
        fields = [
            'game', 'server', 'category', 'subcategory',
            'item_name', 'description', 'price', 'amount', 'quality'
        ]  # Поля, которые будут отображаться в форме
        
    def __init__(self, *args, **kwargs):
        """
        Инициализация формы с настройкой полей
        и добавлением динамических полей фильтрации
        """
        super().__init__(*args, **kwargs)
        
        # Добавляем placeholder'ы для текстовых полей
        self.fields['item_name'].widget.attrs.update({'placeholder': 'Название товара'})
        self.fields['description'].widget.attrs.update({'placeholder': 'Подробное описание товара', 'rows': 4})
        self.fields['price'].widget.attrs.update({'placeholder': 'Цена в рублях'})
        
        # Если есть категория, добавляем поля для фильтров
        if self.instance and self.instance.category_id:
            self.add_filter_fields()
    
    def add_filter_fields(self):
        """
        Динамически добавляет поля для фильтров категории
        в зависимости от типа фильтра (выпадающий список, флажки и т.д.)
        """
        # Получаем активные группы фильтров для категории объявления
        filter_groups = FilterGroup.objects.filter(
            category=self.instance.category,
            is_active=True
        ).prefetch_related('options')
        
        # Для каждой группы фильтров создаем соответствующее поле формы
        for group in filter_groups:
            field_name = f'filter_{group.id}'
            
            # Создаем поле в зависимости от типа фильтра
            if group.filter_type == 'select':
                # Выпадающий список
                choices = [('', f'Выберите {group.display_name.lower()}')]
                choices.extend([
                    (option.id, option.display_name) 
                    for option in group.options.filter(is_active=True)
                ])
                self.fields[field_name] = forms.ChoiceField(
                    label=group.display_name,
                    choices=choices,
                    required=False
                )
            elif group.filter_type == 'checkbox':
                # Множественный выбор с флажками
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=group.display_name,
                    choices=[
                        (option.id, option.display_name) 
                        for option in group.options.filter(is_active=True)
                    ],
                    widget=forms.CheckboxSelectMultiple,
                    required=False
                )
            elif group.filter_type == 'radio':
                # Переключатели (радиокнопки)
                self.fields[field_name] = forms.ChoiceField(
                    label=group.display_name,
                    choices=[
                        (option.id, option.display_name) 
                        for option in group.options.filter(is_active=True)
                    ],
                    widget=forms.RadioSelect,
                    required=False
                )
            elif group.filter_type == 'range':
                # Диапазон значений (два поля: min и max)
                self.fields[f'{field_name}_min'] = forms.DecimalField(
                    label=f'{group.display_name} (от)',
                    required=False
                )
                self.fields[f'{field_name}_max'] = forms.DecimalField(
                    label=f'{group.display_name} (до)',
                    required=False
                )
    
    def save(self, commit=True):
        """
        Сохраняет форму и связанные с ней значения фильтров
        
        Параметры:
            commit (bool): сохранять ли объект в базу данных
            
        Возвращает:
            объект модели Offer с сохраненными данными
        """
        # Сохраняем основной объект предложения
        offer = super().save(commit=False)
        
        if commit:
            offer.save()
            
            # Сохраняем значения фильтров, если категория существует
            if offer.category_id:
                # Удаляем старые значения фильтров
                FilterValue.objects.filter(offer=offer).delete()
                
                # Сохраняем новые значения фильтров
                filter_groups = FilterGroup.objects.filter(
                    category=offer.category,
                    is_active=True
                )
                
                # Обрабатываем каждую группу фильтров
                for group in filter_groups:
                    field_name = f'filter_{group.id}'
                    
                    # Для обычных полей (выпадающий список, переключатели)
                    if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                        if group.filter_type in ['select', 'radio']:
                            # Одиночный выбор
                            option_id = self.cleaned_data[field_name]
                            FilterValue.objects.create(
                                offer=offer,
                                filter_option_id=option_id
                            )
                        elif group.filter_type == 'checkbox':
                            # Множественный выбор
                            for option_id in self.cleaned_data[field_name]:
                                FilterValue.objects.create(
                                    offer=offer,
                                    filter_option_id=option_id
                                )
                    
                    # Для диапазонов (два отдельных поля)
                    if group.filter_type == 'range':
                        min_field = f'{field_name}_min'
                        max_field = f'{field_name}_max'
                        
                        # Сохранение минимального значения
                        if min_field in self.cleaned_data and self.cleaned_data[min_field] is not None:
                            # Находим первую опцию (обычно у диапазонов только одна опция)
                            option = FilterOption.objects.filter(filter_group=group).first()
                            if option:
                                FilterValue.objects.create(
                                    offer=offer,
                                    filter_option=option,
                                    value=f"min:{self.cleaned_data[min_field]}"
                                )
                        
                        # Сохранение максимального значения
                        if max_field in self.cleaned_data and self.cleaned_data[max_field] is not None:
                            # Находим первую опцию (обычно у диапазонов только одна опция)
                            option = FilterOption.objects.filter(filter_group=group).first()
                            if option:
                                FilterValue.objects.create(
                                    offer=offer,
                                    filter_option=option,
                                    value=f"max:{self.cleaned_data[max_field]}"
                                )
        
        return offer 


class ItemForm(forms.ModelForm):
    """Форма для создания и редактирования предметов"""
    class Meta:
        model = Item
        fields = ['name', 'description', 'game', 'quality', 'image']
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        game = cleaned_data.get('game')
        
        logger.debug(f"[FORM] Валидация формы предмета: {name} для игры {game}")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Сохранение предмета"""
        item = super().save(commit=False)
        
        if commit:
            action = 'Обновление' if item.pk else 'Создание'
            logger.info(f"[FORM] {action} предмета: {item.name} для игры {item.game}, качество: {item.quality}")
            item.save()
        
        return item


class UserProfileForm(forms.ModelForm):
    """Форма для редактирования профиля пользователя"""
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. От 9 до 15 цифр."
    )
    phone_number = forms.CharField(validators=[phone_regex], max_length=17, required=False)
    
    class Meta:
        model = UserProfile
        fields = ['avatar', 'phone_number', 'bio', 'location']
        
    def clean_phone_number(self):
        """Проверка номера телефона"""
        phone_number = self.cleaned_data.get('phone_number')
        
        if phone_number:
            logger.debug(f"[FORM] Проверка номера телефона: {phone_number}")
            # Можно добавить дополнительную проверку номера телефона
        
        return phone_number
    
    def save(self, commit=True):
        """Сохранение профиля пользователя"""
        profile = super().save(commit=False)
        
        if commit:
            logger.info(f"[FORM] Обновление профиля пользователя: {profile.user.username}")
            profile.save()
        
        return profile


class SearchForm(forms.Form):
    """Форма для поиска"""
    query = forms.CharField(max_length=100, required=False)
    category = forms.ModelChoiceField(queryset=GameCategory.objects.all(), required=False)
    game = forms.ModelChoiceField(queryset=Game.objects.all(), required=False)
    min_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    def clean(self):
        """Валидация формы"""
        cleaned_data = super().clean()
        query = cleaned_data.get('query')
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        
        logger.debug(f"[FORM] Поисковый запрос: '{query}', диапазон цен: {min_price} - {max_price}")
        
        # Проверка диапазона цен
        if min_price and max_price and min_price > max_price:
            logger.warning(f"[FORM] Некорректный диапазон цен: min={min_price}, max={max_price}")
            raise forms.ValidationError("Минимальная цена не может быть больше максимальной")
            
        return cleaned_data 