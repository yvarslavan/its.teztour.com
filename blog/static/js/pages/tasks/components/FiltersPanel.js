/**
 * FiltersPanel - Компонент панели фильтров
 * Инкапсулирует логику загрузки и управления фильтрами
 */
const __filtersDebugLog = (...args) => { if (window.__TASKS_DEBUG__) console.log(...args); };

class FiltersPanel {
    constructor(eventBus, loadingManager, tasksAPI) {
        this.eventBus = eventBus;
        this.loadingManager = loadingManager;
        this.tasksAPI = tasksAPI;

        this.filtersData = null;
        this.isInitialized = false;
        this.isLoading = false;

        // Кэш фильтров (5 минут)
        this.cache = {
            data: null,
            timestamp: null,
            isValid: () => {
                const now = Date.now();
                const validTime = 5 * 60 * 1000; // 5 минут
                return this.cache.data &&
                       this.cache.timestamp &&
                       (now - this.cache.timestamp) < validTime;
            }
        };

        // Селекторы фильтров
        this.selectors = {
            statusFilter: '#status-filter',
            projectFilter: '#project-filter',
            priorityFilter: '#priority-filter',
            searchFilter: '#search-filter',
            clearButtons: '.clear-filter-btn',
            filterContainers: '.filter-container'
        };

        // Привязываем методы к контексту
        this.handleFilterChange = this.handleFilterChange.bind(this);
        this.handleClearFilter = this.handleClearFilter.bind(this);
        this.handleSearchInput = this.handleSearchInput.bind(this);
        this.debouncedSearch = null;
    }

    /**
     * Инициализация панели фильтров
     */
    async init() {
        try {
            __filtersDebugLog('[FiltersPanel] 🚀 Инициализация панели фильтров...');

            // Настраиваем debounced поиск
            this.debouncedSearch = debounce(this.performSearch.bind(this), 500);

            // Настраиваем обработчики событий
            this._setupEventListeners();

            // Загружаем фильтры
            await this.loadFilters();

            // Инициализируем состояние фильтров
            this._initializeFilterState();

            this.isInitialized = true;
            __filtersDebugLog('[FiltersPanel] ✅ Панель фильтров инициализирована');

            this.eventBus.emit('filters:initialized');

        } catch (error) {
            console.error('[FiltersPanel] ❌ Ошибка инициализации:', error);
            this.eventBus.emit('filters:error', { error: error.message });
            throw error;
        }
    }

    /**
     * Загрузка данных фильтров
     */
    async loadFilters() {
        if (this.isLoading) {
            __filtersDebugLog('[FiltersPanel] Фильтры уже загружаются...');
            return;
        }

        // Проверяем кэш
        if (this.cache.isValid()) {
            __filtersDebugLog('[FiltersPanel] 📦 Используем кэшированные фильтры');
            this._updateFilterOptions(this.cache.data);
            return;
        }

        try {
            __filtersDebugLog('[FiltersPanel] 📥 Загрузка фильтров...');
            this.isLoading = true;
            this._showLoadingIndicator(true);

            // Пробуем оптимизированный API
            let response = await this._tryOptimizedAPI();

            if (!response) {
                // Fallback на старый API
                __filtersDebugLog('[FiltersPanel] 🔄 Fallback на старый API...');
                response = await this._tryFallbackAPI();
            }

            if (response && response.success) {
                const filters = {
                    statuses: response.statuses || [],
                    projects: response.projects || [],
                    priorities: response.priorities || [],
                    hierarchical: response.hierarchical || false
                };

                // Кэшируем данные
                this.cache.data = filters;
                this.cache.timestamp = Date.now();
                this.filtersData = filters;

                this._updateFilterOptions(filters);
                this.eventBus.emit('filters:loaded', { filters });

                __filtersDebugLog('[FiltersPanel] ✅ Фильтры загружены:', {
                    statuses: filters.statuses.length,
                    projects: filters.projects.length,
                    priorities: filters.priorities.length
                });

            } else {
                throw new Error('Не удалось загрузить фильтры из всех источников');
            }

        } catch (error) {
            console.error('[FiltersPanel] ❌ Ошибка загрузки фильтров:', error);
            this._clearAndDisableFilters();
            this.eventBus.emit('filters:error', { error: error.message });
        } finally {
            this.isLoading = false;
            this._showLoadingIndicator(false);
        }
    }

