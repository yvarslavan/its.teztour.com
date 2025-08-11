/**
 * KanbanTooltips.js - Компонент для всплывающих подсказок в канбан-доске
 * Показывает контекстные подсказки при наведении на различные элементы
 */

class KanbanTooltips {
    constructor() {
        this.tooltips = {
            'kanban-card': {
                title: '🖱️ Перетащите для изменения статуса',
                content: 'Зажмите карточку и перетащите в другую колонку для быстрого обновления статуса задачи'
            },
            'kanban-card-id': {
                title: '⚡ Быстрый переход',
                content: 'Кликните для открытия деталей задачи в новой вкладке'
            },
            'kanban-column-header': {
                title: '🔒 Сворачивание колонки',
                content: 'Кликните для сворачивания/разворачивания содержимого колонки'
            },
            'kanban-column-count': {
                title: '📊 Количество задач',
                content: 'Показывает количество задач в данном статусе'
            },
            'priority-badge': {
                title: '🎨 Приоритет задачи',
                content: 'Цветовой индикатор приоритета: красный - высокий, синий - нормальный, зеленый - низкий'
            },
            'view-toggle-btn': {
                title: '🔄 Переключение вида',
                content: 'Переключение между табличным и канбан-видом отображения задач'
            }
        };

        this.activeTooltip = null;
        this.isEnabled = true;
    }

    /**
     * Инициализирует всплывающие подсказки
     */
    init() {
        if (!this.isEnabled) return;

        console.log('[KanbanTooltips] 🎯 Инициализация всплывающих подсказок');

        // Проверяем, не закрыт ли онбординг - если да, то скрываем все подсказки
        const onboardingModal = document.querySelector('.kanban-onboarding-modal');
        if (!onboardingModal || onboardingModal.style.display === 'none') {
            console.log('[KanbanTooltips] 🎯 Онбординг закрыт, скрываем все подсказки при инициализации');
            this.hideAllTooltips();
        }

        // Добавляем обработчики событий для элементов с подсказками
        this.addTooltipListeners();

        // Создаем контейнер для подсказок
        this.createTooltipContainer();

        // Глобальный обработчик: клики вне подсказки — закрыть
        const outsideClickHandler = (e) => {
            const tooltip = e.target.closest('.kanban-tooltip');
            const trigger = e.target.closest('[data-tooltip]');
            if (!tooltip && !trigger) {
                this.hideTooltip();
            }
        };
        // Сохраняем, чтобы можно было отписаться при переинициализации
        this._outsideClickHandler = outsideClickHandler;
        document.addEventListener('click', this._outsideClickHandler, true);

        // Добавляем слушатель для автоматического скрытия при закрытии онбординга
        this.addOnboardingCloseListener();
    }

