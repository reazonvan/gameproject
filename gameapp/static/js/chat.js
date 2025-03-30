// Глобальные переменные
let currentChatId = null;
let currentUserId = null;
let lastMessageId = null;
let messagesContainer = document.getElementById('messages-container');
let activeConversation = null;
let isTyping = false;
let typingTimer = null;
let lastTypingTime = 0;
let unreadMessagesCount = 0;
let lastMessageTime = null;
let debugMode = false;

// Настройка логирования
const Logger = {
    // Уровни логирования
    LEVELS: {
        DEBUG: 0,
        INFO: 1,
        WARNING: 2,
        ERROR: 3
    },
    
    // Текущий уровень логирования
    currentLevel: 1, // По умолчанию INFO
    
    // Логи для буферизации перед отправкой
    logBuffer: [],
    
    // Максимальный размер буфера
    maxBufferSize: 10,
    
    // Флаг включения отправки логов на сервер
    enableServerLogging: true,
    
    /**
     * Инициализация логгера
     */
    init: function(options = {}) {
        console.log('[Logger] Инициализация клиентского логгера');
        
        // Применяем пользовательские настройки
        if (options.level !== undefined) this.currentLevel = options.level;
        if (options.maxBufferSize !== undefined) this.maxBufferSize = options.maxBufferSize;
        if (options.enableServerLogging !== undefined) this.enableServerLogging = options.enableServerLogging;
        
        // Устанавливаем обработчик для отправки логов перед закрытием страницы
        window.addEventListener('beforeunload', () => {
            this.flush(true); // Принудительно отправляем все логи
        });
        
        // Запускаем периодическую отправку логов
        setInterval(() => this.flush(), 30000); // Каждые 30 секунд
        
        this.info('Логгер клиентской части инициализирован', {
            userAgent: navigator.userAgent,
            screenSize: `${window.innerWidth}x${window.innerHeight}`
        });
    },
    
    /**
     * Добавление записи в лог уровня DEBUG
     */
    debug: function(message, data = {}) {
        if (this.currentLevel <= this.LEVELS.DEBUG) {
            this._log('DEBUG', message, data);
        }
    },
    
    /**
     * Добавление записи в лог уровня INFO
     */
    info: function(message, data = {}) {
        if (this.currentLevel <= this.LEVELS.INFO) {
            this._log('INFO', message, data);
        }
    },
    
    /**
     * Добавление записи в лог уровня WARNING
     */
    warning: function(message, data = {}) {
        if (this.currentLevel <= this.LEVELS.WARNING) {
            this._log('WARNING', message, data);
        }
    },
    
    /**
     * Добавление записи в лог уровня ERROR
     */
    error: function(message, data = {}) {
        if (this.currentLevel <= this.LEVELS.ERROR) {
            this._log('ERROR', message, data);
            
            // Для ошибок отправляем логи сразу
            this.flush();
        }
    },
    
    /**
     * Внутренний метод для записи лога
     */
    _log: function(level, message, data) {
        // Создаем запись лога
        const logEntry = {
            level: level,
            message: message,
            data: data,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            sessionId: this._getSessionId()
        };
        
        // Выводим в консоль браузера
        console.log(`[${level}] ${message}`, data);
        
        // Добавляем в буфер для отправки на сервер
        if (this.enableServerLogging) {
            this.logBuffer.push(logEntry);
            
            // Если буфер заполнен, отправляем логи
            if (this.logBuffer.length >= this.maxBufferSize) {
                this.flush();
            }
        }
    },
    
    /**
     * Отправка накопленных логов на сервер
     */
    flush: function(force = false) {
        if (!this.enableServerLogging || this.logBuffer.length === 0) {
            return;
        }
        
        // Если не принудительная отправка и буфер слишком мал, пропускаем
        if (!force && this.logBuffer.length < Math.ceil(this.maxBufferSize / 2)) {
            return;
        }
        
        // Копируем и очищаем буфер
        const logsToSend = [...this.logBuffer];
        this.logBuffer = [];
        
        // Отправляем логи на сервер
        fetch('/api/logs/client/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this._getCsrfToken()
            },
            body: JSON.stringify({ logs: logsToSend }),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                // Если ошибка, возвращаем логи в буфер
                this.logBuffer = logsToSend.concat(this.logBuffer);
                console.error(`Ошибка отправки логов: ${response.status}`);
            }
        })
        .catch(error => {
            // Если ошибка, возвращаем логи в буфер
            this.logBuffer = logsToSend.concat(this.logBuffer);
            console.error(`Ошибка отправки логов: ${error}`);
        });
    },
    
    /**
     * Получение идентификатора сессии
     */
    _getSessionId: function() {
        let sessionId = sessionStorage.getItem('chat_session_id');
        if (!sessionId) {
            sessionId = 'session_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('chat_session_id', sessionId);
        }
        return sessionId;
    },
    
    /**
     * Получение CSRF-токена из cookies
     */
    _getCsrfToken: function() {
        return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
    }
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация логгера
    Logger.init({
        level: debugMode ? Logger.LEVELS.DEBUG : Logger.LEVELS.INFO,
        maxBufferSize: 20
    });
    
    Logger.info('Страница чата загружена');
    
    // Инициализация обработчиков событий
    setupEventListeners();
    
    // Обновление статуса пользователя
    updateUserStatus('online');
    
    // Загрузка списка контактов
    loadContactsList();
    
    // Загрузка списка диалогов
    loadConversationsList();
    
    // Периодическое обновление статуса
    setInterval(function() {
        updateUserStatus('heartbeat');
    }, 30000); // Каждые 30 секунд
    
    // Обработчик перед закрытием страницы
    window.addEventListener('beforeunload', function() {
        Logger.info('Закрытие страницы чата');
        updateUserStatus('offline');
    });
});

