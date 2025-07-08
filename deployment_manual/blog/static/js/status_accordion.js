/**
 * Управление аккордеоном детализации статусов задач
 * Обеспечивает раскрытие/скрытие групп статусов с анимацией
 */

class StatusAccordion {
    constructor() {
        this.accordionContainer = null;
        this.isAllExpanded = false;
        this.statusData = null;

        // Привязываем методы к контексту
        this.toggleItem = this.toggleItem.bind(this);
        this.toggleAll = this.toggleAll.bind(this);
        this.handleKeyPress = this.handleKeyPress.bind(this);
    }

    /**
     * Инициализация аккордеона с данными статусов
     * @param {Object} statusGroups - Группированные данные статусов из API
     * @param {string} containerId - ID контейнера для размещения аккордеона
     */
    init(statusGroups, containerId = 'statusAccordion') {
        console.log('🎵 [ACCORDION] Инициализация аккордеона статусов:', statusGroups);

        this.statusData = statusGroups;
        this.accordionContainer = document.getElementById(containerId);

        if (!this.accordionContainer) {
            console.error('❌ [ACCORDION] Контейнер не найден:', containerId);
            return;
        }

        this.render();
        this.attachEventListeners();

        console.log('✅ [ACCORDION] Аккордеон инициализирован');
    }

    /**
     * Отрисовка HTML структуры аккордеона
     */
    render() {
        if (!this.statusData) {
            this.accordionContainer.innerHTML = '<div class="accordion-error">Нет данных для отображения</div>';
            return;
        }

        const totalTasks = Object.values(this.statusData).reduce((sum, group) => sum + group.total, 0);

        const html = `
            <div class="status-accordion">
                <div class="accordion-controls">
                    <h3>Детализация по статусам</h3>
                    <button class="accordion-toggle-all" id="toggleAllBtn">
                        <i class="fas fa-expand-arrows-alt"></i>
                        <span>Развернуть все</span>
                    </button>
                </div>

                <div class="accordion-content-wrapper">
                    ${this.renderAccordionItems(totalTasks)}
                </div>
            </div>
        `;

        this.accordionContainer.innerHTML = html;
    }

