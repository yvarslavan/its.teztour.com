/**
 * KanbanManager.js - Управление Kanban доской
 * v1.0.0
 */

const __kanbanDebugLog = (...args) => { if (window.__TASKS_DEBUG__) console.log(...args); };

class KanbanManager {
    constructor() {
        this.currentView = 'list';
        this.tasksData = [];
        this.filters = {};
        this.isLoading = false;
        this.isInitialized = false;
        this.eventListenersInitialized = false; // Флаг для предотвращения повторной инициализации обработчиков
        this.lastDragEndedAt = 0;
        this.boundHandleDragStart = this.handleDragStart.bind(this);
        this.boundHandleDragEnd = this.handleDragEnd.bind(this);
        this.boundHandleDragOver = this.handleDragOver.bind(this);
        this.boundHandleDragEnter = this.handleDragEnter.bind(this);
        this.boundHandleDragLeave = this.handleDragLeave.bind(this);
        this.boundHandleDrop = this.handleDrop.bind(this);
        this.cache = {
            tasks: null,
            statuses: null,
            statusCounts: null,
            lastUpdate: null,
            filterKey: '',
            cacheTimeout: 5 * 60 * 1000 // 5 минут
        };
        this.navigationStateKey = 'my_tasks:return_context';
        this.returnContextTtlMs = 10 * 60 * 1000;

        __kanbanDebugLog('[KanbanManager] 🚀 Конструктор Kanban менеджера');

        // Инициализируем только если DOM готов
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.init();
            });
        } else {
            this.init();
        }
    }

    adjustEmptyColumns() {
        try {
            const columns = document.querySelectorAll('.kanban-column');
            columns.forEach(col => {
                const content = col.querySelector('.kanban-column-content');
                if (!content) return;
                const cards = content.querySelectorAll('.kanban-card');
                const isEmpty = cards.length === 0;
                col.classList.toggle('kanban-column-empty', isEmpty);
                const placeholder = content.querySelector('.kanban-empty-placeholder');

                if (isEmpty) {
                    if (!placeholder) {
                        content.insertAdjacentHTML('beforeend', `
                            <div class="kanban-empty-placeholder">
                                <span class="kanban-empty-placeholder-icon">
                                    <i class="fas fa-inbox"></i>
                                </span>
                                <span class="kanban-empty-placeholder-text">Пока задач нет</span>
                            </div>
                        `);
                    }
                } else if (placeholder) {
                    placeholder.remove();
                }
            });
            __kanbanDebugLog('[KanbanManager] ✅ Пустые колонки обновлены');
        } catch (e) {
            console.warn('[KanbanManager] ⚠️ Не удалось обновить пустые колонки:', e);
        }
    }

    init() {
        __kanbanDebugLog('[KanbanManager] 🚀 Инициализация Kanban менеджера');
        try {
            // Проверяем наличие элементов
            const toggleButtons = document.querySelectorAll('.view-toggle-btn');
            const kanbanBoard = document.getElementById('kanban-board');
            const tableContainer = document.querySelector('.table-container');
            __kanbanDebugLog('[KanbanManager] 🔍 Проверка элементов:');
            __kanbanDebugLog('- Кнопки переключения:', toggleButtons.length);
            __kanbanDebugLog('- Kanban доска:', !!kanbanBoard);
            __kanbanDebugLog('- Таблица:', !!tableContainer);

            // Создаём динамические колонки
            this.createDynamicColumns().then(() => {
                this.setupEventListeners();
                this.initDragAndDrop();
                this.initTooltips();
                // При первом рендере также применяем сжатие пустых колонок
                this.adjustEmptyColumns();

                // Загружаем данные задач в Kanban
                this.loadKanbanDataOptimized().then(() => {
                    __kanbanDebugLog('[KanbanManager] 🔒 Ограничения отключены');
                    this.isInitialized = true;
                    __kanbanDebugLog('[KanbanManager] ✅ Инициализация завершена');
                    
                    // Проверяем, какой режим активен по умолчанию
                    const activeView = this.getPreferredInitialView();
                    __kanbanDebugLog('[KanbanManager] 🔍 Активный режим по умолчанию:', activeView);
                    
                    this.switchView(activeView, { skipReload: activeView === 'kanban' });
                }).catch(error => {
                    console.error('[KanbanManager] ❌ Ошибка загрузки данных Kanban:', error);
                    this.isInitialized = true;
                });
            }).catch(error => {
                console.error('[KanbanManager] ❌ Ошибка инициализации:', error);
                this.isInitialized = false;
            });
        } catch (error) {
            console.error('[KanbanManager] ❌ Критическая ошибка инициализации:', error);
            this.isInitialized = false;
        }
    }

    setupEventListeners() {
        try {
            __kanbanDebugLog('[KanbanManager] 🔧 Настройка обработчиков событий');

            // Защита от повторной инициализации обработчиков
            if (this.eventListenersInitialized) {
                __kanbanDebugLog('[KanbanManager] ⚠️ Обработчики событий уже инициализированы, пропускаем');
                return;
            }

            // Переключение между видами
            document.addEventListener('click', (e) => {
                __kanbanDebugLog('[KanbanManager] 🖱️ Клик по элементу:', e.target);

                if (e.target.closest('.view-toggle-btn')) {
                    const btn = e.target.closest('.view-toggle-btn');
                    const view = btn.dataset.view;
                    __kanbanDebugLog('[KanbanManager] 🔄 Переключение на вид:', view);
                    this.switchView(view);
                    return;
                }

                const columnHeader = e.target.closest('.kanban-column-header');
                if (columnHeader) {
                    e.preventDefault();
                    this.toggleColumnCollapse(columnHeader.closest('.kanban-column'));
                    return;
                }

                if (e.target.closest('.kanban-card-drag-handle')) {
                    return;
                }

                const taskCard = e.target.closest('.kanban-card');
                if (taskCard) {
                    if (Date.now() - this.lastDragEndedAt < 250) {
                        return;
                    }

                    const taskId = taskCard.dataset.taskId;
                    if (taskId) {
                        e.preventDefault();
                        this.openTaskDetails(taskId);
                    }
                }
            });

            document.addEventListener('keydown', (e) => {
                const isActivationKey = e.key === 'Enter' || e.key === ' ';
                if (!isActivationKey) {
                    return;
                }

                const columnHeader = e.target.closest('.kanban-column-header');
                if (columnHeader) {
                    e.preventDefault();
                    this.toggleColumnCollapse(columnHeader.closest('.kanban-column'));
                    return;
                }

                if (e.target.closest('.kanban-card-drag-handle')) {
                    return;
                }

                const taskCard = e.target.closest('.kanban-card');
                if (taskCard) {
                    e.preventDefault();
                    this.openTaskDetails(taskCard.dataset.taskId);
                }
            });

            // Обработка фильтров
            this.setupFilterListeners();

            // Устанавливаем флаг инициализации
            this.eventListenersInitialized = true;
            __kanbanDebugLog('[KanbanManager] ✅ Обработчики событий настроены');
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка настройки обработчиков событий:', error);
        }
    }

    setupFilterListeners() {
        try {
            // Слушаем изменения в фильтрах
            const filterSelects = ['status-filter', 'project-filter', 'priority-filter'];

            filterSelects.forEach(filterId => {
                const select = document.getElementById(filterId);
                if (select) {
                    select.addEventListener('change', () => {
                        this.updateFilters();
                        if (this.currentView === 'kanban') {
                            this.loadKanbanDataOptimized();
                        }
                    });
                }
            });
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка настройки фильтров:', error);
        }
    }

    updateFilters() {
        const nextFilters = {
            status: document.getElementById('status-filter')?.value || '',
            project: document.getElementById('project-filter')?.value || '',
            priority: document.getElementById('priority-filter')?.value || ''
        };
        const hasDomFilters = Boolean(nextFilters.status || nextFilters.project || nextFilters.priority);
        const returnContext = !hasDomFilters ? this.readReturnContext() : null;
        const normalizedFilters = returnContext?.view === 'kanban'
            ? {
                status: nextFilters.status || returnContext.filters?.status || '',
                project: nextFilters.project || returnContext.filters?.project || '',
                priority: nextFilters.priority || returnContext.filters?.priority || ''
            }
            : nextFilters;
        const nextFilterKey = this.buildFilterQuery(normalizedFilters).toString();

        if (this.cache.filterKey && this.cache.filterKey !== nextFilterKey) {
            this.clearCache();
        }

        this.filters = normalizedFilters;

        __kanbanDebugLog('[KanbanManager] 🔍 Фильтры обновлены:', this.filters);
    }

    buildFilterQuery(filters = this.filters) {
        const params = new URLSearchParams({
            force_load: '1',
            view: 'kanban',
            exclude_completed: '0'
        });

        if (filters.status) {
            params.set('status_id', filters.status);
        }

        if (filters.project) {
            params.set('project_id', filters.project);
        }

        if (filters.priority) {
            params.set('priority_id', filters.priority);
        }

        return params;
    }

    readReturnContext() {
        try {
            const rawValue = sessionStorage.getItem(this.navigationStateKey);
            if (!rawValue) {
                return null;
            }

            const parsed = JSON.parse(rawValue);
            if (!parsed?.timestamp) {
                return null;
            }

            if ((Date.now() - parsed.timestamp) > this.returnContextTtlMs) {
                return null;
            }

            return parsed;
        } catch (error) {
            console.warn('[KanbanManager] ⚠️ Не удалось прочитать return-context:', error);
            return null;
        }
    }

    getPreferredInitialView() {
        const returnContext = this.readReturnContext();
        if (returnContext?.view === 'kanban') {
            return 'kanban';
        }

        return document.querySelector('.view-toggle-btn.active')?.dataset.view || 'list';
    }

    switchView(view, options = {}) {
        __kanbanDebugLog(`[KanbanManager] 🔄 Переключение на вид: ${view}`);

        // Проверяем, что Kanban инициализирован
        if (!this.isInitialized) {
            console.warn('[KanbanManager] ⚠️ Kanban не инициализирован, пытаемся инициализировать...');
            this.init();
            return;
        }

        // Обновляем активную кнопку
        const allButtons = document.querySelectorAll('.view-toggle-btn');
        __kanbanDebugLog('[KanbanManager] 🔍 Найдено кнопок переключения:', allButtons.length);

        allButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        const targetButton = document.querySelector(`[data-view="${view}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
            __kanbanDebugLog('[KanbanManager] ✅ Активная кнопка обновлена');
        } else {
            console.error('[KanbanManager] ❌ Кнопка для вида не найдена:', view);
        }

        // Переключаем отображение
        this.toggleViewSections(view);

        this.currentView = view;

        // Загружаем данные для Kanban если переключились на него
        if (view === 'kanban' && !options.skipReload) {
            __kanbanDebugLog('[KanbanManager] 📊 Загружаем данные для Kanban');
            this.loadKanbanDataOptimized();

            // Показываем онбординг при первом переходе на канбан
            // this.showOnboardingIfNeeded(); // Отключено по запросу пользователя
        }
    }

    /**
     * Показывает онбординг если пользователь его еще не видел
     */
    showOnboardingIfNeeded() {
        // Проверяем, есть ли компонент онбординга
        if (typeof window.KanbanOnboarding !== 'undefined') {
            const onboarding = new window.KanbanOnboarding();
            onboarding.showIfNeeded();
        } else {
            __kanbanDebugLog('[KanbanManager] ⚠️ Компонент онбординга не найден');
        }
    }

    /**
     * Показывает баннер с подсказками после загрузки данных
     */
    showTipsBanner() {
        // Проверяем, не существует ли уже баннер
        const existingBanner = document.getElementById('kanban-tips-banner');
        if (existingBanner) {
            __kanbanDebugLog('[KanbanManager] ⚠️ Баннер подсказок уже существует, не создаем дубликат');
            return;
        }

        // Проверяем, есть ли компонент подсказок
        if (typeof window.KanbanTips !== 'undefined') {
            const tips = new window.KanbanTips();
            tips.showIfKanbanActive();
        } else {
            __kanbanDebugLog('[KanbanManager] ⚠️ Компонент подсказок не найден');
        }
    }

    /**
     * Инициализирует всплывающие подсказки
     */
    initTooltips() {
        // Проверяем настройку пользователя
        const showKanbanTips = window.showKanbanTips !== undefined ? window.showKanbanTips : true;

        if (!showKanbanTips) {
            __kanbanDebugLog('[KanbanManager] 🚫 Всплывающие подсказки отключены пользователем');
            return;
        }

        // Проверяем, есть ли компонент всплывающих подсказок
        if (typeof window.KanbanTooltips !== 'undefined') {
            const tooltips = new window.KanbanTooltips();
            tooltips.init();
            __kanbanDebugLog('[KanbanManager] ✅ Всплывающие подсказки инициализированы');
        } else {
            __kanbanDebugLog('[KanbanManager] ⚠️ Компонент всплывающих подсказок не найден');
        }
    }

    toggleViewSections(view) {
        __kanbanDebugLog(`[KanbanManager] 🔄 Переключение отображения на: ${view}`);

        const tableContainer = document.querySelector('.table-container');
        const kanbanBoard = document.getElementById('kanban-board');

        __kanbanDebugLog('[KanbanManager] 🔍 Найденные элементы:');
        __kanbanDebugLog('- Таблица:', !!tableContainer);
        __kanbanDebugLog('- Kanban:', !!kanbanBoard);

        if (view === 'list') {
            if (tableContainer) {
                tableContainer.style.display = 'block';
                __kanbanDebugLog('[KanbanManager] ✅ Таблица показана');
                
                // 🔧 ИСПРАВЛЕНИЕ: Инициализируем или перезагружаем DataTable
                setTimeout(() => {
                    if (typeof MyTasksApp !== 'undefined') {
                        __kanbanDebugLog('[KanbanManager] 🔍 Проверка состояния MyTasksApp:', {
                            isInitialized: MyTasksApp.state.isInitialized,
                            hasDataTable: !!MyTasksApp.state.dataTable
                        });
                        
                        if (!MyTasksApp.state.isInitialized) {
                            __kanbanDebugLog('[KanbanManager] 🔄 MyTasksApp не инициализирован, инициализируем...');
                            MyTasksApp.init();
                        } else if (!MyTasksApp.state.dataTable) {
                            __kanbanDebugLog('[KanbanManager] 🔄 DataTable не создан, создаем...');
                            MyTasksApp.initializeDataTable();
                        } else {
                            __kanbanDebugLog('[KanbanManager] 🔄 Перезагружаем данные DataTable...');
                            MyTasksApp.state.dataTable.ajax.reload(null, false); // false = не сбрасывать пагинацию
                        }
                    } else {
                        console.error('[KanbanManager] ❌ MyTasksApp не найден!');
                    }
                }, 100); // Небольшая задержка для корректного отображения
            }
            if (kanbanBoard) {
                kanbanBoard.style.display = 'none';
                __kanbanDebugLog('[KanbanManager] ✅ Kanban скрыт');
            }
        } else if (view === 'kanban') {
            if (tableContainer) {
                tableContainer.style.display = 'none';
                __kanbanDebugLog('[KanbanManager] ✅ Таблица скрыта');
            }
            if (kanbanBoard) {
                kanbanBoard.style.display = 'block';
                __kanbanDebugLog('[KanbanManager] ✅ Kanban показан');
            }
        }
    }

    /**
     * Оптимизированная загрузка данных для Kanban с кэшированием и индикатором загрузки
     */
    async loadKanbanDataOptimized() {
        __kanbanDebugLog('[KanbanManager] 📊 Оптимизированная загрузка данных для Kanban');
        this.updateFilters();
        const filterKey = this.buildFilterQuery().toString();

        // Проверяем кэш
        if (this.isCacheValid(filterKey)) {
            __kanbanDebugLog('[KanbanManager] 📦 Используем кэшированные данные');
            this.renderKanbanBoard(this.cache.tasks);
            return;
        }

        // Показываем индикатор загрузки
        this.showKanbanLoading();
        this.isLoading = true;

        try {
            // Используем новый endpoint для прямого SQL запроса
            const response = await fetch(`/tasks/get-my-tasks-direct-sql?${filterKey}`);

            __kanbanDebugLog('[KanbanManager] 📡 Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            __kanbanDebugLog('[KanbanManager] 📋 Полные данные ответа:', data);

            if (!data.success && data.error) {
                throw new Error(data.error);
            }

            // Извлекаем задачи из ответа
            const tasks = data.data || [];
            const statusCounts = data.status_counts || {};

            __kanbanDebugLog('[KanbanManager] ✅ Получено задач из SQL API:', tasks.length);
            __kanbanDebugLog('[KanbanManager] 📊 Информация о количестве задач по статусам:', statusCounts);

            // Сохраняем задачи в кэш
            this.cache.tasks = tasks;
            this.cache.statusCounts = statusCounts;
            this.cache.lastUpdate = Date.now();
            this.cache.filterKey = filterKey;
            this.tasksData = tasks;

            // Создаем динамические колонки на основе статусов
            await this.createDynamicColumns();

            // Отрисовываем Kanban доску с задачами
            this.renderKanbanBoard(tasks);

            // Завершенные задачи уже включены в основной запрос
            __kanbanDebugLog('[KanbanManager] ✅ Все задачи загружены в одном запросе');

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка загрузки данных:', error);
            this.showError('Ошибка загрузки данных: ' + error.message);
        } finally {
            // Скрываем индикатор загрузки
            this.hideKanbanLoading();
            this.isLoading = false;
        }
    }

    /**
     * Проверка валидности кэша
     */
    isCacheValid(expectedFilterKey = this.buildFilterQuery().toString()) {
        if (!this.cache.tasks || !this.cache.lastUpdate) {
            return false;
        }

        if ((this.cache.filterKey || '') !== expectedFilterKey) {
            return false;
        }

        const now = Date.now();
        const cacheAge = now - this.cache.lastUpdate;

        return cacheAge < this.cache.cacheTimeout;
    }

    /**
     * Очистка кэша
     */
    clearCache() {
        this.cache = {
            tasks: null,
            statuses: null,
            statusCounts: null,
            lastUpdate: null,
            filterKey: '',
            cacheTimeout: 5 * 60 * 1000
        };
        __kanbanDebugLog('[KanbanManager] 🗑️ Кэш очищен');
    }

    /**
     * Загрузка данных для Kanban (старый метод для совместимости)
     */
    async loadKanbanData() {
        return this.loadKanbanDataOptimized();
    }

    /**
     * Отрисовка Kanban доски с динамическими колонками
     */
    renderKanbanBoard(tasks) {
        __kanbanDebugLog('[KanbanManager] 🎨 Отрисовка Kanban доски с динамическими колонками');
        __kanbanDebugLog('[KanbanManager] 📊 Количество задач для отрисовки:', tasks.length);
        const allColumns = document.querySelectorAll('.kanban-column-content');
        allColumns.forEach(column => { column.innerHTML = ''; });
        __kanbanDebugLog('[KanbanManager] 📋 Начинаем распределение задач по колонкам...');

        if (window.__TASKS_DEBUG__) {
            // Подсчитываем статистику статусов только в debug-режиме.
            const statusStats = {};
            const statusIdStats = {};
            tasks.forEach(task => {
                const status = task.status_name || 'Новая';
                const statusId = task.status_id || 'unknown';
                statusStats[status] = (statusStats[status] || 0) + 1;
                statusIdStats[statusId] = (statusIdStats[statusId] || 0) + 1;
            });

            __kanbanDebugLog('[KanbanManager] 📈 Статистика статусов (названия):', statusStats);
            __kanbanDebugLog('[KanbanManager] 📈 Статистика статусов (ID):', statusIdStats);
        }

        // Распределяем задачи по колонкам на основе их статуса
        tasks.forEach((task, index) => {
            const status = task.status_name || 'Новая';
            const statusId = task.status_id || 1; // ID статуса из задачи

            // Находим колонку для этого статуса
            const columnElement = document.querySelector(`[data-status-id="${statusId}"]`);

            if (columnElement) {
                // Создаем карточку задачи
                this.createTaskCard(task, columnElement);
            } else {
                console.warn(`[KanbanManager] ⚠️ Колонка для статуса "${status}" (ID: ${statusId}) не найдена`);

                const allColumns = document.querySelectorAll('.kanban-column-content');

                if (window.__TASKS_DEBUG__) {
                    __kanbanDebugLog('[KanbanManager] 🔍 Доступные колонки:');
                    allColumns.forEach(col => {
                        const debugStatusId = col.getAttribute('data-status-id');
                        const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                        __kanbanDebugLog(`  - ID: ${debugStatusId}, Название: ${columnTitle}`);
                    });
                }

                // Попробуем найти колонку по названию статуса
                const columnByTitle = Array.from(allColumns).find(col => {
                    const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                    return columnTitle && columnTitle.includes(status);
                });

                if (columnByTitle) {
                    this.createTaskCard(task, columnByTitle);
                } else {
                    console.error(`[KanbanManager] ❌ Колонка для статуса "${status}" не найдена ни по ID, ни по названию`);

                    // Fallback: добавляем в первую доступную колонку
                    const firstColumn = allColumns[0];
                    if (firstColumn) {
                        this.createTaskCard(task, firstColumn);
                    }
                }
            }
        });

        __kanbanDebugLog('[KanbanManager] ✅ Kanban доска обновлена');

        // Обновляем индикаторы количества задач
        this.updateTaskCountIndicators();

        if (window.__TASKS_DEBUG__) {
            this.validateAndFixColumnStatusMapping();
            this.fixStatusMismatches();
            this.monitorNewStatuses();
            this.testStatusMapping();
        }

        // Обновляем статистики
        this.updateKanbanStats(tasks);

        // Инициализируем Drag & Drop для новых карточек
        this.initDragAndDrop();

        // Показываем баннер с подсказками
        this.showTipsBanner();

        // Применяем сжатие пустых колонок после полного рендера
        this.adjustEmptyColumns();

        __kanbanDebugLog('[KanbanManager] ✅ Состояние Kanban обновлено');
    }

    /**
     * Обновление индикаторов количества задач
     */
    updateTaskCountIndicators() {
        __kanbanDebugLog('[KanbanManager] 📊 Обновление индикаторов количества задач...');

        const statusCounts = this.cache.statusCounts || {};

        // Обновляем индикаторы для каждой колонки
        Object.keys(statusCounts).forEach(statusId => {
            const countInfo = statusCounts[statusId];
            const columnElement = document.querySelector(`[data-status-id="${statusId}"]`);

            if (columnElement) {
                const columnHeader = columnElement.closest('.kanban-column')?.querySelector('.kanban-column-header');
                const countElement = columnHeader?.querySelector('.kanban-column-count');

                if (countElement) {
                    const shown = countInfo.shown || 0;
                    const total = countInfo.total || 0;
                    this.setCountChipState(countElement, shown, total);
                }
            }
        });

        this.updatePhaseSummaries();
        __kanbanDebugLog('[KanbanManager] ✅ Индикаторы количества задач обновлены');
    }

    /**
     * Обновление счетчика конкретной колонки
     */
    updateColumnCount(columnElement) {
        if (!columnElement) return;

        // Карточки имеют класс .kanban-card
        const taskCards = columnElement.querySelectorAll('.kanban-card');
        const count = taskCards.length;

        // Находим элемент счетчика в заголовке колонки
        const columnHeader = columnElement.closest('.kanban-column')?.querySelector('.kanban-column-header');
        const countElement = columnHeader?.querySelector('.kanban-column-count');

        if (countElement) {
            // Проверяем, есть ли информация о статусе в кэше
            const statusId = columnElement.getAttribute('data-status-id');
            const statusCounts = this.cache.statusCounts || {};
            const countInfo = statusCounts[statusId];
            const shown = countInfo?.shown ?? count;
            const total = countInfo?.total ?? shown;
            this.setCountChipState(countElement, shown, total);

            __kanbanDebugLog(`[KanbanManager] 📊 Обновлен счетчик колонки: ${count} задач`);
        }
        // При каждом обновлении счетчика пересчитываем пустые колонки
        this.adjustEmptyColumns();
        this.updatePhaseSummaries();
    }

    setCountChipState(countElement, shown, total) {
        if (!countElement) return;

        const isPartial = total > shown;
        countElement.classList.toggle('is-partial', isPartial);

        if (isPartial) {
            countElement.innerHTML = `
                <span class="kanban-column-count-primary">${shown}</span>
                <span class="kanban-column-count-secondary">из ${total}</span>
            `;
            countElement.title = `Показано ${shown} из ${total} задач`;
        } else {
            countElement.innerHTML = `
                <span class="kanban-column-count-primary">${shown}</span>
            `;
            countElement.title = `${shown} задач`;
        }
    }

    updatePhaseSummaries() {
        const phases = document.querySelectorAll('.kanban-phase');
        phases.forEach(phase => {
            const phaseKey = phase.getAttribute('data-phase');
            const phaseCount = phase.querySelector(`#phase-count-${phaseKey}`);
            if (!phaseCount) return;

            const cards = phase.querySelectorAll('.kanban-card').length;
            phaseCount.textContent = cards.toString();
            phaseCount.title = `${cards} задач в группе`;
        });
    }

        /**
     * Ограничение количества задач в колонке "Закрыта" - УБРАНО
     */
    limitClosedTasks() {
        __kanbanDebugLog('[KanbanManager] 🔒 Ограничение задач в закрытых колонках - ОТКЛЮЧЕНО');

        // Убираем все индикаторы ограничений
        const limitedIndicators = document.querySelectorAll('.kanban-column-limited-indicator');
        limitedIndicators.forEach(indicator => indicator.remove());

        // Убираем кнопки "Показать еще"
        const showMoreBtns = document.querySelectorAll('.kanban-show-more-btn');
        showMoreBtns.forEach(btn => btn.remove());

        // Убираем класс ограничения с колонок
        const limitedColumns = document.querySelectorAll('.kanban-column-limited');
        limitedColumns.forEach(col => col.classList.remove('kanban-column-limited'));

        // Обновляем счетчики колонок без ограничений
        const allColumns = document.querySelectorAll('.kanban-column-content');
        allColumns.forEach(col => {
            const cards = col.querySelectorAll('.kanban-card');
            const countElement = col.parentElement.querySelector('.kanban-column-count');
            if (countElement) {
                const statusId = col.getAttribute('data-status-id');
                const total = this.cache.statusCounts?.[statusId]?.total ?? cards.length;
                this.setCountChipState(countElement, cards.length, total);
            }
        });

        __kanbanDebugLog('[KanbanManager] ✅ Все ограничения для закрытых колонок убраны');
    }

    /**
     * Создание карточки задачи
     */
    createTaskCard(task, columnElement) {
        __kanbanDebugLog(`[KanbanManager] 🎴 Создание карточки для задачи ${task.id}:`, task);

        // Проверяем, не существует ли уже карточка для этой задачи
        const existingCard = document.querySelector(`[data-task-id="${task.id}"]`);
        if (existingCard) {
            __kanbanDebugLog(`[KanbanManager] ⚠️ Карточка для задачи ${task.id} уже существует, пропускаем создание`);
            return;
        }

        // Убираем ограничение для колонки "Закрыто" (ID: 5)
        const statusId = task.status_id;
        // Ограничение убрано - показываем все задачи

        // Анализируем приоритет
        const priority = task.priority_name || 'Обычный';
        const priorityClass = this.getPriorityClass(priority, task.priority_position);

        if (!priority || priority === 'undefined') {
            __kanbanDebugLog(`[KanbanManager] ⚠️ Неизвестный приоритет "${priority}" -> priority-normal (по умолчанию)`);
        }

        const projectName = this.resolveTaskSource(task);
        const statusKey = this.getStatusKey(task.status_name || '');
        const phaseKey = this.getStatusPhase({
            name: task.status_name || '',
            is_closed: !!task.status_is_closed
        });
        const updatedLabel = this.formatDate(task.updated_on) || 'нет данных';
        const placeholder = columnElement.querySelector('.kanban-empty-placeholder');
        if (placeholder) {
            placeholder.remove();
        }

        const cardHtml = `
            <div class="kanban-card" data-task-id="${task.id}" data-priority="${priorityClass}" data-status-key="${statusKey}" data-phase="${phaseKey}" data-updated-on="${task.updated_on || ''}" tabindex="0" role="link" aria-label="Открыть задачу #${task.id}">
                <div class="kanban-card-header">
                    <div class="kanban-card-meta">
                        <span class="kanban-card-id">#${task.id}</span>
                    </div>
                    <div class="kanban-card-actions">
                        <span class="priority-badge ${priorityClass}">${this.escapeHtml(priority)}</span>
                        <button type="button" class="kanban-card-drag-handle" aria-label="Перетащить задачу #${task.id}" title="Перетащить задачу">
                            <i class="fas fa-grip-lines"></i>
                        </button>
                    </div>
                </div>
                <div class="kanban-card-content">
                    <div class="kanban-card-subject" title="${this.escapeHtml(task.subject || 'Без названия')}">${this.escapeHtml(task.subject || 'Без названия')}</div>
                    <div class="kanban-card-project" title="${this.escapeHtml(projectName)}">${this.escapeHtml(projectName)}</div>
                </div>
                <div class="kanban-card-footer">
                    <span class="kanban-card-date-label">Обновлена</span>
                    <span class="kanban-card-date">${updatedLabel}</span>
                </div>
            </div>
        `;

        // Добавляем карточку в колонку
        columnElement.insertAdjacentHTML('beforeend', cardHtml);
    }

    resolveTaskSource(task) {
        return task.project_name || task.easy_email_to || 'Без проекта';
    }

    // Утилитарные методы
    getPriorityClass(priority, priorityPosition) {
        // Определяем класс по позиции приоритета (enumerations.position), без текстовых сравнений
        if (typeof priorityPosition === 'number') {
            if (priorityPosition >= 7) return 'priority-high';
            if (priorityPosition <= 3) return 'priority-low';
            return 'priority-normal';
        }
        return 'priority-normal';
    }

    toggleColumnCollapse(column) {
        if (!column) return;

        column.classList.toggle('collapsed');
        const isExpanded = !column.classList.contains('collapsed');
        const header = column.querySelector('.kanban-column-header');

        if (header) {
            header.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
        }
    }

    openTaskDetails(taskId) {
        __kanbanDebugLog('[KanbanManager] 🔗 Открытие деталей задачи:', taskId);

        if (!taskId) {
            return;
        }

        if (typeof MyTasksApp !== 'undefined' && typeof MyTasksApp.persistReturnContext === 'function') {
            MyTasksApp.persistReturnContext(taskId);
        } else {
            const currentView = document.querySelector('.view-toggle-btn.active')?.dataset.view || 'list';
            sessionStorage.setItem('return_from_task_view', currentView);
        }

        window.open(`/tasks/my-tasks/${taskId}`, '_blank', 'noopener');
    }

    showKanbanLoading() {
        const kanbanBoard = document.getElementById('kanban-board');
        if (kanbanBoard) {
            // Удаляем существующий индикатор загрузки
            const existingLoading = kanbanBoard.querySelector('.kanban-loading');
            if (existingLoading) {
                existingLoading.remove();
            }

            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'kanban-loading';
            loadingDiv.innerHTML = `
                <div class="loading-content">
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <div class="loading-text">
                        <h3>Загрузка Kanban доски</h3>
                        <p>Загрузка карточек на Kanban-доску...</p>
                    </div>
                    <div class="loading-progress">
                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>
                    </div>
                </div>
            `;
            kanbanBoard.appendChild(loadingDiv);

            // Анимация прогресс-бара
            const progressFill = loadingDiv.querySelector('.progress-fill');
            if (progressFill) {
                let progress = 0;
                const interval = setInterval(() => {
                    progress += Math.random() * 15;
                    if (progress > 90) progress = 90;
                    progressFill.style.width = progress + '%';
                }, 200);

                // Останавливаем анимацию через 5 секунд
                setTimeout(() => {
                    clearInterval(interval);
                }, 5000);
            }
        }
    }

    hideKanbanLoading() {
        const loadingDiv = document.querySelector('.kanban-loading');
        if (loadingDiv) {
            // Плавно скрываем индикатор загрузки
            loadingDiv.style.opacity = '0';
            loadingDiv.style.transform = 'scale(0.95)';

            setTimeout(() => {
                loadingDiv.remove();
            }, 300);
        }
    }

    /**
     * Показать ошибку Kanban
     */
    showKanbanError(message) {
        try {
            const kanbanBoard = document.getElementById('kanban-board');
            if (kanbanBoard) {
                // Удаляем существующий индикатор ошибки
                const existingError = kanbanBoard.querySelector('.kanban-error');
                if (existingError) {
                    existingError.remove();
                }

                const errorDiv = document.createElement('div');
                errorDiv.className = 'kanban-error';
                errorDiv.innerHTML = `
                    <div class="error-content">
                        <div class="error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="error-text">
                            <h3>Ошибка загрузки</h3>
                            <p>${this.escapeHtml(message)}</p>
                        </div>
                        <div class="error-actions">
                            <button onclick="window.kanbanManager.forceRefresh()" class="btn btn-primary">
                                <i class="fas fa-redo"></i> Попробовать снова
                            </button>
                            <button onclick="window.kanbanManager.hideKanbanError()" class="btn btn-secondary">
                                <i class="fas fa-times"></i> Закрыть
                            </button>
                        </div>
                    </div>
                `;

                kanbanBoard.appendChild(errorDiv);
            }
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка показа ошибки Kanban:', error);
            console.error('[KanbanManager] 📢 KANBAN ERROR:', message);
        }
    }

    /**
     * Скрыть ошибку Kanban
     */
    hideKanbanError() {
        try {
            const kanbanBoard = document.getElementById('kanban-board');
            if (kanbanBoard) {
                const errorDiv = kanbanBoard.querySelector('.kanban-error');
                if (errorDiv) {
                    errorDiv.remove();
                }
            }
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка скрытия ошибки Kanban:', error);
        }
    }

    /**
     * Экранирование HTML для безопасности
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Форматирование даты
     */
    formatDate(dateString) {
        if (!dateString) return '';

        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return '';

            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        } catch (error) {
            return '';
        }
    }

    /**
     * Показать ошибку
     */
    showError(message) {
        try {
            this.showErrorMessage(message);
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка показа ошибки:', error);
            console.error('[KanbanManager] 📢 ERROR:', message);
        }
    }

    /**
     * Обновление счетчиков колонок
     */
    updateColumnCounts(distribution) {
        __kanbanDebugLog('[KanbanManager] 🔢 Обновление счетчиков колонок:', distribution);

        Object.entries(distribution).forEach(([columnId, count]) => {
            const countElement = document.getElementById(columnId);
            if (countElement) {
                countElement.textContent = count;
                __kanbanDebugLog(`[KanbanManager] ✅ Счетчик ${columnId}: ${count}`);
            } else {
                console.error(`[KanbanManager] ❌ Элемент счетчика ${columnId} не найден`);
            }
        });

        // Обновляем общий счетчик
        const totalCount = Object.values(distribution).reduce((sum, count) => sum + count, 0);
        const totalElement = document.getElementById('kanban-total-count');
        if (totalElement) {
            totalElement.textContent = totalCount;
            __kanbanDebugLog(`[KanbanManager] ✅ Общий счетчик: ${totalCount}`);
        }
    }

            /**
     * Сортирует статусы в нужном порядке для отображения
     */
    sortStatusesByOrder(statuses) {
        // Сортируем статусы по полю position из базы данных
        const sortedStatuses = [...statuses].sort((a, b) => {
            // Если у статуса есть position, используем его для сортировки
            if (a.position !== undefined && b.position !== undefined) {
                return a.position - b.position;
            }
            // Если position нет, сортируем по ID
            return a.id - b.id;
        });

        __kanbanDebugLog('[KanbanManager] 📋 Статусы отсортированы по position:', sortedStatuses.map(s => `${s.name} (pos: ${s.position || 'N/A'})`));

        return sortedStatuses;
    }

    getPhaseMeta() {
        return {
            active: {
                key: 'active',
                eyebrow: 'Основной поток',
                title: 'Активные статусы',
                description: 'Новые, открытые и рабочие этапы выполнения.'
            },
            exceptions: {
                key: 'exceptions',
                eyebrow: 'Требует внимания',
                title: 'Исключения и паузы',
                description: 'Уточнения, паузы и нестандартные маршруты.'
            },
            terminal: {
                key: 'terminal',
                eyebrow: 'Финализация',
                title: 'Терминальные статусы',
                description: 'Задачи, которые завершены или закрыты для потока.'
            }
        };
    }

    getStatusPhase(status) {
        const normalizedName = (status?.name || '').toLowerCase();

        if (/(уточ|приост|заморож|перенаправ)/.test(normalizedName)) {
            return 'exceptions';
        }

        if (status?.is_closed || /(выполн|закрыт|отклон)/.test(normalizedName)) {
            return 'terminal';
        }

        return 'active';
    }

    groupStatusesByPhase(statuses) {
        const phaseMeta = this.getPhaseMeta();
        const grouped = {
            active: [],
            exceptions: [],
            terminal: []
        };

        statuses.forEach(status => {
            const phaseKey = this.getStatusPhase(status);
            grouped[phaseKey].push(status);
        });

        return Object.keys(phaseMeta)
            .map(key => ({ ...phaseMeta[key], statuses: grouped[key] }))
            .filter(phase => phase.statuses.length > 0);
    }

    getStatusKey(statusName) {
        const normalizedName = (statusName || '').toLowerCase();

        if (normalizedName.includes('нов')) return 'new';
        if (normalizedName.includes('откры')) return 'open';
        if (normalizedName.includes('очеред')) return 'queue';
        if (normalizedName.includes('соглас')) return 'approval';
        if (normalizedName.includes('работ')) return 'progress';
        if (normalizedName.includes('уточ')) return 'clarification';
        if (normalizedName.includes('приост')) return 'paused';
        if (normalizedName.includes('заморож')) return 'frozen';
        if (normalizedName.includes('тестир')) return 'testing';
        if (normalizedName.includes('протест')) return 'tested';
        if (normalizedName.includes('перенаправ')) return 'redirected';
        if (normalizedName.includes('выполн')) return 'done';
        if (normalizedName.includes('закры')) return 'closed';
        if (normalizedName.includes('отклон')) return 'rejected';

        return 'generic';
    }

    buildKanbanPhaseMarkup(phase) {
        const columnsMarkup = phase.statuses
            .map(status => this.buildKanbanColumnMarkup(status, phase.key))
            .join('');

        return `
            <section class="kanban-phase kanban-phase-${phase.key}" data-phase="${phase.key}">
                <div class="kanban-phase-header">
                    <div class="kanban-phase-copy">
                        <span class="kanban-phase-eyebrow">${phase.eyebrow}</span>
                        <div class="kanban-phase-title-row">
                            <h3 class="kanban-phase-title">${phase.title}</h3>
                            <span class="kanban-phase-count" id="phase-count-${phase.key}">0</span>
                        </div>
                        <p class="kanban-phase-description">${phase.description}</p>
                    </div>
                </div>
                <div class="kanban-phase-columns">
                    ${columnsMarkup}
                </div>
            </section>
        `;
    }

    buildKanbanColumnMarkup(status, phaseKey) {
        const statusKey = this.getStatusKey(status.name);

        return `
            <div class="kanban-column" id="kanban-column-${status.id}" data-phase="${phaseKey}" data-status-key="${statusKey}" data-status-closed="${status.is_closed ? 'true' : 'false'}">
                <div class="kanban-column-header" role="button" tabindex="0" aria-expanded="true">
                    <div class="kanban-column-title-group">
                        <span class="kanban-column-status-dot" aria-hidden="true"></span>
                        <span class="kanban-column-title">${this.escapeHtml(status.name)}</span>
                    </div>
                    <div class="kanban-column-meta">
                        <div class="kanban-column-count" id="count-${status.id}" title="0 задач">
                            <span class="kanban-column-count-primary">0</span>
                        </div>
                        <span class="kanban-column-toggle" aria-hidden="true">
                            <i class="fas fa-chevron-down"></i>
                        </span>
                    </div>
                </div>
                <div class="kanban-column-content" data-status-id="${status.id}" data-status-name="${this.escapeHtml(status.name)}" data-status-key="${statusKey}">
                    <div class="kanban-empty-placeholder">
                        <span class="kanban-empty-placeholder-icon">
                            <i class="fas fa-inbox"></i>
                        </span>
                        <span class="kanban-empty-placeholder-text">Пока задач нет</span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Динамическое создание колонок на основе статусов Redmine с оптимизацией
     */
    async createDynamicColumns() {
        __kanbanDebugLog('[KanbanManager] 🏗️ Создание динамических колонок');

        try {
            // Загружаем статусы с оптимизацией
            const statuses = await this.loadStatusesOptimized();

            // Сортируем статусы в нужном порядке
            const sortedStatuses = this.sortStatusesByOrder(statuses);

            // Создаём колонки для каждого статуса
            const kanbanColumns = document.getElementById('kanban-columns');
            if (!kanbanColumns) {
                throw new Error('Контейнер колонок Kanban не найден');
            }

            // Очищаем существующие колонки
            kanbanColumns.innerHTML = '';
            const phases = this.groupStatusesByPhase(sortedStatuses);
            kanbanColumns.innerHTML = phases.map(phase => this.buildKanbanPhaseMarkup(phase)).join('');

            __kanbanDebugLog('[KanbanManager] ✅ Динамические колонки созданы в нужном порядке');
            this.adjustEmptyColumns();

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка создания колонок:', error);
            __kanbanDebugLog('[KanbanManager] 🔄 Создаем fallback колонки...');
            this.createFallbackColumns();
        }
    }

    /**
     * Создание fallback колонок при ошибке API
     */
    createFallbackColumns() {
        try {
            __kanbanDebugLog('[KanbanManager] 🔄 Создание fallback колонок...');

            // Используем базовые статусы в случае ошибки API
            const fallbackStatuses = [
                {id: 1, name: 'Новая', position: 1, is_closed: false},
                {id: 17, name: 'Открыта', position: 2, is_closed: false},
                {id: 19, name: 'В очереди', position: 3, is_closed: false},
                {id: 15, name: 'На согласовании', position: 4, is_closed: false},
                {id: 2, name: 'В работе', position: 5, is_closed: false},
                {id: 9, name: 'Запрошено уточнение', position: 6, is_closed: false},
                {id: 10, name: 'Приостановлена', position: 7, is_closed: false},
                {id: 16, name: 'Заморожена', position: 8, is_closed: false},
                {id: 18, name: 'На тестировании', position: 9, is_closed: false},
                {id: 13, name: 'Протестирована', position: 10, is_closed: false},
                {id: 14, name: 'Перенаправлена', position: 11, is_closed: true},
                {id: 7, name: 'Выполнена', position: 12, is_closed: false},
                {id: 6, name: 'Отклонена', position: 13, is_closed: true},
                {id: 5, name: 'Закрыта', position: 14, is_closed: true}
            ];

            const kanbanColumns = document.getElementById('kanban-columns');
            if (!kanbanColumns) {
                throw new Error('Контейнер колонок не найден');
            }

            // Очищаем существующие колонки
            kanbanColumns.innerHTML = '';
            const phases = this.groupStatusesByPhase(fallbackStatuses);
            kanbanColumns.innerHTML = phases.map(phase => this.buildKanbanPhaseMarkup(phase)).join('');

            __kanbanDebugLog('[KanbanManager] ✅ Fallback колонки созданы в нужном порядке');
            this.adjustEmptyColumns();
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка создания fallback колонок:', error);
        }
    }

            /**
     * Получение цвета для статуса
     */
    getStatusColor(statusName) {
        const statusColors = {
            // Начальные статусы - синие оттенки (новые, только поступившие)
            'Новая': '#2563eb',           // Чисто синий - новая задача
            'Открыта': '#3b82f6',         // Светло-синий - открыта для работы

            // Ожидание - серые оттенки
            'В очереди': '#95a5a6',       // Серый - ждет своей очереди

            // Активная работа - зеленые оттенки (процесс)
            'В работе': '#27ae60',        // Зеленый - активно выполняется

            // Согласование/проверка - оранжевые оттенки (требует внимания)
            'На согласовании': '#f39c12', // Оранжевый - на согласовании
            'На тестировании': '#e67e22', // Темно-оранжевый - тестируется

            // Требует действий - красно-оранжевые оттенки
            'Запрошено уточнение': '#e74c3c', // Красный - требует уточнения

            // Приостановлена/заморожена - темные оттенки
            'Приостановлена': '#34495e',  // Темно-серый - приостановлена
            'Заморожена': '#2c3e50',      // Очень темно-серый - заморожена

            // Завершенные тесты - фиолетовые оттенки
            'Протестирована': '#9b59b6',  // Фиолетовый - прошла тестирование

            // Перенаправления - желто-оранжевые
            'Перенаправлена': '#f1c40f',  // Желтый - перенаправлена

            // Успешно завершенные - зеленые оттенки
            'Выполнена': '#2ecc71',       // Ярко-зеленый - выполнена
            'Закрыта': '#27ae60',         // Темно-зеленый - закрыта

            // Отклоненные - серые оттенки
            'Отклонена': '#7f8c8d'        // Серый - отклонена
        };

        // Если статус не найден, генерируем цвет на основе названия
        if (!statusColors[statusName]) {
            __kanbanDebugLog(`[KanbanManager] 🎨 Новый статус "${statusName}" - генерируем цвет`);

            // Простая хеш-функция для генерации цвета
            let hash = 0;
            for (let i = 0; i < statusName.length; i++) {
                hash = statusName.charCodeAt(i) + ((hash << 5) - hash);
            }

            // Генерируем цвет на основе хеша
            const hue = Math.abs(hash) % 360;
            const saturation = 70 + (Math.abs(hash) % 30); // 70-100%
            const lightness = 45 + (Math.abs(hash) % 20); // 45-65%

            const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
            __kanbanDebugLog(`[KanbanManager] 🎨 Сгенерирован цвет для "${statusName}": ${color}`);

            return color;
        }

        return statusColors[statusName];
    }

        /**
     * Проверка, является ли статус закрытым
     */
    isStatusClosed(statusName) {
        // Используем флаг из данных задачи, если он есть
        try {
            // При вызовах ниже мы передаём только name, поэтому проверяем в кэше
            return false; // безопасный фолбэк; реальные проверки ниже используют task.status_is_closed
        } catch (e) {
            return false;
        }
    }

        /**
     * Обновление данных задачи в локальном кэше
     */
    updateTaskInCache(taskId, newStatusId, newStatusName) {
        __kanbanDebugLog(`[KanbanManager] 🔄 Обновление кэша для задачи #${taskId}: статус ${newStatusId} (${newStatusName})`);

        // Находим задачу в локальном кэше и обновляем её статус
        const taskIndex = this.tasksData.findIndex(task => task.id == taskId);
        if (taskIndex !== -1) {
            this.tasksData[taskIndex].status_id = parseInt(newStatusId);
            this.tasksData[taskIndex].status_name = newStatusName;
            __kanbanDebugLog(`[KanbanManager] ✅ Задача #${taskId} обновлена в кэше`);
        } else {
            console.warn(`[KanbanManager] ⚠️ Задача #${taskId} не найдена в кэше для обновления`);
        }
    }

    /**
     * Проверка и исправление несоответствий между колонками и статусами
     */
    validateAndFixColumnStatusMapping() {
        __kanbanDebugLog('[KanbanManager] 🔍 Проверка соответствия колонок и статусов...');

        // Правильные соответствия статусов из таблицы u_statuses
        const correctStatusMapping = {
            // Маппинг английских названий статусов из Redmine API на русские названия
            'Closed': 'Закрыта',
            'New': 'Новая',
            'In Progress': 'В работе',
            'Rejected': 'Отклонена',
            'Executed': 'Выполнена',
            'The request specification': 'Запрошено уточнение',
            'Paused': 'Приостановлена',
            'Tested': 'Протестирована',
            'Redirected': 'Перенаправлена',
            'On the coordination': 'На согласовании',
            'Frozen': 'Заморожена',
            'Open': 'Открыта',
            'On testing': 'На тестировании',
            'In queue': 'В очереди'
        };

        const allColumns = document.querySelectorAll('.kanban-column-content');
        const columnStatusMap = {};

        // Собираем информацию о колонках
        allColumns.forEach(col => {
            const statusId = col.getAttribute('data-status-id');
            const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            if (statusId && columnTitle) {
                columnStatusMap[statusId] = columnTitle;
            }
        });

        __kanbanDebugLog('[KanbanManager] 📋 Карта колонок:', columnStatusMap);

        // Проверяем соответствие колонок правильным статусам
        Object.keys(columnStatusMap).forEach(statusId => {
            const columnTitle = columnStatusMap[statusId];
            const correctStatusName = correctStatusMapping[statusId];

            if (correctStatusName && !columnTitle.includes(correctStatusName)) {
                console.warn(`[KanbanManager] ⚠️ Несоответствие колонки: ID ${statusId} должен быть "${correctStatusName}", но колонка называется "${columnTitle}"`);
            }
        });

        // Проверяем задачи в кэше
        if (this.tasksData && this.tasksData.length > 0) {
            __kanbanDebugLog('[KanbanManager] 📋 Проверка задач в кэше...');
            this.tasksData.forEach(task => {
                const taskStatusId = task.status_id;
                const taskStatusName = task.status_name;
                const expectedColumnTitle = columnStatusMap[taskStatusId];
                const correctStatusName = correctStatusMapping[taskStatusId];

                if (expectedColumnTitle && !expectedColumnTitle.includes(taskStatusName)) {
                    console.warn(`[KanbanManager] ⚠️ Несоответствие: задача ${task.id} имеет статус "${taskStatusName}" (ID: ${taskStatusId}), но колонка называется "${expectedColumnTitle}"`);
                }

                if (correctStatusName && taskStatusName !== correctStatusName) {
                    console.warn(`[KanbanManager] ⚠️ Неправильное название статуса: задача ${task.id} имеет статус "${taskStatusName}" (ID: ${taskStatusId}), должно быть "${correctStatusName}"`);
                }
            });
        }

        return columnStatusMap;
    }

    /**
     * Мониторинг новых статусов
     */
    monitorNewStatuses() {
        __kanbanDebugLog('[KanbanManager] 🔍 Мониторинг новых статусов...');

        if (!this.tasksData || this.tasksData.length === 0) {
            return;
        }

        // Собираем все уникальные статусы из задач
        const statusSet = new Set();
        this.tasksData.forEach(task => {
            if (task.status_name) {
                statusSet.add(`${task.status_id}: ${task.status_name}`);
            }
        });

        // Проверяем, есть ли новые статусы
        const knownStatuses = new Set([
            '1: Новая',
            '2: В работе',
            '5: Закрыта',
            '6: Отклонена',
            '7: Выполнена',
            '9: Запрошено уточнение',
            '10: Приостановлена',
            '13: Протестирована',
            '14: Перенаправлена',
            '15: На согласовании',
            '16: Заморожена',
            '17: Открыта',
            '18: На тестировании',
            '19: В очереди'
        ]);

        const newStatuses = [];
        statusSet.forEach(status => {
            if (!knownStatuses.has(status)) {
                newStatuses.push(status);
            }
        });

        if (newStatuses.length > 0) {
            console.warn('[KanbanManager] 🆕 Обнаружены новые статусы:', newStatuses);
            console.warn('[KanbanManager] 💡 Рекомендуется обновить fallback колонки и цветовую схему');

            // Показываем уведомление пользователю
            this.showNotification(`Обнаружены новые статусы: ${newStatuses.join(', ')}`, 'info');
        } else {
            __kanbanDebugLog('[KanbanManager] ✅ Все статусы известны');
        }
    }

    /**
     * Принудительное исправление несоответствий статусов
     */
    fixStatusMismatches() {
        __kanbanDebugLog('[KanbanManager] 🔧 Исправление несоответствий статусов...');

        // Правильные соответствия статусов из таблицы u_statuses
        // Примечание: новые статусы будут автоматически подхватываться из API
        const correctStatusMapping = {
            // Маппинг английских названий статусов из Redmine API на русские названия
            'Closed': 'Закрыта',
            'New': 'Новая',
            'In Progress': 'В работе',
            'Rejected': 'Отклонена',
            'Executed': 'Выполнена',
            'The request specification': 'Запрошено уточнение',
            'Paused': 'Приостановлена',
            'Tested': 'Протестирована',
            'Redirected': 'Перенаправлена',
            'On the coordination': 'На согласовании',
            'Frozen': 'Заморожена',
            'Open': 'Открыта',
            'On testing': 'На тестировании',
            'In queue': 'В очереди'
        };

        // Проверяем, есть ли новые статусы в кэше, которых нет в mapping
        if (this.tasksData && this.tasksData.length > 0) {
            const newStatuses = new Set();
            this.tasksData.forEach(task => {
                if (!correctStatusMapping[task.status_id]) {
                    newStatuses.add(`${task.status_id}: ${task.status_name}`);
                }
            });

            if (newStatuses.size > 0) {
                console.warn('[KanbanManager] ⚠️ Обнаружены новые статусы:', Array.from(newStatuses));
                console.warn('[KanbanManager] ⚠️ Рекомендуется обновить correctStatusMapping');
            }
        }

        // Исправляем задачи в кэше
        if (this.tasksData && this.tasksData.length > 0) {
            let fixedCount = 0;
            this.tasksData.forEach(task => {
                const taskStatusId = task.status_id;
                const correctStatusName = correctStatusMapping[taskStatusId];

                if (correctStatusName && task.status_name !== correctStatusName) {
                    __kanbanDebugLog(`[KanbanManager] 🔧 Исправление статуса задачи ${task.id}: "${task.status_name}" -> "${correctStatusName}"`);
                    task.status_name = correctStatusName;
                    fixedCount++;
                }
            });

            if (fixedCount > 0) {
                __kanbanDebugLog(`[KanbanManager] ✅ Исправлено ${fixedCount} несоответствий статусов`);
                // Перерисовываем доску с исправленными данными
                this.renderKanbanBoard(this.tasksData);
            }
        }
    }

    /**
     * Обновление статистик Kanban доски
     */
    updateKanbanStats(tasks) {
        __kanbanDebugLog('[KanbanManager] 📊 Обновление статистик Kanban');

        // Подсчитываем активные задачи (не закрытые)
        const activeTasks = tasks.filter(task => !task.status_is_closed);

        // Подсчитываем задачи, завершенные сегодня
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const completedToday = tasks.filter(task => {
            if (!task.status_is_closed) return false;
            const updatedDate = new Date(task.updated_on);
            const updatedStr = updatedDate.toISOString().split('T')[0];
            return updatedStr === todayStr;
        });

        // Подсчитываем просроченные задачи (с due_date в прошлом)
        const overdueTasks = tasks.filter(task => {
            if (!task.due_date) return false;
            const dueDate = new Date(task.due_date);
            const now = new Date();
            return dueDate < now && !task.status_is_closed;
        });

        // Обновляем элементы статистики
        const activeCountElement = document.getElementById('kanban-active-count');
        const completedTodayElement = document.getElementById('kanban-completed-today');
        const overdueCountElement = document.getElementById('kanban-overdue-count');

        if (activeCountElement) {
            activeCountElement.textContent = activeTasks.length;
        }
        if (completedTodayElement) {
            completedTodayElement.textContent = completedToday.length;
        }
        if (overdueCountElement) {
            overdueCountElement.textContent = overdueTasks.length;
        }

        __kanbanDebugLog('[KanbanManager] ✅ Статистики обновлены:', {
            active: activeTasks.length,
            completedToday: completedToday.length,
            overdue: overdueTasks.length
        });
    }

    /**
     * Тестовая функция для проверки соответствия статусов
     */
    testStatusMapping() {
        __kanbanDebugLog('[KanbanManager] 🧪 Тестирование соответствия статусов...');

        // Проверяем все колонки
        const allColumns = document.querySelectorAll('.kanban-column-content');
        __kanbanDebugLog('[KanbanManager] 📋 Все колонки:');
        allColumns.forEach((col, index) => {
            const statusId = col.getAttribute('data-status-id');
            const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            __kanbanDebugLog(`  ${index + 1}. ID: ${statusId}, Название: "${columnTitle}"`);
        });

        // Проверяем задачи в кэше
        if (this.tasksData && this.tasksData.length > 0) {
            __kanbanDebugLog('[KanbanManager] 📋 Задачи в кэше:');
            this.tasksData.forEach((task, index) => {
                __kanbanDebugLog(`  ${index + 1}. ID: ${task.id}, Статус: "${task.status_name}" (ID: ${task.status_id})`);
            });
        }

        // Проверяем соответствие
        __kanbanDebugLog('[KanbanManager] 🔍 Проверка соответствия:');
        if (this.tasksData) {
            this.tasksData.forEach(task => {
                const targetColumn = document.querySelector(`[data-status-id="${task.status_id}"]`);
                const columnTitle = targetColumn?.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();

                if (targetColumn) {
                    __kanbanDebugLog(`  ✅ Задача ${task.id}: "${task.status_name}" -> "${columnTitle}"`);
                } else {
                    __kanbanDebugLog(`  ❌ Задача ${task.id}: "${task.status_name}" -> КОЛОНКА НЕ НАЙДЕНА`);
                }
            });
        }
    }

    // Публичные методы для интеграции с существующей системой
    refreshData() {
        __kanbanDebugLog('[KanbanManager] 🔄 Обновление данных Kanban');
        this.clearCache(); // Очищаем кэш для принудительного обновления
        this.loadKanbanDataOptimized();
    }

    /**
     * Принудительное обновление данных с индикатором загрузки
     */
    async forceRefresh() {
        __kanbanDebugLog('[KanbanManager] 🔄 Принудительное обновление данных Kanban');

        // Показываем индикатор загрузки
        this.showKanbanLoading();
        this.isLoading = true;

        try {
            // Очищаем кэш
            this.clearCache();

            // Загружаем данные заново
            await this.loadKanbanDataOptimized();

            __kanbanDebugLog('[KanbanManager] ✅ Принудительное обновление завершено');

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка принудительного обновления:', error);
            this.showError('Ошибка обновления данных: ' + error.message);
        } finally {
            // Скрываем индикатор загрузки
            this.hideKanbanLoading();
            this.isLoading = false;
        }
    }

    /**
     * Проверка состояния загрузки
     */
    getLoadingState() {
        return this.isLoading;
    }

    /**
     * Получение статистики кэша
     */
    getCacheStats() {
        const now = Date.now();
        const cacheAge = this.cache.lastUpdate ? now - this.cache.lastUpdate : 0;
        const isValid = this.isCacheValid();

        return {
            hasTasks: !!this.cache.tasks,
            hasStatuses: !!this.cache.statuses,
            lastUpdate: this.cache.lastUpdate,
            cacheAge: cacheAge,
            isValid: isValid,
            tasksCount: this.cache.tasks ? this.cache.tasks.length : 0,
            statusesCount: this.cache.statuses ? this.cache.statuses.length : 0
        };
    }

    applyFilters(filters) {
        this.filters = { ...this.filters, ...filters };
        if (this.currentView === 'kanban') {
            this.loadKanbanData();
        }
    }

        /**
     * Инициализация Drag & Drop
     */
    initDragAndDrop() {
        try {
            __kanbanDebugLog('[KanbanManager] 🎯 Инициализация drag & drop');

            // Находим все карточки задач
            const cards = document.querySelectorAll('.kanban-card');
            const dragHandles = document.querySelectorAll('.kanban-card-drag-handle');
            const dropZones = document.querySelectorAll('.kanban-column-content');

            // Карточка сама по себе не является drag-source
            cards.forEach(card => {
                card.setAttribute('draggable', false);
            });

            dragHandles.forEach(handle => {
                handle.setAttribute('draggable', true);
                handle.removeEventListener('dragstart', this.boundHandleDragStart);
                handle.removeEventListener('dragend', this.boundHandleDragEnd);
                handle.addEventListener('dragstart', this.boundHandleDragStart);
                handle.addEventListener('dragend', this.boundHandleDragEnd);
            });

            // Добавляем обработчики для зон сброса
            dropZones.forEach(zone => {
                zone.removeEventListener('dragover', this.boundHandleDragOver);
                zone.removeEventListener('dragenter', this.boundHandleDragEnter);
                zone.removeEventListener('dragleave', this.boundHandleDragLeave);
                zone.removeEventListener('drop', this.boundHandleDrop);
                zone.addEventListener('dragover', this.boundHandleDragOver);
                zone.addEventListener('dragenter', this.boundHandleDragEnter);
                zone.addEventListener('dragleave', this.boundHandleDragLeave);
                zone.addEventListener('drop', this.boundHandleDrop);
            });

            __kanbanDebugLog('[KanbanManager] ✅ Drag & drop инициализирован');
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка инициализации drag & drop:', error);
        }
    }

    /**
     * Обработка начала перетаскивания
     */
    handleDragStart(event) {
        try {
            __kanbanDebugLog('[KanbanManager] 🎯 handleDragStart вызван');
            __kanbanDebugLog('[KanbanManager] 📋 event.target:', event.target);
            __kanbanDebugLog('[KanbanManager] 📋 event.target.tagName:', event.target.tagName);
            __kanbanDebugLog('[KanbanManager] 📋 event.target.className:', event.target.className);

            const dragHandle = event.target.closest('.kanban-card-drag-handle');
            if (!dragHandle) {
                event.preventDefault();
                return;
            }

            // Ищем ближайший элемент с data-task-id (карточка задачи)
            const taskCard = dragHandle.closest('.kanban-card');
            __kanbanDebugLog('[KanbanManager] 📋 taskCard найден:', taskCard);

            const taskId = taskCard ? taskCard.getAttribute('data-task-id') : null;
            __kanbanDebugLog('[KanbanManager] 📋 taskId:', taskId);

            if (!taskId) {
                console.error('[KanbanManager] ❌ Не удалось найти ID задачи для перетаскивания');
                console.error('[KanbanManager] 📋 event.target:', event.target);
                console.error('[KanbanManager] 📋 event.target.closest("[data-task-id]"):', event.target.closest('[data-task-id]'));
                event.preventDefault();
                return;
            }

            const taskTitle = taskCard.querySelector('.kanban-card-subject')?.textContent || `Задача #${taskId}`;

            __kanbanDebugLog('[KanbanManager] 📋 Устанавливаем dataTransfer...');
            event.dataTransfer.setData('text/plain', taskId);
            event.dataTransfer.setData('text/html', taskTitle);
            event.dataTransfer.effectAllowed = 'move';
            if (event.dataTransfer.setDragImage && taskCard) {
                event.dataTransfer.setDragImage(taskCard, 24, 24);
            }

            taskCard.classList.add('dragging');
            document.body.classList.add('kanban-dragging');

            // Показываем подсказку
            this.showNotification(`Перетаскивание: ${taskTitle}`, 'info');

            __kanbanDebugLog(`[KanbanManager] 🎯 Начало перетаскивания задачи #${taskId}: ${taskTitle}`);
            __kanbanDebugLog(`[KanbanManager] 📋 DataTransfer установлен: text/plain = "${taskId}"`);
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка в handleDragStart:', error);
            event.preventDefault();
        }
    }

    /**
     * Обработка окончания перетаскивания
     */
    handleDragEnd(event) {
        __kanbanDebugLog('[KanbanManager] ✅ Перетаскивание завершено');
        this.lastDragEndedAt = Date.now();
        document.body.classList.remove('kanban-dragging');

        // Принудительно очищаем все drag-состояния
        this.clearAllDragStates();

        // Дополнительная очистка для уверенности
        setTimeout(() => {
            this.clearAllDragStates();
        }, 100);
    }

    /**
     * Обработка перетаскивания над зоной
     */
    handleDragOver(event) {
        event.preventDefault();

        // Проверяем, не пытается ли пользователь перетащить в ту же колонку
        const dropZone = event.currentTarget;
        const newStatusId = dropZone.getAttribute('data-status-id');

        // Находим перетаскиваемую карточку
        const draggingCard = document.querySelector('.kanban-card.dragging');
        if (draggingCard) {
            const currentColumn = draggingCard.closest('[data-status-id]');
            const currentStatusId = currentColumn ? currentColumn.getAttribute('data-status-id') : null;

            // Приводим статусы к строкам для корректного сравнения
            const currentStatusStr = String(currentStatusId);
            const newStatusStr = String(newStatusId);

            if (currentStatusStr === newStatusStr) {
                // Если это та же колонка, показываем визуальный индикатор "недоступно"
                dropZone.classList.add('drag-same-column');
                dropZone.classList.remove('drag-over');
            } else {
                // Если это другая колонка, показываем обычный индикатор
                dropZone.classList.add('drag-over');
                dropZone.classList.remove('drag-same-column');
            }
        } else {
            // Fallback: показываем обычный индикатор
            dropZone.classList.add('drag-over');
        }
    }

    /**
     * Обработка входа в зону перетаскивания
     */
    handleDragEnter(event) {
        // Логика перенесена в handleDragOver для более точного контроля
        this.handleDragOver(event);
    }

    /**
     * Обработка выхода из зоны перетаскивания
     */
    handleDragLeave(event) {
        const dropZone = event.currentTarget;

        // Проверяем, действительно ли мышь покинула зону (не перешла на дочерний элемент)
        if (!dropZone.contains(event.relatedTarget)) {
            dropZone.classList.remove('drag-over');
            dropZone.classList.remove('drag-same-column');
        }
    }

    /**
     * Принудительная очистка всех drag-состояний
     */
    clearAllDragStates() {
        __kanbanDebugLog('[KanbanManager] 🧹 Очистка всех drag-состояний');

        // Убираем все классы drag-over и drag-same-column
        const allDropZones = document.querySelectorAll('.kanban-column-content');
        allDropZones.forEach(zone => {
            zone.classList.remove('drag-over');
            zone.classList.remove('drag-same-column');
        });

        // Убираем класс dragging со всех карточек
        const allCards = document.querySelectorAll('.kanban-card');
        allCards.forEach(card => {
            card.classList.remove('dragging');
        });
    }

    /**
     * Обработка сброса задачи
     */
    async handleDrop(event) {
        __kanbanDebugLog('[KanbanManager] 🎯 handleDrop вызван');
        __kanbanDebugLog('[KanbanManager] 📋 event.dataTransfer:', event.dataTransfer);
        __kanbanDebugLog('[KanbanManager] 📋 event.dataTransfer.types:', event.dataTransfer.types);

        event.preventDefault();
        const dropZone = event.currentTarget;
        const taskId = event.dataTransfer.getData('text/plain');
        const newStatusId = dropZone.getAttribute('data-status-id');

        // КРИТИЧЕСКИ ВАЖНАЯ ПРОВЕРКА: добавляем флаг обработки
        if (this._isProcessingDrop) {
            __kanbanDebugLog('[KanbanManager] ⚠️ Drop уже обрабатывается, игнорируем повторный вызов');
            return;
        }
        this._isProcessingDrop = true;

        // ЭКСПРЕСС-ПРОВЕРКА: быстрая проверка статусов в самом начале
        const quickTaskCard = document.querySelector(`[data-task-id="${taskId}"]`);
        const quickCurrentColumn = quickTaskCard ? quickTaskCard.closest('[data-status-id]') : null;
        const quickCurrentStatusId = quickCurrentColumn ? quickCurrentColumn.getAttribute('data-status-id') : null;

        __kanbanDebugLog(`[KanbanManager] ⚡ ЭКСПРЕСС-ПРОВЕРКА: текущий=${quickCurrentStatusId}, новый=${newStatusId}`);

        if (quickCurrentStatusId && String(quickCurrentStatusId) === String(newStatusId)) {
            __kanbanDebugLog(`[KanbanManager] ⚡ ЭКСПРЕСС-ПРОВЕРКА: статусы одинаковые, немедленно отменяем операцию`);
            this.clearAllDragStates();
            this.showNotification(`Задача #${taskId} уже находится в этом статусе`, 'info');
            this._isProcessingDrop = false;
            return;
        }

        __kanbanDebugLog('[KanbanManager] 📋 taskId из dataTransfer:', taskId);
        __kanbanDebugLog('[KanbanManager] 📋 newStatusId из dropZone:', newStatusId);

        // Проверяем, что получили корректные данные
        if (!taskId) {
            console.error('[KanbanManager] ❌ Не удалось получить ID задачи из dataTransfer');
            console.error('[KanbanManager] 📋 event.dataTransfer.types:', event.dataTransfer.types);
            console.error('[KanbanManager] 📋 Попытка получить text/html:', event.dataTransfer.getData('text/html'));
            this.showErrorMessage('Ошибка: не удалось определить задачу для перемещения');
            this._isProcessingDrop = false; // Сбрасываем флаг
            return;
        }

        if (!newStatusId) {
            console.error('[KanbanManager] ❌ Не удалось получить ID статуса из dropZone');
            this.showErrorMessage('Ошибка: не удалось определить целевой статус');
            this._isProcessingDrop = false; // Сбрасываем флаг
            return;
        }

        // Проверяем, не перетаскивается ли задача в ту же колонку
        __kanbanDebugLog('[KanbanManager] 🔍 Поиск карточки задачи с ID:', taskId);

        // Ищем все карточки с данным ID (может быть несколько)
        const allTaskCards = document.querySelectorAll(`[data-task-id="${taskId}"]`);
        __kanbanDebugLog('[KanbanManager] 🔍 Найдено карточек с ID', taskId, ':', allTaskCards.length);

        // Берём первую найденную карточку
        const taskCard = allTaskCards[0];
        __kanbanDebugLog('[KanbanManager] 🔍 Используем карточку:', taskCard);

        // Дополнительно ищем карточку с классом dragging
        const draggingCard = document.querySelector('.kanban-card.dragging');
        __kanbanDebugLog('[KanbanManager] 🔍 Карточка с классом dragging:', draggingCard);

        // Используем dragging карточку, если она найдена и соответствует ID
        const finalTaskCard = (draggingCard && draggingCard.getAttribute('data-task-id') === taskId) ? draggingCard : taskCard;
        __kanbanDebugLog('[KanbanManager] 🔍 Финальная карточка для проверки:', finalTaskCard);

        if (finalTaskCard) {
            const currentColumn = finalTaskCard.closest('[data-status-id]');
            __kanbanDebugLog('[KanbanManager] 🔍 Текущая колонка:', currentColumn);

            const currentStatusId = currentColumn ? currentColumn.getAttribute('data-status-id') : null;
            __kanbanDebugLog('[KanbanManager] 📋 Текущий статус задачи:', currentStatusId, '(тип:', typeof currentStatusId, ')');
            __kanbanDebugLog('[KanbanManager] 📋 Новый статус:', newStatusId, '(тип:', typeof newStatusId, ')');

            // Приводим статусы к строкам для корректного сравнения
            const currentStatusStr = String(currentStatusId);
            const newStatusStr = String(newStatusId);

            __kanbanDebugLog('[KanbanManager] 📋 Сравнение статусов (строки):', {
                currentStatusStr,
                newStatusStr,
                равны: currentStatusStr === newStatusStr,
                строгоРавны: currentStatusId === newStatusId
            });

            if (currentStatusStr === newStatusStr) {
                __kanbanDebugLog('[KanbanManager] ⚠️ СТАТУСЫ ОДИНАКОВЫЕ - отменяем операцию');
                __kanbanDebugLog('[KanbanManager] ⚠️ Останавливаем выполнение handleDrop');

                // Принудительно очищаем все drag-состояния
                this.clearAllDragStates();

                // Показываем информационное сообщение
                this.showNotification(`Задача #${taskId} уже находится в этом статусе`, 'info');

                // КРИТИЧЕСКИ ВАЖНО: сбрасываем флаг и завершаем выполнение функции
                this._isProcessingDrop = false;
                __kanbanDebugLog('[KanbanManager] ⚠️ RETURN - функция завершается здесь');
                return;
            } else {
                __kanbanDebugLog('[KanbanManager] ✅ СТАТУСЫ РАЗНЫЕ - продолжаем операцию');
            }
        } else {
            __kanbanDebugLog('[KanbanManager] ❌ Карточка задачи НЕ НАЙДЕНА - продолжаем операцию');
        }

        // Получаем название нового статуса из заголовка колонки
        const columnTitle = dropZone.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim() || 'Неизвестный статус';

        __kanbanDebugLog(`[KanbanManager] 🎯 Сброс задачи #${taskId} в статус ${newStatusId} (${columnTitle})`);
        __kanbanDebugLog(`[KanbanManager] 📋 DataTransfer получен: text/plain = "${taskId}"`);

        // Принудительно очищаем все drag-состояния
        this.clearAllDragStates();

        // Повторно ищем карточку после очистки состояний (на случай если она изменилась)
        const taskCardAfterCleanup = document.querySelector(`[data-task-id="${taskId}"]`);
        __kanbanDebugLog('[KanbanManager] 🔍 Карточка после очистки состояний:', taskCardAfterCleanup);

        // Показываем индикатор загрузки
        const cardForUpdate = taskCardAfterCleanup || finalTaskCard;
        if (cardForUpdate) {
            cardForUpdate.classList.add('updating');
            this.showUpdateIndicator(cardForUpdate);
            __kanbanDebugLog('[KanbanManager] ⏳ Показан индикатор загрузки для карточки:', cardForUpdate);
        } else {
            __kanbanDebugLog('[KanbanManager] ⚠️ Карточка не найдена для показа индикатора загрузки');
        }

        try {
            // Обновляем статус задачи в Redmine
            const success = await this.updateTaskStatus(taskId, newStatusId);
            __kanbanDebugLog(`[KanbanManager] 📋 Результат updateTaskStatus для задачи #${taskId}:`, success);

            if (success) {
                __kanbanDebugLog(`[KanbanManager] ✅ Обновление статуса успешно, перемещаем карточку`);
                // Перемещаем карточку в новую колонку с анимацией
                if (taskCard) {
                    // Находим правильную колонку для нового статуса
                    const targetColumn = document.querySelector(`[data-status-id="${newStatusId}"]`);

                    if (targetColumn) {
                        __kanbanDebugLog(`[KanbanManager] 🎯 Перемещаем карточку в правильную колонку для статуса ${newStatusId}`);

                        // Обновляем данные карточки с новым статусом
                        taskCard.setAttribute('data-status-id', newStatusId);
                        taskCard.setAttribute('data-status-name', columnTitle);

                        // Обновляем отображение статуса в карточке
                        const statusElement = taskCard.querySelector('.task-status');
                        if (statusElement) {
                            statusElement.textContent = columnTitle;
                            statusElement.className = `task-status status-${newStatusId}`;
                        }

                        // Перемещаем карточку в правильную колонку
                        this.moveCardWithAnimation(taskCard, targetColumn);

                        // Обновляем счетчики колонок
                        this.updateColumnCounts();

                        this.showSuccessMessage(`Задача #${taskId} перемещена в статус "${columnTitle}"`);
                        __kanbanDebugLog(`[KanbanManager] ✅ Задача #${taskId} перемещена в статус ${newStatusId} (${columnTitle})`);

                        // Обновляем данные задачи в локальном кэше
                        this.updateTaskInCache(taskId, newStatusId, columnTitle);

                        // Проверяем, что карточка действительно переместилась
                        setTimeout(() => {
                            const movedCard = document.querySelector(`[data-task-id="${taskId}"]`);
                            if (movedCard && movedCard.closest(`[data-status-id="${newStatusId}"]`)) {
                                __kanbanDebugLog(`[KanbanManager] ✅ Карточка #${taskId} успешно перемещена в колонку ${newStatusId}`);
                            } else {
                                console.warn(`[KanbanManager] ⚠️ Карточка #${taskId} не найдена в целевой колонке ${newStatusId}`);
                            }
                        }, 500);
                    } else {
                        console.warn(`[KanbanManager] ⚠️ Колонка для статуса ${newStatusId} не найдена`);
                        // Перемещаем в dropZone как fallback
                        this.moveCardWithAnimation(taskCard, dropZone);
                        this.updateColumnCounts();
                    }

                }
            } else {
                // Возвращаем карточку на место при ошибке
                console.error(`[KanbanManager] ❌ Ошибка обновления статуса задачи #${taskId}`);
                // Не показываем дополнительное сообщение, так как updateTaskStatus уже показал ошибку
            }
        } catch (error) {
            console.error(`[KanbanManager] ❌ Ошибка сети при обновлении задачи #${taskId}:`, error);
            this.showErrorMessage(`Ошибка сети: ${error.message}`);
        } finally {
            // Убираем индикатор загрузки
            if (taskCard) {
                taskCard.classList.remove('updating');
                this.hideUpdateIndicator(taskCard);
            }

            // КРИТИЧЕСКИ ВАЖНО: сбрасываем флаг обработки
            this._isProcessingDrop = false;
            __kanbanDebugLog('[KanbanManager] 🏁 handleDrop завершен, флаг сброшен');
        }
    }

    /**
     * Обновление статуса задачи в Redmine
     */
    async updateTaskStatus(taskId, newStatusId) {
        __kanbanDebugLog(`[KanbanManager] 🔄 updateTaskStatus вызван для задачи #${taskId}, новый статус: ${newStatusId}`);

        // ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: проверяем статус ещё раз прямо здесь
        const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskCard) {
            const currentColumn = taskCard.closest('[data-status-id]');
            const currentStatusId = currentColumn ? currentColumn.getAttribute('data-status-id') : null;

            __kanbanDebugLog(`[KanbanManager] 🔄 Дополнительная проверка в updateTaskStatus:`);
            __kanbanDebugLog(`[KanbanManager] 🔄 Текущий статус: ${currentStatusId}, Новый статус: ${newStatusId}`);

            if (String(currentStatusId) === String(newStatusId)) {
                __kanbanDebugLog(`[KanbanManager] ⚠️ ДУБЛИРУЮЩАЯ ПРОВЕРКА: статусы одинаковые, отменяем запрос к серверу`);
                this.showNotification(`Задача #${taskId} уже находится в статусе ${newStatusId}`, 'info');
                return true; // Возвращаем true, чтобы не показывать ошибку
            }
        }

        // Проверяем, не выполняется ли уже обновление для этой задачи
        const updateKey = `updating_${taskId}`;
        if (this[updateKey]) {
            __kanbanDebugLog(`[KanbanManager] ⚠️ Обновление задачи #${taskId} уже выполняется, ждем завершения...`);
            // Ждем завершения текущего обновления
            while (this[updateKey]) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            __kanbanDebugLog(`[KanbanManager] ✅ Предыдущее обновление задачи #${taskId} завершено`);
            return true; // Возвращаем true, так как обновление уже выполнено
        }

        // Устанавливаем флаг обновления
        this[updateKey] = true;

        try {
            // Показываем индикатор загрузки
            this.showNotification('Обновление статуса...', 'info');

            const response = await fetch(`/tasks/api/task/${taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    status_id: newStatusId
                })
            });

            // Пытаемся получить JSON ответ
            let result;
            try {
                result = await response.json();
                __kanbanDebugLog(`[KanbanManager] 📋 Ответ сервера для задачи #${taskId}:`, result);
            } catch (jsonError) {
                console.error(`[KanbanManager] ❌ Ошибка парсинга JSON ответа:`, jsonError);
                throw new Error(`HTTP ${response.status}: Неверный формат ответа сервера`);
            }

            if (!response.ok) {
                // Если есть детальная ошибка в JSON
                if (result && result.error) {
                    throw new Error(`HTTP ${response.status}: ${result.error}`);
                } else {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
            }

            if (result.success) {
                __kanbanDebugLog(`[KanbanManager] ✅ Статус задачи #${taskId} обновлён в Redmine`);
                this.showNotification(`Статус задачи #${taskId} обновлён`, 'success');
                return true;
            } else {
                const errorMessage = result.error || 'Неизвестная ошибка';
                console.error(`[KanbanManager] ❌ Ошибка обновления статуса: ${errorMessage}`);
                console.error(`[KanbanManager] 📋 Полный ответ сервера:`, result);
                this.showErrorMessage(`Ошибка обновления: ${errorMessage}`);
                return false;
            }
        } catch (error) {
            console.error(`[KanbanManager] ❌ Ошибка запроса обновления статуса:`, error);
            this.showErrorMessage(`Ошибка сети: ${error.message}`);
            return false;
        } finally {
            // Снимаем флаг обновления
            this[updateKey] = false;
        }
    }

    /**
     * Получение CSRF токена
     */
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    /**
     * Перемещение карточки с анимацией
     */
    moveCardWithAnimation(card, targetZone) {
        __kanbanDebugLog(`[KanbanManager] 🎯 Перемещение карточки в зону:`, targetZone);

        // Сохраняем оригинальные стили
        const originalTransition = card.style.transition;
        const originalTransform = card.style.transform;

        // Устанавливаем анимацию
        card.style.transition = 'all 0.3s ease';
        card.style.transform = 'scale(1.05)';
        card.style.opacity = '0.8';

        setTimeout(() => {
            // Перемещаем карточку
            targetZone.appendChild(card);

            // Восстанавливаем стили
            card.style.transform = 'scale(1)';
            card.style.opacity = '1';

            setTimeout(() => {
                card.style.transition = originalTransition;
                card.style.transform = originalTransform;
            }, 300);

            __kanbanDebugLog(`[KanbanManager] ✅ Карточка перемещена в новую колонку`);
        }, 150);
    }

    /**
     * Показать индикатор обновления
     */
    showUpdateIndicator(card) {
        const indicator = document.createElement('div');
        indicator.className = 'update-indicator';
        indicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        card.appendChild(indicator);
    }

    /**
     * Скрыть индикатор обновления
     */
    hideUpdateIndicator(card) {
        const indicator = card.querySelector('.update-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    /**
     * Показать сообщение об успехе
     */
    showSuccessMessage(message) {
        try {
            this.showNotification(message, 'success');
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка показа сообщения об успехе:', error);
            __kanbanDebugLog('[KanbanManager] 📢 SUCCESS:', message);
        }
    }

    /**
     * Показать сообщение об ошибке
     */
    showErrorMessage(message) {
        try {
            this.showNotification(message, 'error');
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка показа сообщения об ошибке:', error);
            console.error('[KanbanManager] 📢 ERROR:', message);
        }
    }

    /**
     * Показать уведомление
     */
    showNotification(message, type = 'info') {
        try {
            const notification = document.createElement('div');
            notification.className = `kanban-notification ${type}`;
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
                <span>${message}</span>
            `;

            // Добавляем в контейнер уведомлений
            let container = document.querySelector('.kanban-notifications');
            if (!container) {
                container = document.createElement('div');
                container.className = 'kanban-notifications';
                document.body.appendChild(container);
            }

            container.appendChild(notification);

            // Автоматически удаляем через 3 секунды
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка показа уведомления:', error);
            // Fallback - используем console.log
            __kanbanDebugLog(`[KanbanManager] 📢 ${type.toUpperCase()}: ${message}`);
        }
    }

    /**
     * Обновление счётчиков колонок
     */
    updateColumnCounts() {
        const columns = document.querySelectorAll('.kanban-column');

        columns.forEach(column => {
            const countElement = column.querySelector('.kanban-column-count');
            const taskCards = column.querySelectorAll('.kanban-card');
            const columnContent = column.querySelector('.kanban-column-content');
            const statusId = columnContent?.getAttribute('data-status-id');
            const countInfo = statusId ? (this.cache.statusCounts || {})[statusId] : null;
            const shown = countInfo?.shown ?? taskCards.length;
            const total = countInfo?.total ?? shown;

            if (countElement) {
                this.setCountChipState(countElement, shown, total);
            }
        });

        this.updatePhaseSummaries();
    }

    /**
     * Оптимизированная загрузка статусов с кэшированием
     */
    async loadStatusesOptimized() {
        // Проверяем кэш статусов
        if (this.cache.statuses && this.isCacheValid()) {
            __kanbanDebugLog('[KanbanManager] 📦 Используем кэшированные статусы');
            return this.cache.statuses;
        }

        try {
            __kanbanDebugLog('[KanbanManager] 📡 Загрузка статусов...');
            const response = await fetch('/tasks/get-my-tasks-statuses');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const statuses = await response.json();

            if (!statuses.success) {
                throw new Error(statuses.error || 'Не удалось получить статусы');
            }

            // Кэшируем статусы
            this.cache.statuses = statuses.data;
            this.cache.lastUpdate = Date.now();

            __kanbanDebugLog('[KanbanManager] ✅ Статусы загружены:', statuses.data.length);
            __kanbanDebugLog('[KanbanManager] 📋 Детали статусов:', statuses.data);
            return statuses.data;

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка загрузки статусов:', error);
            throw error;
        }
    }

    /**
     * Принудительно обновляет порядок колонок
     */
    forceUpdateColumnOrder() {
        __kanbanDebugLog('[KanbanManager] 🔄 Принудительное обновление порядка колонок...');

        // Пересоздаем колонки в нужном порядке
        this.createDynamicColumns().then(() => {
            // Перезагружаем данные
            this.loadKanbanDataOptimized().then(() => {
                __kanbanDebugLog('[KanbanManager] ✅ Порядок колонок обновлен');
            });
        }).catch(error => {
            console.error('[KanbanManager] ❌ Ошибка обновления порядка колонок:', error);
        });
    }
}

// Глобальные функции для тестирования
window.forceUpdateKanbanColumns = function() {
    if (window.kanbanManager) {
        window.kanbanManager.forceUpdateColumnOrder();
    } else {
        console.error('[Global] ❌ KanbanManager не инициализирован');
    }
};

window.resetKanbanColumns = function() {
    if (window.kanbanManager) {
        window.kanbanManager.clearCache();
        window.kanbanManager.forceUpdateColumnOrder();
    } else {
        console.error('[Global] ❌ KanbanManager не инициализирован');
    }
};

// Инициализация KanbanManager
function initKanbanManager() {
    try {
        __kanbanDebugLog('[KanbanManager] 🚀 Инициализация...');

        // Создаем экземпляр KanbanManager
        window.kanbanManager = new KanbanManager();

        // Инициализируем менеджер
        window.kanbanManager.init();

        __kanbanDebugLog('[KanbanManager] ✅ Инициализация завершена');

    } catch (error) {
        console.error('[KanbanManager] ❌ Ошибка инициализации:', error);
    }
}

// Запускаем инициализацию
initKanbanManager();

// Глобальная функция для экстренной очистки drag-состояний
window.emergencyDragCleanup = function() {
    __kanbanDebugLog('[Emergency] 🚨 Экстренная очистка drag-состояний...');

    // Убираем все классы drag-over и drag-same-column
    const allDropZones = document.querySelectorAll('.kanban-column-content');
    allDropZones.forEach(zone => {
        zone.classList.remove('drag-over');
        zone.classList.remove('drag-same-column');
        zone.style.backgroundColor = '';
        zone.style.border = '';
    });

    // Убираем класс dragging со всех карточек
    const allCards = document.querySelectorAll('.kanban-card');
    allCards.forEach(card => {
        card.classList.remove('dragging');
        card.style.opacity = '';
    });

    __kanbanDebugLog('[Emergency] ✅ Все drag-состояния экстренно очищены');
};

// Глобальная функция для диагностики карточек и их статусов
window.debugKanbanCards = function() {
    __kanbanDebugLog('[Debug] 🔍 Диагностика карточек Kanban...');

    const allCards = document.querySelectorAll('.kanban-card[data-task-id]');
    __kanbanDebugLog(`[Debug] Найдено карточек: ${allCards.length}`);

    allCards.forEach((card, index) => {
        const taskId = card.getAttribute('data-task-id');
        const column = card.closest('[data-status-id]');
        const statusId = column ? column.getAttribute('data-status-id') : 'НЕ НАЙДЕН';
        const columnTitle = column ? column.querySelector('.kanban-column-title')?.textContent?.trim() : 'НЕ НАЙДЕН';

        __kanbanDebugLog(`[Debug] Карточка ${index + 1}:`, {
            taskId,
            statusId,
            columnTitle,
            element: card,
            column: column
        });
    });

    __kanbanDebugLog('[Debug] ✅ Диагностика завершена');
};

// Глобальная функция для тестирования конкретной задачи
window.testTaskStatus = function(taskId) {
    __kanbanDebugLog(`[Test] 🧪 Тестирование статуса задачи #${taskId}...`);

    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!taskCard) {
        __kanbanDebugLog(`[Test] ❌ Карточка задачи #${taskId} НЕ НАЙДЕНА`);
        return;
    }

    const currentColumn = taskCard.closest('[data-status-id]');
    const currentStatusId = currentColumn ? currentColumn.getAttribute('data-status-id') : null;
    const columnTitle = currentColumn ? currentColumn.querySelector('.kanban-column-title')?.textContent?.trim() : 'НЕ НАЙДЕН';

    __kanbanDebugLog(`[Test] 📋 Задача #${taskId}:`, {
        currentStatusId: currentStatusId,
        currentStatusType: typeof currentStatusId,
        currentStatusString: String(currentStatusId),
        columnTitle: columnTitle,
        taskCard: taskCard,
        currentColumn: currentColumn
    });

    // Тестируем все возможные статусы
    const allColumns = document.querySelectorAll('[data-status-id]');
    allColumns.forEach(column => {
        const statusId = column.getAttribute('data-status-id');
        const title = column.querySelector('.kanban-column-title')?.textContent?.trim();
        const isSame = String(currentStatusId) === String(statusId);

        __kanbanDebugLog(`[Test] 🎯 Сравнение с колонкой "${title}" (ID: ${statusId}): ${isSame ? 'ОДИНАКОВЫЕ' : 'РАЗНЫЕ'}`);
    });
};