/**
 * Настройка обработчиков событий
 */
function setupEventListeners() {
    Logger.debug('Настройка обработчиков событий');
    
    // Обработчик клика по контакту
    document.querySelectorAll('.contact-item').forEach(function(item) {
        item.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            Logger.info('Клик по контакту', { userId: userId });
            loadConversation(userId);
        });
    });
    
    // Обработчик отправки сообщения
    const messageForm = document.getElementById('message-form');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendMessage();
        });
    }
    
    // Обработчик набора текста
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.addEventListener('input', function() {
            handleTypingIndicator();
        });
        
        messageInput.addEventListener('focus', function() {
            Logger.debug('Фокус на поле ввода сообщения');
            markMessagesAsRead();
        });
    }
    
    // Обработчик кнопки отправки
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendMessage();
        });
    }
    
    // Обработчик поиска
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            Logger.debug('Поиск контактов', { query: this.value });
            filterContacts(this.value);
        });
    }
    
    Logger.debug('Обработчики событий настроены');
}

/**
 * Загрузка списка контактов
 */
function loadContactsList() {
    Logger.info('Загрузка списка контактов');
    
    fetch('/api/contacts/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки контактов');
            }
            return response.json();
        })
        .then(data => {
            Logger.debug('Получены данные контактов', { count: data.contacts.length });
            renderContactsList(data.contacts);
        })
        .catch(error => {
            Logger.error('Ошибка при загрузке контактов', { error: error.message });
            showError('Не удалось загрузить список контактов');
        });
}

/**
 * Загрузка списка диалогов
 */
function loadConversationsList() {
    Logger.info('Загрузка списка диалогов');
    
    fetch('/api/conversations/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки диалогов');
            }
            return response.json();
        })
        .then(data => {
            Logger.debug('Получены данные диалогов', { count: data.conversations.length });
            renderConversationsList(data.conversations);
            
            // Если есть активный диалог в URL, открываем его
            const urlParams = new URLSearchParams(window.location.search);
            const conversationId = urlParams.get('conversation_id');
            if (conversationId) {
                Logger.info('Открытие диалога из URL', { conversationId: conversationId });
                openConversation(conversationId);
            }
        })
        .catch(error => {
            Logger.error('Ошибка при загрузке диалогов', { error: error.message });
            showError('Не удалось загрузить список диалогов');
        });
}

/**
 * Загрузка диалога с пользователем
 */
