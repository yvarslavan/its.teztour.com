/**
 * 🚨 МОДИФИЦИРОВАННАЯ ВЕРСИЯ: ТОЛЬКО ОДНОРАЗОВЫЙ СБРОС ФИЛЬТРОВ
 * Дата: 25.12.2024
 * Версия: FILTER_FIX_FINAL
 */

console.log('🔧 [FIXED] Загружается исправленная версия с однократным сбросом фильтров!');

// Глобальные переменные для работы модуля
let tasksDataTable;
window.tasksTable = null; // Для доступа из других модулей
window.detailedStatusData = {}; // Для хранения данных о статусах задач текущего пользователя

// Глобальная функция для управления видимостью кнопок очистки фильтров
window.updateFilterVisibility = function(selectElement) {
    if (!selectElement || selectElement.length === 0) {
        console.warn('[TasksPaginated] 🔍 updateFilterVisibility: selectElement не найден');
        return;
    }

    const rawValue = selectElement.val();
    const value = rawValue || ''; // Безопасная обработка null/undefined
    const filterId = selectElement.attr('id');
    const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
    const clearBtn = $(clearBtnId);
    const container = selectElement.closest('.filter-container');

    console.log('[TasksPaginated] 🔍 Обновление кнопки очистки:', {
        filterId: filterId,
        rawValue: rawValue,
        value: value,
        valueType: typeof rawValue,
        isEmpty: !value || value === '' || value === 'null',
        clearBtnId: clearBtnId,
        clearBtnExists: clearBtn.length > 0,
        containerExists: container.length > 0
    });

    // Более надежная проверка значения
    const hasValue = value && value !== '' && value !== 'null' && value !== null && value !== undefined;

    if (hasValue) {
        // Используем все возможные способы отображения
        clearBtn.addClass('show');
        clearBtn.css({
            'display': 'flex',
            'visibility': 'visible',
            'opacity': '1',
            'pointer-events': 'auto'
        });

        container.addClass('has-value');

        // Проверка видимости после применения стилей
        setTimeout(() => {
            if (!clearBtn.is(':visible')) {
                console.warn('[TasksPaginated] ⚠️ Кнопка до сих пор не видна после CSS, принудительно показываем через атрибуты');
                clearBtn.attr('style', 'display: flex !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;');
            }
        }, 50);

        console.log('[TasksPaginated] ✅ Кнопка очистки ПОКАЗАНА для', filterId, ', значение:', value);
    } else {
        // Используем все возможные способы скрытия
        clearBtn.removeClass('show');
        clearBtn.css({
            'display': 'none',
            'visibility': 'hidden',
            'opacity': '0',
            'pointer-events': 'none'
        });

        container.removeClass('has-value');
        console.log('[TasksPaginated] ❌ Кнопка очистки СКРЫТА для', filterId, ', значение пустое или null');
    }
};

// Модифицированная функция сброса фильтров
function EMERGENCY_RESET_FILTERS() {
    console.log('🔧 [FIXED] Выполняется ОДНОКРАТНЫЙ сброс фильтров');

    const filters = ['#status-filter', '#project-filter', '#priority-filter'];

    // Флаг, позволяющий определить, был ли уже выполнен сброс
    if (window.filtersResetDone) {
        console.log('🔧 [FIXED] Сброс фильтров уже был выполнен, пропускаем');
        return;
    }

    filters.forEach(selector => {
        const $filter = $(selector);
        if ($filter.length > 0) {
            console.log(`🔧 [FIXED] Сбрасываем ${selector}, текущее значение: "${$filter.val()}"`);
            $filter.val('');
            $filter.prop('selectedIndex', 0);
            $filter.closest('.filter-container').removeClass('has-value');
        }
    });

    // Устанавливаем флаг, чтобы больше не выполнять сброс
    window.filtersResetDone = true;
    console.log('🔧 [FIXED] Сброс фильтров выполнен ОДИН раз и больше не будет повторяться');
}

// Запускаем только ОДИН раз при загрузке файла
$(function() {
    console.log('🔧 [FIXED] Document ready - запускаем однократный сброс');
    // Запускаем сброс только один раз после небольшой задержки
    setTimeout(EMERGENCY_RESET_FILTERS, 100);

    // Диагностика фильтров через 2 секунды после загрузки
    setTimeout(function() {
        console.log('🔍 ДИАГНОСТИКА ФИЛЬТРОВ:');
        $('#status-filter, #project-filter, #priority-filter').each(function() {
            const $filter = $(this);
            console.log(`🔍 ${$filter.attr('id')}: значение = "${$filter.val()}", disabled = ${$filter.prop('disabled')}, readonly = ${$filter.prop('readonly')}`);
        });

        // Усиленная проверка обработчиков
        console.log('🔧 [FIXED] Проверка и переназначение обработчиков событий...');
        attachFilterChangeHandlers();
    }, 2000);
});

// Новая функция для гарантированного присоединения обработчиков событий
function attachFilterChangeHandlers() {
    // Удаляем все старые обработчики
    $('#status-filter, #project-filter, #priority-filter').off('change');

    // Добавляем новые обработчики с усиленной диагностикой
    $('#status-filter').on('change', function() {
        const value = $(this).val();
        const text = $(this).find('option:selected').text();
        console.log('🔧 [FIXED] СОБЫТИЕ CHANGE: status-filter изменен на', value, '(текст: ' + text + ')');

        // Обновляем видимость кнопки очистки через глобальную функцию
        if (typeof window.updateFilterVisibility === 'function') {
            window.updateFilterVisibility($(this));
        } else {
            console.warn('🔧 [FIXED] Функция updateFilterVisibility не найдена, используем стандартные средства');
            const filterId = $(this).attr('id');
            const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
            const clearBtn = $(clearBtnId);
            const container = $(this).closest('.filter-container');

            // Простая проверка наличия значения
            if (value && value !== '' && value !== 'null') {
                clearBtn.addClass('show').css('display', 'flex');
                container.addClass('has-value');
            } else {
                clearBtn.removeClass('show').css('display', 'none');
                container.removeClass('has-value');
            }
        }

        // Показываем индикатор загрузки
        if (typeof window.tasksDataTable !== 'undefined' && typeof window.tasksDataTable.processing === 'function') {
            window.tasksDataTable.processing(true);
            console.log('🔧 [FIXED] Показываем индикатор загрузки через DataTables API');
        } else {
            console.log('🔧 [FIXED] Показываем индикатор загрузки через DOM');
            $('.dt-processing').show();
        }

        if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
            window.TasksCounterManager.showLoading('Применение фильтра статуса...');
        }

        if (window.tasksDataTable) {
            console.log('🔧 [FIXED] Вызываем draw() для обновления таблицы');
            window.tasksDataTable.draw();
        } else {
            console.error('🔧 [FIXED] ❌ tasksDataTable не инициализирована!');
        }
    });

    $('#project-filter').on('change', function() {
        const value = $(this).val();
        const text = $(this).find('option:selected').text();
        console.log('🔧 [FIXED] СОБЫТИЕ CHANGE: project-filter изменен на', value, '(текст: ' + text + ')');

        // Обновляем видимость кнопки очистки через глобальную функцию
        if (typeof window.updateFilterVisibility === 'function') {
            window.updateFilterVisibility($(this));
        } else {
            console.warn('🔧 [FIXED] Функция updateFilterVisibility не найдена, используем стандартные средства');
            const filterId = $(this).attr('id');
            const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
            const clearBtn = $(clearBtnId);
            const container = $(this).closest('.filter-container');

            // Простая проверка наличия значения
            if (value && value !== '' && value !== 'null') {
                clearBtn.addClass('show').css('display', 'flex');
                container.addClass('has-value');
            } else {
                clearBtn.removeClass('show').css('display', 'none');
                container.removeClass('has-value');
            }
        }

        // Показываем индикатор загрузки
        if (typeof window.tasksDataTable !== 'undefined' && typeof window.tasksDataTable.processing === 'function') {
            window.tasksDataTable.processing(true);
            console.log('🔧 [FIXED] Показываем индикатор загрузки через DataTables API');
        } else {
            console.log('🔧 [FIXED] Показываем индикатор загрузки через DOM');
            $('.dt-processing').show();
        }

        if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
            window.TasksCounterManager.showLoading('Применение фильтра проекта...');
        }

        if (window.tasksDataTable) {
            console.log('🔧 [FIXED] Вызываем draw() для обновления таблицы');
            window.tasksDataTable.draw();
        } else {
            console.error('🔧 [FIXED] ❌ tasksDataTable не инициализирована!');
        }
    });

    $('#priority-filter').on('change', function() {
        const value = $(this).val();
        const text = $(this).find('option:selected').text();
        console.log('🔧 [FIXED] СОБЫТИЕ CHANGE: priority-filter изменен на', value, '(текст: ' + text + ')');

        // Обновляем видимость кнопки очистки через глобальную функцию
        if (typeof window.updateFilterVisibility === 'function') {
            window.updateFilterVisibility($(this));
        } else {
            console.warn('🔧 [FIXED] Функция updateFilterVisibility не найдена, используем стандартные средства');
            const filterId = $(this).attr('id');
            const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
            const clearBtn = $(clearBtnId);
            const container = $(this).closest('.filter-container');

            // Простая проверка наличия значения
            if (value && value !== '' && value !== 'null') {
                clearBtn.addClass('show').css('display', 'flex');
                container.addClass('has-value');
            } else {
                clearBtn.removeClass('show').css('display', 'none');
                container.removeClass('has-value');
            }
        }

        // Показываем индикатор загрузки
        if (typeof window.tasksDataTable !== 'undefined' && typeof window.tasksDataTable.processing === 'function') {
            window.tasksDataTable.processing(true);
            console.log('🔧 [FIXED] Показываем индикатор загрузки через DataTables API');
        } else {
            console.log('🔧 [FIXED] Показываем индикатор загрузки через DOM');
            $('.dt-processing').show();
        }

        if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
            window.TasksCounterManager.showLoading('Применение фильтра приоритета...');
        }

        if (window.tasksDataTable) {
            console.log('🔧 [FIXED] Вызываем draw() для обновления таблицы');
            window.tasksDataTable.draw();
        } else {
            console.error('🔧 [FIXED] ❌ tasksDataTable не инициализирована!');
        }
    });

    console.log('🔧 [FIXED] Обработчики событий переназначены');
}

/**
 * Модуль для работы с пагинированными задачами Redmine
 */

/*
 * Задачи с пагинацией - Главный JavaScript модуль
 * Последнее обновление: 2024-12-27 08:30 UTC (исправление синтаксической ошибки)
 * Исправления:
 * - Восстановлена функция loadMoreData() после повреждения при редактировании
 * - Добавлена диагностика скроллинга
 * - Исправлены URL-адреса API для совместимости с Blueprint
 */

// Глобальная функция для управления видимостью кнопок очистки фильтров
window.updateFilterVisibility = function(selectElement) {
    if (!selectElement || selectElement.length === 0) {
        console.warn('[TasksPaginated] 🔍 updateFilterVisibility: selectElement не найден');
        return;
    }

    const rawValue = selectElement.val();
    const value = rawValue || ''; // Безопасная обработка null/undefined
    const filterId = selectElement.attr('id');
    const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
    const clearBtn = $(clearBtnId);
    const container = selectElement.closest('.filter-container');

    console.log('[TasksPaginated] 🔍 Обновление кнопки очистки:', {
        filterId: filterId,
        rawValue: rawValue,
        value: value,
        valueType: typeof rawValue,
        isEmpty: !value || value === '' || value === 'null',
        clearBtnId: clearBtnId,
        clearBtnExists: clearBtn.length > 0,
        containerExists: container.length > 0
    });

    // Более надежная проверка значения
    const hasValue = value && value !== '' && value !== 'null' && value !== null && value !== undefined;

    if (hasValue) {
        // Используем все возможные способы отображения
        clearBtn.addClass('show');
        clearBtn.css({
            'display': 'flex',
            'visibility': 'visible',
            'opacity': '1',
            'pointer-events': 'auto'
        });

        container.addClass('has-value');

        // Проверка видимости после применения стилей
        setTimeout(() => {
            if (!clearBtn.is(':visible')) {
                console.warn('[TasksPaginated] ⚠️ Кнопка до сих пор не видна после CSS, принудительно показываем через атрибуты');
                clearBtn.attr('style', 'display: flex !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;');
            }
        }, 50);

        console.log('[TasksPaginated] ✅ Кнопка очистки ПОКАЗАНА для', filterId, ', значение:', value);
    } else {
        // Используем все возможные способы скрытия
        clearBtn.removeClass('show');
        clearBtn.css({
            'display': 'none',
            'visibility': 'hidden',
            'opacity': '0',
            'pointer-events': 'none'
        });

        container.removeClass('has-value');
        console.log('[TasksPaginated] ❌ Кнопка очистки СКРЫТА для', filterId, ', значение пустое или null');
    }
};

$(function() {
    console.log('[TasksPaginated] Инициализация модуля пагинированных задач (v3)');

    // Инициализация
    initializePaginatedTasks();
});

// Инициализация
function initializePaginatedTasks() {
    console.log('[TasksPaginated] Инициализация модуля пагинированных задач (v3)');

    // Принудительный сброс фильтров при первой загрузке
    // (только при необходимости - это влияет на UX)
    console.log('[TasksPaginated] 🔧 Принудительный сброс фильтров при инициализации');
    console.log('[TasksPaginated] Сброс фильтра: status-filter текущее значение:', $('#status-filter').val());
    console.log('[TasksPaginated] Сброс фильтра: project-filter текущее значение:', $('#project-filter').val());
    console.log('[TasksPaginated] Сброс фильтра: priority-filter текущее значение:', $('#priority-filter').val());

    console.log('[TasksPaginated] Начало инициализации...');

    // Инициализация и улучшение UI
    initializeModernUI();

        // Инициализация DataTable - ВАЖНО: вызываем перед загрузкой фильтров
    initializeDataTable();

    // Принудительное обновление таблицы после инициализации для загрузки данных
    if (window.tasksDataTable) {
        console.log('[TasksPaginated] 🔄 Принудительная начальная загрузка данных');
        showTableLoading();
        // Используем специальную функцию для первой загрузки
        window.forceInitialDataLoad();
    }

    // Загрузка фильтров
    loadAllFiltersAsync();

    // Загрузка статистики
    loadFullStatisticsAsync();

    // Настройка обработчиков событий
    setupEventHandlers();

    // Инициализация счетчика фильтров
    initializeFilterCounter();

    // Инициализация переключателей пагинации
    initializePaginationSwitchers();

    // Инициализация кнопок для карточек
    initializeCardToggleButtons();

    // Инициализация глобальной кнопки переключения
    initializeGlobalToggleButton();

    console.log('[TasksPaginated] ✅ Инициализация завершена');
}

