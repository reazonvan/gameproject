/**
 * Скрипт для автоматического обновления статусов пользователей
 */

// Интервал обновления статусов (в миллисекундах)
const USER_STATUS_UPDATE_INTERVAL = 10000; // 10 секунд

// Глобальные переменные
let currentUserStatuses = {};
let statusUpdateInterval = null;

/**
 * Инициализация обновления статусов при загрузке страницы
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[UserStatus] Инициализация скрипта обновления статусов пользователей');
    
    // Выполняем первоначальное обновление статусов
    fetchUserStatuses();
    
    // Обновляем общий счетчик пользователей онлайн
    fetchOnlineUsersCount();
    
    // Устанавливаем интервал для периодического обновления
    statusUpdateInterval = setInterval(fetchUserStatuses, USER_STATUS_UPDATE_INTERVAL);
    
    // Устанавливаем интервал для периодического обновления общего счетчика
    setInterval(fetchOnlineUsersCount, USER_STATUS_UPDATE_INTERVAL * 3); // Реже, чем статусы пользователей
    
    // Обновляем статус текущего пользователя как онлайн
    updateCurrentUserStatus('online');
    
    // Обработчик перед закрытием страницы
    window.addEventListener('beforeunload', function() {
        console.log('[UserStatus] Закрытие страницы');
        clearInterval(statusUpdateInterval);
        updateCurrentUserStatus('offline');
    });
});

/**
 * Получение статусов всех пользователей с сервера
 */
function fetchUserStatuses() {
    console.log('[UserStatus] Запрос статусов пользователей');
    
    fetch('/api/users/status/', {
        method: 'GET',
        headers: {
            'X-Debug-Level': 'normal',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка получения статусов пользователей');
        }
        return response.json();
    })
    .then(data => {
        // Обновляем статусы пользователей в DOM
        if (data.users && Array.isArray(data.users)) {
            updateUserStatusDisplay(data.users);
        }
    })
    .catch(error => {
        console.error('[UserStatus] Ошибка при получении статусов пользователей:', error);
    });
}

/**
 * Получение общего количества пользователей онлайн
 */
function fetchOnlineUsersCount() {
    fetch('/api/users/online-count/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Ошибка получения количества пользователей онлайн');
        }
        return response.json();
    })
    .then(data => {
        // Обновляем счетчик пользователей онлайн
        if (data && data.success && data.online_count !== undefined) {
            updateOnlineUsersCount(data.online_count);
            console.log(`[UserStatus] Получено количество пользователей онлайн: ${data.online_count}`);
        }
    })
    .catch(error => {
        console.error('[UserStatus] Ошибка при получении количества пользователей онлайн:', error);
    });
}

/**
 * Обновление счетчика пользователей онлайн
 */
function updateOnlineUsersCount(count) {
    const countElements = document.querySelectorAll('.online-users-count');
    
    countElements.forEach(element => {
        element.textContent = count;
    });
}

/**
 * Обновление статуса текущего пользователя
 */
function updateCurrentUserStatus(status) {
    console.log('[UserStatus] Обновление статуса пользователя:', status);
    
    fetch(`/update_online_status/?action=${status}`, {
        method: 'GET',
        headers: {
            'X-Debug-Level': 'normal',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .catch(error => {
        console.error('[UserStatus] Ошибка при обновлении статуса:', error);
    });
}

/**
 * Обновление отображения статусов пользователей в DOM
 */
function updateUserStatusDisplay(users) {
    if (!users || users.length === 0) return;
    
    users.forEach(user => {
        // Запоминаем предыдущий статус для этого пользователя
        const previousStatus = currentUserStatuses[user.id] || false;
        
        // Если статус изменился, обновляем отображение
        if (previousStatus !== user.online_status) {
            // Сохраняем новый статус
            currentUserStatuses[user.id] = user.online_status;
            
            // Находим все элементы, отображающие статус этого пользователя
            const statusElements = document.querySelectorAll(`[data-user-id="${user.id}"]`);
            
            statusElements.forEach(element => {
                // Элементы с классом user-status (стандартный индикатор)
                if (element.classList.contains('user-status')) {
                    if (user.online_status) {
                        element.classList.remove('offline');
                        element.classList.add('online');
                        const statusText = element.querySelector('.status-text');
                        if (statusText) statusText.textContent = 'Онлайн';
                    } else {
                        element.classList.remove('online');
                        element.classList.add('offline');
                        const statusText = element.querySelector('.status-text');
                        if (statusText) statusText.textContent = 'Офлайн';
                    }
                }
                
                // Элементы с классом badge (значки статуса)
                if (element.classList.contains('badge') || element.classList.contains('badge-status')) {
                    if (user.online_status) {
                        element.classList.remove('bg-secondary', 'badge-offline');
                        element.classList.add('bg-success', 'badge-online');
                        element.textContent = 'Онлайн';
                    } else {
                        element.classList.remove('bg-success', 'badge-online');
                        element.classList.add('bg-secondary', 'badge-offline');
                        element.textContent = 'Офлайн';
                    }
                }
                
                // Элементы с классом seller-badge (значки в карточках товаров)
                if (element.classList.contains('seller-badge')) {
                    if (user.online_status) {
                        element.classList.remove('bg-secondary');
                        element.classList.add('bg-success');
                        element.textContent = 'Онлайн';
                    } else {
                        element.classList.remove('bg-success');
                        element.classList.add('bg-secondary');
                        element.textContent = 'Офлайн';
                    }
                }
                
                // Индикаторы онлайн для аватаров
                if (element.classList.contains('status-indicator')) {
                    if (user.online_status) {
                        element.classList.remove('indicator-offline');
                        element.classList.add('indicator-online');
                    } else {
                        element.classList.remove('indicator-online');
                        element.classList.add('indicator-offline');
                    }
                }
            });
            
            console.log(`[UserStatus] Обновлен статус пользователя ${user.username}: ${user.online_status ? 'онлайн' : 'офлайн'}`);
        }
    });
    
    // Обновляем общий счетчик пользователей онлайн
    const onlineCount = users.filter(user => user.online_status).length;
    const countElements = document.querySelectorAll('.online-users-count');
    
    countElements.forEach(element => {
        element.textContent = onlineCount;
    });
} 