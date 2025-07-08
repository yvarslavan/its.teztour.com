/**
 * filter_buttons_handler.js - v1.5
 * Обработчик кнопок фильтров для страницы задач
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('[FilterButtons] 🔧 Инициализация обработчика кнопок фильтров');

    // Функция для обновления видимости кнопок очистки
    function updateClearButtonVisibility(selectElement) {
        if (!selectElement || selectElement.length === 0) {
            console.warn('[FilterButtons] ⚠️ selectElement не найден');
            return;
        }

        const value = selectElement.val();
        const filterId = selectElement.attr('id');
        const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
        const clearBtn = $(clearBtnId);
        const container = selectElement.closest('.filter-container');

        console.log(`[FilterButtons] 🔍 Обновление кнопки очистки для ${filterId}:`, {
            value: value,
            hasValue: value && value !== '' && value !== 'null',
            clearBtnExists: clearBtn.length > 0
        });

        // Проверка значения
        if (value && value !== '' && value !== 'null') {
            clearBtn.addClass('show');
            clearBtn.css('display', 'flex');
            container.addClass('has-value');

            // Принудительно показываем кнопку и устанавливаем иконку крестика
            clearBtn.attr('style', 'display: flex !important; visibility: visible !important; opacity: 1 !important;');
            clearBtn.html('<i class="fas fa-times"></i>');
            clearBtn.attr('title', 'Очистить фильтр');

            console.log(`[FilterButtons] ✅ Кнопка очистки ПОКАЗАНА для ${filterId}`);
        } else {
            clearBtn.removeClass('show');
            clearBtn.css('display', 'none');
            container.removeClass('has-value');

            // Принудительно скрываем кнопку
            clearBtn.attr('style', 'display: none !important; visibility: hidden !important; opacity: 0 !important;');

            console.log(`[FilterButtons] ❌ Кнопка очистки СКРЫТА для ${filterId}`);
        }
    }

    // Инициализация кнопок очистки фильтров
    function initializeClearButtons() {
        console.log('[FilterButtons] 🔧 Инициализация кнопок очистки фильтров');

        // Находим все селекты фильтров
        const filters = ['#status-filter', '#project-filter', '#priority-filter'];

        // Обновляем видимость кнопок очистки для каждого фильтра
        filters.forEach(selector => {
            const $filter = $(selector);
            if ($filter.length > 0) {
                updateClearButtonVisibility($filter);

                // Устанавливаем иконку для кнопок очистки
                const filterId = $filter.attr('id');
                const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
                const clearBtn = $(clearBtnId);
                if (clearBtn.length > 0) {
                    clearBtn.html('<i class="fas fa-times"></i>');
                    clearBtn.attr('title', 'Очистить фильтр');
                }
            }
        });

        // Добавляем обработчики событий для кнопок очистки
        $('#clear-status-filter').off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('[FilterButtons] 🔧 Нажата кнопка очистки статуса');

            $('#status-filter').val('').trigger('change');
            updateClearButtonVisibility($('#status-filter'));

            // Добавляем эффект очистки
            addClearEffect($(this).closest('.filter-container'));
        });

        $('#clear-project-filter').off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('[FilterButtons] 🔧 Нажата кнопка очистки проекта');

            $('#project-filter').val('').trigger('change');
            updateClearButtonVisibility($('#project-filter'));

            // Добавляем эффект очистки
            addClearEffect($(this).closest('.filter-container'));
        });

        $('#clear-priority-filter').off('click').on('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('[FilterButtons] 🔧 Нажата кнопка очистки приоритета');

            $('#priority-filter').val('').trigger('change');
            updateClearButtonVisibility($('#priority-filter'));

            // Добавляем эффект очистки
            addClearEffect($(this).closest('.filter-container'));
        });

        // Принудительно устанавливаем правильное отображение кнопок
        setTimeout(() => {
            filters.forEach(selector => {
                const $filter = $(selector);
                if ($filter.length > 0) {
                    const value = $filter.val();
                    const filterId = $filter.attr('id');
                    const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
                    const clearBtn = $(clearBtnId);

                    if (value && value !== '' && value !== 'null') {
                        clearBtn.html('<i class="fas fa-times"></i>');
                        clearBtn.attr('title', 'Очистить фильтр');
                        clearBtn.attr('style', 'display: flex !important; visibility: visible !important; opacity: 1 !important;');
                    }
                }
            });
        }, 500);

        console.log('[FilterButtons] ✅ Обработчики кнопок очистки фильтров инициализированы');
    }

    // Функция для добавления эффекта очистки
    function addClearEffect(container) {
        const effect = $('<div>').addClass('filter-clear-effect');
        container.append(effect);

        // Удаляем эффект после завершения анимации
        setTimeout(() => {
            effect.remove();
        }, 500);
    }

    // Добавляем обработчики изменения фильтров
    function initializeFilterChangeHandlers() {
        console.log('[FilterButtons] 🔧 Инициализация обработчиков изменения фильтров');

        // Обработчик изменения фильтра статуса
        $('#status-filter').off('change.filterButtons').on('change.filterButtons', function() {
            console.log('[FilterButtons] 🔄 Изменен фильтр статуса:', $(this).val());
            updateClearButtonVisibility($(this));
        });

        // Обработчик изменения фильтра проекта
        $('#project-filter').off('change.filterButtons').on('change.filterButtons', function() {
            console.log('[FilterButtons] 🔄 Изменен фильтр проекта:', $(this).val());
            updateClearButtonVisibility($(this));
        });

        // Обработчик изменения фильтра приоритета
        $('#priority-filter').off('change.filterButtons').on('change.filterButtons', function() {
            console.log('[FilterButtons] 🔄 Изменен фильтр приоритета:', $(this).val());
            updateClearButtonVisibility($(this));
        });

        console.log('[FilterButtons] ✅ Обработчики изменения фильтров инициализированы');
    }

    // Проверка и обновление видимости кнопок очистки через интервал
    function setupPeriodicCheck() {
        console.log('[FilterButtons] 🔧 Настройка периодической проверки кнопок очистки');

        // Проверяем каждые 2 секунды
        setInterval(() => {
            const filters = ['#status-filter', '#project-filter', '#priority-filter'];

            filters.forEach(selector => {
                const $filter = $(selector);
                if ($filter.length > 0) {
                    const value = $filter.val();
                    const filterId = $filter.attr('id');
                    const clearBtnId = '#clear-' + filterId.replace('-filter', '') + '-filter';
                    const clearBtn = $(clearBtnId);

                    // Проверяем соответствие между значением и видимостью кнопки
                    const hasValue = value && value !== '' && value !== 'null';
                    const isVisible = clearBtn.is(':visible');

                    if (hasValue && !isVisible) {
                        console.log(`[FilterButtons] 🔄 Исправление: кнопка ${clearBtnId} должна быть видима`);
                        clearBtn.html('<i class="fas fa-times"></i>');
                        clearBtn.attr('title', 'Очистить фильтр');
                        clearBtn.attr('style', 'display: flex !important; visibility: visible !important; opacity: 1 !important;');
                    } else if (!hasValue && isVisible) {
                        console.log(`[FilterButtons] 🔄 Исправление: кнопка ${clearBtnId} должна быть скрыта`);
                        clearBtn.attr('style', 'display: none !important; visibility: hidden !important; opacity: 0 !important;');
                    }
                }
            });
        }, 2000);

        console.log('[FilterButtons] ✅ Периодическая проверка кнопок очистки настроена');
    }

    // Инициализация всех компонентов
    function initialize() {
        console.log('[FilterButtons] 🚀 Инициализация всех компонентов');

        // Инициализация кнопок очистки фильтров
        initializeClearButtons();

        // Инициализация обработчиков изменения фильтров
        initializeFilterChangeHandlers();

        // Настройка периодической проверки
        setupPeriodicCheck();

        console.log('[FilterButtons] ✅ Все компоненты инициализированы');
    }

    // Экспортируем функции в глобальную область видимости
    window.FilterButtonsHandler = {
        updateClearButtonVisibility: updateClearButtonVisibility,
        initialize: initialize
    };

    // Инициализация после небольшой задержки
    setTimeout(() => {
        initialize();
    }, 500);
});