// Инициализация современного UI
function initializeModernUI() {
    // Добавляем элементы UI для современного интерфейса
    appendModernUIElements();

    // Настраиваем темную тему
    setupDarkThemeToggle();

    // Настраиваем кнопку прокрутки вверх
    setupScrollTopButton();

    // Добавляем переключатель режима отображения (таблица/карточки)
    setupViewToggle();

    // Улучшаем отображение строк с высоким приоритетом и просроченными дедлайнами
    setupRowEnhancements();
}

// Добавление элементов современного UI
function appendModernUIElements() {
    // Добавляем переключатель режима отображения перед таблицей
    $('#tasksTable_wrapper').before(`
        <div class="view-toggle-wrapper">
            <button class="view-toggle-btn active" data-view="table">
                <i class="fas fa-table"></i> Таблица
            </button>
            <button class="view-toggle-btn" data-view="cards">
                <i class="fas fa-th-large"></i> Карточки
            </button>
        </div>
    `);

    // Создаем контейнер для карточек (изначально скрытый)
    $('#tasksTable_wrapper').after(`<div class="task-cards-view" style="display:none;"></div>`);
}

// Настройка переключателя темной темы (отключено)
function setupDarkThemeToggle() {
    // Функция отключена
    console.log('[TasksPaginated] 🔧 Переключатель темы отключен');
}

// Настройка кнопки прокрутки вверх (отключено)
function setupScrollTopButton() {
    // Функция отключена
    console.log('[TasksPaginated] 🔧 Кнопка прокрутки вверх отключена');
}

// Настройка переключателя режима отображения
function setupViewToggle() {
    $('.view-toggle-btn').on('click', function() {
        const viewMode = $(this).data('view');

        // Активируем нажатую кнопку
        $('.view-toggle-btn').removeClass('active');
        $(this).addClass('active');

        if (viewMode === 'table') {
            // Показываем таблицу, скрываем карточки
            $('#tasksTable_wrapper').show();
            $('.task-cards-view').hide();
        } else {
            // Показываем карточки, скрываем таблицу
            $('#tasksTable_wrapper').hide();
            $('.task-cards-view').show();

            // Если карточки еще не сгенерированы, создаем их
            if ($('.task-cards-view').children().length === 0) {
                generateTaskCards();
            }
        }

        // Сохраняем предпочтение в localStorage
        localStorage.setItem('tasks_view_mode', viewMode);
    });

    // Применяем сохраненный режим отображения при загрузке
    const savedViewMode = localStorage.getItem('tasks_view_mode');
    if (savedViewMode === 'cards') {
        $('.view-toggle-btn[data-view="cards"]').trigger('click');
    }
}

// Создание карточек для задач
function generateTaskCards() {
    const $cardsContainer = $('.task-cards-view');
    $cardsContainer.empty();

    // Получаем данные из DataTable
    const tableData = window.tasksDataTable.data();

    // Для каждой строки создаем карточку
    tableData.each(function(rowData) {
        const statusInfo = getStatusInfo(rowData.status_name);
        const priorityInfo = getPriorityInfo(rowData.priority_name);

        const cardHtml = `
            <div class="task-card ${(typeof rowData.priority_position === 'number' && rowData.priority_position >= 7) ? 'high-priority-task' : ''}">
                <div class="task-card-header">
                    <a href="/tasks/my-tasks/${rowData.id}" class="task-card-id" target="_blank" rel="noopener noreferrer" title="Открыть задачу #${rowData.id} в новой вкладке">#${rowData.id}</a>
                    <div class="status-badge ${statusInfo.class}" data-status="${escapeHtml(rowData.status_name || 'N/A')}">
                        <i class="${statusInfo.icon}"></i>
                        <span>${escapeHtml(rowData.status_name || 'N/A')}</span>
                    </div>
                </div>
                <div class="task-card-body">
                    <div class="task-card-title">${escapeHtml(rowData.subject)}</div>
                    <div class="task-card-project">${escapeHtml(rowData.project_name || 'Без проекта')}</div>
                    <div class="priority-badge ${priorityInfo.class}" data-priority="${escapeHtml(rowData.priority_name || 'N/A')}">
                        <i class="${priorityInfo.icon}"></i>
                        <span>${escapeHtml(rowData.priority_name || 'N/A')}</span>
                    </div>
                    <div class="task-email mt-2">
                        ${rowData.easy_email_to && rowData.easy_email_to !== '-' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(rowData.easy_email_to)
                          ? `<a href="mailto:${escapeHtml(rowData.easy_email_to)}" class="email-link" title="Написать письмо: ${escapeHtml(rowData.easy_email_to)}">${escapeHtml(rowData.easy_email_to)}</a>`
                          : escapeHtml(rowData.easy_email_to || '-')
                        }
                    </div>
                </div>
                <div class="task-card-footer">
                    <div>Создана: ${formatDate(rowData.created_on)}</div>
                    <div>Обновлена: ${formatDate(rowData.updated_on)}</div>
                </div>
            </div>
        `;

        $cardsContainer.append(cardHtml);
    });
}

// Улучшение строк с выделением приоритетов и дедлайнов
function setupRowEnhancements() {
    // Добавляем проверку существования tasksDataTable
    if (window.tasksDataTable && typeof window.tasksDataTable.on === 'function') {
        // Запускаем обработку после каждого обновления таблицы
        window.tasksDataTable.on('draw.dt', function() {
            enhanceTableRows();
        });
        console.log('[TasksPaginated] Улучшение строк таблицы настроено');
    } else {
        console.warn('[TasksPaginated] tasksDataTable не инициализирована для улучшения строк');
    }
}

// Улучшение строк таблицы
function enhanceTableRows() {
    console.log('[TasksPaginated] Улучшение строк таблицы');

    // Проверяем, что tasksDataTable существует и инициализирована
    if (!window.tasksDataTable || typeof window.tasksDataTable.rows !== 'function') {
        console.warn('[TasksPaginated] ⚠️ tasksDataTable не инициализирована для enhanceTableRows');
        return;
    }

    try {
        window.tasksDataTable.rows().every(function(rowIdx) {
            const data = this.data();
            if (!data) return; // Пропускаем, если данные отсутствуют

            const $row = $(this.node());
            if (!$row.length) return; // Пропускаем, если элемент DOM не найден

            // Добавляем класс для задач с высоким приоритетом по position
            if (typeof data.priority_position === 'number' && data.priority_position >= 7) {
                $row.addClass('high-priority-task');
            }

            // Проверяем на просроченные задачи
            if (data.due_date) {
                const dueDate = new Date(data.due_date);
                const today = new Date();

                // Убираем время для корректного сравнения дат
                today.setHours(0, 0, 0, 0);

                if (dueDate < today) {
                    $row.addClass('overdue-task');
                }
            }
        });
        console.log('[TasksPaginated] ✅ Строки таблицы улучшены успешно');
    } catch (error) {
        console.error('[TasksPaginated] ❌ Ошибка при улучшении строк таблицы:', error);
    }
}

// Функция для инициализации переключателей пагинации
function initializePaginationSwitchers() {
    console.log('[TasksPaginated] Инициализация переключателей пагинации');
    // Пустая реализация, чтобы избежать ошибки
    // Можно добавить реальную функциональность позже
}