    /**
     * Отрисовка элементов аккордеона
     * @param {number} totalTasks - Общее количество задач
     */
    renderAccordionItems(totalTasks) {
        const groupOrder = ['new', 'in_progress', 'closed'];
        const groupIcons = {
            'new': 'fas fa-plus',
            'in_progress': 'fas fa-cog fa-spin',
            'closed': 'fas fa-check'
        };

        return groupOrder.map(groupKey => {
            const group = this.statusData[groupKey];
            if (!group || group.total === 0) return '';

            const percentage = totalTasks > 0 ? Math.round((group.total / totalTasks) * 100) : 0;

            return `
                <div class="accordion-item" data-group="${groupKey}">
                    <div class="accordion-header" role="button" tabindex="0" aria-expanded="false">
                        <div class="accordion-title">
                            <div class="accordion-icon ${groupKey}">
                                <i class="${groupIcons[groupKey]}"></i>
                            </div>
                            <div>
                                <div>${group.name}</div>
                                <div class="accordion-count">${group.total} задач (${percentage}%)</div>
                            </div>
                        </div>
                        <div class="accordion-toggle">
                            <span>Показать детали</span>
                            <i class="fas fa-chevron-down accordion-chevron"></i>
                        </div>
                    </div>

                    <div class="accordion-content">
                        <div class="accordion-body">
                            ${this.renderStatusList(group.statuses, group.total)}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * Отрисовка списка статусов в группе
     * @param {Array} statuses - Массив статусов
     * @param {number} groupTotal - Общее количество задач в группе
     */
    renderStatusList(statuses, groupTotal) {
        if (!statuses || statuses.length === 0) {
            return '<div class="accordion-empty">Нет статусов в этой группе</div>';
        }

        return `
            <div class="status-list">
                ${statuses.map(status => {
                    const percentage = groupTotal > 0 ? Math.round((status.count / groupTotal) * 100) : 0;

                    return `
                        <div class="status-item" data-status-id="${status.id}">
                            <div class="status-info">
                                <div class="status-name">${status.localized_name}</div>
                                ${status.original_name !== status.localized_name ?
                                    `<div class="status-original">${status.original_name}</div>` :
                                    ''
                                }
                            </div>
                            <div class="status-count">
                                <div class="status-badge">${status.count}</div>
                                <div class="status-percentage">${percentage}%</div>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    /**
     * Привязка обработчиков событий
     */
    attachEventListeners() {
        // Кнопка "Развернуть/Свернуть все"
        const toggleAllBtn = document.getElementById('toggleAllBtn');
        if (toggleAllBtn) {
            toggleAllBtn.addEventListener('click', this.toggleAll);
        }

        // Заголовки аккордеона
        const headers = this.accordionContainer.querySelectorAll('.accordion-header');
        headers.forEach(header => {
            header.addEventListener('click', this.toggleItem);
            header.addEventListener('keypress', this.handleKeyPress);
        });
    }

    /**
     * Переключение состояния отдельного элемента аккордеона
     * @param {Event} event - Событие клика
     */
    toggleItem(event) {
        const header = event.currentTarget;
        const item = header.closest('.accordion-item');
        const content = item.querySelector('.accordion-content');
        const toggle = header.querySelector('.accordion-toggle span');

        const isExpanded = item.classList.contains('expanded');

        if (isExpanded) {
            // Сворачиваем
            item.classList.remove('expanded');
            header.setAttribute('aria-expanded', 'false');
            toggle.textContent = 'Показать детали';

            console.log('🎵 [ACCORDION] Свернули группу:', item.dataset.group);
        } else {
            // Разворачиваем
            item.classList.add('expanded');
            header.setAttribute('aria-expanded', 'true');
            toggle.textContent = 'Скрыть детали';

            console.log('🎵 [ACCORDION] Развернули группу:', item.dataset.group);
        }

        // Обновляем состояние кнопки "Развернуть все"
        this.updateToggleAllButton();
    }

    /**
     * Переключение всех элементов аккордеона
     */
    toggleAll() {
        const items = this.accordionContainer.querySelectorAll('.accordion-item');
        const toggleAllBtn = document.getElementById('toggleAllBtn');

        if (this.isAllExpanded) {
            // Сворачиваем все
            items.forEach(item => {
                const header = item.querySelector('.accordion-header');
                const toggle = header.querySelector('.accordion-toggle span');

                item.classList.remove('expanded');
                header.setAttribute('aria-expanded', 'false');
                toggle.textContent = 'Показать детали';
            });

            this.isAllExpanded = false;
            toggleAllBtn.innerHTML = '<i class="fas fa-expand-arrows-alt"></i><span>Развернуть все</span>';

            console.log('🎵 [ACCORDION] Свернули все группы');
        } else {
            // Разворачиваем все
            items.forEach(item => {
                const header = item.querySelector('.accordion-header');
                const toggle = header.querySelector('.accordion-toggle span');

                item.classList.add('expanded');
                header.setAttribute('aria-expanded', 'true');
                toggle.textContent = 'Скрыть детали';
            });

            this.isAllExpanded = true;
            toggleAllBtn.innerHTML = '<i class="fas fa-compress-arrows-alt"></i><span>Свернуть все</span>';

            console.log('🎵 [ACCORDION] Развернули все группы');
        }
    }

    /**
     * Обработка нажатия клавиш для доступности
     * @param {Event} event - Событие нажатия клавиши
     */
    handleKeyPress(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.toggleItem(event);
        }
    }

    /**
     * Обновление состояния кнопки "Развернуть все"
     */
    updateToggleAllButton() {
        const items = this.accordionContainer.querySelectorAll('.accordion-item');
        const expandedItems = this.accordionContainer.querySelectorAll('.accordion-item.expanded');
        const toggleAllBtn = document.getElementById('toggleAllBtn');

        if (expandedItems.length === items.length && items.length > 0) {
            // Все развернуты
            this.isAllExpanded = true;
            toggleAllBtn.innerHTML = '<i class="fas fa-compress-arrows-alt"></i><span>Свернуть все</span>';
        } else {
            // Не все развернуты
            this.isAllExpanded = false;
            toggleAllBtn.innerHTML = '<i class="fas fa-expand-arrows-alt"></i><span>Развернуть все</span>';
        }
    }

    /**
     * Обновление данных аккордеона
     * @param {Object} statusGroups - Новые данные статусов
     */
    updateData(statusGroups) {
        console.log('🎵 [ACCORDION] Обновление данных аккордеона');
        this.statusData = statusGroups;
        this.render();
        this.attachEventListeners();
    }

    /**
     * Показать состояние загрузки
     */
    showLoading() {
        if (this.accordionContainer) {
            this.accordionContainer.innerHTML = `
                <div class="accordion-loading">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span style="margin-left: 0.5rem;">Загрузка детализации статусов...</span>
                </div>
            `;
        }
    }

    /**
     * Показать ошибку
     * @param {string} message - Сообщение об ошибке
     */
    showError(message) {
        if (this.accordionContainer) {
            this.accordionContainer.innerHTML = `
                <div class="accordion-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span style="margin-left: 0.5rem;">${message}</span>
                </div>
            `;
        }
    }

    /**
     * Уничтожение аккордеона и очистка обработчиков
     */
    destroy() {
        if (this.accordionContainer) {
            this.accordionContainer.innerHTML = '';
        }
        this.statusData = null;
        console.log('🎵 [ACCORDION] Аккордеон уничтожен');
    }
}

// Глобальный экземпляр аккордеона
window.statusAccordion = new StatusAccordion();

// Экспорт для использования в модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StatusAccordion;
}
