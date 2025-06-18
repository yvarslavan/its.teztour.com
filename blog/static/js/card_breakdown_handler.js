// Модуль CardBreakdown - обработчик детализации карточек статусов
console.log('[CardBreakdown] 🔧 Инициализация обработчика детализации карточек');

// Объект для экспорта функций
window.CardBreakdown = window.CardBreakdown || {};

// Инициализация при загрузке документа
$(document).ready(function() {
    console.log('[CardBreakdown] 🚀 Инициализация всех компонентов');

    // Инициализируем компоненты
    initializeCardToggles();
    initializeGlobalToggle();
    initializeBreakdownToggle();
    forceApplyStyles();

    console.log('[CardBreakdown] ✅ Все компоненты инициализированы');
});

// Инициализация кнопок переключения детализации карточек
function initializeCardToggles() {
    console.log('[CardBreakdown] 🔧 Инициализация кнопок переключения детализации');

    // Удаляем все существующие обработчики событий
    $('.card-toggle-btn').off('click');

    // Добавляем новые обработчики
    $('.card-toggle-btn').each(function() {
        const targetId = $(this).data('target');
        console.log(`[CardBreakdown] ✅ Добавлен обработчик для кнопки детализации "${targetId}"`);

        $(this).on('click', function(e) {
            e.preventDefault(); // Предотвращаем стандартное действие
            e.stopPropagation(); // Останавливаем всплытие события
            toggleCardBreakdown(targetId, $(this));
            return false; // Дополнительная защита от всплытия
        });
    });
}

// Инициализация глобальной кнопки переключения всех карточек
function initializeGlobalToggle() {
    console.log('[CardBreakdown] 🔧 Инициализация глобальной кнопки переключения');

    const globalBtn = $('#globalToggleBtn');
    if (globalBtn.length > 0) {
        // Удаляем существующие обработчики
        globalBtn.off('click');

        // Добавляем новый обработчик
        globalBtn.on('click', function(e) {
            e.preventDefault(); // Предотвращаем стандартное действие
            e.stopPropagation(); // Останавливаем всплытие события
            toggleAllBreakdowns();
            return false; // Дополнительная защита от всплытия
        });
        console.log('[CardBreakdown] ✅ Добавлен обработчик для глобальной кнопки переключения');
    }

    // Устанавливаем начальное состояние кнопки
    updateGlobalButtonState();
    console.log('[CardBreakdown] ✅ Глобальная кнопка в состоянии "Развернуть все"');
}

// Инициализация кнопки детальной разбивки
function initializeBreakdownToggle() {
    console.log('[CardBreakdown] 🔧 Инициализация кнопки детальной разбивки');

    const expandBtn = $('#expandBreakdownBtn');
    if (expandBtn.length > 0) {
        // Удаляем существующие обработчики
        expandBtn.off('click');

        // Добавляем новый обработчик
        expandBtn.on('click', function(e) {
            e.preventDefault(); // Предотвращаем стандартное действие
            e.stopPropagation(); // Останавливаем всплытие события
            toggleDetailedBreakdown();
            return false; // Дополнительная защита от всплытия
        });
        console.log('[CardBreakdown] ✅ Добавлен обработчик для кнопки детальной разбивки');
    }
}

// Переключение карточки детализации
function toggleCardBreakdown(targetId, button) {
    console.log(`[CardBreakdown] 🔄 Переключение карточки детализации: ${targetId}`);

    const target = $('#' + targetId);

    if (target.length === 0) {
        console.error(`[CardBreakdown] ❌ Целевой элемент #${targetId} не найден!`);
        return;
    }

    // Проверяем текущее состояние
    const isCollapsed = target.hasClass('collapsed');
    console.log(`[CardBreakdown] 🔍 Текущее состояние: ${isCollapsed ? 'свернуто' : 'развернуто'}`);

    // Переключаем классы
    if (isCollapsed) {
        // Разворачиваем
        target.removeClass('collapsed').addClass('expanded');
        button.addClass('expanded');

        // Принудительно применяем стили
        target.css({
            'max-height': '150px',
            'opacity': '1',
            'padding-top': '0.75rem',
            'padding-bottom': '0.75rem',
            'margin-top': '0.75rem',
            'border-top': '1px solid rgba(226, 232, 240, 0.5)',
            'transform': 'translateY(0)',
            'overflow-y': 'auto',
            'pointer-events': 'auto',
            'visibility': 'visible',
            'display': 'block'
        });

        button.find('i').css('transform', 'rotate(180deg)');
        console.log(`[CardBreakdown] ✅ Карточка #${targetId} РАЗВЕРНУТА`);
    } else {
        // Сворачиваем
        target.removeClass('expanded').addClass('collapsed');
        button.removeClass('expanded');

        // Принудительно применяем стили
        target.css({
            'max-height': '0',
            'opacity': '0',
            'padding-top': '0',
            'padding-bottom': '0',
            'margin-top': '0',
            'border-top': 'none',
            'transform': 'translateY(-10px)',
            'pointer-events': 'none',
            'visibility': 'hidden',
            'display': 'block'
        });

        button.find('i').css('transform', 'rotate(0deg)');
        console.log(`[CardBreakdown] ✅ Карточка #${targetId} СВЕРНУТА`);
    }

    // Обновляем состояние глобальной кнопки
    updateGlobalButtonState();

    // Принудительно переназначаем обработчики событий
    setTimeout(function() {
        initializeCardToggles();
    }, 50);
}