// Инициализация DataTable
function initializeDataTable() {
    // Показываем индикатор загрузки перед инициализацией
    showTableLoading();

    // Проверка, не инициализирована ли уже таблица
    if ($.fn.DataTable.isDataTable('#tasksTable')) {
        console.log('[TasksPaginated] ⚠️ Таблица уже инициализирована, пропускаем повторную инициализацию');

        // Если таблица уже существует, получаем её экземпляр
        window.tasksDataTable = $('#tasksTable').DataTable();

        // Принудительно перезагружаем данные
        console.log('[TasksPaginated] 🔄 Принудительное обновление существующей таблицы');
        window.tasksDataTable.ajax.reload();

        // Скрываем модальное окно с ошибкой, если оно существует
        setTimeout(function() {
            const errorModal = $('div:contains("DataTables warning: table id=tasksTable")').closest('.modal, [role="dialog"]');
            if (errorModal.length) {
                console.log('[TasksPaginated] 🛠️ Скрываем модальное окно с ошибкой DataTables');
                errorModal.hide();

                // Если есть кнопка OK, симулируем её нажатие
                const okButton = errorModal.find('button:contains("OK")');
                if (okButton.length) {
                    okButton.click();
                }
            }
        }, 100);

        return;
    }

    const columnMapping = {
        0: 'id',
        1: 'subject',
        2: 'status_name',
        3: 'priority_name',
        4: 'easy_email_to',
        5: 'updated_on',
        6: 'created_on',
        7: 'start_date'
    };

        try {
        console.log('[TasksPaginated] 🚀 Начинаем инициализацию DataTable...');

        // Добавляем обработчик события draw.dt перед инициализацией
        $('#tasksTable').on('draw.dt', function() {
            console.log('[TasksPaginated] DataTable drawCallback.');
            updateInfo();

            // Проверяем активные фильтры
            checkForActiveFilters();

            // Обновляем кнопки очистки
            console.log('[TasksPaginated] DataTable draw event - обновляем кнопки очистки');
            updateAllClearButtons();

            // Улучшаем строки таблицы
            enhanceTableRows();
        });

        // Флаг первой загрузки для решения проблемы с пустой таблицей
        window.isFirstDataLoad = true;

        // Делаем tasksDataTable глобально доступной для других скриптов
        window.tasksDataTable = $('#tasksTable').DataTable({
            processing: true,
            serverSide: true,
            searching: true,
            searchDelay: 1000,
            // Добавляем автоматическую загрузку данных при инициализации
            deferLoading: 1,
            // Обработчик завершения инициализации
            initComplete: function(settings, json) {
                console.log('[TasksPaginated] DataTable initComplete.');

                // Перемещаем элементы UI для лучшего отображения
                $('#tasksTable_filter').appendTo('#searchBoxContainer');
                $('#tasksTable_length').appendTo('#lengthContainer');
                $('#tasksTable_info').appendTo('#tasksInfoContainer');
                $('#tasksTable_paginate').appendTo('#tasksPaginationContainer');

                // Обновляем видимость кнопок очистки
                updateAllClearButtons();

                // Сообщаем другим компонентам, что DataTable полностью инициализирована
                console.log('[TasksPaginated] 📢 DataTable полностью инициализирована, сообщаем другим компонентам');
                $(document).trigger('datatables-initialized');
            },
            ajax: {
                url: "/tasks/get-my-tasks-paginated",
                type: "GET",
                data: function(d) {
                    console.log('[TasksPaginated] 🔄 Формирование AJAX запроса с УЛУЧШЕННЫМ подходом');

                    // Добавляем сортировку
                    const orderColumnIndex = d.order[0].column;
                    const orderColumnName = d.columns[orderColumnIndex].data;
                    const orderDir = d.order[0].dir;

                    console.log('[TasksPaginated] 🔄 Добавлена сортировка:', {
                        column: orderColumnName,
                        direction: orderDir
                    });

                    // Фильтры
                    const statusFilter = $('#status-filter').val();
                    const projectFilter = $('#project-filter').val();
                    const priorityFilter = $('#priority-filter').val();

                    // Флаг первой загрузки для решения проблемы с пустой таблицей
                    const isFirstLoad = window.isFirstDataLoad;

                    console.log('[TasksPaginated] 🔍 Значения фильтров:', {
                        status: statusFilter,
                        project: projectFilter,
                        priority: priorityFilter
                    });

                    const params = {
                        // Стандартные параметры DataTables
                        draw: d.draw,
                        start: d.start,
                        length: d.length,
                        ['search[value]']: d.search.value,

                        // Сортировка
                        ['order[0][column]']: orderColumnIndex,
                        ['order[0][dir]']: orderDir,
                        ['columns[' + orderColumnIndex + '][data]']: orderColumnName,

                        // Фильтры
                        status_id: statusFilter || '',
                        project_id: projectFilter || '',
                        priority_id: priorityFilter || '',

                        // Дополнительные фильтры по имени (используются на сервере)
                        status_name: $('#status-filter option:selected').text() || '',
                        project_name: $('#project-filter option:selected').text() || '',
                        priority_name: $('#priority-filter option:selected').text() || '',

                        // Параметр для принудительной загрузки данных при первом запросе
                        force_load: isFirstLoad ? '1' : '0'
                    };

                    console.log('[TasksPaginated] 📊 Финальные параметры запроса:', params);
                    return params;
                },
                dataSrc: function(json) {
                    console.log('[TasksPaginated] Данные загружены');
                    hideTableLoading();

                    // Обновляем счетчик отфильтрованных задач
                    if (typeof updateFilterCounter === 'function') {
                        updateFilterCounter(json.recordsFiltered);
                    }

                    // Сбрасываем флаг первой загрузки после получения данных
                    if (window.isFirstDataLoad) {
                        console.log('[TasksPaginated] ✅ Первая загрузка данных выполнена успешно');
                        window.isFirstDataLoad = false;
                    }

                    return json.data;
                },
                error: function(xhr, error, thrown) {
                    console.error('[TasksPaginated] Критическая ошибка API:', error, thrown, xhr.responseText);
                    hideTableLoading();
                    showError('Критическая ошибка связи с сервером. Попробуйте перезагрузить страницу.');
                }
            },
            columns: [
                {
                    data: 'id',
                    render: function(data, type, row) {
                        return type === 'display' ? '<a href="/tasks/my-tasks/' + data + '" class="task-id-link" target="_blank" rel="noopener noreferrer" title="Открыть задачу #' + data + ' в новой вкладке">#' + data + '</a>' : data;
                    },
                    orderable: true,
                    searchable: true
                },
                {
                    data: 'subject',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            // Диагностический лог: выводим все данные строки в консоль
                            console.log('[ЗАДАЧА] Данные для строки:', row);

                            // Возвращаем оригинальный, самый простой и надежный вариант рендеринга
                            // Возвращаем оригинальный, самый простой и надежный вариант рендеринга
                            return '<div class="task-title">' + escapeHtml(data) + '</div>' +
                                   '<div class="project-name">' +
                                   '<i class="fas fa-folder-open"></i>' + // Иконка добавлена для консистентности
                                   escapeHtml(row.project_name || 'Без проекта') +
                                   '</div>';
                        }
                        return data;
                    },
                    orderable: true,
                    searchable: true
                },
                {
                    data: 'status_name',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            const statusInfo = getStatusInfo(data);
                            return '<div class="status-badge ' + statusInfo.class + '" data-status="' + escapeHtml(data || 'N/A') + '"><i class="' + statusInfo.icon + '"></i><span>' + escapeHtml(data || 'N/A') + '</span></div>';
                        }
                        return data;
                    },
                    orderable: true
                },
                {
                    data: 'priority_name',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            const priorityInfo = getPriorityInfo(data);
                            return '<div class="priority-badge ' + priorityInfo.class + '" data-priority="' + escapeHtml(data || 'N/A') + '"><i class="' + priorityInfo.icon + '"></i><span>' + escapeHtml(data || 'N/A') + '</span></div>';
                        }
                        return data;
                    },
                    orderable: true
                },
                {
                    data: 'easy_email_to',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            if (!data || data === '-') {
                                return '<div class="task-email">-</div>';
                            }

                            // Проверяем валидность email
                            const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data);

                            if (isValidEmail) {
                                return '<div class="task-email">' +
                                       '<a href="mailto:' + escapeHtml(data) + '" class="email-link" title="Написать письмо: ' + escapeHtml(data) + '">' +
                                       escapeHtml(data) +
                                       '</a>' +
                                       '</div>';
                            } else {
                                return '<div class="task-email">' + escapeHtml(data) + '</div>';
                            }
                        }
                        return data;
                    },
                    orderable: true
                },
                {
                    data: 'updated_on',
                    render: function(data, type, row) {
                        return type === 'display' ? '<div class="task-date">' + formatDate(data) + '</div>' : data;
                    },
                    orderable: true
                },
                {
                    data: 'created_on',
                    render: function(data, type, row) {
                        return type === 'display' ? '<div class="task-date">' + formatDate(data) + '</div>' : data;
                    },
                    orderable: true
                },
                {
                    data: 'start_date',
                    render: function(data, type, row) {
                        return type === 'display' ? '<div class="task-date">' + formatDate(data, true) + '</div>' : data;
                    },
                    orderable: true
                }
            ],
            order: [[5, 'desc']],
            pageLength: 25,
            lengthChange: true,
            lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
            searching: true,
            info: false,
            paging: true,
            pagingType: "full_numbers",
            language: {
                url: "/static/js/datatables/Russian.json",
                processing: '<div class="dt-processing"><div class="spinner-border text-primary" role="status"></div><span class="ml-2">Загрузка...</span></div>',
                lengthMenu: "Показать: _MENU_",
                info: "Показано с _START_ по _END_ из _TOTAL_ записей",
                infoEmpty: "Нет записей для отображения",
                infoFiltered: "(отфильтровано из _MAX_ записей)",
                search: "Поиск:",
                paginate: {
                    first: "Первая",
                    last: "Последняя",
                    next: "Следующая",
                    previous: "Предыдущая"
                },
                emptyTable: "Нет данных в таблице",
                zeroRecords: "Записи не найдены"
            },
            dom: '<"top"<"left-col"l><"right-col"f>>rt<"bottom"<"left-col"i><"right-col"p>>',
            initComplete: function(settings, json) {
                console.log('[TasksPaginated] DataTable initComplete.');

                $('.dataTables_length').detach().appendTo('#lengthContainer');
                $('.dataTables_length label').contents().filter(function(){
                    return this.nodeType === 3;
                }).remove();

                $('.dataTables_filter').detach().appendTo('#searchBoxContainer');
                $('.dataTables_filter label').contents().filter(function(){
                    return this.nodeType === 3;
                }).remove();

                $('#searchBoxContainer input[type="search"]').attr("placeholder", "Поиск по ID (#123), теме, описанию...");

                $('.dataTables_info').detach().appendTo('#tasksInfoContainer');
                $('.dataTables_paginate').detach().appendTo('#tasksPaginationContainer');

                // КРИТИЧНО: Обновляем кнопки очистки после инициализации DataTable
                setTimeout(() => {
                    updateAllClearButtons();
                    console.log('[TasksPaginated] Обновлены кнопки очистки в initComplete');

                    // Проверяем, есть ли данные в таблице
                    if (window.tasksDataTable && window.tasksDataTable.rows().count() === 0) {
                        console.log('[TasksPaginated] ⚠️ Данные не загружены, выполняем принудительную загрузку');
                        window.forceInitialDataLoad();
                    }
                }, 100);

                console.log('[TasksPaginated] Элементы UI перемещены');

                // 6. Перемещение элементов управления в кастомные контейнеры
                const searchBox = document.querySelector('#tasksTable_filter input');
                const lengthSelect = document.querySelector('#tasksTable_length');
                const searchBoxContainer = document.querySelector('#searchBoxContainer');
                const lengthContainer = document.querySelector('#lengthContainer');

                if (searchBox && searchBoxContainer) {
                    // Изменяем placeholder
                    searchBox.placeholder = 'Поиск по ID (#123), теме, описанию...';

                    // Добавляем специфичные классы для стилизации
                    searchBox.classList.add('tasks-search-input');

                    const searchBoxParent = searchBox.parentElement;
                    searchBoxContainer.appendChild(searchBoxParent);
                }

                if (lengthSelect && lengthContainer) {
                    // Добавляем класс для селектора длины
                    const lengthSelectElement = lengthSelect.querySelector('select');
                    if (lengthSelectElement) {
                        lengthSelectElement.classList.add('tasks-length-select');
                    }

                    lengthContainer.appendChild(lengthSelect);
                }

                // Добавляем класс к body для принудительной перезагрузки стилей
                document.body.classList.add('tasks-page-loaded');

                // Принудительно обновляем стили через небольшую задержку
                setTimeout(() => {
                    document.querySelectorAll('.filter-container select, .search-container input, .length-container select').forEach(el => {
                        el.style.fontSize = '16px';
                        el.style.height = '48px';
                        el.style.padding = '12px';
                    });
                }, 100);

                // Удаляем дублирующиеся элементы после инициализации
                setTimeout(() => {
                    removeDuplicateSearchElements();
                }, 200);

                // Сообщаем другим компонентам, что таблица инициализирована
                console.log('[TasksPaginated] 📢 DataTable полностью инициализирована, сообщаем другим компонентам');
                document.dispatchEvent(new CustomEvent('datatables-initialized'));
            },
            drawCallback: function(settings) {
                console.log('[TasksPaginated] DataTable drawCallback.');
                $('#tasksTable tbody tr').addClass('fade-in');

                // Очистка дубликатов при каждой перерисовке (с задержкой для избежания конфликтов)
                setTimeout(() => {
                    removeDuplicateSearchElements();
                }, 100);
            }
        });
        console.log('[TasksPaginated] ✅ DataTable успешно инициализирована.');

        // Проверяем, что tasksDataTable действительно создана
        if (!window.tasksDataTable) {
            console.error('[TasksPaginated] ❌ Критическая ошибка: tasksDataTable не инициализирована после создания!');
        } else {
            console.log('[TasksPaginated] ✅ tasksDataTable успешно создана и доступна глобально');
        }
    } catch (error) {
        console.error('[TasksPaginated] ❌ Ошибка при инициализации DataTable:', error);
        // Показываем сообщение об ошибке пользователю
        showError('Произошла ошибка при инициализации таблицы. Пожалуйста, перезагрузите страницу.');
    }
}

// Нормализация данных больше не нужна - данные приходят в правильном формате

// Обработчики событий
function setupEventHandlers() {
    console.log('[TasksPaginated] Настройка обработчиков событий...');

    // Проверяем, что tasksDataTable инициализирована перед привязкой событий
    if (window.tasksDataTable) {
        window.tasksDataTable.on('search.dt', function() {
            const newSearchTerm = window.tasksDataTable.search();
            console.log('[TasksPaginated] DataTable search event:', newSearchTerm);
        });

        window.tasksDataTable.on('preXhr.dt', function() {
            console.log('[TasksPaginated] Начало загрузки данных...');
            showTableLoading();
        });

        window.tasksDataTable.on('xhr.dt', function() {
            console.log('[TasksPaginated] Данные загружены');
            hideTableLoading();
        });

        // ДОБАВЛЕНО: Обработчик draw event для обновления кнопок очистки
        window.tasksDataTable.on('draw.dt', function() {
            console.log('[TasksPaginated] DataTable draw event - обновляем кнопки очистки');
            updateAllClearButtons();
        });
    } else {
        console.warn('[TasksPaginated] tasksDataTable не инициализирована, пропускаем привязку событий DataTable');
    }

    // Обработчики фильтров
    $(document).on('change', '#status-filter, #project-filter, #priority-filter', function() {
        console.log('[TasksPaginated] Фильтр изменен:', $(this).attr('id'), $(this).val());
        updateClearButtonVisibility($(this)); // Добавляю обновление видимости кнопки сброса

        // КРИТИЧНО: Показываем стандартный спиннер DataTables
        showTableLoading();

        // Показываем загрузку в индикаторе
        if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
            console.log('[TasksPaginated] 🔄 Показываем загрузку в индикаторе при изменении фильтра');
            window.TasksCounterManager.showLoading('Применение фильтров...');
        }

        // Используем стандартный метод для обычной пагинации
        if (window.tasksDataTable) {
            console.log('[TasksPaginated] 🔄 Перерисовываем таблицу с новыми фильтрами...');
            window.tasksDataTable.draw();
        } else {
            console.error('[TasksPaginated] ❌ DataTable не инициализирована!');
        }
    });

    // Обработчики кнопок очистки фильтров
    $(document).on('click', '#clear-status-filter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('[TasksPaginated] 🔄 Клик по кнопке очистки статуса');

        const filter = $('#status-filter');

        // ИСПРАВЛЕНО: Принудительно сбрасываем значение и делаем это явно
        filter.val('').prop('selectedIndex', 0);
        console.log('[TasksPaginated] 🔄 Статус сброшен, новое значение:', filter.val());

        // ИСПРАВЛЕНО: Явно обновляем видимость кнопки
        updateClearButtonVisibility(filter);

        // ИСПРАВЛЕНО: Принудительно вызываем событие change для перерисовки таблицы
        filter.trigger('change');

        console.log('[TasksPaginated] ✅ Статус фильтр очищен');
    });

    $(document).on('click', '#clear-project-filter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('[TasksPaginated] 🔄 Клик по кнопке очистки проекта');

        const filter = $('#project-filter');

        // ИСПРАВЛЕНО: Принудительно сбрасываем значение и делаем это явно
        filter.val('').prop('selectedIndex', 0);
        console.log('[TasksPaginated] 🔄 Проект сброшен, новое значение:', filter.val());

        // ИСПРАВЛЕНО: Явно обновляем видимость кнопки
        updateClearButtonVisibility(filter);

        // ИСПРАВЛЕНО: Принудительно вызываем событие change для перерисовки таблицы
        filter.trigger('change');

        // Очищаем TreeView если он активен
        if (window.projectTreeView) {
            try {
                window.projectTreeView.clearAllSelections();
                console.log('[TasksPaginated] TreeView очищен');
            } catch (error) {
                console.warn('[TasksPaginated] Ошибка при очистке TreeView:', error);
            }
        }

        console.log('[TasksPaginated] ✅ Проект фильтр очищен');
    });

    $(document).on('click', '#clear-priority-filter', function(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('[TasksPaginated] 🔄 Клик по кнопке очистки приоритета');

        const filter = $('#priority-filter');

        // ИСПРАВЛЕНО: Принудительно сбрасываем значение и делаем это явно
        filter.val('').prop('selectedIndex', 0);
        console.log('[TasksPaginated] 🔄 Приоритет сброшен, новое значение:', filter.val());

        // ИСПРАВЛЕНО: Явно обновляем видимость кнопки
        updateClearButtonVisibility(filter);

        // ИСПРАВЛЕНО: Принудительно вызываем событие change для перерисовки таблицы
        filter.trigger('change');

        console.log('[TasksPaginated] ✅ Приоритет фильтр очищен');
    });

    // ПРИМЕЧАНИЕ: Расширенный поиск настраивается в initComplete callback DataTable

    console.log('[TasksPaginated] Обработчики событий настроены.');

    // ДОБАВЛЕНО: Обработчики изменения фильтров для обновления видимости кнопок очистки
    $('#status-filter').on('change', function() {
        updateClearButtonVisibility($(this));
    });

    $('#project-filter').on('change', function() {
        updateClearButtonVisibility($(this));
    });

    $('#priority-filter').on('change', function() {
        updateClearButtonVisibility($(this));
    });

    console.log('[TasksPaginated] Обработчики изменения фильтров добавлены');
}

// ДОБАВЛЕНО: Функция настройки расширенного поиска
function setupAdvancedSearchFilter() {
    if (!window.tasksDataTable) {
        console.log('[TasksPaginated] DataTable не инициализирована для настройки поиска');
        return;
    }

    console.log('[TasksPaginated] Настройка расширенного поиска...');

    // Получаем поле поиска
    const searchInput = $('#tasksTable_filter input[type="search"]');

    if (searchInput.length === 0) {
        console.log('[TasksPaginated] Поле поиска не найдено');
        return;
    }

    // ИСПРАВЛЕНО: Аккуратно отключаем только стандартные обработчики DataTables
    searchInput.off('keyup.DT search.DT input.DT paste.DT cut.DT');
    // Но оставляем возможность для других обработчиков

    // Добавляем обработчик для расширенного поиска
    let searchTimeout;
    searchInput.on('input keyup', function() {
        const searchTerm = $(this).val();
        console.log('[TasksPaginated] Поиск по термину:', searchTerm);

        // Очищаем предыдущий таймаут
        clearTimeout(searchTimeout);

        // Устанавливаем новый таймаут для задержки поиска
        searchTimeout = setTimeout(function() {
            performAdvancedSearch(searchTerm);
        }, 300);
    });

    console.log('[TasksPaginated] Расширенный поиск настроен');
}