    /**
     * Попытка загрузки через оптимизированный API
     */
    async _tryOptimizedAPI() {
        try {
            const response = await fetch('/tasks/get-my-tasks-filters-optimized');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    __filtersDebugLog('[FiltersPanel] ✅ Оптимизированный API успешен');
                    return data;
                }
            }
        } catch (error) {
            console.warn('[FiltersPanel] ⚠️ Оптимизированный API недоступен:', error);
        }
        return null;
    }

    /**
     * Fallback на старый API
     */
    async _tryFallbackAPI() {
        try {
            const response = await fetch('/tasks/get-my-tasks-filters-direct-api');
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    __filtersDebugLog('[FiltersPanel] ✅ Fallback API успешен');
                    return data;
                }
            }
        } catch (error) {
            console.warn('[FiltersPanel] ⚠️ Fallback API недоступен:', error);
        }
        return null;
    }

    /**
     * Обновление опций фильтров
     */
    _updateFilterOptions(filters) {
        __filtersDebugLog('[FiltersPanel] 🔧 Обновление опций фильтров...');

        this._populateStandardSelect(this.selectors.statusFilter, filters.statuses, 'Все статусы');
        this._populateStandardSelect(this.selectors.priorityFilter, filters.priorities, 'Все приоритеты');
        this._populateProjectSelect(this.selectors.projectFilter, filters.projects, 'Все проекты');

        // Обновляем видимость кнопок очистки
        setTimeout(() => {
            this._updateAllClearButtons();
        }, 100);

        __filtersDebugLog('[FiltersPanel] ✅ Опции фильтров обновлены');
    }

    /**
     * Заполнение стандартного селекта
     */
    _populateStandardSelect(selector, options, defaultText) {
        const select = $(selector);
        if (!select.length) {
            console.warn(`[FiltersPanel] ⚠️ Селект ${selector} не найден`);
            return;
        }

        // Очищаем и добавляем дефолтную опцию
        select.empty().append(`<option value="">${defaultText}</option>`);

        // Добавляем опции
        (options || []).forEach(opt => {
            // Обеспечиваем числовой ID
            let id = opt.id;
            if (typeof id === 'string') {
                const numId = parseInt(id, 10);
                if (!isNaN(numId)) {
                    id = numId;
                }
            }

            const option = $('<option></option>')
                .attr('value', id)
                .text(opt.name);

            select.append(option);
        });

        // Сбрасываем к дефолту
        select.val('');
        select.closest('.filter-container').removeClass('has-value');

        __filtersDebugLog(`[FiltersPanel] ✅ Селект ${selector} заполнен: ${options.length} опций`);
    }

    /**
     * Заполнение селекта проектов
     */
    _populateProjectSelect(selector, options, defaultText) {
        const select = $(selector);
        if (!select.length) {
            console.warn(`[FiltersPanel] ⚠️ Селект проектов ${selector} не найден`);
            return;
        }

        // Очищаем и добавляем дефолтную опцию
        select.empty().append(`<option value="">${defaultText}</option>`);

        // Сортируем проекты по алфавиту
        const sortedProjects = (options || []).sort((a, b) => {
            const nameA = (a.original_name || a.name || '').toLowerCase();
            const nameB = (b.original_name || b.name || '').toLowerCase();
            return nameA.localeCompare(nameB);
        });

        // Добавляем проекты
        sortedProjects.forEach(opt => {
            let id = opt.id;
            if (typeof id === 'string') {
                const numId = parseInt(id, 10);
                if (!isNaN(numId)) {
                    id = numId;
                }
            }

            const displayName = opt.original_name || opt.name;
            const option = $('<option></option>')
                .attr('value', id)
                .attr('data-name', displayName.toLowerCase())
                .text(displayName);

            select.append(option);
        });

        // Сбрасываем к дефолту
        select.val('');
        select.closest('.filter-container').removeClass('has-value');

        __filtersDebugLog(`[FiltersPanel] ✅ Селект проектов заполнен: ${sortedProjects.length} опций`);
    }

    /**
     * Получение текущих значений фильтров
     */
    getCurrentFilters() {
        return {
            status: $(this.selectors.statusFilter).val() || '',
            project: $(this.selectors.projectFilter).val() || '',
            priority: $(this.selectors.priorityFilter).val() || '',
            search: $(this.selectors.searchFilter).val() || ''
        };
    }

    /**
     * Применение фильтров
     */
    applyFilters(filters = {}) {
        __filtersDebugLog('[FiltersPanel] 🔍 Применение фильтров:', filters);

        // Устанавливаем значения
        if (filters.status !== undefined) {
            $(this.selectors.statusFilter).val(filters.status);
        }
        if (filters.project !== undefined) {
            $(this.selectors.projectFilter).val(filters.project);
        }
        if (filters.priority !== undefined) {
            $(this.selectors.priorityFilter).val(filters.priority);
        }
        if (filters.search !== undefined) {
            $(this.selectors.searchFilter).val(filters.search);
        }

        // Обновляем видимость кнопок
        this._updateAllClearButtons();

        // Уведомляем об изменении
        this.eventBus.emit('filters:changed', {
            filters: this.getCurrentFilters()
        });
    }

    /**
     * Сброс всех фильтров
     */
    resetAllFilters() {
        __filtersDebugLog('[FiltersPanel] 🔄 Сброс всех фильтров');

        $(this.selectors.statusFilter).val('');
        $(this.selectors.projectFilter).val('');
        $(this.selectors.priorityFilter).val('');
        $(this.selectors.searchFilter).val('');

        // Убираем классы активности
        $(this.selectors.filterContainers).removeClass('has-value');
        $(this.selectors.clearButtons).removeClass('show').hide();

        // Уведомляем об изменении
        this.eventBus.emit('filters:changed', {
            filters: this.getCurrentFilters()
        });

        this.eventBus.emit('filters:reset');
    }

    /**
     * Выполнение поиска
     */
    performSearch(searchTerm) {
        __filtersDebugLog('[FiltersPanel] 🔍 Поиск:', searchTerm);
        this.eventBus.emit('search:changed', { searchTerm });
    }

    /**
     * Настройка обработчиков событий
     */
    _setupEventListeners() {
        // Обработчики изменения фильтров
        $(document).on('change', this.selectors.statusFilter, this.handleFilterChange);
        $(document).on('change', this.selectors.projectFilter, this.handleFilterChange);
        $(document).on('change', this.selectors.priorityFilter, this.handleFilterChange);

        // Обработчик поиска
        $(document).on('input', this.selectors.searchFilter, this.handleSearchInput);

        // Обработчики кнопок очистки
        $(document).on('click', this.selectors.clearButtons, this.handleClearFilter);

        // Обработчик глобального сброса
        $(document).on('click', '#reset-all-filters', () => {
            this.resetAllFilters();
        });

        // Слушаем события от других компонентов
        this.eventBus.on('filters:refresh', () => {
            this.loadFilters();
        });
    }

    /**
     * Обработчик изменения фильтра
     */
    handleFilterChange(event) {
        const filter = $(event.target);
        const value = filter.val();
        const filterId = filter.attr('id');

        __filtersDebugLog('[FiltersPanel] 🔄 Фильтр изменен:', filterId, '=', value);

        // Обновляем видимость кнопки очистки
        this._updateFilterVisibility(filter);

        // Показываем загрузку
        this.loadingManager.show('table', 'Применение фильтра...');

        // Уведомляем об изменении
        this.eventBus.emit('filters:changed', {
            filters: this.getCurrentFilters()
        });
    }

    /**
     * Обработчик ввода в поиск
     */
    handleSearchInput(event) {
        const searchTerm = $(event.target).val();
        __filtersDebugLog('[FiltersPanel] 🔍 Ввод поиска:', searchTerm);

        // Используем debounced поиск
        if (this.debouncedSearch) {
            this.debouncedSearch(searchTerm);
        }
    }

    /**
     * Обработчик кнопки очистки фильтра
     */
    handleClearFilter(event) {
        event.preventDefault();

        const button = $(event.target);
        const filterId = button.data('filter') || button.attr('data-filter');

        if (filterId) {
            const filterSelector = `#${filterId}`;
            const filter = $(filterSelector);

            __filtersDebugLog('[FiltersPanel] 🗑️ Очистка фильтра:', filterId);

            filter.val('');
            this._updateFilterVisibility(filter);

            // Уведомляем об изменении
            this.eventBus.emit('filters:changed', {
                filters: this.getCurrentFilters()
            });
        }
    }

    /**
     * Обновление видимости кнопки очистки для конкретного фильтра
     */
    _updateFilterVisibility(filterElement) {
        const value = filterElement.val();
        const filterId = filterElement.attr('id');
        const clearBtnId = `#clear-${filterId.replace('-filter', '')}-filter`;
        const clearBtn = $(clearBtnId);
        const container = filterElement.closest('.filter-container');

        const hasValue = value && value !== '' && value !== 'null';

        if (hasValue) {
            clearBtn.addClass('show').css('display', 'flex');
            container.addClass('has-value');
        } else {
            clearBtn.removeClass('show').css('display', 'none');
            container.removeClass('has-value');
        }

        __filtersDebugLog(`[FiltersPanel] 👁️ Видимость кнопки ${clearBtnId}:`, hasValue ? 'показана' : 'скрыта');
    }

    /**
     * Обновление всех кнопок очистки
     */
    _updateAllClearButtons() {
        $(this.selectors.statusFilter).each((_, el) => this._updateFilterVisibility($(el)));
        $(this.selectors.projectFilter).each((_, el) => this._updateFilterVisibility($(el)));
        $(this.selectors.priorityFilter).each((_, el) => this._updateFilterVisibility($(el)));
    }

    /**
     * Показать/скрыть индикатор загрузки
     */
    _showLoadingIndicator(show) {
        const indicator = $('.filters-loading-indicator');
        if (show) {
            indicator.show();
            $(this.selectors.statusFilter + ', ' + this.selectors.projectFilter + ', ' + this.selectors.priorityFilter)
                .prop('disabled', true);
        } else {
            indicator.hide();
            $(this.selectors.statusFilter + ', ' + this.selectors.projectFilter + ', ' + this.selectors.priorityFilter)
                .prop('disabled', false);
        }
    }

    /**
     * Очистка и отключение фильтров при ошибке
     */
    _clearAndDisableFilters() {
        __filtersDebugLog('[FiltersPanel] 🚫 Очистка и отключение фильтров');

        $(this.selectors.statusFilter + ', ' + this.selectors.projectFilter + ', ' + this.selectors.priorityFilter)
            .empty()
            .append('<option value="">Ошибка загрузки</option>')
            .prop('disabled', true);

        $(this.selectors.clearButtons).hide();
    }

    /**
     * Инициализация состояния фильтров
     */
    _initializeFilterState() {
        // Сбрасываем все фильтры к начальному состоянию
        this.resetAllFilters();

        // Обновляем видимость кнопок
        this._updateAllClearButtons();
    }

    /**
     * Проверка активных фильтров
     */
    hasActiveFilters() {
        const filters = this.getCurrentFilters();
        return Object.values(filters).some(value => value && value !== '');
    }

    /**
     * Получение количества активных фильтров
     */
    getActiveFiltersCount() {
        const filters = this.getCurrentFilters();
        return Object.values(filters).filter(value => value && value !== '').length;
    }

    /**
     * Получение данных фильтров
     */
    getFiltersData() {
        return this.filtersData;
    }

    /**
     * Принудительное обновление
     */
    refresh() {
        __filtersDebugLog('[FiltersPanel] 🔄 Принудительное обновление фильтров');
        this.cache.data = null; // Сбрасываем кэш
        return this.loadFilters();
    }

    /**
     * Очистка ресурсов
     */
    destroy() {
        // Удаляем обработчики событий
        $(document).off('change', this.selectors.statusFilter, this.handleFilterChange);
        $(document).off('change', this.selectors.projectFilter, this.handleFilterChange);
        $(document).off('change', this.selectors.priorityFilter, this.handleFilterChange);
        $(document).off('input', this.selectors.searchFilter, this.handleSearchInput);
        $(document).off('click', this.selectors.clearButtons, this.handleClearFilter);

        this.isInitialized = false;
        __filtersDebugLog('[FiltersPanel] 🗑️ Компонент очищен');
    }
}

// Экспорт для ES6 модулей и глобального использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FiltersPanel;
} else if (typeof window !== 'undefined') {
    window.FiltersPanel = FiltersPanel;
}

