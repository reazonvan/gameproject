# Модуль фикстур для pytest в Django проекте.
# Этот файл автоматически обнаруживается pytest и предоставляет тестам общие фикстуры.
import pytest
from django.contrib.auth.models import User
from django.test import Client

# Фикстуры - это объекты, которые pytest может внедрять в тесты как зависимости.
# Они используются для подготовки среды тестирования и создания тестовых данных.

@pytest.fixture
def admin_user():
    """Создает и возвращает пользователя с правами администратора."""
    # Создаем пользователя-администратора для тестов административных функций
    user = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpassword'
    )
    return user

@pytest.fixture
def regular_user():
    """Создает и возвращает обычного пользователя."""
    # Создаем обычного пользователя для тестирования функций, доступных зарегистрированным пользователям
    user = User.objects.create_user(
        username='testuser',
        email='user@example.com',
        password='userpassword'
    )
    return user

@pytest.fixture
def admin_client(admin_user):
    """Возвращает клиент, авторизованный как администратор."""
    # Создаем клиент Django и авторизуем его как администратора
    # Зависит от фикстуры admin_user, которая будет вызвана автоматически
    client = Client()
    client.login(username='admin', password='adminpassword')
    return client

@pytest.fixture
def user_client(regular_user):
    """Возвращает клиент, авторизованный как обычный пользователь."""
    # Создаем клиент Django и авторизуем его как обычного пользователя
    # Зависит от фикстуры regular_user, которая будет вызвана автоматически
    client = Client()
    client.login(username='testuser', password='userpassword')
    return client

@pytest.fixture
def guest_client():
    """Возвращает клиент без авторизации."""
    # Создаем клиент Django без авторизации для тестирования публичного доступа
    return Client() 