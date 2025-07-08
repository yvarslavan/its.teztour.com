/**
 * Модуль принудительного применения стилей для решения проблем с отображением элементов
 * Версия: 1.3
 * Дата: 26.12.2023
 */

console.log('[ForceStyles] 🔧 Запуск принудительного применения стилей');

// Основная функция применения всех стилей
function forceApplyAllStyles() {
    // Применяем стили к спиннеру загрузки
    forceApplySpinnerStyles();

    // Применяем стили к карточкам детализации
    forceInitializeCardBreakdowns();

    // Применяем стили к кнопкам очистки фильтров
    forceApplyFilterButtonStyles();

    // Применяем стили к глобальной кнопке переключения
    forceApplyGlobalToggleStyles();

    // Применяем стили к областям детализации карточек
    forceApplyCardBreakdownStyles();

    // Применяем стили к индикатору задач
    forceApplyTasksCounterStyles();

    // Применяем стили к таблице
    forceApplyTableStyles();

    console.log('[ForceStyles] 🎉 Все стили принудительно применены');
}

// Применение стилей к спиннеру загрузки
function forceApplySpinnerStyles() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        console.log('[ForceStyles] ✅ Элемент индикатора загрузки найден');
        // Больше не применяем принудительное отображение спиннера
        // Спиннер должен управляться только через modern_loading_manager.js
    }
}

// Принудительная инициализация карточек детализации
function forceInitializeCardBreakdowns() {
    console.log('[ForceStyles] 🔧 Принудительная инициализация карточек детализации');

    // Находим все карточки детализации
    const cards = document.querySelectorAll('.status-breakdown-card');
    console.log('[ForceStyles] ✅ Найдено ' + cards.length + ' карточек детализации');

    // Находим все кнопки переключения
    const toggleButtons = document.querySelectorAll('.card-toggle-btn');
    console.log('[ForceStyles] ✅ Найдено ' + toggleButtons.length + ' кнопок переключения');

    // Добавляем обработчики для кнопок переключения
    toggleButtons.forEach(button => {
        const targetId = button.getAttribute('data-target');
        if (targetId) {
            console.log('[ForceStyles] ✅ Добавлен обработчик для кнопки #' + targetId);

            button.addEventListener('click', function() {
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    if (targetElement.classList.contains('collapsed')) {
                        targetElement.classList.remove('collapsed');
                        targetElement.classList.add('expanded');
                        button.classList.add('expanded');
                    } else {
                        targetElement.classList.remove('expanded');
                        targetElement.classList.add('collapsed');
                        button.classList.remove('expanded');
                    }
                }
            });
        }
    });

    // Добавляем обработчик для глобальной кнопки переключения
    const globalToggleBtn = document.getElementById('globalToggleBtn');
    if (globalToggleBtn) {
        console.log('[ForceStyles] ✅ Добавлен обработчик для глобальной кнопки переключения');

        globalToggleBtn.addEventListener('click', function() {
            const breakdowns = document.querySelectorAll('.card-breakdown');
            const isCollapsed = globalToggleBtn.classList.contains('collapsed-state');

            breakdowns.forEach(breakdown => {
                if (isCollapsed) {
                    breakdown.classList.remove('collapsed');
                    breakdown.classList.add('expanded');
                } else {
                    breakdown.classList.remove('expanded');
                    breakdown.classList.add('collapsed');
                }
            });

            toggleButtons.forEach(button => {
                if (isCollapsed) {
                    button.classList.add('expanded');
                } else {
                    button.classList.remove('expanded');
                }
            });

            if (isCollapsed) {
                globalToggleBtn.classList.remove('collapsed-state');
                globalToggleBtn.classList.add('expanded-state');
                globalToggleBtn.querySelector('span').textContent = 'Свернуть все';
            } else {
                globalToggleBtn.classList.remove('expanded-state');
                globalToggleBtn.classList.add('collapsed-state');
                globalToggleBtn.querySelector('span').textContent = 'Развернуть все';
            }
        });
    }

    console.log('[ForceStyles] ✅ Карточки детализации принудительно инициализированы');
}

