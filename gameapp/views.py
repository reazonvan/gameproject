from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from datetime import datetime, timedelta
from .models import UserProfile, Message, Conversation, Game, GameCategory, GameSubcategory, Offer, Server, Review, UserActivity
from .forms import UserRegisterForm, LoginForm, OfferForm
import json
import logging
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Настройка логирования
logger = logging.getLogger('chat_logger')

def home(request):
    """
    Главная страница сайта
    """
    logger.info(f"[VIEW] Доступ к главной странице: {request.path}")
    context = {}
    if request.user.is_authenticated:
        logger.debug(f"[VIEW] Аутентифицированный пользователь {request.user.username} зашел на главную страницу")
        context['user'] = request.user
    
    # Подсчет количества активных предложений
    total_offers = Offer.objects.filter(is_tradable=True).count()
    
    # Подсчет количества игровых платформ
    games_count = Game.objects.count()
    
    # Подсчет количества пользователей онлайн
    online_users = UserProfile.objects.filter(online_status=True).count()
    
    context.update({
        'total_offers': total_offers,
        'games': {'count': games_count},
        'online_users': online_users
    })
    
    return render(request, 'gameapp/home.html', context)

def register_view(request):
    """
    Представление для регистрации пользователей
    """
    logger.info(f"[VIEW] Доступ к странице регистрации: {request.path}")
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                # Создаем пользователя
                logger.info(f"[VIEW] Попытка регистрации пользователя: {form.cleaned_data.get('username')}")
                user = form.save()
                
                # Создаем профиль пользователя автоматически через сигнал post_save
                # Выполняем вход
                logger.info(f"[VIEW] Пользователь {user.username} успешно зарегистрирован, выполняем вход")
                login(request, user)
                return redirect('home')
            except Exception as e:
                logger.error(f"[VIEW] Ошибка при регистрации пользователя: {str(e)}")
                form.add_error(None, f"Произошла ошибка при регистрации: {str(e)}")
        else:
            logger.warning(f"[VIEW] Ошибка валидации формы регистрации: {form.errors}")
    else:
        form = UserRegisterForm()
    
    return render(request, 'gameapp/register.html', {'form': form})

def login_view(request):
    """
    Представление для входа пользователей
    """
    logger.info(f"[VIEW] Доступ к странице входа: {request.path}")
    
    if request.user.is_authenticated:
        logger.debug(f"[VIEW] Пользователь {request.user.username} уже аутентифицирован, перенаправление на главную страницу")
        return redirect('home')
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            logger.info(f"[VIEW] Попытка входа пользователя: {username}")
            
            # Проверяем, не заблокирован ли аккаунт
            try:
                user = User.objects.get(username=username)
                if hasattr(user, 'userprofile') and user.userprofile.is_account_locked():
                    locked_until = user.userprofile.account_locked_until
                    logger.warning(f"[VIEW] Попытка входа в заблокированный аккаунт {username}, заблокирован до {locked_until}")
                    form.add_error(None, f"Аккаунт заблокирован до {locked_until}")
                    return render(request, 'gameapp/login.html', {'form': form})
            except User.DoesNotExist:
                logger.warning(f"[VIEW] Попытка входа с несуществующим пользователем: {username}")
                # Продолжаем работу, authenticate вернет None
            
            # Аутентификация пользователя
            user = authenticate(username=username, password=password)
            
            if user is not None:
                logger.info(f"[VIEW] Пользователь {username} успешно аутентифицирован")
                login(request, user)
                
                # Журналируем IP-адрес
                client_ip = get_client_ip(request)
                logger.debug(f"[VIEW] Успешный вход с IP: {client_ip}")
                
                # После успешного входа перенаправляем на целевую страницу или на главную
                next_page = request.GET.get('next', 'home')
                logger.debug(f"[VIEW] Перенаправление на страницу: {next_page}")
                return redirect(next_page)
            else:
                logger.warning(f"[VIEW] Неудачная попытка входа для пользователя: {username}")
                form.add_error(None, "Неверное имя пользователя или пароль")
        else:
            logger.warning(f"[VIEW] Ошибка валидации формы входа: {form.errors}")
    else:
        form = LoginForm()
    
    return render(request, 'gameapp/login.html', {'form': form})

def logout_view(request):
    """
    Представление для выхода пользователей из системы
    """
    username = request.user.username if request.user.is_authenticated else "Анонимный пользователь"
    logger.info(f"[VIEW] Выход пользователя {username} из системы")
    
    logout(request)
    return redirect('login')

def offer_list(request):
    """
    Главная страница со списком предложений
    """
    logger.info(f"[VIEW] Доступ к списку предложений: {request.path}")
    
    # Получаем все активные предложения, сортировка от новых к старым
    offers = Offer.objects.filter(is_tradable=True).order_by('-created_at')
    
    # Если пользователь выполнил поиск
    search_query = request.GET.get('search', '')
    game_filter = request.GET.get('game', '')
    category_filter = request.GET.get('category', '')
    
    if search_query:
        logger.debug(f"[VIEW] Поиск предложений по запросу: {search_query}")
        offers = offers.filter(item_name__icontains=search_query)
    
    if game_filter:
        logger.debug(f"[VIEW] Фильтрация предложений по игре: {game_filter}")
        offers = offers.filter(game_id=game_filter)
        
    if category_filter:
        logger.debug(f"[VIEW] Фильтрация предложений по категории: {category_filter}")
        offers = offers.filter(category_id=category_filter)
    
    # Получаем список игр и категорий для фильтров
    games = Game.objects.all().order_by('title')
    categories = GameCategory.objects.filter(is_active=True).order_by('name')
    
    # Подсчет количества пользователей онлайн
    online_users = UserProfile.objects.filter(online_status=True).count()
    
    context = {
        'offers': offers,
        'games': games,
        'categories': categories,
        'search_query': search_query,
        'game_filter': game_filter,
        'category_filter': category_filter,
        'total_offers': offers.count(),
        'online_users': online_users
    }
    
    return render(request, 'gameapp/offer_list.html', context)

@login_required
def profile(request, username=None):
    """
    Просмотр профиля пользователя
    """
    if username:
        logger.info(f"[VIEW] Пользователь {request.user.username} просматривает профиль {username}")
        user = get_object_or_404(User, username=username)
    else:
        logger.info(f"[VIEW] Пользователь {request.user.username} просматривает свой профиль")
        user = request.user
    
    # Получаем данные профиля
    try:
        profile = user.userprofile
        logger.debug(f"[VIEW] Загружен профиль для {user.username}, онлайн: {profile.online_status}")
    except UserProfile.DoesNotExist:
        logger.warning(f"[VIEW] Профиль не найден для {user.username}, создаем новый")
        profile = UserProfile.objects.create(user=user)

    context = {
        'profile_user': user,
        'profile': profile,
    }
    
    return render(request, 'gameapp/profile.html', context)

@login_required
def chat_view(request):
    """Представление для страницы чата"""
    logger.info(f"[CHAT:VIEW] Пользователь {request.user.username} зашел на страницу чата")
    
    # Получаем ID активного диалога из GET-параметра
    active_conversation_id = request.GET.get('conversation_id')
    logger.debug(f"[CHAT:VIEW] Запрошенный ID диалога: {active_conversation_id}")
    
    # Получаем все диалоги пользователя
    conversations = Conversation.objects.filter(
        Q(initiator=request.user) | Q(receiver=request.user)
    ).order_by('-updated_at')
    
    logger.debug(f"[CHAT:VIEW] Найдено {conversations.count()} диалогов для пользователя {request.user.username}")
    
    # Подготавливаем данные для шаблона
    context = {
        'conversations': [],
        'active_conversation_id': active_conversation_id,
    }
    
    # Обрабатываем каждый диалог
    for conversation in conversations:
        # Определяем собеседника
        other_user = conversation.receiver if conversation.initiator == request.user else conversation.initiator
        logger.debug(f"[CHAT:VIEW] Обработка диалога ID: {conversation.id} с пользователем {other_user.username}")
        
        # Получаем профиль собеседника
        try:
            other_user_profile = UserProfile.objects.get(user=other_user)
        except UserProfile.DoesNotExist:
            logger.warning(f"[CHAT:VIEW] Профиль пользователя {other_user.username} не найден, создаем новый")
            other_user_profile = UserProfile.objects.create(user=other_user)
        
        # Получаем последнее сообщение
        last_message = Message.objects.filter(conversation=conversation).order_by('-created_at').first()
        if last_message:
            logger.debug(f"[CHAT:VIEW] Последнее сообщение в диалоге ID: {conversation.id} - '{last_message.content[:30]}...' от {last_message.sender.username}")
        
        # Считаем непрочитанные сообщения
        unread_count = Message.objects.filter(
            conversation=conversation, 
            sender=other_user,
            is_read=False
        ).count()
        
        logger.debug(f"[CHAT:VIEW] Диалог ID: {conversation.id} имеет {unread_count} непрочитанных сообщений")
        
        # Добавляем данные диалога в контекст
        context['conversations'].append({
            'id': conversation.id,
            'other_user': other_user,
            'other_user_profile': other_user_profile,
            'last_message': last_message,
            'unread_count': unread_count,
        })
    
    logger.info(f"[CHAT:VIEW] Подготовлены данные для {len(context['conversations'])} диалогов пользователя {request.user.username}")
    return render(request, 'gameapp/chat.html', context)