function loadConversation(userId) {
    Logger.info('Загрузка диалога с пользователем', { userId: userId });
    
    // Сохраняем ID пользователя
    currentUserId = userId;
    
    // Показываем индикатор загрузки
    showLoadingIndicator();
    
    fetch(`/api/conversations/${userId}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки диалога');
            }
            return response.json();
        })
        .then(data => {
            Logger.debug('Получены данные диалога', { 
                conversationId: data.conversation_id,
                messagesCount: data.messages.length 
            });
            
            // Сохраняем ID текущего диалога
            currentChatId = data.conversation_id;
            
            // Отображаем диалог
            renderConversation(data);
            
            // Обновляем URL
            updateURL(data.conversation_id);
            
            // Отмечаем сообщения как прочитанные
            markMessagesAsRead();
            
            // Обновляем статусы непрочитанных сообщений
            updateUnreadMessagesCount();
        })
        .catch(error => {
            Logger.error('Ошибка при загрузке диалога', { error: error.message, userId: userId });
            showError('Не удалось загрузить диалог');
        })
        .finally(() => {
            // Скрываем индикатор загрузки
            hideLoadingIndicator();
        });
}

/**
 * Отправка сообщения
 */
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    
    if (!content) {
        Logger.warning('Попытка отправки пустого сообщения');
        return;
    }
    
    if (!currentChatId || !currentUserId) {
        Logger.warning('Попытка отправки сообщения без активного диалога');
        showError('Не выбран собеседник');
        return;
    }
    
    Logger.info('Отправка сообщения', { 
        recipientId: currentUserId,
        contentLength: content.length
    });
    
    // Показываем временное сообщение
    const tempMessageId = 'temp-' + Date.now();
    appendTempMessage(content, tempMessageId);
    
    // Очищаем поле ввода
    messageInput.value = '';
    
    // Отправляем сообщение на сервер
    fetch('/api/messages/send/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            recipient_id: currentUserId,
            content: content
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка отправки сообщения');
        }
        return response.json();
    })
    .then(data => {
        Logger.debug('Сообщение успешно отправлено', { messageId: data.id });
        
        // Заменяем временное сообщение на настоящее
        replaceTempMessage(tempMessageId, data);
        
        // Сохраняем ID последнего сообщения
        lastMessageId = data.id;
        
        // Обновляем список диалогов
        updateConversationsListItem(currentChatId, content);
    })
    .catch(error => {
        Logger.error('Ошибка при отправке сообщения', { error: error.message });
        
        // Помечаем временное сообщение как ошибочное
        markTempMessageAsError(tempMessageId);
        
        showError('Не удалось отправить сообщение');
    });
}

/**
 * Отметка сообщений как прочитанных
 */
function markMessagesAsRead() {
    if (!currentChatId) {
        return;
    }
    
    // Находим все непрочитанные сообщения
    const unreadMessages = document.querySelectorAll('.message:not(.message-outgoing):not(.message-read)');
    if (unreadMessages.length === 0) {
        return;
    }
    
    const messageIds = Array.from(unreadMessages).map(message => message.getAttribute('data-message-id'));
    
    Logger.info('Отметка сообщений как прочитанных', { 
        count: messageIds.length,
        conversationId: currentChatId
    });
    
    fetch('/api/messages/mark-read/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            message_ids: messageIds
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка при отметке сообщений');
        }
        return response.json();
    })
    .then(data => {
        Logger.debug('Сообщения отмечены как прочитанные', { 
            markedCount: data.marked_count 
        });
        
        // Отмечаем сообщения как прочитанные в интерфейсе
        unreadMessages.forEach(message => {
            message.classList.add('message-read');
            const statusElement = message.querySelector('.message-status');
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-check-double"></i>';
            }
        });
        
        // Обновляем счетчик непрочитанных
        updateUnreadMessagesCount();
    })
    .catch(error => {
        Logger.error('Ошибка при отметке сообщений как прочитанных', { error: error.message });
    });
}

/**
 * Обновление статуса пользователя
 */
function updateUserStatus(status) {
    Logger.debug('Обновление статуса пользователя', { status: status });
    
    fetch('/api/users/status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            status: status
        })
    })
    .catch(error => {
        Logger.error('Ошибка при обновлении статуса', { error: error.message });
    });
}

/**
 * Обработка индикатора набора текста
 */
function handleTypingIndicator() {
    const now = Date.now();
    
    // Проверяем, прошло ли достаточно времени с последнего события
    if (!isTyping || now - lastTypingTime > 2000) {
        isTyping = true;
        lastTypingTime = now;
        
        // Отправляем событие "набирает текст"
        sendTypingEvent(true);
        
        Logger.debug('Отправлен статус набора текста', { isTyping: true });
    }
    
    // Сбрасываем таймер
    clearTimeout(typingTimer);
    
    // Устанавливаем новый таймер
    typingTimer = setTimeout(function() {
        isTyping = false;
        
        // Отправляем событие "перестал набирать текст"
        sendTypingEvent(false);
        
        Logger.debug('Отправлен статус набора текста', { isTyping: false });
    }, 3000);
}

/**
 * Отправка события набора текста
 */
function sendTypingEvent(isTyping) {
    if (!currentChatId || !currentUserId) {
        return;
    }
    
    fetch('/api/messages/typing/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            conversation_id: currentChatId,
            recipient_id: currentUserId,
            is_typing: isTyping
        })
    })
    .catch(error => {
        Logger.error('Ошибка при отправке статуса набора текста', { error: error.message });
    });
}

/**
 * Обновление количества непрочитанных сообщений
 */
function updateUnreadMessagesCount() {
    Logger.debug('Обновление счетчика непрочитанных сообщений');
    
    fetch('/api/messages/unread-count/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка получения количества непрочитанных сообщений');
            }
            return response.json();
        })
        .then(data => {
            unreadMessagesCount = data.unread_count;
            
            Logger.debug('Получено количество непрочитанных сообщений', { 
                count: unreadMessagesCount 
            });
            
            // Обновляем счетчик в интерфейсе
            updateUnreadBadge(unreadMessagesCount);
        })
        .catch(error => {
            Logger.error('Ошибка при получении количества непрочитанных сообщений', { 
                error: error.message 
            });
        });
}

/**
 * Получение CSRF-токена из куки
 */
function getCsrfToken() {
    return document.querySelector('input[name="csrfmiddlewaretoken"]').value;
}

/**
 * Обработка ошибок
 */
function showError(message) {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = 'notification error';
    notification.textContent = message;
    
    // Добавляем на страницу
    document.body.appendChild(notification);
    
    // Логируем ошибку
    Logger.warning('Показано уведомление об ошибке', { message: message });
    
    // Удаляем через 5 секунд
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Остальные вспомогательные функции для работы с интерфейсом 