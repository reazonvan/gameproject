# Настройки системы шаблонов Django
TEMPLATES = [
    {  # Словарь с настройками для движка шаблонов
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Используем стандартный движок шаблонов Django
        'DIRS': [],  # Список дополнительных директорий для поиска шаблонов (пустой - ищем только в приложениях)
        'APP_DIRS': True,  # Искать шаблоны в директориях templates внутри приложений
        'OPTIONS': {  # Дополнительные опции для движка шаблонов
            'context_processors': [  # Список процессоров контекста - добавляют переменные в контекст всех шаблонов
                'django.template.context_processors.debug',  # Добавляет переменную debug и sql_queries в контекст
                'django.template.context_processors.request',  # Добавляет объект request в контекст шаблонов
                'django.contrib.auth.context_processors.auth',  # Добавляет переменную user и perms для проверки прав
                'django.contrib.messages.context_processors.messages',  # Добавляет сообщения и уведомления
                'gameapp.context_processors.common_context',  # Пользовательский процессор для общих переменных из gameapp
            ],
        },
    },
] 