// Переключение всех карточек детализации
function toggleAllBreakdowns() {
    const globalBtn = $('#globalToggleBtn');
    const isAllCollapsed = globalBtn.hasClass('collapsed-state');

    console.log(`[CardBreakdown] 🔄 Переключение ВСЕХ детализаций (${$('.card-breakdown').length}), expand=${isAllCollapsed}`);

    // Определяем новое состояние
    if (isAllCollapsed) {
        // Разворачиваем все
        $('.card-breakdown').each(function() {
            const cardBreakdown = $(this);
            cardBreakdown.removeClass('collapsed').addClass('expanded');

            // Принудительно применяем стили к каждой карточке
            cardBreakdown.css({
                'max-height': '150px',
                'opacity': '1',
                'padding-top': '0.75rem',
                'padding-bottom': '0.75rem',
                'margin-top': '0.75rem',
                'border-top': '1px solid rgba(226, 232, 240, 0.5)',
                'transform': 'translateY(0)',
                'overflow-y': 'auto',
                'pointer-events': 'auto',
                'visibility': 'visible',
                'display': 'block'
            });
        });

        // Обновляем состояние кнопок переключения
        $('.card-toggle-btn').addClass('expanded');
        $('.card-toggle-btn i').css('transform', 'rotate(180deg)');

        // Обновляем состояние глобальной кнопки
        globalBtn.removeClass('collapsed-state').addClass('expanded-state');
        globalBtn.find('span').text('Свернуть все');
        globalBtn.find('i').removeClass('fa-expand-alt').addClass('fa-compress-alt');
        console.log('[CardBreakdown] ✅ Глобальная кнопка в состоянии "Свернуть все"');
    } else {
        // Сворачиваем все
        $('.card-breakdown').each(function() {
            const cardBreakdown = $(this);
            cardBreakdown.removeClass('expanded').addClass('collapsed');

            // Принудительно применяем стили к каждой карточке
            cardBreakdown.css({
                'max-height': '0',
                'opacity': '0',
                'padding-top': '0',
                'padding-bottom': '0',
                'margin-top': '0',
                'border-top': 'none',
                'transform': 'translateY(-10px)',
                'pointer-events': 'none',
                'visibility': 'hidden',
                'display': 'block'
            });
        });

        // Обновляем состояние кнопок переключения
        $('.card-toggle-btn').removeClass('expanded');
        $('.card-toggle-btn i').css('transform', 'rotate(0deg)');

        // Обновляем состояние глобальной кнопки
        globalBtn.removeClass('expanded-state').addClass('collapsed-state');
        globalBtn.find('span').text('Развернуть все');
        globalBtn.find('i').removeClass('fa-compress-alt').addClass('fa-expand-alt');
        console.log('[CardBreakdown] ✅ Глобальная кнопка в состоянии "Развернуть все"');
    }

    console.log('[CardBreakdown] ✅ Состояние ВСЕХ детализаций обновлено');
    console.log(`[CardBreakdown] 🔄 Глобальное переключение, развернуть=${isAllCollapsed}`);
}