    /**
     * Добавляет слушатель для автоматического скрытия при закрытии онбординга
     */
    addOnboardingCloseListener() {
        // Слушаем клики по кнопке закрытия онбординга
        document.addEventListener('click', (e) => {
            if (e.target.closest('#onboarding-close-btn') ||
                e.target.closest('.onboarding-close-btn') ||
                e.target.closest('.onboarding-overlay')) {
                console.log('[KanbanTooltips] 🎯 Обнаружено закрытие онбординга, скрываем подсказки');
                this.hideAllTooltips();
            }
        });

        // Слушаем нажатие ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const onboardingModal = document.querySelector('.kanban-onboarding-modal');
                if (onboardingModal && onboardingModal.style.display !== 'none') {
                    console.log('[KanbanTooltips] 🎯 Обнаружено закрытие онбординга по ESC, скрываем подсказки');
                    this.hideAllTooltips();
                }
            }
        });

        // Слушаем изменения в DOM для обнаружения закрытия онбординга
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.removedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE &&
                        node.classList &&
                        node.classList.contains('kanban-onboarding-modal')) {
                        console.log('[KanbanTooltips] 🎯 Обнаружено удаление онбординга из DOM, скрываем подсказки');
                        this.hideAllTooltips();
                    }
                });
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Добавляет обработчики событий для элементов с подсказками
     */
    addTooltipListeners() {
        // Обработчики для карточек задач
        document.addEventListener('mouseover', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.showTooltip(target, e);
            }
        });

        document.addEventListener('mouseout', (e) => {
            const target = e.target.closest('[data-tooltip]');
            if (target) {
                this.hideTooltip();
            }
        });

        // Обработчики для элементов канбана
        document.addEventListener('mouseover', (e) => {
            const tooltipType = this.getTooltipType(e.target);
            if (tooltipType) {
                this.showTooltip(e.target, e, tooltipType);
            }
        });

        document.addEventListener('mouseout', (e) => {
            const tooltipType = this.getTooltipType(e.target);
            if (tooltipType) {
                this.hideTooltip();
            }
        });
    }

    /**
     * Определяет тип подсказки для элемента
     */
    getTooltipType(element) {
        if (element.classList.contains('kanban-card')) return 'kanban-card';
        if (element.classList.contains('kanban-card-id')) return 'kanban-card-id';
        if (element.classList.contains('kanban-column-header')) return 'kanban-column-header';
        if (element.classList.contains('kanban-column-count')) return 'kanban-column-count';
        if (element.classList.contains('priority-badge')) return 'priority-badge';
        if (element.classList.contains('view-toggle-btn')) return 'view-toggle-btn';
        return null;
    }

    /**
     * Создает контейнер для подсказок
     */
    createTooltipContainer() {
        const container = document.createElement('div');
        container.id = 'kanban-tooltip-container';
        container.className = 'kanban-tooltip-container';
        document.body.appendChild(container);

        // Инжект стилей для стабильной работы и кнопки закрытия
        if (!document.getElementById('kanban-tooltips-style')) {
            const style = document.createElement('style');
            style.id = 'kanban-tooltips-style';
            style.textContent = `
                .kanban-tooltip-container{position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:2147483000}
                .kanban-tooltip{position:absolute;max-width:360px;background:#0f172a;color:#e2e8f0;border-radius:10px;padding:12px 14px;box-shadow:0 12px 30px rgba(0,0,0,.35);border:1px solid rgba(255,255,255,.06);opacity:0;transform:translateY(6px) scale(.98);transition:opacity .18s ease,transform .18s ease;pointer-events:auto}
                .kanban-tooltip.show{opacity:1;transform:translateY(0) scale(1)}
                .kanban-tooltip .tooltip-header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:6px}
                .kanban-tooltip .tooltip-title{font-weight:700;font-size:14px}
                .kanban-tooltip .tooltip-content{font-size:13px;line-height:1.4;color:#cbd5e1}
                .kanban-tooltip .tooltip-close{appearance:none;background:transparent;border:none;color:#94a3b8;font-size:18px;line-height:1;cursor:pointer;padding:2px 6px;border-radius:6px;transition:background .15s ease,color .15s ease}
                .kanban-tooltip .tooltip-close:hover{background:rgba(148,163,184,.15);color:#e2e8f0}
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Показывает подсказку
     */
    showTooltip(element, event, tooltipType = null) {
        if (!this.isEnabled) return;

        const type = tooltipType || element.getAttribute('data-tooltip');
        const tooltip = this.tooltips[type];

        if (!tooltip) return;

        // Скрываем предыдущую подсказку
        this.hideTooltip();

        // Создаем новую подсказку
        const tooltipElement = document.createElement('div');
        tooltipElement.className = 'kanban-tooltip';
        tooltipElement.innerHTML = `
            <div class="tooltip-header">
                <span class="tooltip-title">${tooltip.title}</span>
                <button class="tooltip-close" aria-label="Закрыть" title="Закрыть">&times;</button>
            </div>
            <div class="tooltip-content">
                ${tooltip.content}
            </div>
        `;

        // Добавляем в контейнер
        const container = document.getElementById('kanban-tooltip-container');
        if (container) {
            container.appendChild(tooltipElement);
        }

        // Обработчик закрытия по крестику
        const closeBtn = tooltipElement.querySelector('.tooltip-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', (ev) => {
                ev.preventDefault();
                ev.stopPropagation();
                this.hideTooltip();
            }, { capture: true });
        }

        // Позиционируем подсказку
        this.positionTooltip(tooltipElement, event);

        // Сохраняем ссылку на активную подсказку
        this.activeTooltip = tooltipElement;

        // Показываем с анимацией
        setTimeout(() => {
            tooltipElement.classList.add('show');
        }, 10);
    }

    /**
     * Позиционирует подсказку относительно элемента
     */
    positionTooltip(tooltipElement, event) {
        const rect = event.target.getBoundingClientRect();
        const tooltipRect = tooltipElement.getBoundingClientRect();

        let left = event.clientX + 10;
        let top = event.clientY - tooltipRect.height - 10;

        // Проверяем, не выходит ли подсказка за границы экрана
        if (left + tooltipRect.width > window.innerWidth) {
            left = event.clientX - tooltipRect.width - 10;
        }

        if (top < 0) {
            top = event.clientY + 10;
        }

        tooltipElement.style.left = `${left}px`;
        tooltipElement.style.top = `${top}px`;
    }

    /**
     * Скрывает подсказку
     */
    hideTooltip() {
        if (this.activeTooltip) {
            this.activeTooltip.classList.remove('show');
            setTimeout(() => {
                if (this.activeTooltip && this.activeTooltip.parentNode) {
                    this.activeTooltip.parentNode.removeChild(this.activeTooltip);
                }
            }, 200);
            this.activeTooltip = null;
            // Удаляем контейнер, чтобы не оставались «залипания»
            const container = document.getElementById('kanban-tooltip-container');
            if (container && container.childElementCount === 0) {
                container.remove();
            }
        }
    }

    /**
     * Скрывает все всплывающие подсказки
     */
    hideAllTooltips() {
        // Скрываем активную подсказку
        this.hideTooltip();

        // Скрываем все остальные подсказки в контейнере
        const container = document.getElementById('kanban-tooltip-container');
        if (container) {
            const allTooltips = container.querySelectorAll('.kanban-tooltip');
            allTooltips.forEach(tooltip => {
                tooltip.classList.remove('show');
                setTimeout(() => {
                    if (tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 200);
            });
        }

        // Дополнительно: скрываем все подсказки на странице (более агрессивный подход)
        const allTooltipsOnPage = document.querySelectorAll('.kanban-tooltip');
        allTooltipsOnPage.forEach(tooltip => {
            tooltip.classList.remove('show');
            tooltip.style.opacity = '0';
            tooltip.style.transform = 'translateY(10px) scale(0.95)';
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 200);
        });

        // Удаляем весь контейнер подсказок если он есть
        const tooltipContainer = document.getElementById('kanban-tooltip-container');
        if (tooltipContainer) {
            tooltipContainer.remove();
        }

        console.log('[KanbanTooltips] 🎯 Скрыты все всплывающие подсказки');
    }

    /**
     * Принудительно скрывает все подсказки на странице
     */
    forceHideAllTooltips() {
        // Скрываем активную подсказку
        this.hideTooltip();

        // Удаляем все подсказки со страницы
        const allTooltips = document.querySelectorAll('.kanban-tooltip');
        allTooltips.forEach(tooltip => {
            tooltip.style.opacity = '0';
            tooltip.style.transform = 'translateY(10px) scale(0.95)';
            tooltip.classList.remove('show');
            tooltip.remove();
        });

        // Удаляем контейнер подсказок
        const container = document.getElementById('kanban-tooltip-container');
        if (container) {
            container.remove();
        }

        console.log('[KanbanTooltips] 🎯 Принудительно скрыты все подсказки');
    }

    /**
     * Включает/выключает подсказки
     */
    toggle() {
        this.isEnabled = !this.isEnabled;
        if (!this.isEnabled) {
            this.hideTooltip();
        }
        console.log(`[KanbanTooltips] ${this.isEnabled ? '✅' : '❌'} Подсказки ${this.isEnabled ? 'включены' : 'отключены'}`);
    }

    /**
     * Добавляет атрибут data-tooltip к элементу
     */
    addTooltipToElement(element, tooltipType) {
        if (element) {
            element.setAttribute('data-tooltip', tooltipType);
        }
    }

    /**
     * Удаляет подсказку с элемента
     */
    removeTooltipFromElement(element) {
        if (element) {
            element.removeAttribute('data-tooltip');
        }
    }
}

// Экспортируем для использования в других модулях
window.KanbanTooltips = KanbanTooltips;

// Глобальная функция для скрытия всех подсказок
window.hideAllKanbanTooltips = function() {
    if (typeof window.KanbanTooltips !== 'undefined') {
        const tooltips = new window.KanbanTooltips();
        tooltips.forceHideAllTooltips();
        console.log('[Global] 🎯 Принудительно скрыты все всплывающие подсказки через глобальную функцию');
    } else {
        // Альтернативный способ - принудительно удаляем все подсказки
        const tooltips = document.querySelectorAll('.kanban-tooltip');
        tooltips.forEach(tooltip => {
            tooltip.style.opacity = '0';
            tooltip.style.transform = 'translateY(10px) scale(0.95)';
            tooltip.classList.remove('show');
            tooltip.remove();
        });

        // Удаляем контейнер
        const container = document.getElementById('kanban-tooltip-container');
        if (container) {
            container.remove();
        }

        console.log('[Global] 🎯 Принудительно скрыты все всплывающие подсказки (альтернативный способ)');
    }
};

// Экстренная функция для принудительного скрытия всех подсказок
window.emergencyHideTooltips = function() {
    console.log('[Emergency] 🚨 Экстренное скрытие всех подсказок...');

    // Удаляем все подсказки немедленно
    const allTooltips = document.querySelectorAll('.kanban-tooltip');
    allTooltips.forEach(tooltip => {
        tooltip.remove();
    });

    // Удаляем все контейнеры подсказок
    const containers = document.querySelectorAll('#kanban-tooltip-container');
    containers.forEach(container => {
        container.remove();
    });

    // Удаляем все элементы с data-tooltip
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.removeAttribute('data-tooltip');
    });

    console.log('[Emergency] ✅ Все подсказки экстренно удалены');
};
