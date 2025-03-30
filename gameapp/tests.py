# Импорт необходимых модулей для тестирования
from django.test import TestCase, Client  # Базовый класс для тестов и HTTP-клиент
from django.urls import reverse  # Для получения URL по имени
from django.contrib.auth.models import User  # Модель пользователя Django
from decimal import Decimal  # Для точных денежных значений
from django.utils import timezone  # Для работы с датами и временем

# Импорт моделей приложения
from .models import (
    Game, Server, Offer, UserProfile, Review,
    Conversation, Message, GameCategory, GameSubcategory
)

# Импорт форм приложения
from .forms import OfferForm


# Тесты для моделей
class ModelTests(TestCase):
    """Тесты для проверки корректности работы моделей"""

    def setUp(self):
        """Настройка начальных данных для тестов"""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем профиль пользователя
        self.profile = UserProfile.objects.create(
            user=self.user,
            online_status=True,
            last_online=timezone.now()
        )
        
        # Создаем тестовую игру
        self.game = Game.objects.create(
            title='Test Game',
            description='Test Game Description'
        )
        
        # Создаем тестовый сервер
        self.server = Server.objects.create(
            game=self.game,
            name='Test Server',
            region='EU'
        )
        
        # Создаем тестовую категорию
        self.category = GameCategory.objects.create(
            name='Test Category',
            game=self.game
        )
        
        # Создаем тестовое предложение
        self.offer = Offer.objects.create(
            seller=self.user,
            game=self.game,
            server=self.server,
            item_name='Test Item',
            description='Test Item Description',
            price=Decimal('100.00'),
            amount=1,
            quality='common'
        )

    def test_game_creation(self):
        """Тест создания игры и корректности ее атрибутов"""
        self.assertEqual(self.game.title, 'Test Game')
        self.assertEqual(self.game.description, 'Test Game Description')
        self.assertTrue(self.game.slug)  # Проверка, что slug создан
        
    def test_server_creation(self):
        """Тест создания сервера и его связи с игрой"""
        self.assertEqual(self.server.name, 'Test Server')
        self.assertEqual(self.server.game, self.game)
        
    def test_offer_creation(self):
        """Тест создания предложения и его атрибутов"""
        self.assertEqual(self.offer.item_name, 'Test Item')
        self.assertEqual(self.offer.price, Decimal('100.00'))
        self.assertEqual(self.offer.seller, self.user)
        
    def test_user_profile(self):
        """Тест создания профиля пользователя и его атрибутов"""
        self.assertEqual(self.profile.user, self.user)
        self.assertTrue(self.profile.online_status)
        
    def test_review_creation(self):
        """Тест создания отзыва"""
        review = Review.objects.create(
            offer=self.offer,
            reviewer=self.user,
            rating=5,
            comment='Great item!'
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.offer, self.offer)


# Тесты для представлений (views)
class ViewTests(TestCase):
    """Тесты для проверки корректности работы представлений"""

    def setUp(self):
        """Настройка начальных данных для тестов"""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем профиль пользователя
        self.profile = UserProfile.objects.create(
            user=self.user,
            online_status=True,
            last_online=timezone.now()
        )
        
        # Создаем тестовую игру
        self.game = Game.objects.create(
            title='Test Game',
            description='Test Game Description'
        )
        
        # Создаем тестовый сервер
        self.server = Server.objects.create(
            game=self.game,
            name='Test Server',
            region='EU'
        )
        
        # Создаем тестовое предложение
        self.offer = Offer.objects.create(
            seller=self.user,
            game=self.game,
            server=self.server,
            item_name='Test Item',
            description='Test Item Description',
            price=Decimal('100.00'),
            amount=1,
            quality='common'
        )
        
        # Создаем клиент для запросов
        self.client = Client()

    def test_index_view(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gameapp/index.html')
        
    def test_game_detail_view(self):
        """Тест страницы детальной информации об игре"""
        response = self.client.get(reverse('game_detail', args=[self.game.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.game.title)
        
    def test_offer_detail_view(self):
        """Тест страницы детальной информации о предложении"""
        response = self.client.get(reverse('offer_detail', args=[self.offer.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.offer.item_name)
        
    def test_login_view(self):
        """Тест страницы входа"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        
    def test_login_functionality(self):
        """Тест функциональности входа"""
        login_successful = self.client.login(username='testuser', password='testpassword123')
        self.assertTrue(login_successful)


# Тесты для форм
class FormTests(TestCase):
    """Тесты для проверки корректности работы форм"""

    def setUp(self):
        """Настройка начальных данных для тестов"""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем тестовую игру
        self.game = Game.objects.create(
            title='Test Game',
            description='Test Game Description'
        )
        
        # Создаем тестовый сервер
        self.server = Server.objects.create(
            game=self.game,
            name='Test Server',
            region='EU'
        )
        
        # Создаем тестовую категорию
        self.category = GameCategory.objects.create(
            name='Test Category',
            game=self.game
        )

    def test_offer_form_valid(self):
        """Тест валидации формы предложения с корректными данными"""
        form_data = {
            'game': self.game.id,
            'server': self.server.id,
            'category': self.category.id,
            'item_name': 'Test Item',
            'description': 'Test Description',
            'price': '100.00',
            'amount': 1,
            'quality': 'common'
        }
        form = OfferForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_offer_form_invalid(self):
        """Тест отклонения формы предложения с некорректными данными"""
        # Пропускаем обязательные поля
        form_data = {
            'item_name': '',  # Пустое имя предмета
            'price': 'not_a_price',  # Некорректная цена
        }
        form = OfferForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('item_name', form.errors)
        self.assertIn('price', form.errors)


# Тесты для API (если есть)
class APITests(TestCase):
    """Тесты для проверки корректности работы API-эндпоинтов"""

    def setUp(self):
        """Настройка начальных данных для тестов API"""
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Создаем тестовую игру
        self.game = Game.objects.create(
            title='Test Game',
            description='Test Game Description'
        )
        
        # Создаем клиент для запросов
        self.client = Client()
        # Авторизуем пользователя
        self.client.login(username='testuser', password='testpassword123')

    def test_get_categories_api(self):
        """Тест API для получения категорий"""
        response = self.client.get(reverse('get_categories'), {'game_id': self.game.id})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
    def test_check_new_messages_api(self):
        """Тест API для проверки новых сообщений"""
        response = self.client.get(reverse('check_new_messages'))
        self.assertEqual(response.status_code, 200)


# Запуск тестов
if __name__ == "__main__":
    import unittest
    unittest.main() 