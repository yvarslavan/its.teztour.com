/**
 * table_loading_handler.js - v1.0
 * Обработчик индикатора загрузки таблицы
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('[TableLoading] 🔧 Инициализация обработчика индикатора загрузки таблицы');

    // Элементы DOM
    const tableLoadingOverlay = document.querySelector('.table-loading-overlay');
    const tableContainer = document.querySelector('.table-container');

    // Проверяем наличие необходимых элементов
    if (!tableLoadingOverlay || !tableContainer) {
        console.warn('[TableLoading] ⚠️ Не найдены необходимые элементы для индикатора загрузки таблицы');
        return;
    }

    // Функция для показа индикатора загрузки
    function showTableLoading() {
        console.log('[TableLoading] ✅ Показываем индикатор загрузки таблицы');

        tableLoadingOverlay.classList.add('show');
        tableContainer.classList.add('loading');
    }

    // Функция для скрытия индикатора загрузки
    function hideTableLoading() {
        console.log('[TableLoading] ✅ Скрываем индикатор загрузки таблицы');

        tableLoadingOverlay.classList.remove('show');
        tableContainer.classList.remove('loading');
    }

    // Обработчик события начала обработки DataTables
    document.addEventListener('datatable-processing-start', function() {
        console.log('[TableLoading] 🔄 Получено событие начала обработки DataTables');
        showTableLoading();
    });

    // Обработчик события окончания обработки DataTables
    document.addEventListener('datatable-processing-end', function() {
        console.log('[TableLoading] 🔄 Получено событие окончания обработки DataTables');
        hideTableLoading();
    });

    // Функция для инициализации наблюдения за DataTables
    function initDataTablesObserver() {
        console.log('[TableLoading] 🔧 Инициализация наблюдения за DataTables');

        // Если есть глобальный объект DataTables
        if (window.tasksDataTable) {
            // Добавляем обработчики событий
            window.tasksDataTable.on('processing.dt', function(e, settings, processing) {
                console.log('[TableLoading] 🔄 Получено событие processing.dt:', processing);

                if (processing) {
                    showTableLoading();
                } else {
                    hideTableLoading();
                }
            });

            console.log('[TableLoading] ✅ Обработчики событий DataTables добавлены');
        } else {
            console.warn('[TableLoading] ⚠️ Объект DataTables не найден, будет выполнена повторная попытка');

            // Повторная попытка через 1 секунду
            setTimeout(initDataTablesObserver, 1000);
        }
    }

    // Экспортируем функции в глобальную область видимости
    window.TableLoadingHandler = {
        showTableLoading: showTableLoading,
        hideTableLoading: hideTableLoading
    };

    // Инициализация наблюдения за DataTables
    initDataTablesObserver();

    // Добавляем обработчик события инициализации DataTables
    document.addEventListener('datatables-initialized', function() {
        console.log('[TableLoading] 📢 Получено событие datatables-initialized');

        // Повторно инициализируем наблюдение за DataTables
        setTimeout(function() {
            console.log('[TableLoading] 🔄 Повторная инициализация наблюдения после события datatables-initialized');
            initDataTablesObserver();
        }, 100);
    });

    // Скрываем индикатор загрузки через 2 секунды после загрузки страницы
    setTimeout(hideTableLoading, 2000);
});