// Применение стилей к кнопкам очистки фильтров
function forceApplyFilterButtonStyles() {
    const clearButtons = [
        document.getElementById('clear-status-filter'),
        document.getElementById('clear-project-filter'),
        document.getElementById('clear-priority-filter')
    ];

    if (clearButtons.filter(Boolean).length > 0) {
        console.log('[ForceStyles] ✅ Найдено ' + clearButtons.filter(Boolean).length + ' кнопок очистки фильтров, применяем стили');

        clearButtons.forEach(button => {
            if (button) {
                button.style.display = 'flex';
                button.style.alignItems = 'center';
                button.style.justifyContent = 'center';
                button.style.width = '32px';
                button.style.height = '32px';
                button.style.borderRadius = '50%';
                button.style.backgroundColor = '#f0f0f0';
                button.style.border = 'none';
                button.style.cursor = 'pointer';
                button.style.position = 'absolute';
                button.style.right = '10px';
                button.style.top = '50%';
                button.style.transform = 'translateY(-50%)';
                button.style.zIndex = '5';
                button.style.color = '#666';
                button.style.transition = 'all 0.2s ease';

                // Добавляем обработчик для наведения
                button.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#e0e0e0';
                    this.style.color = '#333';
                });

                button.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = '#f0f0f0';
                    this.style.color = '#666';
                });
            }
        });

        console.log('[ForceStyles] ✅ Стили кнопок очистки фильтров принудительно применены');
    }
}

// Применение стилей к глобальной кнопке переключения
function forceApplyGlobalToggleStyles() {
    const globalToggleBtn = document.getElementById('globalToggleBtn');

    if (globalToggleBtn) {
        console.log('[ForceStyles] ✅ Глобальная кнопка переключения найдена, применяем стили');

        globalToggleBtn.style.display = 'flex';
        globalToggleBtn.style.alignItems = 'center';
        globalToggleBtn.style.gap = '8px';
        globalToggleBtn.style.padding = '8px 16px';
        globalToggleBtn.style.background = '#ffffff';
        globalToggleBtn.style.border = '1px solid #e2e8f0';
        globalToggleBtn.style.borderRadius = '8px';
        globalToggleBtn.style.fontSize = '14px';
        globalToggleBtn.style.fontWeight = '500';
        globalToggleBtn.style.color = '#3b82f6';
        globalToggleBtn.style.cursor = 'pointer';
        globalToggleBtn.style.transition = 'all 0.3s ease';
        globalToggleBtn.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.05)';

        // Добавляем обработчик для наведения
        globalToggleBtn.addEventListener('mouseenter', function() {
            this.style.background = '#f0f9ff';
            this.style.borderColor = '#3b82f6';
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 8px rgba(59, 130, 246, 0.2)';
        });

        globalToggleBtn.addEventListener('mouseleave', function() {
            this.style.background = '#ffffff';
            this.style.borderColor = '#e2e8f0';
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.05)';
        });

        console.log('[ForceStyles] ✅ Стили глобальной кнопки переключения принудительно применены');
    }
}

// Применение стилей к областям детализации карточек
function forceApplyCardBreakdownStyles() {
    const cardBreakdowns = document.querySelectorAll('.card-breakdown');

    if (cardBreakdowns.length > 0) {
        console.log('[ForceStyles] ✅ Найдено ' + cardBreakdowns.length + ' детализаций карточек, применяем стили');

        cardBreakdowns.forEach(breakdown => {
            breakdown.style.overflow = 'hidden';
            breakdown.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            breakdown.style.borderTop = '1px solid rgba(226, 232, 240, 0.5)';
            breakdown.style.marginTop = '0.75rem';

            if (breakdown.classList.contains('collapsed')) {
                breakdown.style.maxHeight = '0';
                breakdown.style.opacity = '0';
                breakdown.style.paddingTop = '0';
                breakdown.style.paddingBottom = '0';
                breakdown.style.marginTop = '0';
                breakdown.style.borderTop = 'none';
                breakdown.style.transform = 'translateY(-10px)';
                breakdown.style.pointerEvents = 'none';
                breakdown.style.visibility = 'hidden';
            } else {
                breakdown.style.maxHeight = '150px';
                breakdown.style.opacity = '1';
                breakdown.style.paddingTop = '0.75rem';
                breakdown.style.paddingBottom = '0.75rem';
                breakdown.style.transform = 'translateY(0)';
                breakdown.style.overflowY = 'auto';
                breakdown.style.pointerEvents = 'auto';
                breakdown.style.visibility = 'visible';
            }
        });

        console.log('[ForceStyles] ✅ Стили детализаций карточек принудительно применены');
    }
}

// Применение стилей к индикатору задач
function forceApplyTasksCounterStyles() {
    const tasksCounter = document.getElementById('tasksCounterIndicator');

    if (tasksCounter) {
        console.log('[ForceStyles] ✅ Элемент индикатора задач найден, применяем стили');

        tasksCounter.style.display = 'none';
        tasksCounter.style.visibility = 'hidden';
        tasksCounter.style.opacity = '0';

        console.log('[ForceStyles] ✅ Стили индикатора задач принудительно применены');
    }
}