// Обновление состояния глобальной кнопки на основе состояния карточек
function updateGlobalButtonState() {
    const globalBtn = $('#globalToggleBtn');
    if (globalBtn.length === 0) return;

    const totalCards = $('.card-breakdown').length;
    const expandedCards = $('.card-breakdown.expanded').length;

    if (expandedCards === 0) {
        // Все свернуты
        globalBtn.removeClass('expanded-state').addClass('collapsed-state');
        globalBtn.find('span').text('Развернуть все');
        globalBtn.find('i').removeClass('fa-compress-alt').addClass('fa-expand-alt');
    } else if (expandedCards === totalCards) {
        // Все развернуты
        globalBtn.removeClass('collapsed-state').addClass('expanded-state');
        globalBtn.find('span').text('Свернуть все');
        globalBtn.find('i').removeClass('fa-expand-alt').addClass('fa-compress-alt');
    }
}

// Функция для переключения детальной разбивки
function toggleDetailedBreakdown() {
    console.log('[CardBreakdown] 🔄 Переключение детальной разбивки');

    const detailedBreakdownContent = document.getElementById('detailedBreakdownContent');
    const expandBreakdownBtn = document.getElementById('expandBreakdownBtn');
    const statusItemsGrid = document.getElementById('statusItemsGrid');

    if (!detailedBreakdownContent || !expandBreakdownBtn) {
        console.warn('[CardBreakdown] ⚠️ Элементы детальной разбивки не найдены');
        return;
    }

    // Проверяем текущее состояние
    const isExpanded = detailedBreakdownContent.classList.contains('expanded');

    if (!isExpanded) {
        // Разворачиваем детальную разбивку
        console.log('[CardBreakdown] 🔄 Обновление содержимого разбивки по статусам');

        // Используем сохраненные данные из API (window.detailedStatusData)
        if (window.detailedStatusData) {
            console.log('[CardBreakdown] 📊 Используем данные из API:', window.detailedStatusData);
            renderDetailedBreakdown(window.detailedStatusData);
        } else {
            console.warn('[CardBreakdown] ⚠️ Данные для детальной разбивки недоступны');
            if (statusItemsGrid) {
                statusItemsGrid.innerHTML = '<div class="no-data">Нет данных для отображения</div>';
            }
        }

        // Разворачиваем контент
        detailedBreakdownContent.classList.add('expanded');
        expandBreakdownBtn.innerHTML = '<i class="fas fa-chevron-up"></i><span>Скрыть детали</span>';

        console.log('[CardBreakdown] ✅ Детальная разбивка РАЗВЕРНУТА');
    } else {
        // Сворачиваем детальную разбивку
        detailedBreakdownContent.classList.remove('expanded');
        expandBreakdownBtn.innerHTML = '<i class="fas fa-chevron-down"></i><span>Показать детали</span>';

        console.log('[CardBreakdown] ✅ Детальная разбивка СВЕРНУТА');
    }
}

/**
 * Отображает детальную разбивку по статусам в виде сетки элементов
 * @param {Object} statusCounts - Объект с данными о количестве задач по статусам
 */
function renderDetailedBreakdown(statusCounts) {
    console.log('[CardBreakdown] 🔄 Отрисовка разбивки по статусам');

    const grid = document.getElementById('statusItemsGrid');
    if (!grid) {
        console.error('[CardBreakdown] ⚠️ Контейнер #statusItemsGrid не найден');
        return;
    }

    // Очищаем предыдущее содержимое
    grid.innerHTML = '';

    if (!statusCounts || Object.keys(statusCounts).length === 0) {
        grid.innerHTML = '<div class="no-data">Нет данных для отображения</div>';
        console.warn('[CardBreakdown] ⚠️ Нет данных для отображения');
        return;
    }

    // Создаем массив пар [статус, количество] и сортируем по убыванию количества
    const sortedStatuses = Object.entries(statusCounts)
        .filter(([_, count]) => count > 0)  // Только статусы с ненулевым количеством
        .sort((a, b) => b[1] - a[1]);       // Сортировка по убыванию

    // Отображаем каждый статус как плитку в сетке
    sortedStatuses.forEach(([status, count]) => {
        // Определяем класс статуса для стилизации
        const statusClass = getStatusClass(status);

        // Создаем элемент
        const statusItem = document.createElement('div');
        statusItem.className = `status-item ${statusClass}`;

        // Создаем содержимое с анимацией счетчика
        statusItem.innerHTML = `
            <div class="status-count">${count}</div>
            <div class="status-name">${status}</div>
            <div class="status-badge"></div>
        `;

        // Добавляем в сетку
        grid.appendChild(statusItem);
    });

    console.log(`[CardBreakdown] ✅ Детальная разбивка отрендерена: ${sortedStatuses.length} элементов`);
}