// ДОБАВЛЕНО: Функция выполнения расширенного поиска
function performAdvancedSearch(searchTerm) {
    if (!window.tasksDataTable) {
        return;
    }

    console.log('[TasksPaginated] Выполнение расширенного поиска:', searchTerm);

    // Если поиск пустой, удаляем все кастомные фильтры
    if (!searchTerm || searchTerm.trim() === '') {
        console.log('[TasksPaginated] Очистка поиска');

        // Удаляем все кастомные фильтры поиска
        while ($.fn.dataTable.ext.search.length > 0) {
            $.fn.dataTable.ext.search.pop();
        }

        // Перерисовываем таблицу
        window.tasksDataTable.draw();
        return;
    }

    const searchTermLower = searchTerm.toLowerCase().trim();

    // Удаляем предыдущий кастомный фильтр поиска
    while ($.fn.dataTable.ext.search.length > 0) {
        $.fn.dataTable.ext.search.pop();
    }

    // Добавляем новый кастомный фильтр для расширенного поиска
    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
        // Проверяем, что это наша таблица
        if (settings.nTable.id !== 'tasksTable') {
            return true;
        }

        // Получаем данные текущей строки
        const rowData = window.tasksDataTable.row(dataIndex).data();

        if (!rowData) {
            return false;
        }

        // Создаем поисковую строку из всех доступных полей
        const searchableFields = [
            // ID задачи (с # и без)
            rowData.id ? String(rowData.id) : '',
            rowData.id ? `#${rowData.id}` : '',

            // Тема задачи
            rowData.subject || '',

            // ИСПРАВЛЕНО: Описание задачи
            rowData.description || '',

            // Название проекта
            rowData.project_name || '',

            // Статус
            rowData.status_name || '',

            // Приоритет
            rowData.priority_name || '',

            // Автор
            rowData.author_name || '',

            // Email отправителя
            rowData.email_to || '',

            // Исполнитель
            rowData.assigned_to_name || '',

            // Трекер
            rowData.tracker_name || ''
        ];

        // Объединяем все поля в одну строку для поиска
        const combinedSearchText = searchableFields
            .filter(field => field && field.trim() !== '')
            .join(' ')
            .toLowerCase();

        // Проверяем, содержится ли поисковый термин в объединенной строке
        let isMatch = combinedSearchText.includes(searchTermLower);

        // Дополнительная проверка поиска по номеру задачи с #
        if (!isMatch && searchTermLower.startsWith('#')) {
            const numericSearch = searchTermLower.substring(1);
            const taskIdString = String(rowData.id || '');
            isMatch = taskIdString.includes(numericSearch);
        }

        // Проверяем поиск только по числу (без #)
        if (!isMatch && /^\d+$/.test(searchTermLower)) {
            const taskIdString = String(rowData.id || '');
            isMatch = taskIdString.includes(searchTermLower);
        }

        return isMatch;
    });

    // Применяем фильтр
    window.tasksDataTable.draw();
    console.log('[TasksPaginated] Расширенный поиск применен');
}

// Функция для удаления дублирующихся элементов поиска DataTables
function removeDuplicateSearchElements() {
    try {
        // Удаляем дублирующиеся поисковые поля DataTables
        const searchContainers = $('.dataTables_filter');
        if (searchContainers.length > 1) {
            searchContainers.slice(1).remove();
            console.log('[TasksPaginated] Удалены дублирующиеся элементы поиска');
        }

        // Удаляем дублирующиеся кастомные поисковые поля
        const customSearchInputs = $('input[data-custom-search="true"]');
        if (customSearchInputs.length > 1) {
            customSearchInputs.slice(1).remove();
            console.log('[TasksPaginated] Удалены дублирующиеся кастомные поисковые поля');
        }

        // Удаляем дублирующиеся селекторы длины
        const lengthContainers = $('.dataTables_length');
        if (lengthContainers.length > 1) {
            lengthContainers.slice(1).remove();
            console.log('[TasksPaginated] Удалены дублирующиеся селекторы количества записей');
        }

        // Удаляем дублирующиеся info контейнеры
        const infoContainers = $('.dataTables_info');
        if (infoContainers.length > 1) {
            infoContainers.slice(1).remove();
            console.log('[TasksPaginated] Удалены дублирующиеся info контейнеры');
        }

        // Удаляем дублирующиеся контейнеры пагинации
        const paginateContainers = $('.dataTables_paginate');
        if (paginateContainers.length > 1) {
            paginateContainers.slice(1).remove();
            console.log('[TasksPaginated] Удалены дублирующиеся контейнеры пагинации');
        }

        // Удаляем пустые обертки
        $('.dataTables_wrapper').each(function() {
            const $wrapper = $(this);
            if ($wrapper.children().length === 0) {
                $wrapper.remove();
                console.log('[TasksPaginated] Удалена пустая обертка DataTables');
            }
        });

    } catch (error) {
        console.warn('[TasksPaginated] Ошибка при удалении дублирующихся элементов:', error);
    }
}

// Заглушка для функции скроллинга - больше не используется
function loadScrollDataWithFilters() {
    console.log('[TasksPaginated] loadScrollDataWithFilters больше не поддерживается - используйте tasksDataTable.draw()');
    if (window.tasksDataTable) {
        window.tasksDataTable.draw();
    }
}

// Функция выполнения поиска в скроллинг-режиме - больше не используется
function performScrollingSearch(searchTerm) {
    console.log('[TasksPaginated] Скроллинг поиск больше не поддерживается');
    return;
}

// Функция для управления видимостью кнопок сброса
function updateClearButtonVisibility(selectElement) {
    if (!selectElement || selectElement.length === 0) {
        console.warn('[TasksPaginated] updateClearButtonVisibility: selectElement не найден');
        return;
    }

    const rawValue = selectElement.val();
    const value = rawValue || ''; // Безопасная обработка null/undefined
    const filterId = selectElement.attr('id');
    const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
    const clearBtn = $(clearBtnId);
    const container = selectElement.closest('.filter-container');

    console.log('[TasksPaginated] 🔍 Обновление кнопки очистки:', {
        filterId: filterId,
        rawValue: rawValue,
        value: value,
        valueType: typeof rawValue,
        isEmpty: !value || value === '' || value === 'null',
        clearBtnId: clearBtnId,
        clearBtnExists: clearBtn.length > 0,
        containerExists: container.length > 0
    });

    // УЛУЧШЕНО: Более надежная проверка значения
    const hasValue = value && value !== '' && value !== 'null' && value !== null && value !== undefined;

    if (hasValue) {
        // УЛУЧШЕНО: Используем все возможные способы отображения
        clearBtn.addClass('show');
        clearBtn.css({
            'display': 'flex',
            'visibility': 'visible',
            'opacity': '1',
            'pointer-events': 'auto'
        });

        container.addClass('has-value');

        // УЛУЧШЕНО: Проверка видимости после применения стилей
        setTimeout(() => {
            if (!clearBtn.is(':visible')) {
                console.warn('[TasksPaginated] ⚠️ Кнопка до сих пор не видна после CSS, принудительно показываем через атрибуты');
                clearBtn.attr('style', 'display: flex !important; visibility: visible !important; opacity: 1 !important; pointer-events: auto !important;');
            }
        }, 50);

        console.log('[TasksPaginated] ✅ Кнопка очистки ПОКАЗАНА для', filterId, ', значение:', value);
    } else {
        // УЛУЧШЕНО: Используем все возможные способы скрытия
        clearBtn.removeClass('show');
        clearBtn.css({
            'display': 'none',
            'visibility': 'hidden',
            'opacity': '0',
            'pointer-events': 'none'
        });

        container.removeClass('has-value');
        console.log('[TasksPaginated] ❌ Кнопка очистки СКРЫТА для', filterId, ', значение пустое или null');
    }
}

// Функция для обновления всех кнопок сброса
function updateAllClearButtons() {
    console.log('[TasksPaginated] 🔄 Обновление ВСЕХ кнопок очистки...');

    // Ждем что DOM готов
    if (document.readyState !== 'complete') {
        console.log('[TasksPaginated] DOM не готов, откладываем обновление кнопок');
        setTimeout(updateAllClearButtons, 100);
        return;
    }

    updateClearButtonVisibility($('#status-filter'));
    updateClearButtonVisibility($('#project-filter'));
    updateClearButtonVisibility($('#priority-filter'));

    console.log('[TasksPaginated] ✅ Все кнопки очистки обновлены');
}

// Информация о пагинации
function updateInfo(pagination) {
    if (!pagination) return;

    const start = ((pagination.page - 1) * pagination.per_page) + 1;
    const end = Math.min(pagination.page * pagination.per_page, pagination.total);
    const infoText = 'Показаны записи с ' + start + ' по ' + end + ' из ' + pagination.total;

    $('#tasksInfoContainer .dataTables_info').text(infoText);
}

// Информация о статусах
function getStatusInfo(status) {
    const statusStr = String(status || '');
    const statusLower = statusStr.toLowerCase();
    if (statusLower.includes('новый') || statusLower.includes('new')) {
        return { class: 'status-new', icon: 'fas fa-plus-circle' };
    } else if (statusLower.includes('работе') || statusLower.includes('progress')) {
        return { class: 'status-progress', icon: 'fas fa-play-circle' };
    } else if (statusLower.includes('закрыт') || statusLower.includes('closed')) {
        return { class: 'status-closed', icon: 'fas fa-check-circle' };
    }
    return { class: 'status-default', icon: 'fas fa-circle' };
}

// Информация о приоритетах
function getPriorityInfo(priority) {
    const priorityStr = String(priority || '');
    const priorityLower = priorityStr.toLowerCase();
    if (priorityLower.includes('высок') || priorityLower.includes('urgent') || priorityLower.includes('high')) {
        return { class: 'priority-high', icon: 'fas fa-arrow-up' };
    } else if (priorityLower.includes('норм') || priorityLower.includes('normal') || priorityLower.includes('нормальн')) {
        return { class: 'priority-normal', icon: 'fas fa-circle' };
    } else if (priorityLower.includes('низк') || priorityLower.includes('low')) {
        return { class: 'priority-low', icon: 'fas fa-arrow-down' };
    } else if (priorityLower.includes('критич') || priorityLower.includes('critical') || priorityLower.includes('срочн')) {
        return { class: 'priority-critical', icon: 'fas fa-exclamation-triangle' };
    }
    return { class: 'priority-default', icon: 'fas fa-question' };
}

// Форматирование дат
function formatDate(dateString, isStartDate) {
    if (!dateString) return isStartDate ? '-' : 'Не указано';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        return 'Неверная дата';
    }
}

// Экранирование HTML
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text
        ? String(text).replace(/[&<>"']/g, function(m) { return map[m]; })
        : '';
}

// Функция для отображения индикатора загрузки
function showTableLoading() {
    console.log('[TasksPaginated] Показываем индикатор загрузки...');

    // Используем новый спиннер в стиле Issues
    if (window.loadingManager && typeof window.loadingManager.show === 'function') {
        window.loadingManager.show();
        console.log('[TasksPaginated] Индикатор загрузки показан через LoadingManager');
        return;
    }

    // Fallback: показываем спиннер напрямую
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.style.display = 'flex';
        spinner.classList.add('show');
        console.log('[TasksPaginated] Индикатор загрузки показан через DOM');
    }
}

// Функция для скрытия индикатора загрузки
function hideTableLoading() {
    console.log('[TasksPaginated] Скрываем индикатор загрузки...');

    // Используем новый спиннер в стиле Issues
    if (window.loadingManager && typeof window.loadingManager.hide === 'function') {
        window.loadingManager.hide();
        console.log('[TasksPaginated] Индикатор загрузки скрыт через LoadingManager');
        return;
    }

    // Fallback: скрываем спиннер напрямую
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.classList.remove('show');
        setTimeout(() => {
            spinner.style.display = 'none';
        }, 300);
        console.log('[TasksPaginated] Индикатор загрузки скрыт через DOM');
    }
}

// Делаем функции доступными глобально
window.showTableLoading = showTableLoading;
window.hideTableLoading = hideTableLoading;

function showError(message) {
    console.error('[TasksPaginated] Ошибка:', message);

    const errorHtml = '<div class="alert alert-danger mt-3" role="alert">' +
        '<i class="fas fa-exclamation-triangle"></i>' +
        '<strong>Ошибка:</strong> ' + message +
        '<button type="button" class="close" onclick="$(this).parent().fadeOut()">' +
        '<span>&times;</span>' +
        '</button>' +
        '</div>';
    $('#tasks-container').prepend(errorHtml);
}

// Очистка фильтров
function clearAndDisableFilters() {
    console.log('[TasksPaginated] clearAndDisableFilters вызвана - очищаем и блокируем фильтры');
    $('#status-filter, #project-filter, #priority-filter').each(function() {
        $(this).empty().append('<option value="">Ошибка загрузки</option>').prop('disabled', true);
    });
}

// Кэш для фильтров
let filtersCache = {
    data: null,
    timestamp: null,
    duration: 300000, // 5 минут в миллисекундах
    isLoading: false
};

