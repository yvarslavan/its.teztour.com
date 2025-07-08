/**
 * StatisticsPanel - Компонент панели статистики
 * Инкапсулирует логику загрузки и отображения статистики задач
 */
class StatisticsPanel {
    constructor(eventBus, loadingManager, tasksAPI) {
        this.eventBus = eventBus;
        this.loadingManager = loadingManager;
        this.tasksAPI = tasksAPI;

        this.statisticsData = null;
        this.isInitialized = false;
        this.updateInterval = null;

        // Селекторы элементов
        this.selectors = {
            totalTasks: '#total-tasks-summary, #total-tasks',
            openTasks: '#open-tasks',
            closedTasks: '#closed-db-tasks',
            pausedTasks: '#paused-tasks',
            breakdownCards: '.status-breakdown-card',
            totalBreakdown: '#total-breakdown',
            openBreakdown: '#open-breakdown',
            closedBreakdown: '#closed-breakdown',
            pausedBreakdown: '#paused-breakdown',
            expandButton: '#expandBreakdownBtn'
        };

        // Привязываем методы к контексту
        this.handleStatisticsUpdate = this.handleStatisticsUpdate.bind(this);
        this.handleCardToggle = this.handleCardToggle.bind(this);
    }

    /**
     * Инициализация панели статистики
     */
    async init() {
        try {
            console.log('[StatisticsPanel] 🚀 Инициализация панели статистики...');

            this._setupEventListeners();
            this._initializeCardToggleButtons();

            // Загружаем начальную статистику
            await this.loadStatistics();

            // Настраиваем автообновление (каждые 30 секунд)
            this._setupAutoUpdate(30000);

            this.isInitialized = true;
            console.log('[StatisticsPanel] ✅ Панель статистики инициализирована');

            this.eventBus.emit('statistics:initialized');

        } catch (error) {
            console.error('[StatisticsPanel] ❌ Ошибка инициализации:', error);
            this.eventBus.emit('statistics:error', { error: error.message });
            throw error;
        }
    }