// Применение стилей к таблице
function forceApplyTableStyles() {
    console.log('[ForceStyles] 🔧 Принудительное применение стилей к таблице');

    // Применяем стили к шапке таблицы
    const tableHeaders = document.querySelectorAll('.tasks-table th');
    if (tableHeaders.length > 0) {
        tableHeaders.forEach(header => {
            header.style.backgroundColor = '#f8fafc';
            header.style.color = '#334155';
            header.style.fontWeight = '600';
            header.style.padding = '12px 16px';
            header.style.borderBottom = '2px solid #e2e8f0';
            header.style.textAlign = 'left';
            header.style.fontSize = '14px';
            header.style.position = 'sticky';
            header.style.top = '0';
            header.style.zIndex = '10';
        });

        console.log('[ForceStyles] ✅ Стили шапки таблицы принудительно применены');
    }

    // Применяем стили к ячейкам статуса
    const statusCells = document.querySelectorAll('.status-badge');
    if (statusCells.length > 0) {
        statusCells.forEach(cell => {
            cell.style.display = 'inline-flex';
            cell.style.alignItems = 'center';
            cell.style.padding = '4px 8px';
            cell.style.borderRadius = '16px';
            cell.style.fontSize = '12px';
            cell.style.fontWeight = '500';
            cell.style.lineHeight = '1';
            cell.style.whiteSpace = 'nowrap';
        });
    } else {
        console.log('[ForceStyles] ⚠️ Элементы ячеек статуса не найдены');
    }

    // Применяем стили к ячейкам приоритета
    const priorityCells = document.querySelectorAll('.priority-badge');
    if (priorityCells.length > 0) {
        priorityCells.forEach(cell => {
            cell.style.display = 'inline-flex';
            cell.style.alignItems = 'center';
            cell.style.padding = '4px 8px';
            cell.style.borderRadius = '16px';
            cell.style.fontSize = '12px';
            cell.style.fontWeight = '500';
            cell.style.lineHeight = '1';
            cell.style.whiteSpace = 'nowrap';
        });
    } else {
        console.log('[ForceStyles] ⚠️ Элементы ячеек приоритета не найдены');
    }

    // Применяем стили к индикатору загрузки таблицы
    const tableLoadingOverlay = document.querySelector('.table-loading-overlay');
    if (tableLoadingOverlay) {
        tableLoadingOverlay.style.position = 'absolute';
        tableLoadingOverlay.style.top = '0';
        tableLoadingOverlay.style.left = '0';
        tableLoadingOverlay.style.width = '100%';
        tableLoadingOverlay.style.height = '100%';
        tableLoadingOverlay.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
        tableLoadingOverlay.style.display = 'flex';
        tableLoadingOverlay.style.justifyContent = 'center';
        tableLoadingOverlay.style.alignItems = 'center';
        tableLoadingOverlay.style.zIndex = '50';
        tableLoadingOverlay.style.opacity = '0';
        tableLoadingOverlay.style.visibility = 'hidden';
        tableLoadingOverlay.style.transition = 'opacity 0.3s ease, visibility 0.3s ease';

        console.log('[ForceStyles] ✅ Стили индикатора загрузки таблицы принудительно применены');
    }
}

// Повторное применение стилей через интервал
function setupReapplyInterval() {
    // Первое применение через 1 секунду
    setTimeout(() => {
        forceApplyAllStyles();

        // Затем повторяем каждые 5 секунд в течение 30 секунд
        let count = 0;
        const interval = setInterval(() => {
            count++;
            if (count >= 6) {
                clearInterval(interval);
                return;
            }

            console.log('[ForceStyles] 🔄 Повторная проверка и применение стилей выполнены');
            forceApplyAllStyles();
        }, 5000);
    }, 1000);
}

// Запускаем применение стилей при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    forceApplyAllStyles();
    setupReapplyInterval();
});

// Экспортируем функции для использования из консоли
window.forceApplyAllStyles = forceApplyAllStyles;
window.forceApplySpinnerStyles = forceApplySpinnerStyles;
window.forceInitializeCardBreakdowns = forceInitializeCardBreakdowns;
window.forceApplyFilterButtonStyles = forceApplyFilterButtonStyles;
window.forceApplyGlobalToggleStyles = forceApplyGlobalToggleStyles;
window.forceApplyCardBreakdownStyles = forceApplyCardBreakdownStyles;
window.forceApplyTasksCounterStyles = forceApplyTasksCounterStyles;
window.forceApplyTableStyles = forceApplyTableStyles;
