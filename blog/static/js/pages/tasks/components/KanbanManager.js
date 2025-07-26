/**
 * KanbanManager.js - Управление Kanban доской
 * v1.0.0
 */

class KanbanManager {
    constructor() {
        this.currentView = 'list';
        this.tasksData = [];
        this.filters = {};
        this.isLoading = false;
        this.isInitialized = false;
        this.cache = {
            tasks: null,
            statuses: null,
            completedTasks: null,
            lastUpdate: null,
            cacheTimeout: 5 * 60 * 1000 // 5 минут
        };

        console.log('[KanbanManager] 🚀 Конструктор Kanban менеджера');

        // Инициализируем только если DOM готов
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.init();
            });
        } else {
            this.init();
        }
    }

    init() {
        console.log('[KanbanManager] 🚀 Инициализация Kanban менеджера');

        try {
            // Проверяем наличие элементов
            const toggleButtons = document.querySelectorAll('.view-toggle-btn');
            const kanbanBoard = document.getElementById('kanban-board');
            const tableContainer = document.querySelector('.table-container');

            console.log('[KanbanManager] 🔍 Проверка элементов:');
            console.log('- Кнопки переключения:', toggleButtons.length);
            console.log('- Kanban доска:', !!kanbanBoard);
            console.log('- Таблица:', !!tableContainer);

            // Создаём динамические колонки
            this.createDynamicColumns().then(() => {
                this.setupEventListeners();
                this.initDragAndDrop();
                this.initTooltips(); // Инициализируем всплывающие подсказки

                // Загружаем данные задач в Kanban
                this.loadKanbanDataOptimized().then(() => {
                    // Ограничения убраны - показываем все задачи сразу
                    console.log('[KanbanManager] 🔒 Ограничения отключены');

                    this.isInitialized = true;
                    console.log('[KanbanManager] ✅ Инициализация завершена');
                }).catch(error => {
                    console.error('[KanbanManager] ❌ Ошибка загрузки данных Kanban:', error);
                    this.isInitialized = true; // Инициализация завершена, но данные не загружены
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
            console.log('[KanbanManager] 🔧 Настройка обработчиков событий');

            // Переключение между видами
            document.addEventListener('click', (e) => {
                console.log('[KanbanManager] 🖱️ Клик по элементу:', e.target);

                if (e.target.closest('.view-toggle-btn')) {
                    const btn = e.target.closest('.view-toggle-btn');
                    const view = btn.dataset.view;
                    console.log('[KanbanManager] 🔄 Переключение на вид:', view);
                    this.switchView(view);
                }

                                // Обработка клика по ID задачи в Kanban карточках
                if (e.target.closest('.kanban-card-id')) {
                    e.preventDefault();
                    e.stopPropagation();

                    const taskIdElement = e.target.closest('.kanban-card-id');
                    const taskId = taskIdElement.dataset.taskId;

                    if (taskId) {
                        console.log(`[KanbanManager] 🎯 Клик по задаче ${taskId} в Kanban`);

                        // Сохраняем текущий режим просмотра
                        const currentView = document.querySelector('.view-toggle-btn.active')?.dataset.view || 'list';
                        sessionStorage.setItem('return_from_task_view', currentView);
                        console.log(`[KanbanManager] 💾 Сохранен режим просмотра: ${currentView}`);

                        // Открываем задачу в новой вкладке
                        window.open(`/tasks/my-tasks/${taskId}`, '_blank');
                    }
                }

                // Обработка клика по всей карточке Kanban (кроме ID)
                if (e.target.closest('.kanban-card') && !e.target.closest('.kanban-card-id')) {
                    e.preventDefault();
                    e.stopPropagation();

                    const cardElement = e.target.closest('.kanban-card');
                    const taskId = cardElement.dataset.taskId;

                    if (taskId) {
                        console.log(`[KanbanManager] 🎯 Клик по карточке задачи ${taskId} в Kanban`);

                        // Сохраняем текущий режим просмотра
                        const currentView = document.querySelector('.view-toggle-btn.active')?.dataset.view || 'list';
                        sessionStorage.setItem('return_from_task_view', currentView);
                        console.log(`[KanbanManager] 💾 Сохранен режим просмотра: ${currentView}`);

                        // Открываем задачу в новой вкладке
                        window.open(`/tasks/my-tasks/${taskId}`, '_blank');
                    }
                }
            });

            // Обработка фильтров
            this.setupFilterListeners();

            console.log('[KanbanManager] ✅ Обработчики событий настроены');
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
        this.filters = {
            status: document.getElementById('status-filter')?.value || '',
            project: document.getElementById('project-filter')?.value || '',
            priority: document.getElementById('priority-filter')?.value || ''
        };

        console.log('[KanbanManager] 🔍 Фильтры обновлены:', this.filters);
    }

    switchView(view) {
        console.log(`[KanbanManager] 🔄 Переключение на вид: ${view}`);

        // Проверяем, что Kanban инициализирован
        if (!this.isInitialized) {
            console.warn('[KanbanManager] ⚠️ Kanban не инициализирован, пытаемся инициализировать...');
            this.init();
            return;
        }

        // Обновляем активную кнопку
        const allButtons = document.querySelectorAll('.view-toggle-btn');
        console.log('[KanbanManager] 🔍 Найдено кнопок переключения:', allButtons.length);

        allButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        const targetButton = document.querySelector(`[data-view="${view}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
            console.log('[KanbanManager] ✅ Активная кнопка обновлена');
        } else {
            console.error('[KanbanManager] ❌ Кнопка для вида не найдена:', view);
        }

        // Переключаем отображение
        this.toggleViewSections(view);

        this.currentView = view;

        // Загружаем данные для Kanban если переключились на него
        if (view === 'kanban') {
            console.log('[KanbanManager] 📊 Загружаем данные для Kanban');
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
            console.log('[KanbanManager] ⚠️ Компонент онбординга не найден');
        }
    }

    /**
     * Показывает баннер с подсказками после загрузки данных
     */
    showTipsBanner() {
        // Проверяем, не существует ли уже баннер
        const existingBanner = document.getElementById('kanban-tips-banner');
        if (existingBanner) {
            console.log('[KanbanManager] ⚠️ Баннер подсказок уже существует, не создаем дубликат');
            return;
        }

        // Проверяем, есть ли компонент подсказок
        if (typeof window.KanbanTips !== 'undefined') {
            const tips = new window.KanbanTips();
            tips.showIfKanbanActive();
        } else {
            console.log('[KanbanManager] ⚠️ Компонент подсказок не найден');
        }
    }

    /**
     * Инициализирует всплывающие подсказки
     */
    initTooltips() {
        // Проверяем, есть ли компонент всплывающих подсказок
        if (typeof window.KanbanTooltips !== 'undefined') {
            const tooltips = new window.KanbanTooltips();
            tooltips.init();
            console.log('[KanbanManager] ✅ Всплывающие подсказки инициализированы');
        } else {
            console.log('[KanbanManager] ⚠️ Компонент всплывающих подсказок не найден');
        }
    }

    toggleViewSections(view) {
        console.log(`[KanbanManager] 🔄 Переключение отображения на: ${view}`);

        const tableContainer = document.querySelector('.table-container');
        const kanbanBoard = document.getElementById('kanban-board');

        console.log('[KanbanManager] 🔍 Найденные элементы:');
        console.log('- Таблица:', !!tableContainer);
        console.log('- Kanban:', !!kanbanBoard);

        if (view === 'list') {
            if (tableContainer) {
                tableContainer.style.display = 'block';
                console.log('[KanbanManager] ✅ Таблица показана');
            }
            if (kanbanBoard) {
                kanbanBoard.style.display = 'none';
                console.log('[KanbanManager] ✅ Kanban скрыт');
            }
        } else if (view === 'kanban') {
            if (tableContainer) {
                tableContainer.style.display = 'none';
                console.log('[KanbanManager] ✅ Таблица скрыта');
            }
            if (kanbanBoard) {
                kanbanBoard.style.display = 'block';
                console.log('[KanbanManager] ✅ Kanban показан');
            }
        }
    }

    /**
     * Оптимизированная загрузка данных для Kanban с кэшированием и индикатором загрузки
     */
    async loadKanbanDataOptimized() {
        console.log('[KanbanManager] 📊 Оптимизированная загрузка данных для Kanban');

        // Проверяем кэш
        if (this.isCacheValid()) {
            console.log('[KanbanManager] 📦 Используем кэшированные данные');
            this.renderKanbanBoard(this.cache.tasks);
            return;
        }

        // Показываем индикатор загрузки
        this.showKanbanLoading();
        this.isLoading = true;

        try {
            // Используем новый endpoint для прямого SQL запроса
            const response = await fetch('/tasks/get-my-tasks-direct-sql?force_load=1&view=kanban&exclude_completed=0');

            console.log('[KanbanManager] 📡 Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            console.log('[KanbanManager] 📋 Полные данные ответа:', data);

            if (!data.success && data.error) {
                throw new Error(data.error);
            }

            // Извлекаем задачи из ответа
            const tasks = data.data || [];
            const statusCounts = data.status_counts || {};

            console.log('[KanbanManager] ✅ Получено задач из SQL API:', tasks.length);
            console.log('[KanbanManager] 📊 Информация о количестве задач по статусам:', statusCounts);

            // Сохраняем задачи в кэш
            this.cache.tasks = tasks;
            this.cache.statusCounts = statusCounts;
            this.cache.lastUpdate = Date.now();
            this.tasksData = tasks;

            // Создаем динамические колонки на основе статусов
            await this.createDynamicColumns();

            // Отрисовываем Kanban доску с задачами
            this.renderKanbanBoard(tasks);

            // Завершенные задачи уже включены в основной запрос
            console.log('[KanbanManager] ✅ Все задачи загружены в одном запросе');

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
    isCacheValid() {
        if (!this.cache.tasks || !this.cache.lastUpdate) {
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
            completedTasks: null,
            statusCounts: null,
            lastUpdate: null,
            cacheTimeout: 5 * 60 * 1000
        };
        console.log('[KanbanManager] 🗑️ Кэш очищен');
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
        console.log('[KanbanManager] 🎨 Отрисовка Kanban доски с динамическими колонками');
        console.log('[KanbanManager] 📊 Количество задач для отрисовки:', tasks.length);

        // Очищаем все колонки
        const allColumns = document.querySelectorAll('.kanban-column-content');
        allColumns.forEach(column => {
            column.innerHTML = '';
        });

        console.log('[KanbanManager] 📋 Начинаем распределение задач по колонкам...');

                    // Подсчитываем статистику статусов для отладки
            const statusStats = {};
            const statusIdStats = {};
            tasks.forEach(task => {
                const status = task.status_name || 'Новая';
                const statusId = task.status_id || 'unknown';
                statusStats[status] = (statusStats[status] || 0) + 1;
                statusIdStats[statusId] = (statusIdStats[statusId] || 0) + 1;
            });

            console.log('[KanbanManager] 📈 Статистика статусов (названия):', statusStats);
            console.log('[KanbanManager] 📈 Статистика статусов (ID):', statusIdStats);

                // Распределяем задачи по колонкам на основе их статуса
        tasks.forEach((task, index) => {
            console.log(`[KanbanManager] 📋 Задача ${index + 1}: ID=${task.id}, Статус="${task.status_name}", StatusID=${task.status_id}`);

            const status = task.status_name || 'Новая';
            const statusId = task.status_id || 1; // ID статуса из задачи

            console.log(`[KanbanManager] 🔍 Анализ статуса: "${status}" (ID: ${statusId})`);

            // Находим колонку для этого статуса
            const columnElement = document.querySelector(`[data-status-id="${statusId}"]`);

            if (columnElement) {
                console.log(`[KanbanManager] ✅ Найдена колонка для статуса "${status}" (ID: ${statusId})`);

                // Создаем карточку задачи
                this.createTaskCard(task, columnElement);

                // Обновляем счетчик колонки
                this.updateColumnCount(columnElement);
            } else {
                console.warn(`[KanbanManager] ⚠️ Колонка для статуса "${status}" (ID: ${statusId}) не найдена`);

                // Показываем все доступные колонки для отладки
                const allColumns = document.querySelectorAll('.kanban-column-content');
                console.log('[KanbanManager] 🔍 Доступные колонки:');
                allColumns.forEach(col => {
                    const statusId = col.getAttribute('data-status-id');
                    const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                    console.log(`  - ID: ${statusId}, Название: ${columnTitle}`);
                });

                // Попробуем найти колонку по названию статуса
                console.log('[KanbanManager] 🔍 Попытка найти колонку по названию статуса...');
                const columnByTitle = Array.from(allColumns).find(col => {
                    const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                    return columnTitle && columnTitle.includes(status);
                });

                if (columnByTitle) {
                    console.log(`[KanbanManager] ✅ Найдена колонка по названию для статуса "${status}"`);
                    this.createTaskCard(task, columnByTitle);
                    this.updateColumnCount(columnByTitle);
                } else {
                    console.error(`[KanbanManager] ❌ Колонка для статуса "${status}" не найдена ни по ID, ни по названию`);

                    // Fallback: добавляем в первую доступную колонку
                    const firstColumn = allColumns[0];
                    if (firstColumn) {
                        console.log(`[KanbanManager] 🔄 Fallback: добавляем в первую колонку`);
                        this.createTaskCard(task, firstColumn);
                        this.updateColumnCount(firstColumn);
                    }
                }
            }
        });

        console.log('[KanbanManager] ✅ Kanban доска обновлена');

        // Обновляем индикаторы количества задач
        this.updateTaskCountIndicators();

        // Проверяем соответствие колонок и статусов
        this.validateAndFixColumnStatusMapping();

        // Исправляем несоответствия статусов
        this.fixStatusMismatches();

        // Мониторим новые статусы
        this.monitorNewStatuses();

        // Тестируем соответствие статусов
        this.testStatusMapping();

        // Обновляем статистики
        this.updateKanbanStats(tasks);

        // Инициализируем Drag & Drop для новых карточек
        this.initDragAndDrop();

        // Показываем баннер с подсказками
        this.showTipsBanner();

        console.log('[KanbanManager] ✅ Ограничение по 10 задач в каждом статусе применено');
    }

    /**
     * Обновление индикаторов количества задач
     */
    updateTaskCountIndicators() {
        console.log('[KanbanManager] 📊 Обновление индикаторов количества задач...');

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

                    if (total > shown) {
                        // Показываем "Показано X из Y"
                        countElement.textContent = `${shown} из ${total}`;
                        countElement.title = `Показано ${shown} из ${total} задач`;
                        countElement.style.color = '#ff6b35'; // Оранжевый цвет для индикатора
                    } else {
                        // Показываем просто количество
                        countElement.textContent = shown.toString();
                        countElement.title = `${shown} задач`;
                        countElement.style.color = ''; // Сброс цвета
                    }
                }
            }
        });

        console.log('[KanbanManager] ✅ Индикаторы количества задач обновлены');
    }

    /**
     * Обновление счетчика конкретной колонки
     */
    updateColumnCount(columnElement) {
        if (!columnElement) return;

        const taskCards = columnElement.querySelectorAll('.task-card');
        const count = taskCards.length;

        // Находим элемент счетчика в заголовке колонки
        const columnHeader = columnElement.closest('.kanban-column')?.querySelector('.kanban-column-header');
        const countElement = columnHeader?.querySelector('.kanban-column-count');

        if (countElement) {
            // Проверяем, есть ли информация о статусе в кэше
            const statusId = columnElement.getAttribute('data-status-id');
            const statusCounts = this.cache.statusCounts || {};
            const countInfo = statusCounts[statusId];

            if (countInfo && countInfo.total > countInfo.shown) {
                // Используем информацию из кэша для индикатора
                const shown = countInfo.shown || count;
                const total = countInfo.total;
                countElement.textContent = `${shown} из ${total}`;
                countElement.title = `Показано ${shown} из ${total} задач`;
                countElement.style.color = '#ff6b35'; // Оранжевый цвет для индикатора
            } else {
                // Показываем просто количество
                countElement.textContent = count.toString();
                countElement.title = `${count} задач`;
                countElement.style.color = ''; // Сброс цвета
            }

            console.log(`[KanbanManager] 📊 Обновлен счетчик колонки: ${count} задач`);
        }
    }

        /**
     * Ограничение количества задач в колонке "Закрыта" - УБРАНО
     */
    limitClosedTasks() {
        console.log('[KanbanManager] 🔒 Ограничение задач в закрытых колонках - ОТКЛЮЧЕНО');

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
                countElement.textContent = cards.length;
                countElement.title = `Задач: ${cards.length}`;
            }
        });

        console.log('[KanbanManager] ✅ Все ограничения для закрытых колонок убраны');
    }

    /**
     * Загрузка дополнительных завершенных задач
     */
    async loadMoreCompletedTasks() {
        console.log('[KanbanManager] 📥 Загрузка дополнительных завершенных задач...');

        try {
            const response = await fetch('/tasks/get-completed-tasks?limit=10');
            const data = await response.json();

            if (data.success && data.data.length > 0) {
                // Сортируем по дате обновления (новые сверху)
                data.data.sort((a, b) => {
                    const dateA = new Date(a.updated_on);
                    const dateB = new Date(b.updated_on);
                    return dateB - dateA;
                });

                // Берем все задачи
                const tasksToAdd = data.data;

                const closedColumn = document.querySelector('[data-status-id="5"]');
                if (closedColumn) {
                    tasksToAdd.forEach(task => {
                        // Проверяем, не существует ли уже карточка
                        const existingCard = document.querySelector(`[data-task-id="${task.id}"]`);
                        if (!existingCard) {
                            this.createTaskCard(task, closedColumn);
                        }
                    });

                    this.updateColumnCount(closedColumn);
                    console.log('[KanbanManager] ✅ Добавлены дополнительные задачи в колонку "Закрыта"');
                }
            }
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка загрузки дополнительных задач:', error);
        }
    }

        /**
     * Автоматическая загрузка завершённых задач при отрисовке Kanban
     */
    loadCompletedTasksOnKanbanRender() {
        console.log('[KanbanManager] 🔘 Автоматическая загрузка завершённых задач');

        if (!this.completedTasksLoaded) {
            console.log('[KanbanManager] ✅ Загружаем завершённые задачи автоматически');
            this.loadCompletedTasks();
        } else {
            console.log('[KanbanManager] ⚠️ Завершённые задачи уже загружены');
        }
    }

    /**
     * Загрузка 5 завершённых задач
     */
    async loadCompletedTasks() {
        console.log('[KanbanManager] 📥 Загрузка 5 завершённых задач');

        try {
            const response = await fetch('/tasks/get-completed-tasks');

            console.log('[KanbanManager] 📡 Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[KanbanManager] ❌ HTTP ошибка:', errorText);
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const data = await response.json();
            console.log('[KanbanManager] 📋 Данные ответа:', data);

            if (!data.success) {
                throw new Error(data.error || 'Ошибка загрузки завершённых задач');
            }

            console.log('[KanbanManager] ✅ Получено завершённых задач:', data.data.length);

                        // Сортируем задачи по дате обновления (новые сверху)
            data.data.sort((a, b) => {
                const dateA = new Date(a.updated_on);
                const dateB = new Date(b.updated_on);
                return dateB - dateA; // Убывающий порядок
            });

            console.log('[KanbanManager] ✅ Сортировка применена');

            // Ограничиваем до 5 последних завершённых задач
            const limitedTasks = data.data;
            console.log(`[KanbanManager] 📊 Показываем все ${limitedTasks.length} задач`);

            // Отладочная информация о распределении задач по статусам
            const statusDistribution = {};
            limitedTasks.forEach(task => {
                const statusName = task.status_name || 'Неизвестно';
                statusDistribution[statusName] = (statusDistribution[statusName] || 0) + 1;
            });
            console.log('[KanbanManager] 📊 Распределение задач по статусам:', statusDistribution);

            // Очищаем все колонки с закрытыми статусами перед добавлением новых задач
            const closedStatusIds = [5, 6, 14]; // Закрыта, Отклонена, Перенаправлена
            closedStatusIds.forEach(statusId => {
                const column = document.querySelector(`[data-status-id="${statusId}"]`);
                if (column) {
                    column.innerHTML = '';
                    console.log(`[KanbanManager] ✅ Колонка статуса ${statusId} очищена`);
                }
            });

            // Добавляем задачи в соответствующие колонки по их статусу
            limitedTasks.forEach(task => {
                console.log(`[KanbanManager] 📋 Добавляем завершённую задачу ${task.id} со статусом "${task.status_name}" (ID: ${task.status_id})`);

                // Показываем все доступные колонки для отладки
                const allColumns = document.querySelectorAll('.kanban-column-content');
                console.log('[KanbanManager] 🔍 Доступные колонки для завершённых задач:');
                allColumns.forEach(col => {
                    const statusId = col.getAttribute('data-status-id');
                    const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                    console.log(`  - ID: ${statusId}, Название: ${columnTitle}`);
                });

                // Находим колонку по ID статуса задачи
                const targetColumn = document.querySelector(`[data-status-id="${task.status_id}"]`);

                if (targetColumn) {
                    console.log(`[KanbanManager] ✅ Найдена колонка для статуса ${task.status_id}`);
                    this.createTaskCard(task, targetColumn);

                    // Обновляем счетчик колонки
                    this.updateColumnCount(targetColumn);
                } else {
                    console.warn(`[KanbanManager] ⚠️ Колонка для статуса ${task.status_id} не найдена, добавляем в колонку "Закрыта" как fallback`);

                    // Fallback: добавляем в колонку "Закрыта"
                    const closedColumn = document.getElementById('status-5-column');
                    if (closedColumn) {
                        const columnContent = closedColumn.querySelector('.kanban-column-content');
                        if (columnContent) {
                            this.createTaskCard(task, columnContent);
                            this.updateColumnCount(columnContent);
                        }
                    }
                }
            });

            this.completedTasksLoaded = true;
            console.log('[KanbanManager] ✅ Завершённые задачи загружены и отображены');

            // Обновляем счётчики всех колонок
            this.updateColumnCounts();

            // Подсчитываем только задачи со статусом "Закрыта" для счётчика
            const closedTasksCount = data.data.filter(task => task.status_id === 5).length;
            const closedCount = document.getElementById('status-5-count');
            if (closedCount) {
                closedCount.textContent = closedTasksCount;
                console.log('[KanbanManager] 🔢 Обновлённый счётчик колонки "Закрыта":', closedCount.textContent);
            }

            // Обновляем общий счётчик задач
            const totalCount = document.querySelector('.total-tasks-count');
            if (totalCount) {
                const currentTotal = parseInt(totalCount.textContent) || 0;
                const newTotal = currentTotal + data.data.length;
                totalCount.textContent = newTotal;
                console.log('[KanbanManager] 🔢 Обновлённый общий счётчик:', newTotal);
            }

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка загрузки завершённых задач:', error);
            this.showKanbanError(`Ошибка загрузки завершённых задач: ${error.message}`);
        }
    }



    /**
     * Создание карточки задачи
     */
    createTaskCard(task, columnElement) {
        console.log(`[KanbanManager] 🎴 Создание карточки для задачи ${task.id}:`, task);

        // Проверяем, не существует ли уже карточка для этой задачи
        const existingCard = document.querySelector(`[data-task-id="${task.id}"]`);
        if (existingCard) {
            console.log(`[KanbanManager] ⚠️ Карточка для задачи ${task.id} уже существует, пропускаем создание`);
            return;
        }

        // Убираем ограничение для колонки "Закрыто" (ID: 5)
        const statusId = task.status_id;
        // Ограничение убрано - показываем все задачи

        // Анализируем приоритет
        const priority = task.priority_name || 'Обычный';
        console.log(`[KanbanManager] 🏷️ Анализ приоритета: "${priority}" -> "${this.getPriorityClass(priority)}"`);

        const priorityClass = this.getPriorityClass(priority);

        if (!priority || priority === 'undefined') {
            console.log(`[KanbanManager] ⚠️ Неизвестный приоритет "${priority}" -> priority-normal (по умолчанию)`);
        }

        // Создаем HTML карточки с названием проекта
        const projectName = task.project_name || 'Неизвестный проект';
        const cardHtml = `
            <div class="kanban-card" data-task-id="${task.id}" data-priority="${priorityClass}" data-updated-on="${task.updated_on || ''}" draggable="true">
                <div class="kanban-card-header">
                    <div class="kanban-card-id" data-task-id="${task.id}" style="cursor: pointer; color: #2563eb;">#${task.id}</div>
                    <div class="kanban-card-priority">
                        <span class="priority-badge ${priorityClass}">${this.escapeHtml(priority)}</span>
                    </div>
                </div>
                <div class="kanban-card-content">
                    <div class="kanban-card-project" style="font-size: 0.8em; color: #6b7280; margin-bottom: 4px;">${this.escapeHtml(projectName)}</div>
                    <div class="kanban-card-subject">${this.escapeHtml(task.subject || 'Без названия')}</div>
                    <div class="kanban-card-date">${this.formatDate(task.updated_on)}</div>
                </div>
            </div>
        `;

        // Добавляем карточку в колонку
        columnElement.insertAdjacentHTML('beforeend', cardHtml);

                // Добавляем обработчик клика для открытия деталей задачи
        const newCard = columnElement.lastElementChild;
        if (newCard) {
            // Обработчик клика для аккордеона (убираем, так как теперь используется onclick в HTML)
            // Клик по кнопке "Открыть" обрабатывается через onclick в HTML

            // Обработчики drag & drop для новой карточки
            if (this.boundHandleDragStart && this.boundHandleDragEnd) {
                newCard.addEventListener('dragstart', this.boundHandleDragStart);
                newCard.addEventListener('dragend', this.boundHandleDragEnd);
                console.log(`[KanbanManager] ✅ Обработчики drag & drop добавлены для карточки ${task.id}`);
            } else {
                // Создаем простые обработчики для этой карточки
                newCard.addEventListener('dragstart', (e) => {
                    console.log(`🎯 Drag start для карточки ${task.id}`);
                    e.dataTransfer.setData('text/plain', task.id);
                    newCard.style.opacity = '0.5';
                });

                newCard.addEventListener('dragend', (e) => {
                    console.log(`✅ Drag end для карточки ${task.id}`);
                    newCard.style.opacity = '1';
                });

                            console.log(`[KanbanManager] ✅ Простые обработчики drag & drop добавлены для карточки ${task.id}`);
        }

        // Также добавляем обработчики для зон сброса, если их еще нет
        const dropZones = document.querySelectorAll('.kanban-column-content');
        dropZones.forEach((zone, index) => {
            // Проверяем, есть ли уже обработчики
            const hasDropHandler = zone._hasDropHandler;
            if (!hasDropHandler) {
                zone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    zone.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                });

                zone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    const taskId = e.dataTransfer.getData('text/plain');
                    const statusId = zone.getAttribute('data-status-id');
                    console.log(`🎯 Drop задачи ${taskId} в зону ${index + 1} (статус: ${statusId})`);
                    zone.style.backgroundColor = '';

                    // Обновляем статус задачи
                    if (window.kanbanManager && window.kanbanManager.updateTaskStatus) {
                        window.kanbanManager.updateTaskStatus(taskId, statusId);
                    }
                });

                zone.addEventListener('dragenter', (e) => {
                    e.preventDefault();
                    zone.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
                });

                zone.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    zone.style.backgroundColor = '';
                });

                zone._hasDropHandler = true;
                console.log(`[KanbanManager] ✅ Обработчики drop добавлены для зоны ${index + 1}`);
            }
        });
    }
    }

    // Утилитарные методы
    getPriorityClass(priority) {
        if (!priority) return 'priority-normal';

        const priorityLower = priority.toLowerCase();
        console.log(`[KanbanManager] 🔍 Анализ приоритета: "${priority}" -> "${priorityLower}"`);

        // Высокие приоритеты (красный)
        if (priorityLower.includes('срочный') || priorityLower.includes('urgent') || priorityLower.includes('высокий') || priorityLower.includes('high') || priorityLower.includes('критический')) {
            console.log(`[KanbanManager] 🔴 Приоритет "${priority}" -> priority-high (красный)`);
            return 'priority-high';
        }
        // Низкие приоритеты (зеленый)
        else if (priorityLower.includes('низкий') || priorityLower.includes('low')) {
            console.log(`[KanbanManager] 🟢 Приоритет "${priority}" -> priority-low (зеленый)`);
            return 'priority-low';
        }
        // Обычные приоритеты (синий)
        else {
            console.log(`[KanbanManager] 🔵 Приоритет "${priority}" -> priority-normal (синий)`);
            return 'priority-normal';
        }
    }

    openTaskDetails(taskId) {
        console.log('[KanbanManager] 🔗 Открытие деталей задачи:', taskId);
        window.location.href = `/tasks/my-tasks/${taskId}`;
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
        console.log('[KanbanManager] 🔢 Обновление счетчиков колонок:', distribution);

        Object.entries(distribution).forEach(([columnId, count]) => {
            const countElement = document.getElementById(columnId);
            if (countElement) {
                countElement.textContent = count;
                console.log(`[KanbanManager] ✅ Счетчик ${columnId}: ${count}`);
            } else {
                console.error(`[KanbanManager] ❌ Элемент счетчика ${columnId} не найден`);
            }
        });

        // Обновляем общий счетчик
        const totalCount = Object.values(distribution).reduce((sum, count) => sum + count, 0);
        const totalElement = document.getElementById('kanban-total-count');
        if (totalElement) {
            totalElement.textContent = totalCount;
            console.log(`[KanbanManager] ✅ Общий счетчик: ${totalCount}`);
        }
    }

            /**
     * Сортирует статусы в нужном порядке для отображения
     */
    sortStatusesByOrder(statuses) {
        // Определяем порядок колонок согласно требованиям
        const columnOrder = [
            // 1 строка
            'Новая',
            'В работе',
            'Запрошено уточнение',
            'Выполнена',
            'Закрыта',
            // 2 строка
            'Отклонена',
            'На согласовании',
            'Приостановлена',
            'Протестирована',
            'Перенаправлена',
            // 3 строка
            'Заморожена',
            'Открыта',
            'Сообщи ка понял задачу!'
        ];

        // Сортируем статусы согласно порядку
        const sortedStatuses = [];
        const remainingStatuses = [];

        // Сначала добавляем статусы в нужном порядке
        columnOrder.forEach(statusName => {
            const foundStatus = statuses.find(status =>
                status.name === statusName ||
                status.name.includes(statusName) ||
                statusName.includes(status.name)
            );
            if (foundStatus) {
                sortedStatuses.push(foundStatus);
            }
        });

        // Затем добавляем оставшиеся статусы
        statuses.forEach(status => {
            const isAlreadyIncluded = sortedStatuses.some(s => s.id === status.id);
            if (!isAlreadyIncluded) {
                remainingStatuses.push(status);
            }
        });

        // Объединяем отсортированные и оставшиеся статусы
        const result = [...sortedStatuses, ...remainingStatuses];

        console.log('[KanbanManager] 📋 Статусы отсортированы:', result.map(s => s.name));

        return result;
    }

    /**
     * Динамическое создание колонок на основе статусов Redmine с оптимизацией
     */
    async createDynamicColumns() {
        console.log('[KanbanManager] 🏗️ Создание динамических колонок');

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

            console.log('[KanbanManager] 🏗️ Создаем колонки для статусов:');
            console.log('[KanbanManager] 📋 Отсортированные статусы:', sortedStatuses);

            sortedStatuses.forEach((status, index) => {
                console.log(`- ${status.name} (ID: ${status.id}, is_closed: ${status.is_closed})`);

                const columnHtml = `
                    <div class="kanban-column" id="kanban-column-${status.id}">
                        <div class="kanban-column-header" onclick="this.closest('.kanban-column').classList.toggle('collapsed')">
                            <div class="kanban-column-title">
                                <i class="fas fa-circle" style="color: ${this.getStatusColor(status.name)}"></i>
                                ${this.escapeHtml(status.name)}
                            </div>
                            <div class="kanban-column-count" id="count-${status.id}">0</div>
                            <div class="kanban-column-toggle">
                                <i class="fas fa-chevron-down"></i>
                            </div>
                        </div>
                        <div class="kanban-column-content" data-status-id="${status.id}" data-status-name="${this.escapeHtml(status.name)}">
                            <!-- Задачи будут добавлены здесь -->
                        </div>
                    </div>
                `;

                kanbanColumns.insertAdjacentHTML('beforeend', columnHtml);

                // Проверяем, что заголовок создался корректно
                const columnElement = kanbanColumns.lastElementChild;
                const header = columnElement.querySelector('.kanban-column-header');
                const title = columnElement.querySelector('.kanban-column-title');
                console.log(`[KanbanManager] 🔍 Колонка ${index + 1}:`, {
                    id: status.id,
                    name: status.name,
                    headerExists: !!header,
                    titleExists: !!title,
                    titleText: title ? title.textContent : 'null'
                });
            });

            console.log('[KanbanManager] ✅ Динамические колонки созданы в нужном порядке');

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка создания колонок:', error);
            console.log('[KanbanManager] 🔄 Создаем fallback колонки...');
            this.createFallbackColumns();
        }
    }

    /**
     * Создание fallback колонок при ошибке API
     */
    createFallbackColumns() {
        try {
            console.log('[KanbanManager] 🔄 Создание fallback колонок...');

            // Используем реальные статусы из API в нужном порядке
            const fallbackStatuses = [
                // 1 строка
                {id: 1, name: 'Новая', is_closed: false},
                {id: 2, name: 'В работе', is_closed: false},
                {id: 9, name: 'Запрошено уточнение', is_closed: false},
                {id: 7, name: 'Выполнена', is_closed: true},
                {id: 5, name: 'Закрыта', is_closed: true},
                // 2 строка
                {id: 6, name: 'Отклонена', is_closed: true},
                {id: 15, name: 'На согласовании', is_closed: false},
                {id: 10, name: 'Приостановлена', is_closed: false},
                {id: 13, name: 'Протестирована', is_closed: false},
                {id: 14, name: 'Перенаправлена', is_closed: true},
                // 3 строка
                {id: 16, name: 'Заморожена', is_closed: false},
                {id: 17, name: 'Открыта', is_closed: false},
                {id: 20, name: 'Сообщи ка понял задачу!', is_closed: false}
            ];

            const kanbanColumns = document.getElementById('kanban-columns');
            if (!kanbanColumns) {
                throw new Error('Контейнер колонок не найден');
            }

            // Очищаем существующие колонки
            kanbanColumns.innerHTML = '';

            // Создаём fallback колонки в нужном порядке
            fallbackStatuses.forEach((status, index) => {
                const columnHtml = `
                    <div class="kanban-column" id="status-${status.id}-column">
                        <div class="kanban-column-header" onclick="this.closest('.kanban-column').classList.toggle('collapsed')">
                            <div class="kanban-column-title">
                                <i class="fas fa-circle" style="color: ${this.getStatusColor(status.name)}"></i>
                                ${status.name}
                            </div>
                            <div class="kanban-column-count" id="status-${status.id}-count">0</div>
                            <div class="kanban-column-toggle">
                                <i class="fas fa-chevron-down"></i>
                            </div>
                        </div>
                        <div class="kanban-column-content" data-status-id="${status.id}" data-status-name="${this.escapeHtml(status.name)}">
                            <!-- Задачи будут добавляться сюда -->
                        </div>
                    </div>
                `;

                kanbanColumns.insertAdjacentHTML('beforeend', columnHtml);
            });

            console.log('[KanbanManager] ✅ Fallback колонки созданы в нужном порядке');
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка создания fallback колонок:', error);
        }
    }

            /**
     * Получение цвета для статуса
     */
    getStatusColor(statusName) {
        const statusColors = {
            'Новая': '#3498db',
            'В работе': '#f39c12',
            'Закрыта': '#27ae60',
            'Отклонена': '#95a5a6',
            'Выполнена': '#2ecc71',
            'Запрошено уточнение': '#e67e22',
            'Приостановлена': '#f39c12',
            'Протестирована': '#9b59b6',
            'Перенаправлена': '#e74c3c',
            'На согласовании': '#f39c12',
            'Заморожена': '#34495e',
            'Открыта': '#3498db',
            'На тестировании': '#9b59b6',
            'В очереди': '#95a5a6'
        };

        // Если статус не найден, генерируем цвет на основе названия
        if (!statusColors[statusName]) {
            console.log(`[KanbanManager] 🎨 Новый статус "${statusName}" - генерируем цвет`);

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
            console.log(`[KanbanManager] 🎨 Сгенерирован цвет для "${statusName}": ${color}`);

            return color;
        }

        return statusColors[statusName];
    }

        /**
     * Проверка, является ли статус закрытым
     */
    isStatusClosed(statusName) {
        // Проверяем русские названия закрытых статусов из u_statuses
        const closedStatuses = [
            'Закрыта',          // Русское название из u_statuses
            'Отклонена',        // Русское название из u_statuses
            'Перенаправлена'    // Русское название из u_statuses
        ];
        return closedStatuses.includes(statusName);
    }

        /**
     * Обновление данных задачи в локальном кэше
     */
    updateTaskInCache(taskId, newStatusId, newStatusName) {
        console.log(`[KanbanManager] 🔄 Обновление кэша для задачи #${taskId}: статус ${newStatusId} (${newStatusName})`);

        // Находим задачу в локальном кэше и обновляем её статус
        const taskIndex = this.tasksData.findIndex(task => task.id == taskId);
        if (taskIndex !== -1) {
            this.tasksData[taskIndex].status_id = parseInt(newStatusId);
            this.tasksData[taskIndex].status_name = newStatusName;
            console.log(`[KanbanManager] ✅ Задача #${taskId} обновлена в кэше`);
        } else {
            console.warn(`[KanbanManager] ⚠️ Задача #${taskId} не найдена в кэше для обновления`);
        }
    }

    /**
     * Проверка и исправление несоответствий между колонками и статусами
     */
    validateAndFixColumnStatusMapping() {
        console.log('[KanbanManager] 🔍 Проверка соответствия колонок и статусов...');

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

        console.log('[KanbanManager] 📋 Карта колонок:', columnStatusMap);

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
            console.log('[KanbanManager] 📋 Проверка задач в кэше...');
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
        console.log('[KanbanManager] 🔍 Мониторинг новых статусов...');

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
            console.log('[KanbanManager] ✅ Все статусы известны');
        }
    }

    /**
     * Принудительное исправление несоответствий статусов
     */
    fixStatusMismatches() {
        console.log('[KanbanManager] 🔧 Исправление несоответствий статусов...');

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
                    console.log(`[KanbanManager] 🔧 Исправление статуса задачи ${task.id}: "${task.status_name}" -> "${correctStatusName}"`);
                    task.status_name = correctStatusName;
                    fixedCount++;
                }
            });

            if (fixedCount > 0) {
                console.log(`[KanbanManager] ✅ Исправлено ${fixedCount} несоответствий статусов`);
                // Перерисовываем доску с исправленными данными
                this.renderKanbanBoard(this.tasksData);
            }
        }
    }

    /**
     * Обновление статистик Kanban доски
     */
    updateKanbanStats(tasks) {
        console.log('[KanbanManager] 📊 Обновление статистик Kanban');

        // Подсчитываем активные задачи (не закрытые)
        const activeTasks = tasks.filter(task => !this.isStatusClosed(task.status_name));

        // Подсчитываем задачи, завершенные сегодня
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const completedToday = tasks.filter(task => {
            if (!this.isStatusClosed(task.status_name)) return false;
            const updatedDate = new Date(task.updated_on);
            const updatedStr = updatedDate.toISOString().split('T')[0];
            return updatedStr === todayStr;
        });

        // Подсчитываем просроченные задачи (с due_date в прошлом)
        const overdueTasks = tasks.filter(task => {
            if (!task.due_date) return false;
            const dueDate = new Date(task.due_date);
            const now = new Date();
            return dueDate < now && !this.isStatusClosed(task.status_name);
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

        console.log('[KanbanManager] ✅ Статистики обновлены:', {
            active: activeTasks.length,
            completedToday: completedToday.length,
            overdue: overdueTasks.length
        });
    }

    /**
     * Тестовая функция для проверки соответствия статусов
     */
    testStatusMapping() {
        console.log('[KanbanManager] 🧪 Тестирование соответствия статусов...');

        // Проверяем все колонки
        const allColumns = document.querySelectorAll('.kanban-column-content');
        console.log('[KanbanManager] 📋 Все колонки:');
        allColumns.forEach((col, index) => {
            const statusId = col.getAttribute('data-status-id');
            const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            console.log(`  ${index + 1}. ID: ${statusId}, Название: "${columnTitle}"`);
        });

        // Проверяем задачи в кэше
        if (this.tasksData && this.tasksData.length > 0) {
            console.log('[KanbanManager] 📋 Задачи в кэше:');
            this.tasksData.forEach((task, index) => {
                console.log(`  ${index + 1}. ID: ${task.id}, Статус: "${task.status_name}" (ID: ${task.status_id})`);
            });
        }

        // Проверяем соответствие
        console.log('[KanbanManager] 🔍 Проверка соответствия:');
        if (this.tasksData) {
            this.tasksData.forEach(task => {
                const targetColumn = document.querySelector(`[data-status-id="${task.status_id}"]`);
                const columnTitle = targetColumn?.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();

                if (targetColumn) {
                    console.log(`  ✅ Задача ${task.id}: "${task.status_name}" -> "${columnTitle}"`);
                } else {
                    console.log(`  ❌ Задача ${task.id}: "${task.status_name}" -> КОЛОНКА НЕ НАЙДЕНА`);
                }
            });
        }
    }

    // Публичные методы для интеграции с существующей системой
    refreshData() {
        console.log('[KanbanManager] 🔄 Обновление данных Kanban');
        this.clearCache(); // Очищаем кэш для принудительного обновления
        this.loadKanbanDataOptimized();
    }

    /**
     * Принудительное обновление данных с индикатором загрузки
     */
    async forceRefresh() {
        console.log('[KanbanManager] 🔄 Принудительное обновление данных Kanban');

        // Показываем индикатор загрузки
        this.showKanbanLoading();
        this.isLoading = true;

        try {
            // Очищаем кэш
            this.clearCache();

            // Загружаем данные заново
            await this.loadKanbanDataOptimized();

            console.log('[KanbanManager] ✅ Принудительное обновление завершено');

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
            hasCompletedTasks: !!this.cache.completedTasks,
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
            console.log('[KanbanManager] 🎯 Инициализация drag & drop');

            // Находим все карточки задач
            const cards = document.querySelectorAll('.kanban-card');
            const dropZones = document.querySelectorAll('.kanban-column-content');

            // Добавляем обработчики для карточек
            cards.forEach(card => {
                card.setAttribute('draggable', true);
                card.addEventListener('dragstart', this.handleDragStart.bind(this));
                card.addEventListener('dragend', this.handleDragEnd.bind(this));
            });

            // Добавляем обработчики для зон сброса
            dropZones.forEach(zone => {
                zone.addEventListener('dragover', this.handleDragOver.bind(this));
                zone.addEventListener('dragenter', this.handleDragEnter.bind(this));
                zone.addEventListener('dragleave', this.handleDragLeave.bind(this));
                zone.addEventListener('drop', this.handleDrop.bind(this));
            });

            console.log('[KanbanManager] ✅ Drag & drop инициализирован');
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка инициализации drag & drop:', error);
        }
    }

    /**
     * Обработка начала перетаскивания
     */
    handleDragStart(event) {
        try {
            console.log('[KanbanManager] 🎯 handleDragStart вызван');
            console.log('[KanbanManager] 📋 event.target:', event.target);
            console.log('[KanbanManager] 📋 event.target.tagName:', event.target.tagName);
            console.log('[KanbanManager] 📋 event.target.className:', event.target.className);

            // Ищем ближайший элемент с data-task-id (карточка задачи)
            const taskCard = event.target.closest('[data-task-id]');
            console.log('[KanbanManager] 📋 taskCard найден:', taskCard);

            const taskId = taskCard ? taskCard.getAttribute('data-task-id') : null;
            console.log('[KanbanManager] 📋 taskId:', taskId);

            if (!taskId) {
                console.error('[KanbanManager] ❌ Не удалось найти ID задачи для перетаскивания');
                console.error('[KanbanManager] 📋 event.target:', event.target);
                console.error('[KanbanManager] 📋 event.target.closest("[data-task-id]"):', event.target.closest('[data-task-id]'));
                event.preventDefault();
                return;
            }

            const taskTitle = taskCard.querySelector('.kanban-card-subject')?.textContent || `Задача #${taskId}`;

            console.log('[KanbanManager] 📋 Устанавливаем dataTransfer...');
            event.dataTransfer.setData('text/plain', taskId);
            event.dataTransfer.setData('text/html', taskTitle);
            event.dataTransfer.effectAllowed = 'move';

            taskCard.classList.add('dragging');

            // Показываем подсказку
            this.showNotification(`Перетаскивание: ${taskTitle}`, 'info');

            console.log(`[KanbanManager] 🎯 Начало перетаскивания задачи #${taskId}: ${taskTitle}`);
            console.log(`[KanbanManager] 📋 DataTransfer установлен: text/plain = "${taskId}"`);
        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка в handleDragStart:', error);
            event.preventDefault();
        }
    }

    /**
     * Обработка окончания перетаскивания
     */
    handleDragEnd(event) {
        event.target.classList.remove('dragging');
        console.log('[KanbanManager] ✅ Перетаскивание завершено');
    }

    /**
     * Обработка перетаскивания над зоной
     */
    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('drag-over');
    }

    /**
     * Обработка входа в зону перетаскивания
     */
    handleDragEnter(event) {
        event.currentTarget.classList.add('drag-over');
    }

    /**
     * Обработка выхода из зоны перетаскивания
     */
    handleDragLeave(event) {
        event.currentTarget.classList.remove('drag-over');
    }

    /**
     * Обработка сброса задачи
     */
    async handleDrop(event) {
        console.log('[KanbanManager] 🎯 handleDrop вызван');
        console.log('[KanbanManager] 📋 event.dataTransfer:', event.dataTransfer);
        console.log('[KanbanManager] 📋 event.dataTransfer.types:', event.dataTransfer.types);

        event.preventDefault();
        const dropZone = event.currentTarget;
        const taskId = event.dataTransfer.getData('text/plain');
        const newStatusId = dropZone.getAttribute('data-status-id');

        console.log('[KanbanManager] 📋 taskId из dataTransfer:', taskId);
        console.log('[KanbanManager] 📋 newStatusId из dropZone:', newStatusId);

        // Проверяем, что получили корректные данные
        if (!taskId) {
            console.error('[KanbanManager] ❌ Не удалось получить ID задачи из dataTransfer');
            console.error('[KanbanManager] 📋 event.dataTransfer.types:', event.dataTransfer.types);
            console.error('[KanbanManager] 📋 Попытка получить text/html:', event.dataTransfer.getData('text/html'));
            this.showErrorMessage('Ошибка: не удалось определить задачу для перемещения');
            return;
        }

        if (!newStatusId) {
            console.error('[KanbanManager] ❌ Не удалось получить ID статуса из dropZone');
            this.showErrorMessage('Ошибка: не удалось определить целевой статус');
            return;
        }

        // Получаем название нового статуса из заголовка колонки
        const columnTitle = dropZone.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim() || 'Неизвестный статус';

        console.log(`[KanbanManager] 🎯 Сброс задачи #${taskId} в статус ${newStatusId} (${columnTitle})`);
        console.log(`[KanbanManager] 📋 DataTransfer получен: text/plain = "${taskId}"`);

        // Убираем визуальные эффекты
        dropZone.classList.remove('drag-over');

        // Показываем индикатор загрузки
        const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskCard) {
            taskCard.classList.add('updating');
            this.showUpdateIndicator(taskCard);
        }

        try {
            // Обновляем статус задачи в Redmine
            const success = await this.updateTaskStatus(taskId, newStatusId);
            console.log(`[KanbanManager] 📋 Результат updateTaskStatus для задачи #${taskId}:`, success);

            if (success) {
                console.log(`[KanbanManager] ✅ Обновление статуса успешно, перемещаем карточку`);
                // Перемещаем карточку в новую колонку с анимацией
                if (taskCard) {
                    // Находим правильную колонку для нового статуса
                    const targetColumn = document.querySelector(`[data-status-id="${newStatusId}"]`);

                    if (targetColumn) {
                        console.log(`[KanbanManager] 🎯 Перемещаем карточку в правильную колонку для статуса ${newStatusId}`);

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
                        console.log(`[KanbanManager] ✅ Задача #${taskId} перемещена в статус ${newStatusId} (${columnTitle})`);

                        // Обновляем данные задачи в локальном кэше
                        this.updateTaskInCache(taskId, newStatusId, columnTitle);

                        // Проверяем, что карточка действительно переместилась
                        setTimeout(() => {
                            const movedCard = document.querySelector(`[data-task-id="${taskId}"]`);
                            if (movedCard && movedCard.closest(`[data-status-id="${newStatusId}"]`)) {
                                console.log(`[KanbanManager] ✅ Карточка #${taskId} успешно перемещена в колонку ${newStatusId}`);
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

                    // Если задача перемещена в закрытый статус, обновляем только завершенные задачи
                    const closedStatusIds = [5, 6, 14]; // ID закрытых статусов: Закрыта, Отклонена, Перенаправлена
                    if (closedStatusIds.includes(parseInt(newStatusId))) {
                        console.log(`[KanbanManager] 🔄 Обновление завершенных задач после перемещения в закрытый статус ${newStatusId}`);
                        setTimeout(() => {
                            this.loadCompletedTasks();
                        }, 1000);
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
        }
    }

    /**
     * Обновление статуса задачи в Redmine
     */
    async updateTaskStatus(taskId, newStatusId) {
        // Проверяем, не выполняется ли уже обновление для этой задачи
        const updateKey = `updating_${taskId}`;
        if (this[updateKey]) {
            console.log(`[KanbanManager] ⚠️ Обновление задачи #${taskId} уже выполняется, ждем завершения...`);
            // Ждем завершения текущего обновления
            while (this[updateKey]) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            console.log(`[KanbanManager] ✅ Предыдущее обновление задачи #${taskId} завершено`);
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
                console.log(`[KanbanManager] 📋 Ответ сервера для задачи #${taskId}:`, result);
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
                console.log(`[KanbanManager] ✅ Статус задачи #${taskId} обновлён в Redmine`);
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
        console.log(`[KanbanManager] 🎯 Перемещение карточки в зону:`, targetZone);

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

            console.log(`[KanbanManager] ✅ Карточка перемещена в новую колонку`);
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
            console.log('[KanbanManager] 📢 SUCCESS:', message);
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
            console.log(`[KanbanManager] 📢 ${type.toUpperCase()}: ${message}`);
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

            if (countElement) {
                countElement.textContent = taskCards.length;
            }
        });
    }

    /**
     * Оптимизированная загрузка статусов с кэшированием
     */
    async loadStatusesOptimized() {
        // Проверяем кэш статусов
        if (this.cache.statuses && this.isCacheValid()) {
            console.log('[KanbanManager] 📦 Используем кэшированные статусы');
            return this.cache.statuses;
        }

        try {
            console.log('[KanbanManager] 📡 Загрузка статусов...');
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

            console.log('[KanbanManager] ✅ Статусы загружены:', statuses.data.length);
            console.log('[KanbanManager] 📋 Детали статусов:', statuses.data);
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
        console.log('[KanbanManager] 🔄 Принудительное обновление порядка колонок...');

        // Пересоздаем колонки в нужном порядке
        this.createDynamicColumns().then(() => {
            // Перезагружаем данные
            this.loadKanbanDataOptimized().then(() => {
                console.log('[KanbanManager] ✅ Порядок колонок обновлен');
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
        console.log('[KanbanManager] 🚀 Инициализация...');

        // Создаем экземпляр KanbanManager
        window.kanbanManager = new KanbanManager();

        // Инициализируем менеджер
        window.kanbanManager.init();

        console.log('[KanbanManager] ✅ Инициализация завершена');

    } catch (error) {
        console.error('[KanbanManager] ❌ Ошибка инициализации:', error);
    }
}

// Запускаем инициализацию
initKanbanManager();