// Загрузка фильтров - УЛУЧШЕННАЯ ВЕРСИЯ с иерархическим деревом
function loadAllFiltersAsync() {
    if (filtersCache.isLoading) {
        console.log('[TasksPaginated] Фильтры уже загружаются, пропускаем...');
        return;
    }

    // Проверяем кэш (5 минут)
    const now = Date.now();
    const cacheValidTime = 5 * 60 * 1000; // 5 минут
    if (filtersCache.data &&
        filtersCache.timestamp &&
        (now - filtersCache.timestamp) < cacheValidTime) {
        console.log('[TasksPaginated] Используем кэшированные фильтры');
        updateFilterOptions(filtersCache.data);
        return;
    }

    console.log('[TasksPaginated] 🚀 Загрузка фильтров с архитектурой разделения ответственности...');
    filtersCache.isLoading = true;
    showFiltersLoadingIndicator(true);

    // Используем быстрый API с прямыми SQL запросами
    $.get('/tasks/get-my-tasks-filters-optimized')
        .done(function(response) {
            if (response.success) {
                console.log('[TasksPaginated] 🏗️ Фильтры получены с правильной архитектурой');
                console.log('[TasksPaginated] Статусы (локализованные из u_statuses):', response.statuses?.length || 0);
                console.log('[TasksPaginated] Проекты (иерархические):', response.projects?.length || 0);
                console.log('[TasksPaginated] Приоритеты (отдельный API):', response.priorities?.length || 0);

                // ДИАГНОСТИКА: Выводим примеры данных для каждого типа фильтра
                if (response.statuses && response.statuses.length > 0) {
                    console.log('[TasksPaginated] 🔍 ПРИМЕР СТАТУСА:', response.statuses[0]);
                }
                if (response.projects && response.projects.length > 0) {
                    console.log('[TasksPaginated] 🔍 ПРИМЕР ПРОЕКТА:', response.projects[0]);
                }
                if (response.priorities && response.priorities.length > 0) {
                    console.log('[TasksPaginated] 🔍 ПРИМЕР ПРИОРИТЕТА:', response.priorities[0]);
                }

                if (response.performance) {
                    console.log('[TasksPaginated] Производительность:', response.performance);
                    if (response.performance.architecture) {
                        console.log('[TasksPaginated] Архитектура:', response.performance.architecture);
                    }
                }

                const filters = {
                    statuses: response.statuses || [],
                    projects: response.projects || [],
                    priorities: response.priorities || [],
                    hierarchical: response.hierarchical || false
                };

                // Кэшируем данные
                filtersCache.data = filters;
                filtersCache.timestamp = now;

                updateFilterOptionsHierarchical(filters);
            } else {
                console.error('[TasksPaginated] Иерархический API вернул success: false');
                fallbackToOldAPI();
            }
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            console.warn('[TasksPaginated] Иерархический API недоступен, переходим на старый API');
            console.warn('[TasksPaginated] Ошибка:', textStatus, errorThrown);
            fallbackToOldAPI();
        })
        .always(function() {
            filtersCache.isLoading = false;
            showFiltersLoadingIndicator(false);
        });

    // Fallback на старый API
    function fallbackToOldAPI() {
        console.log('[TasksPaginated] Используем старый API фильтров...');
        $.get('/tasks/get-my-tasks-filters-direct-api')
            .done(function(response) {
                if (response.success) {
                    console.log('[TasksPaginated] Старый API сработал успешно');
                    const filters = {
                        statuses: response.statuses || [],
                        projects: response.projects || [],
                        priorities: response.priorities || [],
                        hierarchical: false
                    };

                    // Кэшируем данные
                    filtersCache.data = filters;
                    filtersCache.timestamp = now;

                    updateFilterOptions(filters);
                } else {
                    console.error('[TasksPaginated] Старый API тоже не сработал');
                    clearAndDisableFilters();
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error('[TasksPaginated] Все API недоступны:', textStatus, errorThrown);
                clearAndDisableFilters();
            });
    }
}

// Обновление опций фильтров - НОВАЯ ВЕРСИЯ с поддержкой иерархии
function updateFilterOptionsHierarchical(filters) {
    // Обновляем обычные фильтры
    populateStandardSelect('#status-filter', filters.statuses, 'Все статусы');
    populateStandardSelect('#priority-filter', filters.priorities, 'Все приоритеты');

    // ОТКЛЮЧЕНО: TreeView для упрощения и избежания конфликтов
    // Всегда используем простую фильтрацию проектов
    console.log('[TasksPaginated] 📋 Используем простую фильтрацию для проектов (TreeView отключен для стабильности)');
    populateProjectSelect('#project-filter', filters.projects, 'Все проекты');

    // КРИТИЧНО: Обновляем видимость кнопок очистки после загрузки всех фильтров
    setTimeout(() => {
        updateAllClearButtons();
        console.log('[TasksPaginated] Видимость кнопок очистки обновлена после загрузки фильтров');
    }, 100);

    console.log('[TasksPaginated] Фильтры обновлены успешно');
}

// ОТКЛЮЧЕНО: Инициализация TreeView для проектов
// ПРИЧИНА: Упрощение интерфейса и избежание конфликтов фильтрации
function initializeProjectTreeView(projects) {
    console.warn('[TasksPaginated] TreeView отключен - используется простая фильтрация проектов');

    // Показываем обычный селект вместо TreeView
    const oldSelect = $('#project-filter');
    oldSelect.show();

    // Заполняем обычный селект
    populateProjectSelect('#project-filter', projects, 'Все проекты');

    return; // Досрочный выход - остальной код TreeView не выполняется
}

// Обновление опций фильтров - СТАРАЯ ВЕРСИЯ для обратной совместимости
function updateFilterOptions(filters) {
    console.log('[TasksPaginated] Обновление фильтров (старый режим) - статусы:', filters.statuses?.length, ', проекты:', filters.projects?.length, ', приоритеты:', filters.priorities?.length);

    populateStandardSelect('#status-filter', filters.statuses, 'Все статусы');
    populateProjectSelect('#project-filter', filters.projects, 'Все проекты');
    populateStandardSelect('#priority-filter', filters.priorities, 'Все приоритеты');

    // Обновляем видимость кнопок сброса после загрузки фильтров
    updateAllClearButtons();

    console.log('[TasksPaginated] Фильтры обновлены успешно (старый режим)');
}

// Функция для заполнения обычных селектов
function populateStandardSelect(selector, options, defaultOptionText) {
    const select = $(selector);
    console.log('[TasksPaginated] populateStandardSelect для', selector, '- найден селект:', select.length > 0, ', опций:', (options || []).length);

    if (select.length) {
        // ИСПРАВЛЕНО: НЕ сохраняем currentValue - принудительно сбрасываем к дефолту
        select.empty().append('<option value="">' + defaultOptionText + '</option>');

        // ИСПРАВЛЕНО v2: Гарантируем, что ID всегда числовой
        (options || []).forEach(function(opt) {
            // Проверяем и конвертируем ID в число если нужно
            let id = opt.id;
            if (typeof id === 'string') {
                // Пробуем конвертировать строку в число
                const numId = parseInt(id, 10);
                if (!isNaN(numId)) {
                    id = numId; // Используем числовое значение если возможно
                }
            }

            // Добавляем опцию с правильным ID
            select.append('<option value="' + id + '">' + escapeHtml(opt.name) + '</option>');

            // Логируем для диагностики
            console.log('[TasksPaginated] Добавлена опция:', {
                name: opt.name,
                original_id: opt.id,
                id_type: typeof opt.id,
                used_id: id,
                used_id_type: typeof id
            });
        });

        // КРИТИЧНО: Принудительно устанавливаем пустое значение (дефолт)
        select.val('');

        const container = select.closest('.filter-container');
        // После принудительного сброса контейнер НЕ должен иметь has-value
        container.removeClass('has-value');

        console.log('[TasksPaginated] Селект', selector, 'заполнен и сброшен к дефолту, итого опций:', select.find('option').length, ', текущее значение:', select.val());
    } else {
        console.error('[TasksPaginated] Селект', selector, 'не найден в DOM!');
    }
}

// Функция для заполнения селекта проектов ПРОСТЫМ СПИСКОМ
function populateProjectSelect(selector, options, defaultOptionText) {
    const select = $(selector);
    if (!select.length) return;

    // ИСПРАВЛЕНО: НЕ сохраняем currentValue - принудительно сбрасываем к дефолту
    select.empty().append('<option value="">' + defaultOptionText + '</option>');

    console.log('[Projects] Получено проектов для отображения (простой список):', options.length);

    // Сортируем проекты по алфавиту для удобства
    const sortedProjects = (options || []).sort(function(a, b) {
        const nameA = (a.original_name || a.name || '').toLowerCase();
        const nameB = (b.original_name || b.name || '').toLowerCase();
        return nameA.localeCompare(nameB);
    });

    // Добавляем все проекты как простой список
    sortedProjects.forEach(function(opt) {
        const option = document.createElement('option');

        // ИСПРАВЛЕНО v2: Гарантируем, что ID всегда числовой
        let id = opt.id;
        if (typeof id === 'string') {
            // Пробуем конвертировать строку в число
            const numId = parseInt(id, 10);
            if (!isNaN(numId)) {
                id = numId; // Используем числовое значение если возможно
            }
        }

        option.value = id;

        // Простое отображение только названия проекта
        const displayName = opt.original_name || opt.name;
        option.textContent = displayName;

        // Добавляем минимальные атрибуты для поиска
        option.setAttribute('data-name', displayName.toLowerCase());

        // Логируем для диагностики
        console.log('[Projects] Добавлен проект:', {
            name: displayName,
            original_id: opt.id,
            id_type: typeof opt.id,
            used_id: id,
            used_id_type: typeof id
        });

        select.append(option);
    });

    // КРИТИЧНО: Принудительно устанавливаем пустое значение (дефолт)
    select.val('');

    // Обновляем визуальное состояние контейнера - убираем has-value
    const container = select.closest('.filter-container');
    container.removeClass('has-value');

    // Добавляем функциональность поиска для селекта проектов
    addSearchFunctionality(select);

    console.log('[Projects] Простой список проектов загружен и сброшен к дефолту, значение:', select.val());
}

// ПРОСТАЯ функция поиска для проектов
function addSearchFunctionality(select) {
    const selectElement = select[0];
    if (!selectElement || selectElement.dataset.searchEnabled) return;

    selectElement.dataset.searchEnabled = 'true';
    console.log('[Projects] Добавляем простой поиск для селекта проектов');

    // Сохраняем оригинальные опции один раз
    const originalHTML = selectElement.innerHTML;
    const allOptions = Array.from(selectElement.options);

    // КРИТИЧНО: Отключаем стандартное поведение select
    selectElement.style.pointerEvents = 'none';
    selectElement.setAttribute('readonly', true);

    // Создаем невидимый overlay для перехвата кликов НО исключаем кнопку очистки
    const overlay = document.createElement('div');
    overlay.className = 'project-select-overlay';
    overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 5;
        cursor: pointer;
        background: transparent;
    `;

    // Добавляем overlay в контейнер
    const container = selectElement.closest('.filter-container');
    if (container.style.position === 'static' || !container.style.position) {
        container.style.position = 'relative';
    }
    container.appendChild(overlay);

    // ИСПРАВЛЕНО: Обработчик клика проверяет что клик НЕ по кнопке очистки
    overlay.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        // Проверяем что клик НЕ попал в область кнопки очистки
        const clearBtn = container.querySelector('.filter-clear-btn');
        if (clearBtn) {
            const clearBtnRect = clearBtn.getBoundingClientRect();
            const clickX = e.clientX;
            const clickY = e.clientY;

            // Если клик попал в область кнопки очистки, игнорируем
            if (clickX >= clearBtnRect.left && clickX <= clearBtnRect.right &&
                clickY >= clearBtnRect.top && clickY <= clearBtnRect.bottom) {
                console.log('[Projects] Клик по кнопке очистки, игнорируем overlay');
                return;
            }
        }

        console.log('[Projects] Клик по overlay - показываем кастомный дропдаун');
        // Показываем простой список с поиском
        showProjectSearchDropdown(selectElement, allOptions, originalHTML);
    });

    // Дополнительно блокируем любые события на select
    selectElement.addEventListener('mousedown', function(e) {
        e.preventDefault();
        e.stopPropagation();
    });

    selectElement.addEventListener('focus', function(e) {
        e.preventDefault();
        this.blur();
    });
}

// Простой dropdown для поиска проектов
function showProjectSearchDropdown(selectElement, allOptions, originalHTML) {
    // Удаляем существующий dropdown если есть
    const existingDropdown = document.querySelector('.project-search-dropdown');
    if (existingDropdown) {
        existingDropdown.remove();
    }

    const container = selectElement.closest('.filter-container');
    const rect = selectElement.getBoundingClientRect();

    // Альтернативный подход: создаем дропдаун в body с фиксированным позиционированием
    const useBodyDropdown = true;

    // Убеждаемся что контейнер имеет position: relative
    const containerStyle = window.getComputedStyle(container);
    if (containerStyle.position === 'static') {
        container.style.position = 'relative';
    }

    // Добавляем overflow: visible для родительских элементов
    let parent = container.parentElement;
    while (parent && parent !== document.body) {
        const parentStyle = window.getComputedStyle(parent);
        if (parentStyle.overflow === 'hidden') {
            parent.style.overflow = 'visible';
            console.log('[Projects] Исправлен overflow для:', parent.className);
        }
        parent = parent.parentElement;
    }

    // Создаем dropdown - либо в body (фиксированный), либо в контейнере
    const dropdown = document.createElement('div');
    dropdown.className = 'project-search-dropdown';

    if (useBodyDropdown) {
        // Используем fixed позиционирование с правильными координатами
        console.log('[Projects] Создание body dropdown, координаты:', {
            top: rect.bottom + 2,
            left: rect.left,
            width: rect.width,
            selectRect: rect
        });
        dropdown.style.cssText = `
            position: fixed !important;
            top: ${rect.bottom + 2}px !important;
            left: ${rect.left}px !important;
            width: ${rect.width}px !important;
            background: white !important;
            border: 2px solid #ddd !important;
            border-radius: 8px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
            z-index: 999999 !important;
            max-height: 300px !important;
            overflow: hidden !important;
            transform: translateZ(0) !important;
        `;
    } else {
        // Обычное позиционирование в контейнере
        dropdown.style.cssText = `
            position: absolute !important;
            top: 100% !important;
            left: 0 !important;
            right: 0 !important;
            background: white !important;
            border: 2px solid #ddd !important;
            border-radius: 8px !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3) !important;
            z-index: 999999 !important;
            max-height: 300px !important;
            overflow: hidden !important;
            transform: translateZ(0) !important;
        `;
    }

    // Поле поиска
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Поиск проектов...';
    searchInput.style.cssText = `
        width: 100%;
        padding: 12px;
        border: none;
        border-bottom: 1px solid #eee;
        font-size: 14px;
        outline: none;
    `;

    // Список опций
    const optionsList = document.createElement('div');
    optionsList.style.cssText = `
        max-height: 250px;
        overflow-y: auto;
    `;

    // Функция для отображения опций
    function renderOptions(searchTerm = '') {
        optionsList.innerHTML = '';

        allOptions.forEach(option => {
            const optionText = option.textContent.toLowerCase();
            if (optionText.includes(searchTerm.toLowerCase())) {
                const optionDiv = document.createElement('div');
                optionDiv.textContent = option.textContent;
                optionDiv.style.cssText = `
                    padding: 10px 12px;
                    cursor: pointer;
                    border-bottom: 1px solid #f5f5f5;
                    transition: background-color 0.2s;
                `;

                // Выделяем выбранную опцию
                if (option.value === selectElement.value) {
                    optionDiv.style.backgroundColor = '#e3f2fd';
                    optionDiv.style.fontWeight = 'bold';
                }

                optionDiv.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#f5f5f5';
                });

                optionDiv.addEventListener('mouseleave', function() {
                    if (option.value !== selectElement.value) {
                        this.style.backgroundColor = 'white';
                    }
                });

                optionDiv.addEventListener('click', function() {
                    selectElement.value = option.value;
                    selectElement.dispatchEvent(new Event('change'));
                    dropdown.remove();

                    // Обновляем кнопку очистки
                    if (typeof updateClearButtonVisibility === 'function') {
                        updateClearButtonVisibility($(selectElement));
                    }

                    // Перезагружаем таблицу если нужно
                    if (typeof loadScrollDataWithFilters === 'function') {
                        loadScrollDataWithFilters();
                    }
                });

                optionsList.appendChild(optionDiv);
            }
        });
    }

    // Поиск в реальном времени
    searchInput.addEventListener('input', function() {
        renderOptions(this.value);
    });

    // Собираем dropdown
    dropdown.appendChild(searchInput);
    dropdown.appendChild(optionsList);

    // Добавляем в DOM
    if (useBodyDropdown) {
        document.body.appendChild(dropdown);
    } else {
        container.appendChild(dropdown);
    }

    // Показываем все опции изначально
    renderOptions();

    // Фокус на поиск
    setTimeout(() => searchInput.focus(), 10);

    // Закрытие при клике вне
    function closeDropdown(e) {
        if (!dropdown.contains(e.target) && !selectElement.contains(e.target)) {
            dropdown.remove();
            document.removeEventListener('click', closeDropdown);
            if (useBodyDropdown) {
                window.removeEventListener('scroll', updateDropdownPosition);
                window.removeEventListener('resize', closeDropdownHandler);
            }
        }
    }

    // Для body dropdown - обновляем позицию при скролле
    function updateDropdownPosition() {
        if (useBodyDropdown && dropdown.parentElement) {
            const newRect = selectElement.getBoundingClientRect();
            dropdown.style.top = `${newRect.bottom + 2}px`;
            dropdown.style.left = `${newRect.left}px`;
            dropdown.style.width = `${newRect.width}px`;
        }
    }

    function closeDropdownHandler() {
        dropdown.remove();
        document.removeEventListener('click', closeDropdown);
        if (useBodyDropdown) {
            window.removeEventListener('scroll', updateDropdownPosition);
            window.removeEventListener('resize', closeDropdownHandler);
        }
    }

    setTimeout(() => {
        document.addEventListener('click', closeDropdown);
        if (useBodyDropdown) {
            window.addEventListener('scroll', updateDropdownPosition);
            window.addEventListener('resize', closeDropdownHandler);
        }
    }, 10);

    // Закрытие по Escape
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeDropdownHandler();
        }
    });

    console.log('[Projects] Простой поиск открыт, опций доступно:', allOptions.length);
}

// Индикатор загрузки фильтров (быстрый)
function showFiltersLoadingIndicator(isLoading) {
    if(isLoading) {
        // Только меняем текст первой опции, не блокируем селекты
        $('#status-filter').find('option:first').text('⏳ Загрузка...');
        $('#project-filter').find('option:first').text('⏳ Загрузка...');
        $('#priority-filter').find('option:first').text('⏳ Загрузка...');

        // Добавляем класс для визуального эффекта
        $('.filters-section').addClass('loading-filters');
    } else {
        $('#status-filter').find('option:first').text('Все статусы');
        $('#project-filter').find('option:first').text('Все проекты');
        $('#priority-filter').find('option:first').text('Все приоритеты');

        $('.filters-section').removeClass('loading-filters');
    }
}

// Загрузка статистики для блока "Разбивка по статусам"
function loadFullStatisticsAsync() {
    console.log('[TasksPaginated] Загрузка статистики разбивки по статусам...');

    // Показываем состояние загрузки
    showLoadingState();

    $.get('/tasks/get-my-tasks-statistics-optimized')
        .done(function(response) {
            if (response.success || response.total_tasks !== undefined) {
                console.log('[TasksPaginated] Статистика получена:', response);
                updateStatusBreakdownCards(response);
                updateDetailedStatusBreakdown(response);

                // Инициализируем аккордеон статусов
                initializeStatusAccordion(response);
            } else {
                console.error('[TasksPaginated] Ошибка загрузки статистики:', response.error);
                showErrorState();
                showAccordionError();
            }
        })
        .fail(function() {
            console.error('[TasksPaginated] Критическая ошибка API статистики.');
            showErrorState();
            showAccordionError();
        });
}

function showLoadingState() {
    $('.status-breakdown-card').addClass('loading');
    $('#total-tasks-summary').addClass('loading').text('...');
    $('#total-tasks, #open-tasks, #closed-db-tasks, #paused-tasks').text('...');
}

function showErrorState() {
    $('.status-breakdown-card').removeClass('loading');
    $('#total-tasks-summary').removeClass('loading').text('Ошибка');
    $('#total-tasks, #open-tasks, #closed-db-tasks, #paused-tasks').text('Ошибка');
}

function updateStatusBreakdownCards(stats) {
    console.log('[TasksPaginated] Обновление карточек разбивки по статусам...');

    // Убираем состояние загрузки
    $('.status-breakdown-card').removeClass('loading');
    $('#total-tasks-summary').removeClass('loading');

    // Основные значения
    const totalTasks = stats.total_tasks || stats.total || 0;
    const newTasks = stats.new_tasks || stats.new || 0;
    const inProgressTasks = stats.in_progress_tasks || stats.in_progress || 0;
    const closedTasks = stats.closed_tasks || stats.closed || 0;

    // ИСПРАВЛЕННАЯ логика вычисления метрик
    const actuallyClosedTasks = stats.statistics?.additional_stats?.actually_closed_tasks || 0; // Реально закрытые в БД

    // ИСПРАВЛЕНО: Используем данные прямо из API (NEW_TASKS = ОТКРЫТЫЕ)
    const openTasks = newTasks; // API уже правильно классифицировал NEW задачи

    console.log('[TasksPaginated] Открытые задачи из API:', {
        newTasks: newTasks,
        openTasks: openTasks
    });

    // ИСПРАВЛЕНО: Используем данные прямо из API (IN_PROGRESS_TASKS = ПРИОСТАНОВЛЕННЫЕ)
    const pausedTasks = inProgressTasks; // API уже правильно классифицировал IN_PROGRESS задачи

    console.log('[TasksPaginated] Приостановленные задачи из API:', {
        inProgressTasks: inProgressTasks,
        pausedTasks: pausedTasks
    });

    // Обновляем значения с анимацией
    animateAndUpdateValue('#total-tasks-summary', totalTasks);
    animateAndUpdateValue('#total-tasks', totalTasks);
    animateAndUpdateValue('#open-tasks', openTasks);
    animateAndUpdateValue('#closed-db-tasks', actuallyClosedTasks);
    animateAndUpdateValue('#paused-tasks', pausedTasks);

    // Обновляем детализацию в карточках
    updateCardBreakdowns(stats.statistics?.debug_status_counts || {}, {
        totalTasks,
        openTasks,
        actuallyClosedTasks,
        pausedTasks
    });

    console.log('[TasksPaginated] Разбивка по статусам обновлена:', {
        total: totalTasks,
        open: openTasks,
        closed_db: actuallyClosedTasks,
        paused: pausedTasks,
        in_progress: inProgressTasks
    });
}

function animateAndUpdateValue(selector, value) {
    const element = $(selector);
    element.addClass('animate-count').text(value);
    setTimeout(() => element.removeClass('animate-count'), 600);
}

    function updateCardBreakdowns(statusCounts, cardValues) {
    console.log('[TasksPaginated] Обновление детализации в карточках...');

    // Обновляем детализацию для "Открытые задачи" - добавлены русские названия
    updateCardBreakdown('#open-breakdown', statusCounts, [
        'New', 'Open', 'Новая', 'Новый', 'Открыта', 'Открыт', 'Открытая'
    ]);

    // Обновляем детализацию для "Закрытые в БД" - добавлены русские названия
    updateCardBreakdown('#closed-breakdown', statusCounts, [
        'Closed', 'Rejected', 'Redirected', 'Закрыта', 'Закрыт', 'Закрытая',
        'Отклонена', 'Отклонен', 'Отклонённая', 'Перенаправлена', 'Перенаправлен'
    ]);

    // Обновляем детализацию для "Приостановленные" - добавлены русские названия
    updateCardBreakdown('#paused-breakdown', statusCounts, [
        'Paused', 'Frozen', 'In Progress', 'Executed', 'On testing',
        'The request specification', 'On the coordination', 'Tested',
        'Приостановлена', 'Приостановлен', 'Заморожена', 'Заморожен',
        'В работе', 'В процессе', 'Выполнена', 'Выполнен', 'На тестировании',
        'На согласовании', 'Согласование', 'Запрошено уточнение', 'Уточнение',
        'Протестирована', 'Протестирован'
    ]);

    // Обновляем детализацию для "Всего задач" - показываем ВСЕ статусы
    updateCardBreakdownAll('#total-breakdown', statusCounts);

    // ВАЖНО: Переинициализируем состояние кнопок после обновления содержимого
    setTimeout(() => {
        $('.card-breakdown').addClass('collapsed').removeClass('expanded');
        $('.card-toggle-btn').removeClass('expanded');
        console.log('[TasksPaginated] Состояние кнопок переустановлено после обновления карточек');
    }, 100);
}

function updateCardBreakdown(containerId, statusCounts, relevantStatuses) {
    const container = $(containerId);
    if (container.length === 0) {
        console.warn(`[TasksPaginated] Контейнер ${containerId} не найден`);
        return;
    }

    container.empty();

    // Преобразуем все статусы в массив для более гибкой обработки
    const allStatusEntries = Object.entries(statusCounts)
        .map(([name, count]) => ({ name, count }))
        .filter(item => item.count > 0);

    // Фильтрация по релевантным статусам с учетом и русских, и английских названий
    const filteredStatuses = allStatusEntries.filter(item => {
        const statusName = item.name.toLowerCase();
        // Проверяем, соответствует ли статус любому из списка релевантных
        return relevantStatuses.some(relevantStatus => {
            const relevantLower = relevantStatus.toLowerCase();
            // Прямое совпадение или частичное совпадение для разных языковых вариантов
            return statusName === relevantLower ||
                   statusName.includes(relevantLower) ||
                   relevantLower.includes(statusName);
        });
    });

    if (filteredStatuses.length === 0) {
        container.html('<div class="breakdown-item"><span class="breakdown-status-name">Нет данных</span></div>');
        return;
    }

    // Сортируем статусы по количеству задач (по убыванию)
    filteredStatuses.sort((a, b) => b.count - a.count);

    // Создаем элементы детализации
    filteredStatuses.forEach(item => {
        const breakdownItem = $(`
            <div class="breakdown-item">
                <span class="breakdown-status-name">${item.name}</span>
                <span class="breakdown-status-count">${item.count}</span>
            </div>
        `);
        container.append(breakdownItem);
    });

    console.log(`[TasksPaginated] Детализация обновлена для ${containerId}:`, filteredStatuses);
}

function updateCardBreakdownAll(containerId, statusCounts) {
    const container = $(containerId);
    if (container.length === 0) {
        console.warn(`[TasksPaginated] Контейнер ${containerId} не найден`);
        return;
    }

    container.empty();

    if (!statusCounts || Object.keys(statusCounts).length === 0) {
        container.html('<div class="breakdown-item"><span class="breakdown-status-name">Нет данных</span></div>');
        return;
    }

    // Преобразуем все статусы в массив и сортируем по убыванию количества
    const allStatuses = Object.entries(statusCounts)
        .map(([name, count]) => ({ name, count }))
        .filter(item => item.count > 0)
        .sort((a, b) => b.count - a.count);

    if (allStatuses.length === 0) {
        container.html('<div class="breakdown-item"><span class="breakdown-status-name">Нет задач</span></div>');
        return;
    }

    // Создаем элементы детализации для всех статусов
    allStatuses.forEach(item => {
        const breakdownItem = $(`
            <div class="breakdown-item">
                <span class="breakdown-status-name">${item.name}</span>
                <span class="breakdown-status-count">${item.count}</span>
            </div>
        `);
        container.append(breakdownItem);
    });

    console.log(`[TasksPaginated] Полная детализация для ${containerId}:`, allStatuses);
}

function updateDetailedStatusBreakdown(stats) {
    if (!stats.statistics?.debug_status_counts) {
        console.log('[TasksPaginated] Детальные данные статусов недоступны');
        window.detailedStatusData = {};
        return;
    }

    const statusCounts = stats.statistics.debug_status_counts;
    console.log('[TasksPaginated] Обновление детальной разбивки:', statusCounts);

    // Проверяем, что statusCounts является объектом и содержит данные
    if (typeof statusCounts !== 'object' || Object.keys(statusCounts).length === 0) {
        console.log('[TasksPaginated] Нет данных для детальной разбивки');
        window.detailedStatusData = {};
        return;
    }

    // Сохраняем данные для детальной разбивки, чтобы CardBreakdown мог их использовать
    window.detailedStatusData = statusCounts;
    console.log('[TasksPaginated] Сохранены данные для детальной разбивки:', window.detailedStatusData);

    // Активируем кнопку детальной разбивки
    const expandBreakdownBtn = $('#expandBreakdownBtn');
    if (expandBreakdownBtn.length > 0) {
        expandBreakdownBtn.removeClass('disabled').prop('disabled', false);
        console.log('[TasksPaginated] Кнопка детальной разбивки активирована');
    }
}

// Инициализация кнопки развертывания детальной разбивки
function initializeDetailedBreakdown() {
    console.log('[TasksPaginated] Инициализация кнопки детальной разбивки...');

    // Очищаем старые обработчики чтобы избежать дублирования
    $(document).off('click', '#expandBreakdownBtn');

    $(document).on('click', '#expandBreakdownBtn', function() {
        console.log('[TasksPaginated] Клик по кнопке детальной разбивки');

        const button = $(this);
        const content = $('#detailedBreakdownContent');
        const isExpanded = content.hasClass('expanded');

        console.log('[TasksPaginated] Текущее состояние expanded:', isExpanded);

        if (isExpanded) {
            // Сворачиваем
            console.log('[TasksPaginated] Сворачиваем детальную разбивку');
            content.removeClass('expanded');
            button.removeClass('expanded');
            button.find('span').text('Показать детали');
        } else {
            // Разворачиваем
            console.log('[TasksPaginated] Разворачиваем детальную разбивку');

            // Всегда рендерим данные заново
            if (window.detailedStatusData) {
                console.log('[TasksPaginated] Рендерим детальные данные:', window.detailedStatusData);
                renderDetailedStatusBreakdown(window.detailedStatusData);
            } else {
                console.warn('[TasksPaginated] Нет данных для детальной разбивки!');
                $('#statusItemsGrid').html('<div class="no-data">Нет данных для отображения</div>');
            }

            content.addClass('expanded');
            button.addClass('expanded');
            button.find('span').text('Скрыть детали');
        }
    });

    // Также нужно проверить, есть ли у нас данные, и если да, активировать кнопку
    if (window.detailedStatusData) {
        const expandBtn = $('#expandBreakdownBtn');
        if (expandBtn.length > 0) {
            expandBtn.prop('disabled', false).removeClass('disabled');
            console.log('[TasksPaginated] Кнопка детальной разбивки активирована при инициализации');
        }
    }

    console.log('[TasksPaginated] Кнопка детальной разбивки инициализирована');
}

function renderDetailedStatusBreakdown(statusCounts) {
    console.log('[TasksPaginated] Начинаем рендеринг детальной разбивки с данными:', statusCounts);

    // Сохраняем данные для модуля CardBreakdown
    window.detailedStatusData = statusCounts;

    // Делегируем отрисовку модулю CardBreakdown если он доступен
    if (window.CardBreakdown && typeof window.CardBreakdown.renderDetailedBreakdown === 'function') {
        console.log('[TasksPaginated] Делегируем отрисовку модулю CardBreakdown');
        window.CardBreakdown.renderDetailedBreakdown(statusCounts);
        return;
    }

    // Запасной вариант, если модуль CardBreakdown недоступен
    const grid = $('#statusItemsGrid');
    if (grid.length === 0) {
        console.error('[TasksPaginated] Контейнер #statusItemsGrid не найден!');
        return;
    }

    console.log('[TasksPaginated] Очищаем grid контейнер');
    grid.empty();

    if (!statusCounts || Object.keys(statusCounts).length === 0) {
        console.warn('[TasksPaginated] Нет данных для рендеринга');
        grid.html('<div class="no-data">Нет данных для отображения</div>');
        return;
    }

    let itemsAdded = 0;
    // Сортируем статусы по количеству задач (по убыванию)
    Object.entries(statusCounts)
        .sort(([, countA], [, countB]) => countB - countA)
        .forEach(([statusName, count]) => {
            // Показываем только те статусы, у которых есть хотя бы одна задача
            if (count > 0) {
                const statusType = getStatusType(statusName);
                const statusItem = $(`
                    <div class="status-item ${statusType}">
                        <span class="status-name">${statusName}</span>
                        <span class="status-count animate-count">${count}</span>
                    </div>
                `);
                grid.append(statusItem);
                itemsAdded++;
                console.log(`[TasksPaginated] Добавлен элемент: ${statusName} = ${count} (тип: ${statusType})`);
            }
        });

    if (itemsAdded === 0) {
        grid.html('<div class="no-data">У вас нет задач со статусами</div>');
    } else {
        console.log(`[TasksPaginated] Детальная разбивка отрендерена: ${itemsAdded} элементов`);
    }
}

// Функция для определения типа статуса (используется в renderDetailedStatusBreakdown)
function getStatusType(statusName) {
    const status = statusName.toLowerCase();

    // РЕАЛЬНО ЗАКРЫТЫЕ статусы (is_closed=1 в БД)
    if (status.includes('закрыта') || status.includes('закрыт') || status.includes('closed') ||
        status.includes('отклонена') || status.includes('отклонен') || status.includes('rejected') ||
        status.includes('перенаправлена') || status.includes('redirected')) {
        return 'status-closed';
    }
    // НОВЫЕ и ОТКРЫТЫЕ статусы
    if (status.includes('новая') || status.includes('новый') || status.includes('new') ||
             status.includes('открыта') || status.includes('открыт') || status.includes('open')) {
        return 'status-new';
    }
    // В РАБОТЕ и ПРОЦЕССЕ (включая те что кажутся "завершенными", но is_closed=0)
    else if (status.includes('в работе') || status.includes('in progress') ||
             status.includes('тестирован') || status.includes('tested') ||
             status.includes('testing') || status.includes('on testing') ||
             status.includes('согласован') || status.includes('coordination') ||
             status.includes('on the coordination') ||
             status.includes('уточнение') || status.includes('specification') ||
             status.includes('request specification') ||
             status.includes('выполнена') || status.includes('выполнен') || status.includes('executed') ||
             status.includes('протестирована') || status.includes('протестирован')) {
        return 'status-in-progress';
    }
    // ПРИОСТАНОВЛЕННЫЕ И ЗАМОРОЖЕННЫЕ
    else if (status.includes('приостановлена') || status.includes('приостановлен') || status.includes('paused') ||
             status.includes('заморожен') || status.includes('заморожена') || status.includes('frozen')) {
        return 'status-paused';
    }

    return 'status-default'; // По умолчанию
}

// Обработчик обновления информации о таблице
$('#tasksTable').on('draw.dt', function() {
    console.log('[TasksPaginated] 📊 DataTable draw event triggered');
    updateInfo();

    // Проверяем активные фильтры
    checkForActiveFilters();

    // Обновляем счетчик задач
    console.log('[TasksPaginated] 🔄 Обновляем индикатор через DataTable draw:', window.tasksDataTable);

    try {
        // Безопасное обращение к TasksCounterManager
        if (window.TasksCounterManager && typeof window.TasksCounterManager.updateCount === 'function') {
            window.TasksCounterManager.updateCount(window.tasksDataTable.rows({search:'applied'}).count());
        } else {
            console.log('[TasksPaginated] ⚠️ TasksCounterManager не найден или метод updateCount не определен');
        }
    } catch (e) {
        console.error('[TasksPaginated] ❌ Ошибка при обновлении счетчика:', e);
    }
});

// Функция полного сброса всех фильтров к дефолтному состоянию
function resetAllFilters() {
    console.log('[TasksPaginated] 🔄 Полный сброс всех фильтров к дефолтному состоянию');

    // Сбрасываем все селекты фильтров
    $('#status-filter').val('').trigger('change');
    $('#project-filter').val('').trigger('change');
    $('#priority-filter').val('').trigger('change');

    // Очищаем TreeView если он активен
    if (window.projectTreeView) {
        try {
            window.projectTreeView.clearAllSelections();
            console.log('[TasksPaginated] TreeView очищен');
        } catch (error) {
            console.warn('[TasksPaginated] Ошибка при очистке TreeView:', error);
        }
    }

    // Очищаем поле поиска DataTables
    const searchInput = $('#tasksTable_filter input[type="search"]');
    if (searchInput.length > 0) {
        searchInput.val('').trigger('input');
        console.log('[TasksPaginated] Поле поиска очищено');
    }

    // Удаляем все кастомные фильтры поиска
    while ($.fn.dataTable.ext.search.length > 0) {
        $.fn.dataTable.ext.search.pop();
    }

    // Обновляем видимость кнопок очистки
    updateAllClearButtons();

    // Скрываем счетчик фильтров если он был показан
    if (window.TasksCounterManager && typeof window.TasksCounterManager.hide === 'function') {
        window.TasksCounterManager.hide();
    }

    // Перерисовываем таблицу для применения изменений
    if (window.tasksDataTable) {
        window.tasksDataTable.draw();
    }

    console.log('[TasksPaginated] ✅ Все фильтры сброшены к дефолтному состоянию');
}

// Делаем функцию глобально доступной
window.resetAllFilters = resetAllFilters;

// Инициализация при загрузке DOM
$(function() {
    if (window.tasksDataTable) {
        console.log('[TasksPaginated] DataTable уже инициализирована');
        return;
    }
    initializePaginatedTasks();

    // Инициализируем детальную разбивку
    initializeDetailedBreakdown();

    // Принудительно проверяем работу кнопок переключения карточек
    setTimeout(() => {
        console.log('[TasksPaginated] 🛠️ Принудительная повторная инициализация кнопок переключения карточек...');

        // Повторно привязываем обработчики для кнопок переключения
        $('.card-toggle-btn').off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const $button = $(this);
            const targetId = $button.data('target');
            const $breakdown = $('#' + targetId);

            console.log('[TasksPaginated] 🔄 Клик по кнопке переключения. Target:', targetId, 'Found element:', $breakdown.length);

            if (!$breakdown.length) {
                console.warn('[TasksPaginated] ⚠️ Элемент детализации не найден:', targetId);
                return;
            }

            // Переключаем состояние
            if ($breakdown.hasClass('collapsed')) {
                // Разворачиваем
                $breakdown.removeClass('collapsed').addClass('expanded');
                $button.addClass('expanded');
                console.log('[TasksPaginated] 📊 Детализация развернута:', targetId);
            } else {
                // Сворачиваем
                $breakdown.removeClass('expanded').addClass('collapsed');
                $button.removeClass('expanded');
                console.log('[TasksPaginated] 📊 Детализация свернута:', targetId);
            }

            // Обновляем состояние глобальной кнопки
            updateGlobalToggleButtonState();
        });

        console.log('[TasksPaginated] ✅ Кнопки переключения карточек переинициализированы');
    }, 1000);
});

// ДОБАВЛЕНО: Дополнительная проверка кнопок очистки при полной загрузке страницы
$(window).on('load', function() {
    setTimeout(() => {
        console.log('[TasksPaginated] 🔧 Финальная проверка кнопок очистки при полной загрузке страницы');
        updateAllClearButtons();

        // Дополнительная диагностика
        $('#status-filter, #project-filter, #priority-filter').each(function() {
            const filterId = $(this).attr('id');
            const value = $(this).val();
            const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
            const clearBtn = $(clearBtnId);

            console.log(`[TasksPaginated] 🔍 Финальная диагностика ${filterId}:`, {
                value: value,
                hasShow: clearBtn.hasClass('show'),
                isVisible: clearBtn.is(':visible'),
                display: clearBtn.css('display')
            });
        });
    }, 500);
});

// Инициализация индикатора при загрузке страницы
$(function() {
    console.log('[TasksCounter] 📋 Страница загружена, инициализируем индикатор');

    setTimeout(() => {
        if (window.TasksCounterManager && window.TasksCounterManager.initialize) {
            window.TasksCounterManager.initialize();
        } else {
            console.warn('[TasksCounter] ⚠️ TasksCounterManager не найден или метод initialize не определен');
        }
    }, 200);
});

// Принудительная инициализация кнопок переключения карточек при полной загрузке страницы
$(function() {
    console.log('[TasksPaginated] 🛠️ Принудительная инициализация кнопок детализации при полной загрузке');

    // Прямая привязка обработчиков к кнопкам переключения карточек
    $('.card-toggle-btn').each(function() {
        const $btn = $(this);
        $btn.off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const targetId = $(this).data('target');
            const $breakdown = $('#' + targetId);

            console.log('[TasksPaginated] 🖱️ Клик по кнопке карточки:', targetId);

            if ($breakdown.hasClass('collapsed')) {
                // Разворачиваем
                $breakdown.removeClass('collapsed').addClass('expanded');
                $(this).addClass('expanded');
                console.log('[TasksPaginated] 📊 Детализация развернута:', targetId);
            } else {
                // Сворачиваем
                $breakdown.removeClass('expanded').addClass('collapsed');
                $(this).removeClass('expanded');
                console.log('[TasksPaginated] 📊 Детализация свернута:', targetId);
            }
        });
    });
});

console.log('[TasksPaginated] 🎉 Файл tasks_paginated.js полностью загружен с индикатором количества задач (v2024-CLEAR-BUTTONS-FIXED-v6)');

// Функция для принудительного обновления данных таблицы (доступна глобально)
window.forceReloadTasksTable = function() {
    console.log('[TasksPaginated] 🔄 Принудительное обновление данных таблицы');
    if (window.tasksDataTable) {
        showTableLoading();
        window.tasksDataTable.ajax.reload();
        return "✅ Обновление таблицы запущено";
    } else {
        console.error('[TasksPaginated] ❌ tasksDataTable не инициализирована');
        return "❌ Ошибка: таблица не инициализирована";
    }
};

// Функция для принудительной загрузки данных при первой загрузке страницы
window.forceInitialDataLoad = function() {
    console.log('[TasksPaginated] 🔄 Принудительная начальная загрузка данных');
    if (window.tasksDataTable) {
        window.isFirstDataLoad = true; // Устанавливаем флаг первой загрузки
        showTableLoading();
        window.tasksDataTable.ajax.reload();
        return "✅ Начальная загрузка данных запущена";
    } else {
        console.error('[TasksPaginated] ❌ tasksDataTable не инициализирована');
        return "❌ Ошибка: таблица не инициализирована";
    }
};

// Функция для экстренного сброса фильтров и перезагрузки таблицы (доступна глобально)
window.emergencyResetAndReload = function() {
    console.log('[TasksPaginated] 🚨 ЭКСТРЕННЫЙ СБРОС ФИЛЬТРОВ И ПЕРЕЗАГРУЗКА');

    try {
        // Сбрасываем все фильтры
        $('#status-filter, #project-filter, #priority-filter').val('').trigger('change');

        // Очищаем поле поиска
        $('.dataTables_filter input').val('').trigger('input');

        // Перезагружаем таблицу
        if (window.tasksDataTable) {
            showTableLoading();
            window.tasksDataTable.search('').draw();
            window.tasksDataTable.ajax.reload();
        } else {
            // Если таблица не инициализирована, пробуем инициализировать её
            initializeDataTable();
        }

        return "✅ Экстренный сброс выполнен";
    } catch (error) {
        console.error('[TasksPaginated] ❌ Ошибка при экстренном сбросе:', error);
        return "❌ Ошибка: " + error.message;
    }
};

// ===== МОДУЛЬ ИНДИКАТОРА КОЛИЧЕСТВА ЗАДАЧ =====

// Менеджер индикатора количества найденных задач
window.TasksCounterManager = {
    // Элементы интерфейса
    indicator: null,
    counterNumber: null,
    counterPrefix: null,
    counterSuffix: null,
    counterIcon: null,
    counterStatus: null,
    progressBar: null,
    closeBtn: null,

    // Состояние
    isVisible: false,
    isLoading: false,
    currentCount: 0,
    totalCount: 0,
    isFiltered: false,
    currentPaginationType: 'pages',

    // Инициализация
    init: function() {
        console.log('[TasksCounter] 🚀 Инициализация менеджера индикатора задач');

        if (!this.cacheElements()) {
            console.error('[TasksCounter] ❌ Не удалось инициализировать - элементы не найдены');
            return false;
        }

        this.bindEvents();
        this.setupCloseButton();
        this.hide(); // Первоначально скрыт

        console.log('[TasksCounter] ✅ Менеджер индикатора инициализирован');
        return true;
    },

    // Кеширование элементов DOM
    cacheElements: function() {
        this.indicator = document.getElementById('tasksCounterIndicator');
        this.counterNumber = document.getElementById('counterNumber');
        this.counterPrefix = document.getElementById('counterPrefix');
        this.counterSuffix = document.getElementById('counterSuffix');
        this.counterIcon = document.getElementById('counterIcon');
        this.counterStatus = document.getElementById('counterStatus');
        this.progressBar = document.getElementById('counterProgressBar');
        this.closeBtn = document.getElementById('counterCloseBtn');

        if (!this.indicator) {
            console.error('[TasksCounter] ❌ Основной элемент индикатора не найден (#tasksCounterIndicator)');
            return false;
        }

        console.log('[TasksCounter] ✅ Элементы DOM кешированы');
        return true;
    },

    // Привязка событий
    bindEvents: function() {
        const self = this;

        // Отслеживание изменений режима пагинации
        $(document).on('paginationModeChanged', function(e, mode) {
            console.log('[TasksCounter] 📊 Режим пагинации:', mode);
            self.currentPaginationType = mode;
            self.updateModeStyle(mode);
        });

        console.log('[TasksCounter] ✅ События привязаны');
    },

    // Настройка кнопки закрытия
    setupCloseButton: function() {
        if (this.closeBtn) {
            this.closeBtn.addEventListener('click', () => {
                console.log('[TasksCounter] 🔘 Кнопка закрытия нажата - сбрасываем все фильтры');

                // Вызываем функцию полного сброса всех фильтров
                if (typeof resetAllFilters === 'function') {
                    resetAllFilters();
                } else {
                    console.warn('[TasksCounter] Функция resetAllFilters не найдена, просто скрываем индикатор');
                    this.hide();
                }
            });
        }
    },

    // Показать индикатор
    show: function() {
        if (this.isVisible || !this.indicator) return;

        console.log('[TasksCounter] 👁️ Показываем индикатор');
        this.indicator.style.display = 'block';
        this.isVisible = true;

        setTimeout(() => {
            this.indicator.classList.add('show');
        }, 50);
    },

    // Скрыть индикатор
    hide: function() {
        if (!this.isVisible || !this.indicator) return;

        console.log('[TasksCounter] 🙈 Скрываем индикатор');
        this.indicator.classList.remove('show');
        this.isVisible = false;

        setTimeout(() => {
            this.indicator.style.display = 'none';
        }, 300);
    },

    // Обновить счетчик
    updateCounter: function(filtered, total, isFiltered = false) {
        if (!this.indicator) return;

        console.log('[TasksCounter] 🔄 Обновляем счетчик:', {
            filtered: filtered,
            total: total,
            isFiltered: isFiltered,
            mode: this.currentPaginationType
        });

        this.currentCount = filtered;
        this.totalCount = total;
        this.isFiltered = isFiltered;

        if (filtered === 0) {
            this.showEmpty();
        } else {
            this.showCounter(filtered, total, isFiltered);
        }
    },

    // Показать состояние счетчика
    showCounter: function(count, total, isFiltered) {
        if (!this.indicator) return;

        this.clearStates();
        this.indicator.classList.add('counter-success');

        // Обновляем цифру
        if (this.counterNumber) {
            this.counterNumber.textContent = count.toLocaleString('ru-RU');
        }

        // Обновляем префикс и суффикс
        if (this.counterPrefix && this.counterSuffix) {
            if (isFiltered) {
                this.counterPrefix.textContent = 'Найдено ';
                this.counterSuffix.textContent = ` ${this.getTaskWord(count)} из ${total.toLocaleString('ru-RU')}`;
            } else {
                this.counterPrefix.textContent = 'Всего ';
                this.counterSuffix.textContent = ` ${this.getTaskWord(count)}`;
            }
        }

        // Обновляем иконку
        if (this.counterIcon) {
            this.counterIcon.className = isFiltered ? 'fas fa-filter' : 'fas fa-tasks';
        }

        this.show();
    },

    // Показать состояние загрузки
    showLoading: function(message = 'Загрузка...') {
        if (!this.indicator) return;

        console.log('[TasksCounter] ⏳ Показываем загрузку:', message);

        this.clearStates();
        this.indicator.classList.add('counter-loading');

        if (this.counterIcon) {
            this.counterIcon.className = 'fas fa-spinner fa-spin';
        }

        this.show();
    },

    // Показать пустое состояние
    showEmpty: function() {
        if (!this.indicator) return;

        console.log('[TasksCounter] 📭 Показываем пустое состояние');

        this.clearStates();
        this.indicator.classList.add('counter-empty');

        if (this.counterIcon) {
            this.counterIcon.className = 'fas fa-inbox';
        }

        if (this.counterNumber) {
            this.counterNumber.textContent = 'не найдены';
        }

        this.show();
    },

    // Показать ошибку
    showError: function(message = 'Ошибка загрузки') {
        if (!this.indicator) return;

        console.log('[TasksCounter] ❌ Показываем ошибку:', message);

        this.clearStates();
        this.indicator.classList.add('counter-error');

        if (this.counterIcon) {
            this.counterIcon.className = 'fas fa-exclamation-triangle';
        }

        this.show();
    },

    // Очистить все состояния
    clearStates: function() {
        if (!this.indicator) return;

        this.indicator.classList.remove(
            'counter-loading', 'counter-success', 'counter-empty',
            'counter-error', 'counter-filtered', 'pagination-pages'
        );
    },

    // Обновить стили для режима пагинации
    updateModeStyle: function(mode) {
        if (!this.indicator) return;

        console.log('[TasksCounter] 🎨 Обновляем стили для страничной пагинации');

        this.indicator.classList.remove('pagination-pages');
        this.indicator.classList.add('pagination-pages');
    },

    // Получить правильную форму слова "задача"
    getTaskWord: function(count) {
        const lastDigit = count % 10;
        const lastTwoDigits = count % 100;

        if (lastTwoDigits >= 11 && lastTwoDigits <= 19) {
            return 'задач';
        }

        switch (lastDigit) {
            case 1:
                return 'задача';
            case 2:
            case 3:
            case 4:
                return 'задачи';
            default:
                return 'задач';
        }
    }
};

// Публичный API для внешнего использования
window.TasksCounterAPI = {
    show: function() {
        if (window.TasksCounterManager && typeof window.TasksCounterManager.show === 'function') {
            window.TasksCounterManager.show();
        }
    },

    hide: function() {
        if (window.TasksCounterManager && typeof window.TasksCounterManager.hide === 'function') {
            window.TasksCounterManager.hide();
        }
    },

    updateCounter: function(filtered, total, isFiltered) {
        if (window.TasksCounterManager && typeof window.TasksCounterManager.updateCount === 'function') {
            window.TasksCounterManager.updateCount(filtered);
        }
    },

    showLoading: function(message) {
        if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
            window.TasksCounterManager.showLoading(message);
        }
    },

    showEmpty: function() {
        if (window.TasksCounterManager && typeof window.TasksCounterManager.hide === 'function') {
            window.TasksCounterManager.hide();
        }
    },

    showError: function(message) {
        if (window.TasksCounterManager && typeof window.TasksCounterManager.showError === 'function') {
            window.TasksCounterManager.showError(message);
        }
    }
};

/**
 * Инициализирует счетчик отфильтрованных задач
 * Создает и настраивает элементы DOM для отображения количества задач
 */
function initializeFilterCounter() {
    console.log('[TasksPaginated] Инициализация счетчика фильтров...');

    // Проверяем наличие элемента для отображения счетчика
    const counterElement = $('#filtered-tasks-count');
    if (counterElement.length === 0) {
        console.warn('[TasksPaginated] Элемент счетчика фильтров не найден!');
        return;
    }

    // Устанавливаем начальное значение
    counterElement.text('0');

    // Скрываем секцию результатов фильтрации при инициализации
    const resultsSection = $('.filter-results-section');
    if (resultsSection.length > 0) {
        resultsSection.hide();
    }

    console.log('[TasksPaginated] Счетчик фильтров инициализирован (скрыт).');
}

/**
 * Обновляет счетчик отфильтрованных задач
 * @param {number} count - Количество задач после применения фильтров
 */
function updateFilterCounter(count) {
    console.log(`[TasksPaginated] Обновление счетчика фильтров: ${count}`);

    // Проверяем наличие элемента для отображения счетчика
    const counterElement = $('#filtered-tasks-count');
    if (counterElement.length === 0) {
        console.warn('[TasksPaginated] Элемент счетчика фильтров не найден!');
        return;
    }

    // Обновляем значение счетчика
    counterElement.text(count);

    // Показываем секцию результатов фильтрации если есть что показывать
    const resultsSection = $('.filter-results-section');
    if (resultsSection.length > 0) {
        if (count > 0) {
            resultsSection.show();
            // Добавляем анимацию пульсации для привлечения внимания
            $('.results-badge-bright .results-pulse').addClass('pulse').delay(1500).queue(function(next) {
                $(this).removeClass('pulse');
                next();
            });
        } else {
            resultsSection.hide();
        }
    }

    console.log('[TasksPaginated] Счетчик фильтров обновлен.');
}

// Инициализация при загрузке документа
$(function() {
    console.log('[TasksPaginated] Инициализация модуля пагинированных задач (v3)');

    // Инициализация
    initializePaginatedTasks();
});

// Функция для инициализации кнопок переключения карточек
function initializeCardToggleButtons() {
    console.log('[TasksPaginated] Инициализация кнопок переключения карточек');
    // Пустая реализация, чтобы избежать ошибки
    // Реальная логика уже реализована в card_breakdown_handler.js
}

// Функция для проверки активных фильтров
function checkForActiveFilters() {
    console.log('[TasksPaginated] Проверка активных фильтров');

    const statusFilter = $('#status-filter').val();
    const projectFilter = $('#project-filter').val();
    const priorityFilter = $('#priority-filter').val();
    const searchValue = $('.dataTables_filter input').val();

    // Проверяем, есть ли активные фильтры
    const hasActiveFilters = statusFilter || projectFilter || priorityFilter || (searchValue && searchValue.length > 0);

    // Обновляем счетчик фильтров, если он существует
    if (typeof updateFilterCounter === 'function') {
        // Получаем количество отфильтрованных задач
        const filteredCount = window.tasksDataTable ? window.tasksDataTable.rows({search:'applied'}).count() : 0;
        updateFilterCounter(filteredCount);
    }

    return hasActiveFilters;
}

// Функция для инициализации глобальной кнопки переключения
function initializeGlobalToggleButton() {
    console.log('[TasksPaginated] Инициализация глобальной кнопки переключения');
    // Пустая реализация, чтобы избежать ошибки
    // Реальная логика уже реализована в card_breakdown_handler.js
}

// Функция для инициализации аккордеона статусов
function initializeStatusAccordion(response) {
    console.log('[TasksPaginated] Инициализация аккордеона статусов...');

    // Проверяем, есть ли данные статистики
    const statusCounts = response.statistics?.debug_status_counts || {};

    if (Object.keys(statusCounts).length === 0) {
        showAccordionNoData();
        return;
    }

    // Загружаем расширенную статистику для аккордеона
    $.get('/tasks/api/statistics-extended')
        .done(function(extendedResponse) {
            if (extendedResponse.success && extendedResponse.status_groups) {
                console.log('[TasksPaginated] Расширенная статистика получена для аккордеона:', extendedResponse);

                // Инициализируем аккордеон с данными
                if (typeof window.StatusAccordion !== 'undefined') {
                    window.StatusAccordion.init(extendedResponse.status_groups, 'statusAccordion');
                    hideAccordionLoading();
                } else {
                    console.warn('[TasksPaginated] StatusAccordion класс не найден, пытаемся загрузить...');
                    // Пытаемся загрузить скрипт аккордеона
                    loadStatusAccordionScript().then(() => {
                        if (typeof window.StatusAccordion !== 'undefined') {
                            window.StatusAccordion.init(extendedResponse.status_groups, 'statusAccordion');
                            hideAccordionLoading();
                        } else {
                            showAccordionError();
                        }
                    }).catch(() => {
                        showAccordionError();
                    });
                }
            } else {
                console.error('[TasksPaginated] Ошибка получения расширенной статистики:', extendedResponse);
                showAccordionError();
            }
        })
        .fail(function(xhr, status, error) {
            console.error('[TasksPaginated] Ошибка API расширенной статистики:', error);
            showAccordionError();
        });
}

// Функция для динамической загрузки скрипта аккордеона
function loadStatusAccordionScript() {
    return new Promise((resolve, reject) => {
        if (typeof window.StatusAccordion !== 'undefined') {
            resolve();
            return;
        }

        const script = document.createElement('script');
        script.src = '/static/js/status_accordion.js?v=' + Math.random();
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Функции управления состоянием аккордеона
function hideAccordionLoading() {
    $('#accordionLoading').hide();
    $('#accordionError').hide();
    $('#accordionNoData').hide();
}

function showAccordionError() {
    $('#accordionLoading').hide();
    $('#accordionError').show();
    $('#accordionNoData').hide();
}

function showAccordionNoData() {
    $('#accordionLoading').hide();
    $('#accordionError').hide();
    $('#accordionNoData').show();
}
