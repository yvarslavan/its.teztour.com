// ============================================================================
// БЛОК "АКТИВНЫЕ ЗАЯВКИ" - JavaScript для страницы "Мои заявки"
// ============================================================================

console.log('[MyIssuesActivity] ✅ Файл my_issues_activity.js загружен!');
console.log('[MyIssuesActivity] 🔍 Проверка доступности элементов при загрузке:');
console.log('[MyIssuesActivity] - activity-loading:', !!document.getElementById('activity-loading'));
console.log('[MyIssuesActivity] - activity-empty:', !!document.getElementById('activity-empty'));
console.log('[MyIssuesActivity] - activity-error:', !!document.getElementById('activity-error'));
console.log('[MyIssuesActivity] - activity-list:', !!document.getElementById('activity-list'));

// Автоматическая загрузка при готовности DOM
document.addEventListener('DOMContentLoaded', function() {
    console.log('[MyIssuesActivity] 🚀 DOM готов, запускаем загрузку активности...');
    setTimeout(loadRecentActivity, 1000); // Небольшая задержка для полной загрузки
});

/**
 * Загрузка последней активности по заявкам
 */
function loadRecentActivity() {
    console.log('[MyIssuesActivity] 🚀 Начало загрузки активности');

    const container = document.getElementById('recent-activity-container');
    const loading = document.getElementById('activity-loading');
    const list = document.getElementById('activity-list');
    const empty = document.getElementById('activity-empty');
    const error = document.getElementById('activity-error');

    console.log('[MyIssuesActivity] 🔍 Проверка элементов:', {
        container: !!container,
        loading: !!loading,
        list: !!list,
        empty: !!empty,
        error: !!error
    });

    if (!container) {
        console.error('[MyIssuesActivity] ❌ Контейнер не найден!');
        return;
    }

    // Показываем спиннер
    loading.style.display = 'flex';
    list.style.display = 'none';
    empty.style.display = 'none';
    error.style.display = 'none';

    // Запрос к API
    console.log('[MyIssuesActivity] 📡 Отправка запроса к API...');
    console.log('[MyIssuesActivity] 🔗 URL запроса: /my-issues/api/recent-activity');

    fetch('/my-issues/api/recent-activity', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin' // Важно для передачи cookies с сессией
    })
        .then(response => {
            console.log('[MyIssuesActivity] 📥 Получен ответ:', response.status, response.statusText);
            console.log('[MyIssuesActivity] 📊 Заголовки ответа:', Object.fromEntries(response.headers.entries()));

            if (!response.ok) {
                console.error('[MyIssuesActivity] ❌ HTTP ошибка:', response.status, response.statusText);
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return response.json();
        })
        .then(data => {
            console.log('[MyIssuesActivity] ✅ Данные получены:', data);
            console.log('[MyIssuesActivity] 📊 Структура ответа:', {
                success: data.success,
                hasData: !!data.data,
                dataLength: data.data ? data.data.length : 0,
                count: data.count,
                error: data.error
            });

            // Детальная отладка - выводим все ключи объекта
            console.log('[MyIssuesActivity] 🔍 Все ключи в ответе:', Object.keys(data));
            console.log('[MyIssuesActivity] 🔍 Полный ответ (JSON):', JSON.stringify(data, null, 2));

            // Детальная отладка данных
            if (data.data && data.data.length > 0) {
                console.log('[MyIssuesActivity] 🔍 Первые 3 записи данных:', data.data.slice(0, 3));
                console.log('[MyIssuesActivity] 🔍 Тип данных:', typeof data.data, Array.isArray(data.data));
            } else {
                console.log('[MyIssuesActivity] ⚠️ Данные пустые или отсутствуют');
            }

            // Скрываем спиннер ВСЕГДА
            loading.style.display = 'none';

            if (!data.success) {
                // Проверяем, не является ли это случаем отсутствия данных
                // Если ошибка связана с отсутствием данных, показываем пустой блок
                if (data.error && (
                    data.error.includes('нет данных') ||
                    data.error.includes('не найдено') ||
                    data.error.includes('пустой') ||
                    data.error.includes('отсутствует')
                )) {
                    console.log('[MyIssuesActivity] 📭 Нет активности (обработано как пустой результат)');
                    empty.style.display = 'flex';
                    list.style.display = 'none';
                    error.style.display = 'none';
                    updateActivityCount(0);
                    return;
                }

                // Реальная ошибка загрузки данных
                console.error('[MyIssuesActivity] ❌ Ошибка получения данных:', data.error);
                error.style.display = 'flex';
                return;
            }

            // Проверяем данные в разных возможных полях
            const activityData = data.data || data.activity || data.issues || [];
            console.log('[MyIssuesActivity] 🔍 Проверка данных:', {
                'data.data': data.data,
                'data.activity': data.activity,
                'data.issues': data.issues,
                'activityData': activityData,
                'activityDataLength': activityData.length
            });

            if (!activityData || activityData.length === 0) {
                // Нет данных - показываем пустой блок
                console.log('[MyIssuesActivity] 📭 Нет активности - показываем пустой блок');
                empty.style.display = 'flex';
                list.style.display = 'none';
                error.style.display = 'none';
                updateActivityCount(0);

                console.log('[MyIssuesActivity] 📊 Состояние элементов для пустого состояния:', {
                    loading: loading.style.display,
                    empty: empty.style.display,
                    error: error.style.display,
                    list: list.style.display
                });
                return;
            }

            // Отображаем список
            console.log(`[MyIssuesActivity] 📋 Отображаем список активности: ${activityData.length} записей`);
            empty.style.display = 'none';
            error.style.display = 'none';
            renderActivityList(activityData);
            list.style.display = 'block';
            updateActivityCount(activityData.length);
        })
        .catch(err => {
            console.error('[MyIssuesActivity] ❌ Ошибка загрузки:', err);
            console.error('[MyIssuesActivity] ❌ Тип ошибки:', typeof err);
            console.error('[MyIssuesActivity] ❌ Сообщение ошибки:', err.message);
            console.error('[MyIssuesActivity] ❌ Стек ошибки:', err.stack);

            loading.style.display = 'none';

            // Если это ошибка сети или сервера, показываем ошибку
            // Но если это может быть связано с отсутствием данных,
            // можно показать пустой блок (закомментировано для безопасности)
            error.style.display = 'flex';
            empty.style.display = 'none';
            list.style.display = 'none';

            console.log('[MyIssuesActivity] 📊 Состояние элементов после ошибки:', {
                loading: loading.style.display,
                empty: empty.style.display,
                error: error.style.display,
                list: list.style.display
            });
        });
}

