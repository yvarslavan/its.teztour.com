/**
 * Исправления для спиннера загрузки в tasks_paginated.js
 * Заменяет старые вызовы на новые функции управления спиннером
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('[SpinnerFix] Применение исправлений для спиннера загрузки...');

    // Переопределяем обработчики фильтров после загрузки основного скрипта
    setTimeout(function() {
        // Переопределяем обработчик для status-filter
        $('#status-filter').off('change').on('change', function() {
            const value = $(this).val();
            const text = $(this).find('option:selected').text();
            console.log('[SpinnerFix] СОБЫТИЕ CHANGE: status-filter изменен на', value, '(текст: ' + text + ')');

            // Обновляем видимость кнопки очистки
            if (typeof window.updateFilterVisibility === 'function') {
                window.updateFilterVisibility($(this));
            }

            // Показываем индикатор загрузки через новый менеджер
            if (window.loadingManager && typeof window.loadingManager.show === 'function') {
                window.loadingManager.show();
            }

            if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
                window.TasksCounterManager.showLoading('Применение фильтра статуса...');
            }

            if (window.tasksDataTable) {
                console.log('[SpinnerFix] Вызываем draw() для обновления таблицы');
                window.tasksDataTable.draw();
            }
        });

        // Переопределяем обработчик для project-filter
        $('#project-filter').off('change').on('change', function() {
            const value = $(this).val();
            const text = $(this).find('option:selected').text();
            console.log('[SpinnerFix] СОБЫТИЕ CHANGE: project-filter изменен на', value, '(текст: ' + text + ')');

            // Обновляем видимость кнопки очистки
            if (typeof window.updateFilterVisibility === 'function') {
                window.updateFilterVisibility($(this));
            }

            // Показываем индикатор загрузки через новый менеджер
            if (window.loadingManager && typeof window.loadingManager.show === 'function') {
                window.loadingManager.show();
            }

            if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
                window.TasksCounterManager.showLoading('Применение фильтра проекта...');
            }

            if (window.tasksDataTable) {
                console.log('[SpinnerFix] Вызываем draw() для обновления таблицы');
                window.tasksDataTable.draw();
            }
        });

        // Переопределяем обработчик для priority-filter
        $('#priority-filter').off('change').on('change', function() {
            const value = $(this).val();
            const text = $(this).find('option:selected').text();
            console.log('[SpinnerFix] СОБЫТИЕ CHANGE: priority-filter изменен на', value, '(текст: ' + text + ')');

            // Обновляем видимость кнопки очистки
            if (typeof window.updateFilterVisibility === 'function') {
                window.updateFilterVisibility($(this));
            }

            // Показываем индикатор загрузки через новый менеджер
            if (window.loadingManager && typeof window.loadingManager.show === 'function') {
                window.loadingManager.show();
            }

            if (window.TasksCounterManager && typeof window.TasksCounterManager.showLoading === 'function') {
                window.TasksCounterManager.showLoading('Применение фильтра приоритета...');
            }

            if (window.tasksDataTable) {
                console.log('[SpinnerFix] Вызываем draw() для обновления таблицы');
                window.tasksDataTable.draw();
            }
        });

        console.log('[SpinnerFix] Обработчики фильтров переопределены');
    }, 1000);
});