    /**
     * Загрузка статистики
     */
    async loadStatistics() {
        try {
            console.log('[StatisticsPanel] 📊 Загрузка статистики...');

            this._showLoadingState();
            this.loadingManager.show('statistics', 'Загрузка статистики...');

            // Используем существующий API endpoint
            const response = await fetch('/tasks/get-my-tasks-statistics-optimized');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success || data.total_tasks !== undefined) {
                this.statisticsData = data;
                this._updateStatisticsDisplay(data);
                this.eventBus.emit('statistics:loaded', { data });
            } else {
                throw new Error(data.error || 'Неизвестная ошибка API');
            }

        } catch (error) {
            console.error('[StatisticsPanel] ❌ Ошибка загрузки статистики:', error);
            this._showErrorState();
            this.eventBus.emit('statistics:error', { error: error.message });
        } finally {
            this.loadingManager.hide('statistics');
        }
    }

    /**
     * Обновление отображения статистики
     */
    _updateStatisticsDisplay(stats) {
        console.log('[StatisticsPanel] 🎨 Обновление отображения статистики:', stats);

        // Убираем состояние загрузки
        this._hideLoadingState();

        // Извлекаем основные метрики
        const metrics = this._extractMetrics(stats);

        // Обновляем основные значения с анимацией
        this._animateAndUpdateValue(this.selectors.totalTasks, metrics.total);
        this._animateAndUpdateValue(this.selectors.openTasks, metrics.open);
        this._animateAndUpdateValue(this.selectors.closedTasks, metrics.closed);
        this._animateAndUpdateValue(this.selectors.pausedTasks, metrics.paused);

        // Обновляем детализацию в карточках
        this._updateCardBreakdowns(stats.statistics?.debug_status_counts || {}, metrics);

        // Сохраняем данные для детальной разбивки
        window.detailedStatusData = stats.statistics?.debug_status_counts || {};

        // Активируем кнопку развертывания если есть данные
        this._updateExpandButton();

        console.log('[StatisticsPanel] ✅ Статистика обновлена:', metrics);
    }

    /**
     * Извлечение метрик из данных статистики
     */
    _extractMetrics(stats) {
        const total = stats.total_tasks || stats.total || 0;
        const newTasks = stats.new_tasks || stats.new || 0;
        const inProgressTasks = stats.in_progress_tasks || stats.in_progress || 0;
        const actuallyClosedTasks = stats.statistics?.additional_stats?.actually_closed_tasks || 0;

        return {
            total: total,
            open: newTasks,        // API классифицирует NEW как открытые
            paused: inProgressTasks, // API классифицирует IN_PROGRESS как приостановленные
            closed: actuallyClosedTasks
        };
    }

    /**
     * Анимированное обновление значения
     */
    _animateAndUpdateValue(selector, value) {
        const elements = $(selector);
        elements.each(function() {
            const $element = $(this);
            $element.addClass('animate-count').text(value);
            setTimeout(() => $element.removeClass('animate-count'), 600);
        });
    }

    /**
     * Обновление детализации в карточках
     */
    _updateCardBreakdowns(statusCounts, metrics) {
        console.log('[StatisticsPanel] 🔧 Обновление детализации карточек...');

        // Обновляем каждую категорию
        this._updateCardBreakdown(
            this.selectors.openBreakdown,
            statusCounts,
            ['New', 'Open', 'Новая', 'Новый', 'Открыта', 'Открыт', 'Открытая']
        );

        this._updateCardBreakdown(
            this.selectors.closedBreakdown,
            statusCounts,
            ['Closed', 'Rejected', 'Redirected', 'Закрыта', 'Закрыт', 'Закрытая',
             'Отклонена', 'Отклонен', 'Отклонённая', 'Перенаправлена', 'Перенаправлен']
        );

        this._updateCardBreakdown(
            this.selectors.pausedBreakdown,
            statusCounts,
            ['Paused', 'Frozen', 'In Progress', 'Executed', 'On testing',
             'The request specification', 'On the coordination', 'Tested',
             'Приостановлена', 'Приостановлен', 'Заморожена', 'Заморожен',
             'В работе', 'В процессе', 'Выполнена', 'Выполнен', 'На тестировании',
             'На согласовании', 'Согласование', 'Запрошено уточнение', 'Уточнение',
             'Протестирована', 'Протестирован']
        );

        // Обновляем общую детализацию (все статусы)
        this._updateCardBreakdownAll(this.selectors.totalBreakdown, statusCounts);

        // Сбрасываем состояние кнопок после обновления
        setTimeout(() => {
            $('.card-breakdown').addClass('collapsed').removeClass('expanded');
            $('.card-toggle-btn').removeClass('expanded');
            console.log('[StatisticsPanel] 🔄 Состояние кнопок сброшено');
        }, 100);
    }

    /**
     * Обновление детализации для конкретной категории
     */
    _updateCardBreakdown(containerSelector, statusCounts, relevantStatuses) {
        const container = $(containerSelector);

        if (container.length === 0) {
            console.warn(`[StatisticsPanel] ⚠️ Контейнер ${containerSelector} не найден`);
            return;
        }

        container.empty();

        // Получаем отфильтрованные статусы
        const filteredStatuses = this._filterStatusesByRelevance(statusCounts, relevantStatuses);

        if (filteredStatuses.length === 0) {
            container.html('<div class="breakdown-item"><span class="breakdown-status-name">Нет данных</span></div>');
            return;
        }

        // Сортируем по убыванию количества
        filteredStatuses.sort((a, b) => b.count - a.count);

        // Создаем элементы
        filteredStatuses.forEach(item => {
            const breakdownItem = $(`
                <div class="breakdown-item">
                    <span class="breakdown-status-name">${this._escapeHtml(item.name)}</span>
                    <span class="breakdown-status-count">${item.count}</span>
                </div>
            `);
            container.append(breakdownItem);
        });

        console.log(`[StatisticsPanel] ✅ Детализация обновлена для ${containerSelector}:`, filteredStatuses.length);
    }

    /**
     * Обновление полной детализации (все статусы)
     */
    _updateCardBreakdownAll(containerSelector, statusCounts) {
        const container = $(containerSelector);

        if (container.length === 0) {
            console.warn(`[StatisticsPanel] ⚠️ Контейнер ${containerSelector} не найден`);
            return;
        }

        container.empty();

        if (!statusCounts || Object.keys(statusCounts).length === 0) {
            container.html('<div class="breakdown-item"><span class="breakdown-status-name">Нет данных</span></div>');
            return;
        }

        // Преобразуем все статусы в массив и сортируем
        const allStatuses = Object.entries(statusCounts)
            .map(([name, count]) => ({ name, count }))
            .filter(item => item.count > 0)
            .sort((a, b) => b.count - a.count);

        if (allStatuses.length === 0) {
            container.html('<div class="breakdown-item"><span class="breakdown-status-name">Нет задач</span></div>');
            return;
        }

        // Создаем элементы для всех статусов
        allStatuses.forEach(item => {
            const breakdownItem = $(`
                <div class="breakdown-item">
                    <span class="breakdown-status-name">${this._escapeHtml(item.name)}</span>
                    <span class="breakdown-status-count">${item.count}</span>
                </div>
            `);
            container.append(breakdownItem);
        });

        console.log(`[StatisticsPanel] ✅ Полная детализация обновлена:`, allStatuses.length);
    }

    /**
     * Фильтрация статусов по релевантности
     */
    _filterStatusesByRelevance(statusCounts, relevantStatuses) {
        const allStatusEntries = Object.entries(statusCounts)
            .map(([name, count]) => ({ name, count }))
            .filter(item => item.count > 0);

        return allStatusEntries.filter(item => {
            const statusName = item.name.toLowerCase();
            return relevantStatuses.some(relevantStatus => {
                const relevantLower = relevantStatus.toLowerCase();
                return statusName === relevantLower ||
                       statusName.includes(relevantLower) ||
                       relevantLower.includes(statusName);
            });
        });
    }

    /**
     * Показать состояние загрузки
     */
    _showLoadingState() {
        $(this.selectors.breakdownCards).addClass('loading');
        $('#total-tasks-summary').addClass('loading').text('...');
        $('#total-tasks, #open-tasks, #closed-db-tasks, #paused-tasks').text('...');
    }

    /**
     * Скрыть состояние загрузки
     */
    _hideLoadingState() {
        $(this.selectors.breakdownCards).removeClass('loading');
        $('#total-tasks-summary').removeClass('loading');
    }

    /**
     * Показать состояние ошибки
     */
    _showErrorState() {
        this._hideLoadingState();
        $('#total-tasks-summary').text('Ошибка');
        $('#total-tasks, #open-tasks, #closed-db-tasks, #paused-tasks').text('Ошибка');
    }

    /**
     * Обновление кнопки развертывания
     */
    _updateExpandButton() {
        const expandButton = $(this.selectors.expandButton);
        if (expandButton.length > 0) {
            const hasData = window.detailedStatusData && Object.keys(window.detailedStatusData).length > 0;
            expandButton.toggleClass('disabled', !hasData).prop('disabled', !hasData);
        }
    }

    /**
     * Инициализация кнопок переключения карточек
     */
    _initializeCardToggleButtons() {
        // Инициализируем обработчики для кнопок переключения
        $(document).on('click', '.card-toggle-btn', this.handleCardToggle);

        // Сбрасываем начальное состояние
        $('.card-breakdown').addClass('collapsed').removeClass('expanded');
        $('.card-toggle-btn').removeClass('expanded');
    }

    /**
     * Обработчик переключения карточек
     */
    handleCardToggle(event) {
        event.preventDefault();

        const button = $(event.currentTarget);
        const card = button.closest('.status-breakdown-card');
        const breakdown = card.find('.card-breakdown');

        const isExpanded = breakdown.hasClass('expanded');

        if (isExpanded) {
            // Сворачиваем
            breakdown.removeClass('expanded').addClass('collapsed');
            button.removeClass('expanded');
        } else {
            // Разворачиваем
            breakdown.removeClass('collapsed').addClass('expanded');
            button.addClass('expanded');
        }

        console.log('[StatisticsPanel] 🔄 Карточка переключена:', isExpanded ? 'свернута' : 'развернута');
    }

    /**
     * Настройка автообновления
     */
    _setupAutoUpdate(interval) {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        this.updateInterval = setInterval(() => {
            if (this.isInitialized) {
                console.log('[StatisticsPanel] 🔄 Автообновление статистики...');
                this.loadStatistics();
            }
        }, interval);
    }

    /**
     * Настройка слушателей событий
     */
    _setupEventListeners() {
        // Слушаем события от других компонентов
        this.eventBus.on('table:dataLoaded', this.handleStatisticsUpdate);
        this.eventBus.on('filters:changed', this.handleStatisticsUpdate);
        this.eventBus.on('statistics:refresh', () => {
            this.loadStatistics();
        });
    }

    /**
     * Обработчик обновления статистики при изменении данных
     */
    handleStatisticsUpdate(data) {
        // Обновляем статистику при изменении данных таблицы или фильтров
        setTimeout(() => {
            this.loadStatistics();
        }, 500); // Небольшая задержка для завершения операций
    }

    /**
     * Утилита для экранирования HTML
     */
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Получение текущих данных статистики
     */
    getCurrentData() {
        return this.statisticsData;
    }

    /**
     * Принудительное обновление
     */
    refresh() {
        console.log('[StatisticsPanel] 🔄 Принудительное обновление статистики');
        return this.loadStatistics();
    }

    /**
     * Очистка ресурсов
     */
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }

        $(document).off('click', '.card-toggle-btn', this.handleCardToggle);

        this.isInitialized = false;
        console.log('[StatisticsPanel] 🗑️ Компонент очищен');
    }
}

// Экспорт для ES6 модулей и глобального использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StatisticsPanel;
} else if (typeof window !== 'undefined') {
    window.StatisticsPanel = StatisticsPanel;
}