@login_required
def get_conversation(request, user_id):
    """
    Получает или создает диалог с пользователем
    """
    other_user = get_object_or_404(User, id=user_id)
    logger.info(f"[VIEW] Пользователь {request.user.username} открывает диалог с {other_user.username}")
    
    try:
        # Получаем или создаем диалог
        conversation = Conversation.get_or_create_conversation(request.user, other_user)
        
        # Получаем все сообщения
        messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
        logger.debug(f"[VIEW] Загружено {messages.count()} сообщений из диалога {conversation.id}")
        
        # Помечаем все непрочитанные сообщения как прочитанные
        unread_messages = messages.filter(sender=other_user, is_read=False)
        if unread_messages.exists():
            logger.debug(f"[VIEW] Отмечаем {unread_messages.count()} сообщений как прочитанные")
            for message in unread_messages:
                message.mark_as_read()
        
        # Форматируем сообщения для ответа
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%d.%m.%Y %H:%M'),
                'sender_id': message.sender.id,
                'is_sender': message.sender == request.user,
                'is_read': message.is_read,
            })
        
        data = {
            'conversation_id': conversation.id,
            'messages': messages_data,
            'other_user': {
                'id': other_user.id,
                'username': other_user.username,
                'online_status': other_user.userprofile.online_status if hasattr(other_user, 'userprofile') else False,
                'last_online': other_user.userprofile.last_online.strftime('%d.%m.%Y %H:%M') if hasattr(other_user, 'userprofile') and other_user.userprofile.last_online else None,
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"[VIEW] Ошибка при получении диалога с {other_user.username}: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def send_message(request):
    """
    Отправка сообщения
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            recipient_id = data.get('recipient_id')
            content = data.get('content')
            
            if not recipient_id or not content:
                logger.warning(f"[VIEW] Некорректные данные при отправке сообщения: {data}")
                return JsonResponse({'error': 'Необходимо указать получателя и содержимое сообщения'}, status=400)
            
            recipient = get_object_or_404(User, id=recipient_id)
            logger.info(f"[VIEW] Пользователь {request.user.username} отправляет сообщение пользователю {recipient.username}")
            
            # Получаем или создаем диалог
            conversation = Conversation.get_or_create_conversation(request.user, recipient)
            
            # Создаем сообщение
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
                timestamp=timezone.now(),
                is_read=False
            )
            
            logger.debug(f"[VIEW] Создано новое сообщение (ID: {message.id}) в диалоге {conversation.id}")
            
            # Обновляем время последнего сообщения в диалоге
            conversation.last_message_time = timezone.now()
            conversation.save()
            
            # Возвращаем данные нового сообщения
            return JsonResponse({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%d.%m.%Y %H:%M'),
                'sender_id': message.sender.id,
                'is_sender': True,
                'is_read': message.is_read,
            })
            
        except Exception as e:
            logger.error(f"[VIEW] Ошибка при отправке сообщения: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    logger.warning(f"[VIEW] Попытка отправки сообщения с использованием метода {request.method}")
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

@login_required
def mark_messages_as_read(request):
    """
    Отметить сообщения как прочитанные
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            
            if not message_ids:
                logger.warning(f"[VIEW] Не указаны ID сообщений для отметки как прочитанные")
                return JsonResponse({'error': 'Необходимо указать ID сообщений'}, status=400)
            
            logger.info(f"[VIEW] Пользователь {request.user.username} отмечает сообщения как прочитанные: {message_ids}")
            
            # Получаем сообщения, которые нужно отметить
            messages = Message.objects.filter(id__in=message_ids, is_read=False)
            
            # Проверяем, что пользователь не является отправителем этих сообщений
            messages = messages.exclude(sender=request.user)
            
            if not messages.exists():
                logger.warning(f"[VIEW] Не найдено непрочитанных сообщений с указанными ID для пользователя {request.user.username}")
            
            # Отмечаем сообщения как прочитанные
            marked_count = 0
            for message in messages:
                message.mark_as_read()
                marked_count += 1
            
            logger.debug(f"[VIEW] Отмечено {marked_count} сообщений как прочитанные")
            
            return JsonResponse({'success': True, 'marked_count': marked_count})
            
        except Exception as e:
            logger.error(f"[VIEW] Ошибка при отметке сообщений как прочитанные: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)
    
    logger.warning(f"[VIEW] Попытка отметки сообщений как прочитанные с использованием метода {request.method}")
    return JsonResponse({'error': 'Метод не разрешен'}, status=405)

@login_required
def get_unread_messages_count(request):
    """
    Получает количество непрочитанных сообщений
    """
    try:
        logger.info(f"[VIEW] Запрос на получение количества непрочитанных сообщений для пользователя {request.user.username}")
        
        # Получаем диалоги пользователя
        conversations = Conversation.objects.filter(
            Q(user1=request.user) | Q(user2=request.user)
        )
        
        # Получаем количество непрочитанных сообщений
        unread_count = Message.objects.filter(
            conversation__in=conversations,
            is_read=False
        ).exclude(sender=request.user).count()
        
        logger.debug(f"[VIEW] Найдено {unread_count} непрочитанных сообщений для пользователя {request.user.username}")
        
        return JsonResponse({'unread_count': unread_count})
        
    except Exception as e:
        logger.error(f"[VIEW] Ошибка при получении количества непрочитанных сообщений: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_client_ip(request):
    """
    Получает IP-адрес клиента из запроса.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def login_view(request):
    """Страница авторизации"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Проверяем, не заблокирован ли аккаунт
        try:
            user_obj = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user_obj)
            
            if profile.is_account_locked():
                remaining_time = profile.account_locked_until - timezone.now()
                minutes = remaining_time.seconds // 60
                error_message = f"Аккаунт временно заблокирован из-за множества неудачных попыток входа. Повторите через {minutes} минут."
                return render(request, 'gameapp/login.html', {'error_message': error_message})
                
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            # Если пользователь не существует, продолжаем обычную аутентификацию
            pass
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Получаем профиль пользователя и обновляем статистику
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Получаем IP-адрес
            ip_address = get_client_ip(request)
            
            # Обновляем статистику входа
            profile.update_login_stats(ip_address)
            
            # Сбрасываем счетчик неудачных попыток
            profile.reset_failed_login_attempts()
            
            # Обновляем статус онлайн
            profile.update_online_status()
            
            # Записываем активность пользователя - вход в систему
            record_user_activity(user, 'login', {'ip_address': ip_address})
            
            return redirect('index')
        else:
            # Увеличиваем счетчик неудачных попыток, если пользователь существует
            try:
                user_obj = User.objects.get(username=username)
                profile = UserProfile.objects.get(user=user_obj)
                profile.increment_failed_login()
                
                if profile.is_account_locked():
                    remaining_time = profile.account_locked_until - timezone.now()
                    minutes = remaining_time.seconds // 60
                    error_message = f"Аккаунт временно заблокирован из-за множества неудачных попыток входа. Повторите через {minutes} минут."
                else:
                    error_message = "Неверное имя пользователя или пароль"
            except (User.DoesNotExist, UserProfile.DoesNotExist):
                error_message = "Неверное имя пользователя или пароль"
            
            return render(request, 'gameapp/login.html', {'error_message': error_message})
    
    return render(request, 'gameapp/login.html')

def register_view(request):
    """Страница регистрации"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        phone_number = request.POST.get('phone_number')
        avatar = request.FILES.get('avatar')
        
        # Проверяем совпадение паролей
        if password1 != password2:
            return render(request, 'gameapp/register.html', {'error_message': 'Пароли не совпадают'})
        
        # Проверяем уникальность имени пользователя
        if User.objects.filter(username=username).exists():
            return render(request, 'gameapp/register.html', {'error_message': 'Пользователь с таким именем уже существует'})
        
        # Проверяем уникальность email
        if User.objects.filter(email=email).exists():
            return render(request, 'gameapp/register.html', {'error_message': 'Пользователь с таким email уже существует'})
        
        # Проверяем уникальность телефона
        if UserProfile.objects.filter(phone_number=phone_number).exists():
            return render(request, 'gameapp/register.html', {'error_message': 'Пользователь с таким номером телефона уже существует'})
        
        # Создаем пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        
        # Получаем IP-адрес пользователя
        ip_address = get_client_ip(request)
        
        # Обновляем профиль пользователя (который создается автоматически через сигнал post_save)
        try:
            profile = UserProfile.objects.get(user=user)
            profile.phone_number = phone_number
            profile.registration_ip = ip_address
            profile.last_login_ip = ip_address
            profile.last_session_start = timezone.now()
            
            # Добавляем аватар, если загружен
            if avatar:
                profile.avatar = avatar
                
            profile.save()
        except UserProfile.DoesNotExist:
            # В случае если профиль не был создан сигналом, создаем его вручную
            profile = UserProfile.objects.create(
                user=user,
                phone_number=phone_number,
                registration_ip=ip_address,
                last_login_ip=ip_address,
                last_session_start=timezone.now(),
                avatar=avatar if avatar else None
            )
        
        # Авторизуем пользователя
        login(request, user)
        
        # Обновляем статус онлайн
        profile.update_online_status()
        
        # Перенаправляем на главную страницу
        return redirect('offer_list')
    
    return render(request, 'gameapp/register.html')

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@login_required
def start_chat_with_seller(request):
    """Представление для прямого создания чата с продавцом"""
    user = request.user
    
    # Получаем параметры из URL
    username = request.GET.get('username')
    offer_id = request.GET.get('offer_id')
    
    if not username:
        messages.error(request, "Ошибка: не указано имя продавца")
        return redirect('chat')
    
    try:
        # Ищем продавца
        seller = User.objects.get(username=username)
        
        # Проверяем, не пытается ли пользователь написать сам себе
        if seller == user:
            messages.error(request, "Вы не можете написать сообщение самому себе")
            return redirect('chat')
        
        # Ищем существующую беседу или создаем новую
        conversation = Conversation.objects.filter(
            (Q(initiator=user) & Q(receiver=seller)) |
            (Q(initiator=seller) & Q(receiver=user))
        ).first()
        
        if not conversation:
            # Создаем новую беседу
            conversation = Conversation.objects.create(
                initiator=user,
                receiver=seller
            )
            
            # Если указан ID предложения, создаем первое сообщение
            if offer_id:
                try:
                    offer = Offer.objects.get(id=offer_id)
                    Message.objects.create(
                        conversation=conversation,
                        sender=user,
                        content=f"Здравствуйте! Меня интересует ваше предложение #{offer_id} ({offer.item_name}).",
                        is_read=False
                    )
                except Offer.DoesNotExist:
                    pass
        
        # Перенаправляем на страницу чата с указанием ID беседы
        return redirect(f'/chat/?conversation_id={conversation.id}')
    
    except User.DoesNotExist:
        messages.error(request, f"Пользователь {username} не найден")
        return redirect('chat')
    except Exception as e:
        messages.error(request, f"Ошибка при создании беседы: {str(e)}")
        return redirect('chat')

@login_required
@require_POST
@csrf_exempt
def create_conversation(request):
    """API: Создание нового диалога с пользователем"""
    try:
        logger.info(f"[CHAT:CREATE_CONVERSATION] Запрос на создание нового диалога от пользователя {request.user.username}")
        
        # Получаем данные из запроса
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        logger.debug(f"[CHAT:CREATE_CONVERSATION] Запрошено создание диалога с пользователем ID: {user_id}")
        
        if not user_id:
            logger.warning(f"[CHAT:CREATE_CONVERSATION] Ошибка: не указан ID пользователя для создания диалога")
            return JsonResponse({'error': 'Не указан ID пользователя'}, status=400)
        
        # Находим пользователя, с которым создаем диалог
        try:
            other_user = User.objects.get(id=user_id)
            logger.debug(f"[CHAT:CREATE_CONVERSATION] Найден пользователь: {other_user.username} (ID: {user_id})")
        except User.DoesNotExist:
            logger.error(f"[CHAT:CREATE_CONVERSATION] Пользователь с ID: {user_id} не найден")
            return JsonResponse({'error': 'Пользователь не найден'}, status=404)
        
        # Проверяем, не создаем ли диалог с самим собой
        if other_user == request.user:
            logger.warning(f"[CHAT:CREATE_CONVERSATION] Попытка создать диалог с самим собой от пользователя {request.user.username}")
            return JsonResponse({'error': 'Нельзя создать диалог с самим собой'}, status=400)
        
        # Проверяем, существует ли уже диалог с этим пользователем
        existing_conversation = Conversation.objects.filter(
            (Q(initiator=request.user) & Q(receiver=other_user)) |
            (Q(initiator=other_user) & Q(receiver=request.user))
        ).first()
        
        if existing_conversation:
            logger.info(f"[CHAT:CREATE_CONVERSATION] Найден существующий диалог ID: {existing_conversation.id} между {request.user.username} и {other_user.username}")
            return JsonResponse({
                'success': True,
                'conversation_id': existing_conversation.id,
                'is_new': False
            })
        
        # Создаем новый диалог
        conversation = Conversation.objects.create(
            initiator=request.user,
            receiver=other_user
        )
        
        logger.info(f"[CHAT:CREATE_CONVERSATION] Создан новый диалог ID: {conversation.id} между {request.user.username} и {other_user.username}")
        
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'is_new': True
        })
    except json.JSONDecodeError:
        logger.error(f"[CHAT:CREATE_CONVERSATION] Ошибка декодирования JSON при создании диалога")
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        logger.error(f"[CHAT:CREATE_CONVERSATION] Ошибка при создании диалога: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_messages(request, conversation_id):
    """API: Получение всех сообщений беседы"""
    try:
        logger.info(f"[CHAT:GET_MESSAGES] Запрос сообщений для диалога ID: {conversation_id} от пользователя {request.user.username}")
        debug_level = request.headers.get('X-Debug-Level', 'normal')
        
        # Детальное логирование в verbose режиме
        if debug_level == 'verbose':
            logger.debug(f"[CHAT:GET_MESSAGES] Детальная информация о запросе: METHOD={request.method}, PATH={request.path}, GET={request.GET}, HEADERS={dict(request.headers)}")
        
        # Проверяем, существует ли беседа и имеет ли пользователь к ней доступ
        conversation = get_object_or_404(
            Conversation,
            Q(initiator=request.user) | Q(receiver=request.user),
            id=conversation_id
        )
        
        logger.debug(f"[CHAT:GET_MESSAGES] Найден диалог ID: {conversation_id} между {conversation.initiator.username} и {conversation.receiver.username}")
        
        # Получаем данные из запроса
        unread_only = request.GET.get('unread_only') == 'true'
        if unread_only:
            logger.debug(f"[CHAT:GET_MESSAGES] Запрошены только непрочитанные сообщения для диалога ID: {conversation_id}")
        
        # Получаем сообщения для беседы, отсортированные по времени (сначала старые)
        messages_query = Message.objects.filter(conversation=conversation)
        
        if unread_only:
            messages_query = messages_query.filter(is_read=False)
            logger.debug(f"[CHAT:GET_MESSAGES] Фильтруем только непрочитанные сообщения в диалоге ID: {conversation_id}")
        
        messages = messages_query.order_by('created_at')
        
        logger.info(f"[CHAT:GET_MESSAGES] Найдено {messages.count()} сообщений для диалога ID: {conversation_id}")
        
        # Формируем данные сообщений для ответа
        messages_data = []
        for message in messages:
            logger.debug(f"[CHAT:GET_MESSAGES] Обработка сообщения ID: {message.id}, отправитель: {message.sender.username}, прочитано: {message.is_read}")
            
            # Если сообщение от другого пользователя и не прочитано, отмечаем как прочитанное
            if message.sender != request.user and not message.is_read:
                logger.debug(f"[CHAT:GET_MESSAGES] Отмечаем сообщение ID: {message.id} как прочитанное")
                message.is_read = True
                message.save(update_fields=['is_read'])
            
            message_data = {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'created_at': message.created_at.isoformat(),
                'is_read': message.is_read
            }
            messages_data.append(message_data)
        
        if debug_level == 'verbose':
            logger.debug(f"[CHAT:GET_MESSAGES] Отправляем {len(messages_data)} сообщений в ответе")
        
        return JsonResponse({'messages': messages_data})
    except Exception as e:
        logger.error(f"[CHAT:GET_MESSAGES] Ошибка при получении сообщений: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_new_messages(request, conversation_id):
    """API: Получить только новые сообщения"""
    try:
        logger.info(f"[CHAT:GET_NEW_MESSAGES] Запрос новых сообщений для диалога ID: {conversation_id} от пользователя {request.user.username}")
        
        # Получаем параметр last_message_id из запроса
        last_message_id = request.GET.get('last_message_id')
        logger.debug(f"[CHAT:GET_NEW_MESSAGES] Параметр last_message_id: {last_message_id}")
        
        # Проверяем, существует ли беседа и имеет ли пользователь к ней доступ
        conversation = get_object_or_404(
            Conversation,
            Q(initiator=request.user) | Q(receiver=request.user),
            id=conversation_id
        )
        
        logger.debug(f"[CHAT:GET_NEW_MESSAGES] Найден диалог ID: {conversation_id} между {conversation.initiator.username} и {conversation.receiver.username}")
        
        # Определяем другого участника беседы
        other_user = conversation.receiver if conversation.initiator == request.user else conversation.initiator
        
        # Получаем сообщения, которые новее указанного ID
        query = Message.objects.filter(conversation=conversation)
        if last_message_id:
            query = query.filter(id__gt=last_message_id)
        
        messages = query.order_by('created_at')
        
        logger.info(f"[CHAT:GET_NEW_MESSAGES] Найдено {messages.count()} новых сообщений для диалога ID: {conversation_id}")
        
        # Формируем данные сообщений для ответа
        messages_data = []
        for message in messages:
            logger.debug(f"[CHAT:GET_NEW_MESSAGES] Обработка сообщения ID: {message.id}, отправитель: {message.sender.username}, прочитано: {message.is_read}")
            
            # Если сообщение от другого пользователя и не прочитано, отмечаем как прочитанное
            if message.sender != request.user and not message.is_read:
                logger.debug(f"[CHAT:GET_NEW_MESSAGES] Отмечаем сообщение ID: {message.id} как прочитанное")
                message.is_read = True
                message.save(update_fields=['is_read'])
            
            # Получаем все изображения сообщения
            images = []
            for img in message.images.all():
                logger.debug(f"[CHAT:GET_NEW_MESSAGES] Добавляем изображение ID: {img.id} к сообщению ID: {message.id}")
                images.append({
                    'id': img.id,
                    'url': img.image.url
                })
            
            file_data = None
            if message.file:
                logger.debug(f"[CHAT:GET_NEW_MESSAGES] Обрабатываем файл сообщения ID: {message.id}: {message.file.name}")
                file_data = {
                    'url': message.file.url,
                    'name': message.file.name.split('/')[-1],
                    'size': message.file.size,
                    'type': message.file.content_type if hasattr(message.file, 'content_type') else 'application/octet-stream'
                }
            
            voice_data = None
            if message.voice:
                logger.debug(f"[CHAT:GET_NEW_MESSAGES] Обрабатываем голосовое сообщение ID: {message.id}: {message.voice.name}, длительность: {message.voice_duration or 0}с")
                voice_data = {
                    'url': message.voice.url,
                    'duration': message.voice_duration or 0
                }
            
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                'created_at': message.created_at.isoformat(),
                'sender_id': message.sender.id,
                'is_read': message.is_read,
                'is_current_user': message.sender == request.user,
                'images': images,
                'file': file_data,
                'voice': voice_data
            })
        
        # Отмечаем сообщения как прочитанные
        unread_count = conversation.messages.filter(sender=other_user, is_read=False).count()
        if unread_count > 0:
            logger.debug(f"[CHAT:GET_NEW_MESSAGES] Отмечаем {unread_count} непрочитанных сообщений как прочитанные")
            conversation.messages.filter(sender=other_user, is_read=False).update(is_read=True)
        
        # Проверяем статус ввода
        is_typing = getattr(other_user, 'is_typing', False)
        
        # Возвращаем данные в формате JSON
        logger.debug(f"[CHAT:GET_NEW_MESSAGES] Отправка {len(messages_data)} новых сообщений клиенту")
        return JsonResponse({
            'messages': messages_data,
            'current_user_id': request.user.id,
            'is_typing': is_typing
        })
    except Exception as e:
        logger.error(f"[CHAT:GET_NEW_MESSAGES] Ошибка при получении новых сообщений: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def send_message(request, conversation_id):
    """API: Отправка сообщения в беседу"""
    try:
        logger.info(f"[CHAT:SEND_MESSAGE] Запрос на отправку сообщения в диалог ID: {conversation_id} от пользователя {request.user.username}")
        
        # Проверяем, существует ли беседа и имеет ли пользователь к ней доступ
        conversation = get_object_or_404(
            Conversation,
            Q(initiator=request.user) | Q(receiver=request.user),
            id=conversation_id
        )
        
        logger.debug(f"[CHAT:SEND_MESSAGE] Найден диалог ID: {conversation_id} между {conversation.initiator.username} и {conversation.receiver.username}")
        
        # Получаем данные сообщения из запроса
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        logger.debug(f"[CHAT:SEND_MESSAGE] Содержимое сообщения: '{content[:50]}{'...' if len(content) > 50 else ''}'")
        
        if not content:
            logger.warning(f"[CHAT:SEND_MESSAGE] Попытка отправки пустого сообщения в диалог ID: {conversation_id}")
            return JsonResponse({'error': 'Сообщение не может быть пустым'}, status=400)
        
        # Определяем получателя
        recipient = conversation.receiver if conversation.initiator == request.user else conversation.initiator
        logger.debug(f"[CHAT:SEND_MESSAGE] Получатель сообщения: {recipient.username}")
        
        # Создаем новое сообщение
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            recipient=recipient,
            content=content
        )
        
        logger.debug(f"[CHAT:SEND_MESSAGE] Создано новое сообщение ID: {message.id} в диалоге ID: {conversation_id}")
        
        # Обновляем время последнего обновления беседы
        prev_update_time = conversation.updated_at
        conversation.updated_at = timezone.now()
        conversation.save()
        
        logger.debug(f"[CHAT:SEND_MESSAGE] Обновлено время последнего обновления диалога с {prev_update_time} на {conversation.updated_at}")
        
        logger.info(f"[CHAT:SEND_MESSAGE] Сообщение ID: {message.id} успешно отправлено в диалог ID: {conversation_id}")
        
        # Формируем ответ с данными созданного сообщения
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'created_at': message.created_at.isoformat()
            }
        })
    except json.JSONDecodeError:
        logger.error(f"[CHAT:SEND_MESSAGE] Ошибка декодирования JSON при отправке сообщения в диалог ID: {conversation_id}")
        return JsonResponse({'error': 'Неверный формат данных'}, status=400)
    except Exception as e:
        logger.error(f"[CHAT:SEND_MESSAGE] Ошибка при отправке сообщения: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def mark_message_read(request, message_id):
    """API: Отметка сообщения как прочитанного"""
    try:
        debug_level = request.headers.get('X-Debug-Level', 'normal')
        logger.info(f"[CHAT:MARK_READ] Запрос на отметку сообщения ID: {message_id} как прочитанного от пользователя {request.user.username}")
        
        if debug_level == 'verbose':
            logger.debug(f"[CHAT:MARK_READ] Детальная информация о запросе: METHOD={request.method}, PATH={request.path}, HEADERS={dict(request.headers)}")
        
        # Находим сообщение и проверяем, имеет ли пользователь доступ к нему
        message = get_object_or_404(
            Message,
            Q(conversation__initiator=request.user) | Q(conversation__receiver=request.user),
            id=message_id
        )
        
        logger.debug(f"[CHAT:MARK_READ] Найдено сообщение ID: {message_id} в диалоге ID: {message.conversation.id}, отправитель: {message.sender.username}")
        
        # Отмечаем сообщение как прочитанное только если получатель - текущий пользователь
        if message.sender != request.user and not message.is_read:
            old_status = message.is_read
            message.is_read = True
            message.save(update_fields=['is_read'])
            logger.info(f"[CHAT:MARK_READ] Сообщение ID: {message_id} статус прочтения изменен: {old_status} -> {message.is_read}")
        else:
            if debug_level == 'verbose':
                logger.debug(f"[CHAT:MARK_READ] Сообщение ID: {message_id} не требует изменения статуса (уже прочитано или отправлено текущим пользователем)")
        
        return JsonResponse({'success': True})
    except Exception as e:
        logger.error(f"[CHAT:MARK_READ] Ошибка при отметке сообщения как прочитанного: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def profile_view(request, username=None):
    """Представление для страницы профиля пользователя"""
    if username:
        # Если указан username, показываем профиль этого пользователя
        profile_user = get_object_or_404(User, username=username)
        is_own_profile = (profile_user == request.user)
    else:
        # Иначе показываем профиль текущего пользователя
        profile_user = request.user
        is_own_profile = True
    
    # Получаем профиль пользователя с исправленной датой
    profile = UserProfile.get_profile_with_corrected_date(profile_user)
    
    # Обновляем статус онлайн для отображаемого профиля
    # Это нужно, чтобы авторизованный пользователь всегда видел свой статус "в сети"
    if profile_user == request.user:
        now = timezone.now()
        # Обязательно ставим статус онлайн для своего профиля
        profile.online_status = True
        profile.save(update_fields=['online_status'])
    
    # Получаем предложения пользователя
    offers = Offer.objects.filter(seller=profile_user).order_by('-created_at')
    
    # Получаем отзывы на предложения пользователя
    reviews = Review.objects.filter(offer__seller=profile_user).order_by('-created_at')
    
    # Вычисляем средний рейтинг
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating_int = int(avg_rating)  # Целая часть для отображения звезд
    avg_rating_half = avg_rating_int + 0.5 if avg_rating - avg_rating_int >= 0.3 else avg_rating_int  # Для отображения половинчатых звезд
    
    # Определяем уровень продавца
    seller_level = calculate_activity_level(profile_user)
    
    # Если это чужой профиль, используем представление публичного профиля продавца
    if not is_own_profile:
        # Группируем предложения по играм для удобного отображения
        games_with_offers = []
        game_ids = offers.values_list('game', flat=True).distinct()
        
        for game_id in game_ids:
            game = Game.objects.get(pk=game_id)
            game_offers = offers.filter(game=game)
            games_with_offers.append({
                'title': game.title,
                'offers': game_offers,
                'count': game_offers.count()
            })
        
        # Сортируем игры по количеству предложений (больше предложений - выше)
        games_with_offers.sort(key=lambda x: x['count'], reverse=True)
        
        context = {
            'profile_user': profile_user,
            'profile': profile,
            'games_with_offers': games_with_offers,
            'reviews': reviews[:10],  # Ограничиваем количество отзывов для первого отображения
            'reviews_count': reviews.count(),
            'avg_rating': round(avg_rating, 1),
            'avg_rating_int': avg_rating_int,
            'avg_rating_half': avg_rating_half,
            'seller_level': seller_level,
            'is_own_profile': is_own_profile,
        }
        
        # Записываем просмотр профиля в активность
        record_user_activity(
            request.user, 
            'profile_view', 
            details={'viewed_profile': profile_user.username},
            related_object_id=profile_user.id,
            related_object_type='User'
        )
        
        return render(request, 'gameapp/seller_profile.html', context)
    
    # Иначе для собственного профиля используем существующий шаблон
    context = {
        'profile_user': profile_user,
        'profile': profile,
        'offers': offers,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'is_own_profile': is_own_profile,
    }
    
    return render(request, 'gameapp/profile.html', context)

def calculate_activity_level(user):
    """Рассчитать уровень активности пользователя (от 1 до 5)"""
    # Считаем количество действий пользователя за последние 30 дней
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    activities_count = UserActivity.objects.filter(
        user=user, 
        timestamp__gte=thirty_days_ago
    ).count()
    
    # Количество созданных предложений
    offers_count = Offer.objects.filter(seller=user).count()
    
    # Получаем профиль пользователя или создаем его, если он не существует
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Количество завершенных сделок
    deals_count = profile.deals_count
    
    # Рассчитываем уровень активности на основе всех факторов
    total_score = activities_count + (offers_count * 2) + (deals_count * 3)
    
    if total_score > 50:
        return 5  # Очень активный
    elif total_score > 30:
        return 4
    elif total_score > 15:
        return 3
    elif total_score > 5:
        return 2
    else:
        return 1  # Низкая активность

@login_required
def update_avatar(request):
    """Обновление аватарки пользователя"""
    if request.method == 'POST':
        avatar = request.FILES.get('avatar')
        if avatar:
            try:
                # Получаем профиль пользователя
                profile, created = UserProfile.objects.get_or_create(user=request.user)
                
                # Удаляем старую аватарку, если она существует
                if profile.avatar:
                    try:
                        # Сохраняем путь к старой аватарке
                        old_avatar_path = profile.avatar.path
                        # Удаляем файл, если он существует
                        if os.path.isfile(old_avatar_path):
                            os.remove(old_avatar_path)
                    except (ValueError, OSError) as e:
                        # Если возникла ошибка при удалении файла, просто логируем её
                        print(f"Ошибка при удалении старого аватара: {e}")
                
                # Обновляем аватарку
                profile.avatar = avatar
                profile.save()
                
                # Записываем активность - обновление профиля
                record_user_activity(request.user, 'profile_update', {'updated_field': 'avatar'})
                
                messages.success(request, 'Аватарка успешно обновлена!')
            except Exception as e:
                print(f"Ошибка при обновлении аватара: {e}")
                messages.error(request, f'Ошибка при обновлении аватарки: {str(e)}')
        else:
            messages.error(request, 'Ошибка при загрузке аватарки. Пожалуйста, выберите файл изображения.')
    
    # Перенаправляем на страницу профиля
    return redirect('profile')

def record_user_activity(user, activity_type, details=None, related_object_id=None, related_object_type=None):
    """
    Записывает активность пользователя
    :param user: Объект пользователя
    :param activity_type: Тип активности (из списка UserActivity.ACTIVITY_TYPES)
    :param details: Дополнительные детали в формате JSON
    :param related_object_id: ID связанного объекта
    :param related_object_type: Тип связанного объекта
    :return: Объект созданной активности
    """
    # Создаем запись об активности
    activity = UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        details=details,
        related_object_id=related_object_id,
        related_object_type=related_object_type
    )
    
    # Обновляем статистику активности в профиле пользователя
    today = timezone.now().date().strftime('%Y-%m-%d')
    
    try:
        profile = UserProfile.objects.get(user=user)
        activity_log = profile.activity_log or {}
        
        # Увеличиваем счетчик активностей для текущего дня
        if today in activity_log:
            activity_log[today] += 1
        else:
            activity_log[today] = 1
            
        # Сохраняем обновленные данные
        profile.activity_log = activity_log
        profile.save(update_fields=['activity_log'])
    except UserProfile.DoesNotExist:
        pass
    
    return activity

@login_required
def update_online_status_view(request):
    """Обновляет статус онлайн пользователя"""
    try:
        action = request.GET.get('action', 'heartbeat')
        debug_level = request.headers.get('X-Debug-Level', 'normal')
        
        if hasattr(request.user, 'userprofile'):
            now = timezone.now()
            
            # Проверяем, не установлена ли дата в будущем
            if request.user.userprofile.last_online > now:
                # Если дата в будущем, исправляем её
                logger.warning(f"[CHAT] Обнаружена дата в будущем для пользователя {request.user.username} (ID: {request.user.id})")
                request.user.userprofile.last_online = now
            
            # Обрабатываем различные типы действий
            if action == 'offline':
                # Пользователь явно указал, что он выходит
                if debug_level == 'verbose':
                    logger.debug(f"[CHAT] Пользователь {request.user.username} (ID: {request.user.id}) выходит из сети")
                
                request.user.userprofile.online_status = False
                
                # Обновляем время онлайн, если был начат сеанс
                if request.user.userprofile.last_session_start:
                    session_duration = now - request.user.userprofile.last_session_start
                    if request.user.userprofile.total_time_online:
                        request.user.userprofile.total_time_online += session_duration
                    else:
                        request.user.userprofile.total_time_online = session_duration
                    request.user.userprofile.last_session_start = None
                
                request.user.userprofile.save(update_fields=[
                    'online_status', 'last_online', 'total_time_online', 'last_session_start'
                ])
                
                logger.info(f"[CHAT] Пользователь {request.user.username} установил статус 'не в сети'")
            elif action == 'online':
                # Пользователь явно указал, что он в сети
                if debug_level == 'verbose':
                    logger.debug(f"[CHAT] Пользователь {request.user.username} (ID: {request.user.id}) входит в сеть")
                
                request.user.userprofile.last_online = now
                request.user.userprofile.online_status = True
                
                # Если пользователь заходит после отсутствия, начинаем новый сеанс
                if not request.user.userprofile.last_session_start:
                    request.user.userprofile.last_session_start = now
                
                request.user.userprofile.save(update_fields=[
                    'online_status', 'last_online', 'last_session_start'
                ])
                
                logger.info(f"[CHAT] Пользователь {request.user.username} установил статус 'в сети'")
            else:  # heartbeat - обычное обновление статуса
                if debug_level == 'verbose':
                    logger.debug(f"[CHAT] Heartbeat запрос от пользователя {request.user.username} (ID: {request.user.id})")
                
                # Обновляем время последнего посещения
                request.user.userprofile.last_online = now
                
                # Обновляем статус онлайн
                request.user.userprofile.update_online_status()
                
                logger.info(f"[CHAT] Обновлен heartbeat пользователя {request.user.username}")
        else:
            logger.error(f"[CHAT] У пользователя {request.user.username} (ID: {request.user.id}) отсутствует профиль")
        
        return HttpResponse(status=204)  # No Content
    except Exception as e:
        logger.error(f"[CHAT] Ошибка при обновлении статуса: {str(e)}")
        return HttpResponse(status=500)

@login_required
def logout_view(request):
    """Выход пользователя с обновлением статуса"""
    if hasattr(request.user, 'userprofile'):
        # Обновляем время последнего входа
        now = timezone.now()
        request.user.userprofile.last_online = now
        
        # Расчет времени онлайн для текущей сессии
        if request.user.userprofile.last_session_start:
            session_duration = now - request.user.userprofile.last_session_start
            if request.user.userprofile.total_time_online:
                request.user.userprofile.total_time_online += session_duration
            else:
                request.user.userprofile.total_time_online = session_duration
            request.user.userprofile.last_session_start = None
        
        # Отмечаем, что пользователь не в сети
        request.user.userprofile.online_status = False
        request.user.userprofile.save()
    
    # Выполняем стандартный выход из системы
    logout(request)
    
    # Перенаправляем на главную страницу
    return redirect('index')

def create_offer_view(request):
    """Страница создания объявления о продаже"""
    # Перенаправляем неавторизованных пользователей на страницу входа
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Получаем ID игры из параметров, если есть
    game_id = request.GET.get('game')
    selected_game = None
    
    if game_id:
        try:
            selected_game = Game.objects.get(id=game_id)
        except Game.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # Если выбрана игра, создаем объявление
        game_id = request.POST.get('game')
        
        try:
            game = Game.objects.get(id=game_id)
            server_id = request.POST.get('server')
            server = Server.objects.get(id=server_id)
            
            # Получаем остальные данные формы
            category_id = request.POST.get('category')
            subcategory_id = request.POST.get('subcategory')
            item_name = request.POST.get('item_name')
            description = request.POST.get('description')
            price = request.POST.get('price')
            amount = request.POST.get('amount', 1)
            quality = request.POST.get('quality', 'common')
            is_tradable = request.POST.get('is_tradable', True)
            
            # Создаем базовое объявление
            offer = Offer(
                seller=request.user,
                game=game,
                server=server,
                item_name=item_name,
                description=description,
                price=price,
                amount=amount,
                quality=quality,
                is_tradable=is_tradable == 'on'
            )
            
            # Добавляем категорию и подкатегорию, если они указаны
            if category_id:
                try:
                    category = GameCategory.objects.get(id=category_id)
                    offer.category = category
                    
                    if subcategory_id:
                        subcategory = GameSubcategory.objects.get(id=subcategory_id)
                        if subcategory.category == category:
                            offer.subcategory = subcategory
                except (GameCategory.DoesNotExist, GameSubcategory.DoesNotExist):
                    pass
            
            # Сохраняем объявление
            offer.save()
            
            # Обрабатываем изображения, если они есть
            images = request.FILES.getlist('images')
            if images:
                for i, image in enumerate(images):
                    OfferImage.objects.create(
                        offer=offer,
                        image=image,
                        order=i
                    )
            
            # Обновляем счетчик предложений в профиле пользователя
            try:
                profile = UserProfile.objects.get(user=request.user)
                profile.offers_count += 1
                profile.save(update_fields=['offers_count'])
                
                # Записываем действие в активность пользователя
                record_user_activity(
                    request.user, 
                    'offer_create', 
                    details={'offer_id': offer.id, 'offer_name': offer.item_name},
                    related_object_id=offer.id,
                    related_object_type='Offer'
                )
            except UserProfile.DoesNotExist:
                pass
            
            # Перенаправляем на страницу созданного объявления
            return redirect('offer_detail', offer_id=offer.id)
            
        except (Game.DoesNotExist, Server.DoesNotExist) as e:
            return render(request, 'gameapp/create_offer.html', {
                'error_message': f'Ошибка при создании объявления: {str(e)}',
                'selected_game': selected_game,
                'games': Game.objects.all()
            })
    
    # Если игра выбрана, показываем форму создания объявления
    if selected_game:
        servers = Server.objects.filter(game=selected_game)
        categories = GameCategory.objects.filter(game=selected_game, is_active=True).order_by('order', 'name')
        
        return render(request, 'gameapp/create_offer.html', {
            'selected_game': selected_game,
            'servers': servers,
            'categories': categories,
            'quality_choices': Offer.ITEM_QUALITY_CHOICES
        })
    
    # Если игра не выбрана, показываем список игр для выбора
    games = Game.objects.all().order_by('title')
    return render(request, 'gameapp/create_offer.html', {'games': games})

@login_required
def get_message_statuses(request, conversation_id):
    """API: Получить статусы сообщений (прочитано/непрочитано)"""
    try:
        conversation = get_object_or_404(
            Conversation,
            Q(initiator=request.user) | Q(receiver=request.user),
            id=conversation_id
        )
        
        # Получаем только сообщения отправленные пользователем
        messages = Message.objects.filter(
            conversation=conversation,
            sender=request.user
        ).order_by('-timestamp')
        
        # Формируем статусы для каждого сообщения
        message_statuses = []
        for message in messages:
            message_statuses.append({
                'message_id': message.id,
                'is_read': message.is_read
            })
        
        return JsonResponse({
            'status': 'success',
            'message_statuses': message_statuses
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def game_detail(request, slug):
    game = get_object_or_404(Game, slug=slug)
    categories = GameCategory.objects.filter(is_active=True).order_by('order', 'name')
    context = {
        'game': game,
        'categories': categories,
    }
    return render(request, 'gameapp/game_detail.html', context)

@login_required
def game_category(request, slug):
    category = get_object_or_404(GameCategory, slug=slug, is_active=True)
    subcategories = GameSubcategory.objects.filter(category=category, is_active=True).order_by('order', 'name')
    
    # Получаем активные фильтры для этой категории
    filter_groups = FilterGroup.objects.filter(category=category, is_active=True).order_by('order')
    
    # Получаем параметры фильтрации из GET-запроса
    filter_params = {}
    for group in filter_groups:
        filter_value = request.GET.get(group.name)
        if filter_value:
            filter_params[group.name] = filter_value
    
    # Получаем базовый QuerySet предложений для этой категории
    offers = Offer.objects.filter(category=category).order_by('-created_at')
    
    # Применяем фильтры
    if filter_params:
        # Для каждого фильтра получаем ID опций и находим предложения с такими значениями фильтров
        for group_name, value in filter_params.items():
            try:
                group = FilterGroup.objects.get(category=category, name=group_name)
                
                if group.filter_type == 'range':
                    # Для диапазонов (например, цена от-до)
                    value_parts = value.split('-')
                    if len(value_parts) == 2:
                        min_val, max_val = value_parts
                        if min_val:
                            offers = offers.filter(price__gte=float(min_val))
                        if max_val:
                            offers = offers.filter(price__lte=float(max_val))
                else:
                    # Для селектов и чекбоксов - фильтруем по значениям фильтров
                    option_ids = FilterOption.objects.filter(
                        filter_group=group, 
                        name__in=value.split(','),
                        is_active=True
                    ).values_list('id', flat=True)
                    
                    if option_ids:
                        offers = offers.filter(
                            filter_values__filter_option_id__in=option_ids
                        ).distinct()
            except Exception as e:
                # Если возникла ошибка при обработке фильтра, пропускаем его
                print(f"Error applying filter {group_name}: {e}")
    
    # Пагинация
    paginator = Paginator(offers, 12)  # 12 предложений на страницу
    page = request.GET.get('page')
    try:
        offers_page = paginator.page(page)
    except PageNotAnInteger:
        offers_page = paginator.page(1)
    except EmptyPage:
        offers_page = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'subcategories': subcategories,
        'offers': offers_page,
        'filter_groups': filter_groups,
        'filter_params': filter_params,
    }
    return render(request, 'gameapp/game_category.html', context)

@login_required
def game_subcategory(request, category_slug, slug):
    category = get_object_or_404(GameCategory, slug=category_slug, is_active=True)
    subcategory = get_object_or_404(GameSubcategory, category=category, slug=slug, is_active=True)
    
    # Получаем активные фильтры для родительской категории
    filter_groups = FilterGroup.objects.filter(category=category, is_active=True).order_by('order')
    
    # Получаем параметры фильтрации из GET-запроса
    filter_params = {}
    for group in filter_groups:
        filter_value = request.GET.get(group.name)
        if filter_value:
            filter_params[group.name] = filter_value
    
    # Получаем базовый QuerySet предложений для этой подкатегории
    offers = Offer.objects.filter(subcategory=subcategory).order_by('-created_at')
    
    # Применяем фильтры (аналогично методу game_category)
    if filter_params:
        for group_name, value in filter_params.items():
            try:
                group = FilterGroup.objects.filter(category=category, name=group_name).first()
                if not group:
                    continue
                    
                if group.filter_type == 'range':
                    value_parts = value.split('-')
                    if len(value_parts) == 2:
                        min_val, max_val = value_parts
                        if min_val:
                            offers = offers.filter(price__gte=float(min_val))
                        if max_val:
                            offers = offers.filter(price__lte=float(max_val))
                else:
                    option_ids = FilterOption.objects.filter(
                        filter_group=group, 
                        name__in=value.split(','),
                        is_active=True
                    ).values_list('id', flat=True)
                    
                    if option_ids:
                        offers = offers.filter(
                            filter_values__filter_option_id__in=option_ids
                        ).distinct()
            except Exception as e:
                print(f"Error applying filter {group_name}: {e}")
    
    # Пагинация
    paginator = Paginator(offers, 12)  # 12 предложений на страницу
    page = request.GET.get('page')
    try:
        offers_page = paginator.page(page)
    except PageNotAnInteger:
        offers_page = paginator.page(1)
    except EmptyPage:
        offers_page = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'offers': offers_page,
        'filter_groups': filter_groups,
        'filter_params': filter_params,
    }
    return render(request, 'gameapp/game_subcategory.html', context)

@login_required
def create_offer(request):
    form = None
    
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.seller = request.user
            offer.save()
            form.save_m2m()  # Сохраняем many-to-many поля
            
            return redirect('offer_detail', offer.id)
    else:
        form = OfferForm()
    
    return render(request, 'gameapp/create_offer.html', {
        'form': form,
        'games': Game.objects.all(),
        'servers': Server.objects.all()
    })

# Добавляем Ajax-представление для получения категорий по ID игры
@login_required
def get_categories(request):
    game_id = request.GET.get('game_id')
    if game_id:
        categories = GameCategory.objects.filter(
            game_id=game_id, 
            is_active=True
        ).values('id', 'name')
        return JsonResponse(list(categories), safe=False)
    return JsonResponse([], safe=False)

# Обновляем Ajax-представление для получения подкатегорий
@login_required
def get_subcategories(request):
    category_id = request.GET.get('category_id')
    if category_id:
        subcategories = GameSubcategory.objects.filter(
            category_id=category_id, 
            is_active=True
        ).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    return JsonResponse([], safe=False)

@login_required
def notifications_view(request):
    """Отображает все уведомления пользователя."""
    # Проверяем, существует ли таблица уведомлений в базе данных
    cursor = connection.cursor()
    
    try:
        # Пробуем получить данные из таблицы, чтобы проверить её существование
        cursor.execute("SELECT 1 FROM gameapp_notification LIMIT 1")
        table_exists = True
    except Exception:
        # Если таблица не существует, устанавливаем флаг
        table_exists = False
    finally:
        cursor.close()
    
    # Если таблица не существует, возвращаем пустые списки
    if not table_exists:
        unread_notifications = []
        read_notifications = []
    else:
        try:
            # Получаем непрочитанные уведомления
            unread_notifications = request.user.notifications.filter(is_read=False)
            
            # Получаем прочитанные уведомления (ограничиваем 50 последними)
            read_notifications = request.user.notifications.filter(is_read=True)[:50]
            
            # Отметка уведомлений как прочитанные
            if request.method == 'POST':
                action = request.POST.get('action')
                
                if action == 'mark_all_read':
                    # Отмечаем все как прочитанные
                    from .models import Notification
                    Notification.mark_all_as_read(request.user)
                    return redirect('notifications')
                    
                elif action == 'mark_read':
                    # Отмечаем конкретное уведомление
                    notification_id = request.POST.get('notification_id')
                    if notification_id:
                        notification = get_object_or_404(request.user.notifications, id=notification_id)
                        notification.mark_as_read()
                        return redirect('notifications')
                        
                elif action == 'delete':
                    # Удаляем уведомление
                    notification_id = request.POST.get('notification_id')
                    if notification_id:
                        notification = get_object_or_404(request.user.notifications, id=notification_id)
                        notification.delete()
                        return redirect('notifications')
        except Exception:
            # Если произошла ошибка, просто возвращаем пустые списки
            unread_notifications = []
            read_notifications = []
    
    # Определяем текущую и вчерашнюю даты для шаблона
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    
    context = {
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'today': today,
        'yesterday': yesterday,
        'table_exists': table_exists,
    }
    
    return render(request, 'gameapp/notifications.html', context)

@login_required
@require_GET
def check_new_messages(request):
    """API-эндпоинт для проверки новых сообщений пользователя"""
    user = request.user
    
    try:
        # Предполагаем, что у вас есть модель Message с полями sender, recipient, is_read, content и created_at
        from .models import Message
        
        # Получаем количество непрочитанных сообщений
        new_messages_count = Message.objects.filter(recipient=user, is_read=False).count()
        
        # Получаем последнее сообщение, если оно есть
        last_message = None
        if new_messages_count > 0:
            last_msg = Message.objects.filter(recipient=user, is_read=False).order_by('-created_at').first()
            if last_msg:
                # Сокращаем текст сообщения, если он слишком длинный
                short_text = last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content
                last_message = {
                    'sender': last_msg.sender.username,
                    'short_text': short_text,
                    'time': last_msg.created_at.strftime('%H:%M')
                }
        
        return JsonResponse({
            'success': True,
            'new_messages': new_messages_count,
            'last_message': last_message
        })
    except Exception as e:
        # В случае ошибки возвращаем пустой ответ
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'new_messages': 0
        })

@login_required
def get_users_status(request):
    """API: Получить статусы пользователей для чата"""
    try:
        logger.info(f"[CHAT] Запрос статусов пользователей от {request.user.username} (ID: {request.user.id})")
        debug_level = request.headers.get('X-Debug-Level', 'normal')
        
        # Получаем всех пользователей, с которыми есть диалоги
        conversations = Conversation.objects.filter(
            Q(initiator=request.user) | Q(receiver=request.user)
        )
        
        user_ids = set()
        for conversation in conversations:
            if conversation.initiator != request.user:
                user_ids.add(conversation.initiator.id)
            if conversation.receiver != request.user:
                user_ids.add(conversation.receiver.id)
        
        if debug_level == 'verbose':
            logger.debug(f"[CHAT] Найдено {len(user_ids)} пользователей для проверки статуса")
        
        # Получаем профили всех пользователей
        profiles = UserProfile.objects.filter(user_id__in=user_ids)
        
        # Формируем список пользователей с их статусами
        users_status = []
        for profile in profiles:
            # Обновляем статус, чтобы получить актуальные данные
            profile.update_online_status()
            
            users_status.append({
                'id': profile.user.id,
                'username': profile.user.username,
                'online_status': profile.online_status,
                'last_online': profile.last_online.isoformat()
            })
            
            if debug_level == 'verbose':
                logger.debug(f"[CHAT] Статус пользователя {profile.user.username} (ID: {profile.user.id}): online={profile.online_status}")
        
        logger.info(f"[CHAT] Отправлены статусы {len(users_status)} пользователей")
        return JsonResponse({'users': users_status})
    except Exception as e:
        logger.error(f"[CHAT] Ошибка при получении статусов пользователей: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def get_online_users_count(request):
    """API: Получить количество пользователей онлайн"""
    try:
        # Получаем количество пользователей со статусом онлайн
        online_count = UserProfile.objects.filter(online_status=True).count()
        logger.info(f"[VIEW] Запрос количества пользователей онлайн. Результат: {online_count}")
        
        return JsonResponse({
            'success': True,
            'online_count': online_count
        })
    except Exception as e:
        logger.error(f"[VIEW] Ошибка при получении количества пользователей онлайн: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'online_count': 0
        })

@login_required
def game_catalog(request):
    """Отображение каталога игр"""
    logger.info(f"[VIEW] Доступ к каталогу игр: {request.path}")
    games = Game.objects.all().order_by('title')
    
    # Группируем игры по первой букве для алфавитного списка
    games_by_letter = {}
    for game in games:
        first_letter = game.title[0].upper()
        if first_letter not in games_by_letter:
            games_by_letter[first_letter] = []
        games_by_letter[first_letter].append(game)
    
    # Сортируем буквы алфавита
    sorted_letters = sorted(games_by_letter.keys())
    
    # Подсчет количества предложений
    total_offers = Offer.objects.filter(is_tradable=True).count()
    
    # Подсчет пользователей онлайн
    online_users = UserProfile.objects.filter(online_status=True).count()
    
    context = {
        'games': games,
        'games_by_letter': games_by_letter,
        'sorted_letters': sorted_letters,
        'total_games': games.count(),
        'total_offers': total_offers,
        'online_users': online_users
    }
    
    return render(request, 'gameapp/game_catalog.html', context)

@login_required
def offer_listing(request):
    """Расширенное представление для списка предложений с фильтрацией"""
    logger.info(f"[VIEW] Доступ к расширенному списку предложений: {request.path}")
    
    # Базовый QuerySet предложений
    offers = Offer.objects.filter(is_tradable=True).order_by('-created_at')
    
    # Получаем параметры фильтров из GET-запроса
    game_id = request.GET.get('game')
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    server_id = request.GET.get('server')
    quality = request.GET.get('quality')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    seller_id = request.GET.get('seller')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', '-created_at')  # По умолчанию сортировка по дате (новые сверху)
    
    # Применяем фильтры, если они указаны
    filter_applied = False
    
    if game_id:
        offers = offers.filter(game_id=game_id)
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по игре ID: {game_id}")
    
    if category_id:
        offers = offers.filter(category_id=category_id)
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по категории ID: {category_id}")
    
    if subcategory_id:
        offers = offers.filter(subcategory_id=subcategory_id)
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по подкатегории ID: {subcategory_id}")
    
    if server_id:
        offers = offers.filter(server_id=server_id)
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по серверу ID: {server_id}")
    
    if quality:
        offers = offers.filter(quality=quality)
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по качеству: {quality}")
    
    if min_price:
        offers = offers.filter(price__gte=float(min_price))
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по минимальной цене: {min_price}")
    
    if max_price:
        offers = offers.filter(price__lte=float(max_price))
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по максимальной цене: {max_price}")
    
    if seller_id:
        offers = offers.filter(seller_id=seller_id)
        filter_applied = True
        logger.debug(f"[VIEW] Применен фильтр по продавцу ID: {seller_id}")
    
    if search_query:
        offers = offers.filter(
            Q(item_name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
        filter_applied = True
        logger.debug(f"[VIEW] Применен поиск по запросу: {search_query}")
    
    # Применяем сортировку
    offers = offers.order_by(sort_by)
    
    # Пагинация
    items_per_page = 12
    paginator = Paginator(offers, items_per_page)
    page = request.GET.get('page')
    
    try:
        offers_page = paginator.page(page)
    except PageNotAnInteger:
        offers_page = paginator.page(1)
    except EmptyPage:
        offers_page = paginator.page(paginator.num_pages)
    
    # Получаем данные для фильтров
    games = Game.objects.all().order_by('title')
    categories = GameCategory.objects.filter(is_active=True).order_by('name')
    servers = Server.objects.all().order_by('name')
    
    # Подсчет пользователей онлайн
    online_users = UserProfile.objects.filter(online_status=True).count()
    
    # Подготовка контекста для шаблона
    context = {
        'offers': offers_page,
        'games': games,
        'categories': categories,
        'servers': servers,
        'quality_choices': Offer.ITEM_QUALITY_CHOICES,
        'filter_applied': filter_applied,
        'total_count': paginator.count,
        'current_page': offers_page.number,
        'num_pages': paginator.num_pages,
        'page_range': paginator.page_range,
        'has_previous': offers_page.has_previous(),
        'has_next': offers_page.has_next(),
        'sort_by': sort_by,
        'query_params': request.GET.copy(),
        'online_users': online_users
    }
    
    return render(request, 'gameapp/offer_listing.html', context)

@login_required
def offer_detail(request, offer_id):
    """Представление для детальной страницы предложения"""
    logger.info(f"[VIEW] Доступ к детальной странице предложения ID: {offer_id}")
    
    # Получаем предложение по ID
    offer = get_object_or_404(Offer, id=offer_id)
    
    # Получаем продавца и его профиль
    seller = offer.seller
    try:
        seller_profile = UserProfile.objects.get(user=seller)
        # Обновляем статус онлайн продавца
        seller_profile.update_online_status()
    except UserProfile.DoesNotExist:
        logger.warning(f"[VIEW] Профиль продавца не найден для пользователя {seller.username}")
        seller_profile = None
    
    # Получаем отзывы о данном предложении
    reviews = Review.objects.filter(offer=offer).order_by('-created_at')
    
    # Вычисляем средний рейтинг
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Получаем другие предложения продавца (исключаем текущее)
    other_offers = Offer.objects.filter(seller=seller).exclude(id=offer_id).order_by('-created_at')[:5]
    
    # Получаем похожие предложения (в той же категории/подкатегории)
    similar_offers = Offer.objects.filter(
        Q(game=offer.game) & 
        (Q(category=offer.category) | Q(subcategory=offer.subcategory))
    ).exclude(id=offer_id).order_by('-created_at')[:5]
    
    # Контекст для шаблона
    context = {
        'offer': offer,
        'seller': seller,
        'seller_profile': seller_profile,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'other_offers': other_offers,
        'similar_offers': similar_offers,
        'is_owner': request.user == seller,
    }
    
    # Если пользователь не является владельцем предложения, записываем просмотр
    if request.user != seller:
        # Здесь можно добавить логику для отслеживания просмотров
        logger.debug(f"[VIEW] Пользователь {request.user.username} просмотрел предложение ID: {offer_id}")
        
        # Записываем активность просмотра предложения
        record_user_activity(
            request.user, 
            'offer_view', 
            details={'offer_id': offer.id, 'offer_name': offer.item_name},
            related_object_id=offer.id,
            related_object_type='Offer'
        )
    
    return render(request, 'gameapp/offer_detail.html', context)

@login_required
@require_POST
def send_voice_message(request, conversation_id):
    """API: Отправить голосовое сообщение"""
    try:
        logger.info(f"[CHAT:VOICE_MESSAGE] Запрос на отправку голосового сообщения в диалог ID: {conversation_id} от пользователя {request.user.username}")
        
        # Проверяем, существует ли беседа и имеет ли пользователь к ней доступ
        conversation = get_object_or_404(
            Conversation,
            Q(initiator=request.user) | Q(receiver=request.user),
            id=conversation_id
        )
        
        logger.debug(f"[CHAT:VOICE_MESSAGE] Найден диалог ID: {conversation_id} между {conversation.initiator.username} и {conversation.receiver.username}")
        
        # Получаем аудиофайл и продолжительность
        voice_file = request.FILES.get('voice')
        duration = int(request.POST.get('duration', 0))
        
        file_size = voice_file.size if voice_file else 0
        logger.debug(f"[CHAT:VOICE_MESSAGE] Получен голосовой файл размером {file_size} байт, длительность {duration}с")
        
        if not voice_file:
            logger.warning(f"[CHAT:VOICE_MESSAGE] Попытка отправки пустого голосового сообщения в диалог ID: {conversation_id}")
            return JsonResponse({'error': 'Голосовое сообщение не найдено'}, status=400)
        
        # Определяем получателя сообщения
        recipient = conversation.receiver if conversation.initiator == request.user else conversation.initiator
        logger.debug(f"[CHAT:VOICE_MESSAGE] Получатель голосового сообщения: {recipient.username}")
        
        # Создаем новое сообщение
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            recipient=recipient,
            is_read=False,
            voice=voice_file,
            voice_duration=duration
        )
        
        # Обновляем время последнего обновления беседы
        prev_update_time = conversation.updated_at
        conversation.updated_at = timezone.now()
        conversation.save()
        
        logger.debug(f"[CHAT:VOICE_MESSAGE] Обновлено время последнего обновления диалога с {prev_update_time} на {conversation.updated_at}")
        logger.info(f"[CHAT:VOICE_MESSAGE] Голосовое сообщение ID: {message.id} успешно отправлено в диалог ID: {conversation_id}")
        
        # Записываем активность
        details = {
            'message_id': message.id,
            'conversation_id': conversation.id,
            'duration': duration,
            'file_size': file_size
        }
        record_user_activity(request.user, 'message_sent', details=details, related_object_id=message.id, related_object_type='Message')
        
        # Возвращаем данные о созданном сообщении
        return JsonResponse({
            'id': message.id,
            'content': None,
            'created_at': message.created_at.isoformat(),
            'sender_id': message.sender.id,
            'is_read': message.is_read,
            'images': [],
            'file': None,
            'voice': {
                'url': message.voice.url,
                'duration': message.voice_duration
            }
        })
    except Exception as e:
        logger.error(f"[CHAT:VOICE_MESSAGE] Ошибка при отправке голосового сообщения: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)