/**
 * Отрисовка списка активности
 */
function renderActivityList(activities) {
    const list = document.getElementById('activity-list');
    if (!list) return;

    list.innerHTML = '';

    activities.forEach(activity => {
        const item = createActivityItem(activity);
        list.appendChild(item);
    });

    console.log(`[MyIssuesActivity] Отрисовано ${activities.length} элементов`);
}

/**
 * Создание элемента активности
 */
function createActivityItem(activity) {
    const item = document.createElement('div');
    item.className = 'activity-item';
    item.setAttribute('data-activity-type', activity.activity_type);

    // Определяем цвет иконки в зависимости от типа активности
    const iconColors = {
        'status': '#3b82f6',      // синий
        'comment': '#10b981',     // зеленый
        'priority': '#f59e0b',    // оранжевый
        'assigned': '#8b5cf6',    // фиолетовый
        'description': '#6b7280', // серый
        'attachment': '#14b8a6',  // бирюзовый
        'update': '#3b82f6'       // синий
    };

    const iconColor = iconColors[activity.activity_type] || '#6b7280';

    item.innerHTML = `
        <div class="activity-icon-wrapper">
            <i class="fas fa-clock activity-icon-simple" style="color: ${iconColor};"></i>
        </div>
        <div class="activity-content">
            <div class="activity-main">
                <a href="/my-issues/${activity.issue_id}" class="activity-issue-link">
                    <span class="activity-issue-id">#${activity.issue_id}</span>
                    <span class="activity-subject">${escapeHtml(activity.subject)}</span>
                </a>
            </div>
            <div class="activity-meta">
                <span class="activity-type-text">${activity.activity_text}</span>
                <span class="activity-separator">•</span>
                <span class="activity-time">${activity.time_ago}</span>
            </div>
            <div class="activity-details">
                <span class="activity-status">
                    <i class="fas fa-circle" style="font-size: 8px; color: ${iconColor};"></i>
                    ${activity.status_name}
                </span>
            </div>
        </div>
    `;

    return item;
}

/**
 * Экранирование HTML для безопасности
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Автообновление активности каждые 2 минуты
 */
function startActivityAutoRefresh() {
    // Загружаем сразу при загрузке страницы
    loadRecentActivity();

    // Обновляем каждые 2 минуты (120000 мс)
    setInterval(loadRecentActivity, 120000);

    console.log('[MyIssuesActivity] Автообновление запущено (каждые 2 минуты)');
}

/**
 * Инициализация аккордеона
 */
function initActivityAccordion() {
    const header = document.getElementById('activity-accordion-toggle');
    const content = document.getElementById('activity-accordion-content');

    if (!header || !content) {
        console.error('[MyIssuesActivity] Элементы аккордеона не найдены');
        return;
    }

    // По умолчанию аккордеон открыт
    header.classList.add('active');
    content.classList.add('active');

    // Обработчик клика
    header.addEventListener('click', function() {
        const isActive = header.classList.contains('active');

        if (isActive) {
            // Закрываем
            header.classList.remove('active');
            content.classList.remove('active');
        } else {
            // Открываем
            header.classList.add('active');
            content.classList.add('active');
        }
    });

    console.log('[MyIssuesActivity] Аккордеон инициализирован');
}

/**
 * Обновление счетчика активности
 */
function updateActivityCount(count) {
    const badge = document.getElementById('activity-count-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Запускаем загрузку активности при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('[MyIssuesActivity] DOM загружен, запуск инициализации');
    initActivityAccordion();
    startActivityAutoRefresh();
});
