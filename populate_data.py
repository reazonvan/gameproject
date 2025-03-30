import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gameproject.settings')
django.setup()

from django.contrib.auth.models import User
from gameapp.models import Game, Server, Offer, UserProfile, Review
from django.utils import timezone
from decimal import Decimal
import random

# Функция для создания тестовых пользователей
def create_users():
    """
    Создает или получает тестовых пользователей.
    
    Returns:
        list: Список объектов User
    """
    users = []
    usernames = ['seller1', 'seller2', 'buyer1', 'buyer2', 'gamer1']
    
    # Проверяем существующих пользователей
    for username in usernames:
        # Получаем или создаем пользователя, используя метод get_or_create
        # чтобы избежать дублирования при повторном запуске скрипта
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'password': 'pbkdf2_sha256$1000000$password123'
            }
        )
        if created:
            # Для новых пользователей устанавливаем пароль и создаем профиль
            user.set_password('password123')
            user.save()
            UserProfile.objects.create(
                user=user,
                online_status=random.choice([True, False]),
                last_online=timezone.now()
            )
        users.append(user)
    
    return users

# Функция для создания тестовых игр
def create_games():
    """
    Создает или получает тестовые игры.
    
    Returns:
        list: Список объектов Game
    """
    games = []
    game_data = [
        {'title': 'World of Warcraft', 'description': 'MMORPG от Blizzard'},
        {'title': 'Counter-Strike 2', 'description': 'Популярный шутер от Valve'},
        {'title': 'Dota 2', 'description': 'MOBA игра от Valve'},
        {'title': 'Minecraft', 'description': 'Песочница для творчества'},
        {'title': 'Fortnite', 'description': 'Популярная королевская битва'},
    ]
    
    # Создаем игры из предопределенных данных
    for data in game_data:
        # Получаем или создаем игру, чтобы избежать дублирования
        game, created = Game.objects.get_or_create(
            title=data['title'],
            defaults={'description': data['description']}
        )
        games.append(game)
    
    return games

# Функция для создания тестовых серверов
def create_servers(games):
    """
    Создает или получает тестовые игровые серверы.
    
    Args:
        games (list): Список объектов Game
        
    Returns:
        list: Список объектов Server
    """
    servers = []
    server_data = [
        {'game_index': 0, 'name': 'Европа', 'region': 'EU'},
        {'game_index': 0, 'name': 'Америка', 'region': 'US'},
        {'game_index': 1, 'name': 'Global', 'region': 'Global'},
        {'game_index': 2, 'name': 'Европа', 'region': 'EU'},
        {'game_index': 2, 'name': 'Россия', 'region': 'RU'},
        {'game_index': 3, 'name': 'Основной', 'region': 'Global'},
        {'game_index': 4, 'name': 'Основной', 'region': 'Global'},
    ]
    
    # Создаем серверы из предопределенных данных
    for data in server_data:
        # Получаем или создаем сервер, связанный с соответствующей игрой
        server, created = Server.objects.get_or_create(
            game=games[data['game_index']],
            name=data['name'],
            region=data['region']
        )
        servers.append(server)
    
    return servers

# Функция для создания тестовых предложений
def create_offers(users, games, servers):
    """
    Создает или получает тестовые предложения о продаже игровых предметов.
    
    Args:
        users (list): Список объектов User
        games (list): Список объектов Game
        servers (list): Список объектов Server
        
    Returns:
        list: Список объектов Offer
    """
    offers = []
    offer_data = [
        {
            'seller_index': 0,
            'game_index': 0,
            'server_index': 0,
            'item_name': 'Эпический меч',
            'description': 'Легендарный меч с высоким уроном',
            'price': Decimal('1500.00'),
            'amount': 1,
            'quality': 'epic'
        },
        {
            'seller_index': 0,
            'game_index': 0,
            'server_index': 1,
            'item_name': 'Золото (1000 шт)',
            'description': 'Внутриигровая валюта',
            'price': Decimal('500.00'),
            'amount': 1000,
            'quality': 'common'
        },
        {
            'seller_index': 1,
            'game_index': 1,
            'server_index': 2,
            'item_name': 'AWP | Dragon Lore',
            'description': 'Редкий скин для снайперской винтовки',
            'price': Decimal('80000.00'),
            'amount': 1,
            'quality': 'legendary'
        },
        {
            'seller_index': 1,
            'game_index': 2,
            'server_index': 3,
            'item_name': 'Arcana Pudge',
            'description': 'Аркана для героя Pudge',
            'price': Decimal('2200.00'),
            'amount': 1,
            'quality': 'legendary'
        },
        {
            'seller_index': 2,
            'game_index': 3,
            'server_index': 5,
            'item_name': 'Алмазный набор (64 шт)',
            'description': 'Набор алмазов для крафта',
            'price': Decimal('120.00'),
            'amount': 64,
            'quality': 'rare'
        },
        {
            'seller_index': 4,
            'game_index': 4,
            'server_index': 6,
            'item_name': 'Редкий скин персонажа',
            'description': 'Эксклюзивный скин из коллекции',
            'price': Decimal('1800.00'),
            'amount': 1,
            'quality': 'epic'
        },
    ]
    
    # Создаем предложения из предопределенных данных
    for data in offer_data:
        # Получаем или создаем предложение с указанными характеристиками
        offer, created = Offer.objects.get_or_create(
            seller=users[data['seller_index']],
            game=games[data['game_index']],
            server=servers[data['server_index']],
            item_name=data['item_name'],
            defaults={
                'description': data['description'],
                'price': data['price'],
                'amount': data['amount'],
                'quality': data['quality']
            }
        )
        offers.append(offer)
    
    return offers

# Функция для создания тестовых отзывов
def create_reviews(users, offers):
    """
    Создает отзывы на предложения.
    
    Args:
        users (list): Список объектов User
        offers (list): Список объектов Offer
    """
    review_data = [
        {'offer_index': 0, 'reviewer_index': 2, 'rating': 5, 'comment': 'Отличный продавец, быстрая доставка!'},
        {'offer_index': 0, 'reviewer_index': 3, 'rating': 4, 'comment': 'Хороший товар, немного задержка с доставкой'},
        {'offer_index': 1, 'reviewer_index': 2, 'rating': 5, 'comment': 'Всё отлично, спасибо!'},
        {'offer_index': 2, 'reviewer_index': 3, 'rating': 5, 'comment': 'Редкий скин, очень доволен покупкой'},
        {'offer_index': 3, 'reviewer_index': 4, 'rating': 3, 'comment': 'Нормально, но цена высоковата'},
        {'offer_index': 4, 'reviewer_index': 0, 'rating': 5, 'comment': 'Хороший набор по выгодной цене'},
    ]
    
    # Создаем отзывы из предопределенных данных
    for data in review_data:
        # Получаем или создаем отзыв на указанное предложение
        Review.objects.get_or_create(
            offer=offers[data['offer_index']],
            reviewer=users[data['reviewer_index']],
            defaults={
                'rating': data['rating'],
                'comment': data['comment']
            }
        )

# Основной блок скрипта - выполняется, если скрипт запущен напрямую
if __name__ == '__main__':
    print('Начинаем заполнение базы данных...')  # Выводим сообщение о начале работы
    users = create_users()  # Создаем пользователей
    games = create_games()  # Создаем игры
    servers = create_servers(games)  # Создаем серверы для игр
    offers = create_offers(users, games, servers)  # Создаем предложения о продаже
    create_reviews(users, offers)  # Создаем отзывы на предложения
    print('База данных успешно заполнена!')  # Выводим сообщение об успешном завершении 