/**
 * Определяет CSS-класс для стилизации плитки статуса
 * @param {string} statusName - Название статуса
 * @returns {string} CSS-класс для стилизации
 */
function getStatusClass(statusName) {
    // Приводим название статуса к нижнему регистру для сравнения
    const status = statusName.toLowerCase();

    // Новые и открытые задачи
    if (status.includes('нов') || status.includes('new') ||
        status.includes('открыт') || status.includes('open')) {
        return 'status-new';
    }

    // Закрытые и отклоненные задачи
    else if (status.includes('закрыт') || status.includes('closed') ||
             status.includes('reject') || status.includes('отклон')) {
        return 'status-closed';
    }

    // Перенаправленные задачи
    else if (status.includes('redirect') || status.includes('перенаправ')) {
        return 'status-redirected';
    }

    // Выполненные задачи
    else if (status.includes('выполн') || status.includes('executed') ||
             status.includes('resolved') || status.includes('решен')) {
        return 'status-executed';
    }

    // Задачи на тестировании
    else if (status.includes('тест') || status.includes('test')) {
        return 'status-testing';
    }

    // Приостановленные и замороженные задачи
    else if (status.includes('приостановл') || status.includes('paused') ||
             status.includes('заморож') || status.includes('frozen')) {
        return 'status-paused';
    }

    // Задачи в процессе и в работе
    else if (status.includes('в работе') || status.includes('progress') ||
             status.includes('процесс') || status.includes('in ')) {
        return 'status-progress';
    }

    // Задачи на согласовании и координации
    else if (status.includes('согласован') || status.includes('координации') ||
             status.includes('coordination')) {
        return 'status-coordination';
    }

    // Специфические задачи
    else if (status.includes('specification') || status.includes('специфик')) {
        return 'status-specification';
    }

    // Для всех остальных статусов
    return 'status-other';
}

// Применение стилей принудительно
function forceApplyStyles() {
    console.log('[CardBreakdown] 🔧 Принудительное применение стилей к элементам детализации');

    // Применяем стили к карточкам
    $('.card-breakdown').each(function() {
        const cardBreakdown = $(this);

        // Убеждаемся, что карточка имеет один из классов состояния
        if (!cardBreakdown.hasClass('collapsed') && !cardBreakdown.hasClass('expanded')) {
            cardBreakdown.addClass('collapsed');
            console.log('[CardBreakdown] ⚠️ Карточка без состояния, добавлен класс collapsed');
        }

        if (cardBreakdown.hasClass('expanded')) {
            cardBreakdown.css({
                'max-height': '150px',
                'opacity': '1',
                'padding-top': '0.75rem',
                'padding-bottom': '0.75rem',
                'margin-top': '0.75rem',
                'border-top': '1px solid rgba(226, 232, 240, 0.5)',
                'transform': 'translateY(0)',
                'overflow-y': 'auto',
                'pointer-events': 'auto',
                'visibility': 'visible',
                'display': 'block'
            });

            // Находим соответствующую кнопку
            const targetId = cardBreakdown.attr('id');
            if (targetId) {
                const button = $(`.card-toggle-btn[data-target="${targetId}"]`);
                if (button.length) {
                    button.addClass('expanded');
                    button.find('i').css('transform', 'rotate(180deg)');
                }
            }
        } else {
            cardBreakdown.css({
                'max-height': '0',
                'opacity': '0',
                'padding-top': '0',
                'padding-bottom': '0',
                'margin-top': '0',
                'border-top': 'none',
                'transform': 'translateY(-10px)',
                'pointer-events': 'none',
                'visibility': 'hidden',
                'display': 'block'
            });

            // Находим соответствующую кнопку
            const targetId = cardBreakdown.attr('id');
            if (targetId) {
                const button = $(`.card-toggle-btn[data-target="${targetId}"]`);
                if (button.length) {
                    button.removeClass('expanded');
                    button.find('i').css('transform', 'rotate(0deg)');
                }
            }
        }
    });

    // Обновляем состояние глобальной кнопки
    updateGlobalButtonState();

    console.log('[CardBreakdown] ✅ Стили принудительно применены к элементам детализации');
}

// Экспортируем функции для использования из других модулей
window.CardBreakdown.renderDetailedBreakdown = renderDetailedBreakdown;
window.CardBreakdown.toggleDetailedBreakdown = toggleDetailedBreakdown;
