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
        this.completedTasksLoaded = false;

        // Определяем колонки Kanban
        this.columns = [
            { id: 'new-column', name: 'Новые', icon: 'fas fa-plus-circle' },
            { id: 'in-progress-column', name: 'В работе', icon: 'fas fa-cog' },
            { id: 'testing-column', name: 'На тестировании', icon: 'fas fa-flask' },
            { id: 'completed-column', name: 'Завершённые', icon: 'fas fa-check-circle' }
        ];

        this.init();
    }

    init() {
        console.log('[KanbanManager] 🚀 Инициализация Kanban менеджера');

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
            console.log('[KanbanManager] ✅ Инициализация завершена');
        }).catch(error => {
            console.error('[KanbanManager] ❌ Ошибка инициализации:', error);
        });
    }

    setupEventListeners() {
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

            // Обработка кликов по карточкам задач - убрано, так как детали открываются только по клику на номер
            // if (e.target.closest('.kanban-card')) {
            //     const card = e.target.closest('.kanban-card');
            //     const taskId = card.dataset.taskId;
            //     if (taskId) {
            //         console.log('[KanbanManager] 🔗 Клик по карточке задачи:', taskId);
            //         this.openTaskDetails(taskId);
            //     }
            // }
        });

        // Обработка фильтров
        this.setupFilterListeners();

        console.log('[KanbanManager] ✅ Обработчики событий настроены');
    }

    setupFilterListeners() {
        // Слушаем изменения в фильтрах
        const filterSelects = ['status-filter', 'project-filter', 'priority-filter'];

        filterSelects.forEach(filterId => {
            const select = document.getElementById(filterId);
            if (select) {
                select.addEventListener('change', () => {
                    this.updateFilters();
                    if (this.currentView === 'kanban') {
                        this.loadKanbanData();
                    }
                });
            }
        });
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
            this.loadKanbanData();
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
     * Загрузка данных для Kanban
     */
    async loadKanbanData() {
        console.log('[KanbanManager] 📊 Загрузка данных для Kanban');

        try {
            // Загружаем задачи для Kanban доски с специальной логикой
            // Убираем exclude_completed=1 чтобы включить все задачи
            const response = await fetch('/tasks/get-my-tasks-paginated?length=1000&start=0&force_load=1&view=kanban');

            console.log('[KanbanManager] 📡 Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            console.log('[KanbanManager] 📋 Полные данные ответа:', data);

            if (!data.success && data.error) {
                throw new Error(data.error);
            }

            // Извлекаем задачи из ответа DataTables
            const tasks = data.data || [];

            // Фильтруем задачи для Kanban: показываем активные + "Запрошено уточнение"
            const filteredTasks = tasks.filter(task => {
                const statusId = task.status_id;
                const statusName = task.status_name;

                // Включаем активные задачи (не закрытые)
                const isActive = !this.isStatusClosed(statusName);

                // Включаем задачи со статусом "Запрошено уточнение" (ID: 9)
                const isClarificationRequested = statusId === 9;

                return isActive || isClarificationRequested;
            });

            // Сохраняем отфильтрованные задачи в кэш
            this.tasksData = filteredTasks;

            console.log('[KanbanManager] ✅ Получено задач из API:', tasks.length);
            console.log('[KanbanManager] ✅ Отфильтровано для Kanban:', filteredTasks.length);
            console.log('[KanbanManager] 📋 Структура ответа:', {
                success: data.success,
                draw: data.draw,
                recordsTotal: data.recordsTotal,
                recordsFiltered: data.recordsFiltered,
                dataLength: data.data ? data.data.length : 0
            });

            if (tasks.length > 0) {
                console.log('[KanbanManager] 📋 Примеры данных задач:');
                console.log('Задача 1:', tasks[0]);
                console.log('Задача 2:', tasks[1]);
                console.log('Задача 3:', tasks[2]);

                // Проверяем структуру первой задачи
                const firstTask = tasks[0];
                console.log('[KanbanManager] 🔍 Анализ структуры первой задачи:');
                console.log('- ID:', firstTask.id);
                console.log('- Subject:', firstTask.subject);
                console.log('- Status:', firstTask.status_name);
                console.log('- Priority:', firstTask.priority_name);
                console.log('- Project:', firstTask.project_name);
                console.log('- Assigned to:', firstTask.assigned_to_name);
            } else {
                console.log('[KanbanManager] ⚠️ Нет задач для отображения');
            }

            // Создаем динамические колонки на основе статусов
            await this.createDynamicColumns();

            // Отрисовываем Kanban доску с отфильтрованными задачами
            this.renderKanbanBoard(filteredTasks);

            // Загружаем завершенные задачи
            this.loadCompletedTasksOnKanbanRender();

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка загрузки данных:', error);
            this.showError('Ошибка загрузки данных: ' + error.message);
        }
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

        // Ограничиваем количество задач в колонке "Закрыто"
        this.limitClosedTasks();
    }

    /**
     * Обновление счетчика конкретной колонки
     */
    updateColumnCount(columnElement) {
        const taskCards = columnElement.querySelectorAll('.kanban-card');
        const countElement = columnElement.parentElement.querySelector('.kanban-column-count');

        if (countElement) {
            countElement.textContent = taskCards.length;
        }
    }

        /**
     * Ограничение количества задач в колонке "Закрыто"
     */
    limitClosedTasks() {
        console.log('[KanbanManager] 🔒 Ограничение задач в колонке "Закрыто"...');

        const closedColumn = document.querySelector('[data-status-id="5"]');
        if (closedColumn) {
            const cards = closedColumn.querySelectorAll('.kanban-card');
            console.log(`[KanbanManager] 📊 Найдено ${cards.length} задач в колонке "Закрыто"`);

            if (cards.length > 5) {
                // Удаляем лишние карточки (оставляем только первые 5)
                for (let i = 5; i < cards.length; i++) {
                    cards[i].remove();
                    console.log(`[KanbanManager] 🗑️ Удалена лишняя карточка ${i + 1}`);
                }

                // Обновляем счетчик
                const countElement = closedColumn.parentElement.querySelector('.kanban-column-count');
                if (countElement) {
                    countElement.textContent = '5';
                }

                console.log('[KanbanManager] ✅ Колонка "Закрыто" ограничена до 5 задач');
            } else if (cards.length < 5) {
                console.log(`[KanbanManager] ⚠️ В колонке "Закрыто" только ${cards.length} задач, нужно загрузить больше`);
                // Попробуем загрузить больше завершенных задач
                this.loadMoreCompletedTasks();
            }
        } else {
            console.log('[KanbanManager] ⚠️ Колонка "Закрыто" не найдена');
        }
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

                // Берем первые 5 задач
                const tasksToAdd = data.data.slice(0, 5);

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
                    console.log('[KanbanManager] ✅ Добавлены дополнительные задачи в колонку "Закрыто"');
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
            const limitedTasks = data.data.slice(0, 5);
            console.log(`[KanbanManager] 📊 Ограничиваем до ${limitedTasks.length} последних задач`);

            // Очищаем все колонки с закрытыми статусами перед добавлением новых задач
            const closedStatusIds = [5, 6, 7, 14]; // Закрыта, Отклонена, Выполнена, Перенаправлена
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

        // Проверяем ограничение для колонки "Закрыто" (ID: 5)
        const statusId = task.status_id;
        if (statusId === 5) { // Колонка "Закрыто"
            const existingCards = columnElement.querySelectorAll('.kanban-card');
            if (existingCards.length >= 5) {
                console.log(`[KanbanManager] ⚠️ Колонка "Закрыто" уже содержит ${existingCards.length} задач, пропускаем задачу ${task.id}`);
                return;
            }
        }

        // Анализируем приоритет
        const priority = task.priority_name || 'Обычный';
        console.log(`[KanbanManager] 🏷️ Анализ приоритета: "${priority}" -> "${this.getPriorityClass(priority)}"`);

        const priorityClass = this.getPriorityClass(priority);

        if (!priority || priority === 'undefined') {
            console.log(`[KanbanManager] ⚠️ Неизвестный приоритет "${priority}" -> priority-normal (по умолчанию)`);
        }

        // Создаем HTML карточки (простая и компактная)
        const cardHtml = `
            <div class="kanban-card" data-task-id="${task.id}" data-priority="${priorityClass}" draggable="true">
                <div class="kanban-card-header">
                    <div class="kanban-card-id" onclick="event.stopPropagation(); window.open('/tasks/my-tasks/${task.id}', '_blank')" style="cursor: pointer; color: #2563eb;">#${task.id}</div>
                    <div class="kanban-card-priority">
                        <span class="priority-badge ${priorityClass}">${this.escapeHtml(priority)}</span>
                    </div>
                </div>
                <div class="kanban-card-content">
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
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'kanban-loading';
            loadingDiv.innerHTML = `
                <div class="loading-content">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Загрузка Kanban доски...</span>
                </div>
            `;
            kanbanBoard.appendChild(loadingDiv);
        }
    }

    hideKanbanLoading() {
        const loadingDiv = document.querySelector('.kanban-loading');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    showKanbanError(message) {
        const kanbanBoard = document.getElementById('kanban-board');
        if (kanbanBoard) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'kanban-error';
            errorDiv.innerHTML = `
                <div class="error-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${message}</span>
                    <button onclick="window.loadKanbanData()">Попробовать снова</button>
                </div>
            `;
            kanbanBoard.appendChild(errorDiv);
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
        console.error('[KanbanManager] ❌ Ошибка:', message);
        // Можно добавить отображение ошибки в UI
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
     * Динамическое создание колонок на основе статусов Redmine
     */
    async createDynamicColumns() {
        console.log('[KanbanManager] 🏗️ Создание динамических колонок');

        try {
            // Получаем список всех статусов из Redmine
            console.log('[KanbanManager] 📡 Запрос статусов к /tasks/get-my-tasks-statuses');
            const response = await fetch('/tasks/get-my-tasks-statuses');

            console.log('[KanbanManager] 📡 Ответ сервера:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[KanbanManager] ❌ HTTP ошибка:', errorText);
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const statuses = await response.json();
            console.log('[KanbanManager] 📋 Полный ответ API:', statuses);

            if (!statuses.success) {
                throw new Error(statuses.error || 'Не удалось получить статусы');
            }

            console.log('[KanbanManager] 📊 Полученные статусы:', statuses.data);

            // Создаём колонки для каждого статуса
            const kanbanColumns = document.getElementById('kanban-columns');
            if (!kanbanColumns) {
                throw new Error('Контейнер колонок Kanban не найден');
            }

            // Очищаем существующие колонки
            kanbanColumns.innerHTML = '';

            console.log('[KanbanManager] 🏗️ Создаем колонки для статусов:');
            statuses.data.forEach(status => {
                console.log(`  - ID: ${status.id}, Name: "${status.name}", is_closed: ${status.is_closed}`);
            });

            // Проверяем, есть ли статус "Закрыта" в полученных данных
            const closedStatus = statuses.data.find(s => s.name === 'Закрыта');
            if (closedStatus) {
                console.log(`[KanbanManager] ✅ Статус "Закрыта" найден: ID=${closedStatus.id}, is_closed=${closedStatus.is_closed}`);
            } else {
                console.warn('[KanbanManager] ⚠️ Статус "Закрыта" не найден в полученных данных');
                console.log('[KanbanManager] 📋 Все полученные статусы:');
                statuses.data.forEach(s => console.log(`  - "${s.name}" (ID: ${s.id})`));
            }

            // Создаём колонки для каждого статуса
            statuses.data.forEach((status, index) => {
                console.log(`[KanbanManager] 🏗️ Создание колонки: ID=${status.id}, Name="${status.name}"`);

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
                        <div class="kanban-column-content" data-status-id="${status.id}">
                            <!-- Задачи будут добавляться сюда -->
                        </div>
                    </div>
                `;

                kanbanColumns.insertAdjacentHTML('beforeend', columnHtml);
                console.log(`[KanbanManager] ✅ Колонка создана: data-status-id="${status.id}"`);
            });

            console.log('[KanbanManager] ✅ Динамические колонки созданы');

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка создания динамических колонок:', error);

            // Создаём fallback колонки
            console.log('[KanbanManager] 🔄 Создание fallback колонок');
            this.createFallbackColumns();
        }
    }

    /**
     * Создание fallback колонок при ошибке API
     */
    createFallbackColumns() {
        // Используем реальные статусы из API
        const fallbackStatuses = [
            {id: 1, name: 'Новая', is_closed: false},
            {id: 2, name: 'В работе', is_closed: false},
            {id: 5, name: 'Закрыта', is_closed: true},
            {id: 6, name: 'Отклонена', is_closed: true},
            {id: 7, name: 'Выполнена', is_closed: true},
            {id: 9, name: 'Запрошено уточнение', is_closed: false},
            {id: 10, name: 'Приостановлена', is_closed: false},
            {id: 13, name: 'Протестирована', is_closed: false},
            {id: 14, name: 'Перенаправлена', is_closed: true},
            {id: 15, name: 'На согласовании', is_closed: false},
            {id: 16, name: 'Заморожена', is_closed: false},
            {id: 17, name: 'Открыта', is_closed: false},
            {id: 18, name: 'На тестировании', is_closed: false},
            {id: 19, name: 'В очереди', is_closed: false}
        ];

        const kanbanColumns = document.getElementById('kanban-columns');
        if (!kanbanColumns) {
            console.error('[KanbanManager] ❌ Контейнер колонок не найден');
            return;
        }

        // Очищаем существующие колонки
        kanbanColumns.innerHTML = '';

        // Создаём fallback колонки
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
                    <div class="kanban-column-content" data-status-id="${status.id}">
                        <!-- Задачи будут добавляться сюда -->
                    </div>
                </div>
            `;

            kanbanColumns.insertAdjacentHTML('beforeend', columnHtml);
        });

        console.log('[KanbanManager] ✅ Fallback колонки созданы');
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
        const closedStatuses = [
            'Закрыта',
            'Отклонена',
            'Выполнена',
            'Перенаправлена'
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
            1: 'Новая',
            2: 'В работе',
            5: 'Закрыта',
            6: 'Отклонена',
            7: 'Выполнена',
            9: 'Запрошено уточнение',
            10: 'Приостановлена',
            13: 'Протестирована',
            14: 'Перенаправлена',
            15: 'На согласовании',
            16: 'Заморожена',
            17: 'Открыта',
            18: 'На тестировании',
            19: 'В очереди'
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
            1: 'Новая',
            2: 'В работе',
            5: 'Закрыта',
            6: 'Отклонена',
            7: 'Выполнена',
            9: 'Запрошено уточнение',
            10: 'Приостановлена',
            13: 'Протестирована',
            14: 'Перенаправлена',
            15: 'На согласовании',
            16: 'Заморожена',
            17: 'Открыта',
            18: 'На тестировании',
            19: 'В очереди'
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
        this.loadKanbanData();
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
        console.log('[KanbanManager] 🎯 Инициализация Drag & Drop');

        try {
            // Находим все карточки задач
            const taskCards = document.querySelectorAll('.kanban-card');
            const dropZones = document.querySelectorAll('.kanban-column-content');

            console.log(`[KanbanManager] 📊 Найдено карточек: ${taskCards.length}, зон сброса: ${dropZones.length}`);

            if (taskCards.length === 0) {
                console.warn('[KanbanManager] ⚠️ Карточки задач не найдены');
                return;
            }

            if (dropZones.length === 0) {
                console.warn('[KanbanManager] ⚠️ Зоны сброса не найдены');
                return;
            }

            // Создаем привязанные обработчики
            this.boundHandleDragStart = this.handleDragStart.bind(this);
            this.boundHandleDragEnd = this.handleDragEnd.bind(this);
            this.boundHandleDragOver = this.handleDragOver.bind(this);
            this.boundHandleDrop = this.handleDrop.bind(this);
            this.boundHandleDragEnter = this.handleDragEnter.bind(this);
            this.boundHandleDragLeave = this.handleDragLeave.bind(this);

            // Очищаем старые обработчики для карточек
            taskCards.forEach(card => {
                // Удаляем старые обработчики
                card.removeEventListener('dragstart', this.boundHandleDragStart);
                card.removeEventListener('dragend', this.boundHandleDragEnd);

                // Устанавливаем draggable и добавляем новые обработчики
                card.setAttribute('draggable', true);
                card.addEventListener('dragstart', this.boundHandleDragStart);
                card.addEventListener('dragend', this.boundHandleDragEnd);

                // Добавляем визуальную подсказку
                card.title = 'Перетащите для изменения статуса';
            });

            // Очищаем старые обработчики для зон сброса
            dropZones.forEach(zone => {
                // Удаляем старые обработчики
                zone.removeEventListener('dragover', this.boundHandleDragOver);
                zone.removeEventListener('drop', this.boundHandleDrop);
                zone.removeEventListener('dragenter', this.boundHandleDragEnter);
                zone.removeEventListener('dragleave', this.boundHandleDragLeave);

                // Добавляем новые обработчики
                zone.addEventListener('dragover', this.boundHandleDragOver);
                zone.addEventListener('drop', this.boundHandleDrop);
                zone.addEventListener('dragenter', this.boundHandleDragEnter);
                zone.addEventListener('dragleave', this.boundHandleDragLeave);

                // Добавляем визуальную подсказку
                zone.title = 'Перетащите задачу сюда для изменения статуса';
            });

            console.log('[KanbanManager] ✅ Drag & Drop инициализирован');
            this.showNotification('Drag & Drop активирован', 'info');

        } catch (error) {
            console.error('[KanbanManager] ❌ Ошибка инициализации Drag & Drop:', error);
            this.showErrorMessage('Ошибка инициализации Drag & Drop');
        }
    }

    /**
     * Обработка начала перетаскивания
     */
        handleDragStart(event) {
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

            if (success) {
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
                    } else {
                        console.warn(`[KanbanManager] ⚠️ Колонка для статуса ${newStatusId} не найдена`);
                        // Перемещаем в dropZone как fallback
                        this.moveCardWithAnimation(taskCard, dropZone);
                        this.updateColumnCounts();
                    }

                    // Обновляем счетчики колонок
                    this.updateColumnCounts();

                    // Если задача перемещена в закрытый статус, обновляем только завершенные задачи
                    const closedStatusIds = [5, 6, 7, 14]; // ID закрытых статусов: Закрыта, Отклонена, Выполнена, Перенаправлена
                    if (closedStatusIds.includes(parseInt(newStatusId))) {
                        console.log(`[KanbanManager] 🔄 Обновление завершенных задач после перемещения в закрытый статус ${newStatusId}`);
                        setTimeout(() => {
                            this.loadCompletedTasks();
                        }, 1000);
                    }
                }
            } else {
                // Возвращаем карточку на место при ошибке
                this.showErrorMessage(`Ошибка обновления задачи #${taskId}`);
                console.error(`[KanbanManager] ❌ Ошибка обновления статуса задачи #${taskId}`);
            }
        } catch (error) {
            this.showErrorMessage(`Ошибка сети при обновлении задачи #${taskId}`);
            console.error(`[KanbanManager] ❌ Ошибка сети:`, error);
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

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                console.log(`[KanbanManager] ✅ Статус задачи #${taskId} обновлён в Redmine`);
                return true;
            } else {
                console.error(`[KanbanManager] ❌ Ошибка обновления статуса: ${result.error}`);
                return false;
            }
        } catch (error) {
            console.error(`[KanbanManager] ❌ Ошибка запроса обновления статуса:`, error);
            return false;
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
        this.showNotification(message, 'success');
    }

    /**
     * Показать сообщение об ошибке
     */
    showErrorMessage(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Показать уведомление
     */
    showNotification(message, type = 'info') {
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
}

// Инициализация при загрузке страницы
function initKanbanManager() {
    console.log('[KanbanManager] 🚀 Попытка инициализации...');

    // Проверяем, что DOM готов
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('[KanbanManager] 📄 DOM готов, инициализируем...');
            window.kanbanManager = new KanbanManager();
        });
    } else {
        console.log('[KanbanManager] 📄 DOM уже готов, инициализируем сразу...');
        window.kanbanManager = new KanbanManager();
    }

    // Добавляем глобальные методы для доступа
    window.loadKanbanData = function() {
        if (window.kanbanManager) {
            window.kanbanManager.loadKanbanData();
        } else {
            console.error('[KanbanManager] ❌ KanbanManager не инициализирован');
        }
    };

    window.loadCompletedTasks = function() {
        if (window.kanbanManager) {
            window.kanbanManager.loadCompletedTasks();
        } else {
            console.error('[KanbanManager] ❌ KanbanManager не инициализирован');
        }
    };

    // Глобальные функции для тестирования
    window.testKanbanStatuses = function() {
        if (window.kanbanManager) {
            window.kanbanManager.testStatusMapping();
        } else {
            console.error('KanbanManager не инициализирован');
        }
    };

    window.debugKanbanColumns = function() {
        const allColumns = document.querySelectorAll('.kanban-column-content');
        console.log('🔍 Все колонки Kanban:');
        allColumns.forEach((col, index) => {
            const statusId = col.getAttribute('data-status-id');
            const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            console.log(`  ${index + 1}. ID: ${statusId}, Название: "${columnTitle}"`);
        });
    };

    window.debugKanbanCards = function() {
        const allCards = document.querySelectorAll('.kanban-card');
        console.log('🎴 Все карточки задач:');
        allCards.forEach((card, index) => {
            const taskId = card.getAttribute('data-task-id');
            const priority = card.getAttribute('data-priority');
            const subject = card.querySelector('.kanban-card-subject')?.textContent?.trim();
            console.log(`  ${index + 1}. ID: ${taskId}, Приоритет: ${priority}, Название: "${subject}"`);
        });
    };

        window.testDragAndDrop = function() {
        console.log('🧪 Тестирование Drag & Drop...');

        // Проверяем карточки
        const allCards = document.querySelectorAll('.kanban-card');
        console.log(`📊 Найдено карточек: ${allCards.length}`);

        allCards.forEach((card, index) => {
            const taskId = card.getAttribute('data-task-id');
            const draggable = card.getAttribute('draggable');
            console.log(`  Карточка ${index + 1}: ID=${taskId}, draggable=${draggable}`);
        });

        // Проверяем зоны сброса
        const allDropZones = document.querySelectorAll('.kanban-column-content');
        console.log(`📊 Найдено зон сброса: ${allDropZones.length}`);

        allDropZones.forEach((zone, index) => {
            const statusId = zone.getAttribute('data-status-id');
            const columnTitle = zone.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            console.log(`  Зона ${index + 1}: statusId=${statusId}, название="${columnTitle}"`);
        });
    };

    window.testDragStart = function() {
        console.log('🧪 Тестирование dragstart события...');

        const firstCard = document.querySelector('.kanban-card');
        if (firstCard) {
            console.log('📋 Создаем событие dragstart для первой карточки');
            const dragEvent = new DragEvent('dragstart', {
                bubbles: true,
                cancelable: true,
                dataTransfer: new DataTransfer()
            });
            firstCard.dispatchEvent(dragEvent);
        } else {
            console.error('❌ Карточки не найдены');
        }
    };

        window.testDragEvent = function() {
        console.log('🧪 Тестирование drag события...');

        const firstCard = document.querySelector('.kanban-card');
        const firstZone = document.querySelector('.kanban-column-content');

        if (firstCard && firstZone) {
            console.log('📋 Создаем событие drop');
            const dropEvent = new DragEvent('drop', {
                bubbles: true,
                cancelable: true,
                dataTransfer: new DataTransfer()
            });

            // Устанавливаем данные в dataTransfer
            dropEvent.dataTransfer.setData('text/plain', firstCard.getAttribute('data-task-id'));

            firstZone.dispatchEvent(dropEvent);
        } else {
            console.error('❌ Карточки или зоны сброса не найдены');
        }
    };

            window.testAccordion = function() {
        console.log('🧪 Тестирование аккордеона колонок...');

        const allColumns = document.querySelectorAll('.kanban-column');
        console.log(`📊 Найдено колонок: ${allColumns.length}`);

        allColumns.forEach((column, index) => {
            const isCollapsed = column.classList.contains('collapsed');
            const title = column.querySelector('.kanban-column-title')?.textContent?.trim();
            console.log(`  Колонка ${index + 1}: "${title}", collapsed=${isCollapsed}`);
        });

        // Тестируем сворачивание первой колонки
        const firstColumn = allColumns[0];
        if (firstColumn) {
            console.log('📋 Сворачиваем первую колонку');
            firstColumn.classList.toggle('collapsed');
        }
    };

        window.debugTaskStatus = function() {
        console.log('🔍 Отладка статусов задач и колонок...');

        // Показываем все колонки
        const allColumns = document.querySelectorAll('.kanban-column-content');
        console.log('📋 Все колонки:');
        allColumns.forEach((col, index) => {
            const statusId = col.getAttribute('data-status-id');
            const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            const taskCount = col.querySelectorAll('.kanban-card').length;
            console.log(`  ${index + 1}. ID=${statusId}, Название="${columnTitle}", Задач=${taskCount}`);
        });

        // Показываем все задачи
        const allTasks = document.querySelectorAll('.kanban-card');
        console.log('📋 Все задачи:');
        allTasks.forEach((task, index) => {
            const taskId = task.getAttribute('data-task-id');
            const priority = task.getAttribute('data-priority');
            const column = task.closest('.kanban-column-content');
            const columnTitle = column?.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            console.log(`  ${index + 1}. ID=${taskId}, Приоритет=${priority}, Колонка="${columnTitle}"`);
        });

        // Проверяем задачу "Запрошено уточнение"
        const clarificationTasks = Array.from(allTasks).filter(task => {
            const column = task.closest('.kanban-column-content');
            const columnTitle = column?.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            return columnTitle && columnTitle.includes('Запрошено уточнение');
        });

        console.log(`🔍 Задач в статусе "Запрошено уточнение": ${clarificationTasks.length}`);
        clarificationTasks.forEach((task, index) => {
            const taskId = task.getAttribute('data-task-id');
            console.log(`  ${index + 1}. Задача #${taskId}`);
        });
    };

        window.findTaskById = function(taskId) {
        console.log(`🔍 Поиск задачи #${taskId}...`);

        const task = document.querySelector(`[data-task-id="${taskId}"]`);
        if (task) {
            const column = task.closest('.kanban-column-content');
            const columnTitle = column?.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
            const priority = task.getAttribute('data-priority');
            console.log(`✅ Задача #${taskId} найдена:`);
            console.log(`  - Колонка: "${columnTitle}"`);
            console.log(`  - Приоритет: ${priority}`);
            console.log(`  - Элемент:`, task);
        } else {
            console.log(`❌ Задача #${taskId} не найдена на доске`);

            // Проверяем все колонки
            const allColumns = document.querySelectorAll('.kanban-column-content');
            console.log('📋 Проверяем все колонки:');
            allColumns.forEach((col, index) => {
                const statusId = col.getAttribute('data-status-id');
                const columnTitle = col.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                const taskCount = col.querySelectorAll('.kanban-card').length;
                console.log(`  ${index + 1}. ID=${statusId}, Название="${columnTitle}", Задач=${taskCount}`);
            });
        }
    };

        window.testLoadAllTasks = async function() {
        console.log('🔍 Тестирование загрузки всех задач без фильтров...');

        try {
            // Загружаем все задачи без фильтров
            const response = await fetch('/tasks/get-my-tasks-paginated?length=1000&start=0&force_load=1&view=kanban');

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('📋 Ответ API (все задачи):', data);

            if (data.success && data.data) {
                console.log(`✅ Получено задач: ${data.data.length}`);

                // Ищем задачу #258367
                const targetTask = data.data.find(task => task.id == 258367);
                if (targetTask) {
                    console.log('✅ Задача #258367 найдена в API:');
                    console.log('  - ID:', targetTask.id);
                    console.log('  - Subject:', targetTask.subject);
                    console.log('  - Status:', targetTask.status_name);
                    console.log('  - Status ID:', targetTask.status_id);
                    console.log('  - Priority:', targetTask.priority_name);
                    console.log('  - Project:', targetTask.project_name);
                    console.log('  - Assigned to:', targetTask.assigned_to_name);
                } else {
                    console.log('❌ Задача #258367 не найдена в API');

                    // Показываем все задачи для анализа
                    console.log('📋 Все задачи в API:');
                    data.data.forEach((task, index) => {
                        console.log(`${index + 1}. ID=${task.id}, Статус="${task.status_name}", StatusID=${task.status_id}`);
                    });
                }
            } else {
                console.log('❌ Ошибка в ответе API:', data);
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки:', error);
        }
    };

        window.testLoadTasksWithParams = async function() {
        console.log('🔍 Тестирование загрузки задач с разными параметрами...');

        const testParams = [
            { name: 'Без фильтров', params: 'length=1000&start=0&force_load=1&view=kanban' },
            { name: 'С exclude_completed=0', params: 'length=1000&start=0&exclude_completed=0&force_load=1&view=kanban' },
            { name: 'С exclude_completed=1', params: 'length=1000&start=0&exclude_completed=1&force_load=1&view=kanban' },
            { name: 'Только активные', params: 'length=1000&start=0&exclude_completed=1&force_load=1&view=kanban&status=9' }
        ];

        for (const test of testParams) {
            console.log(`\n📋 Тест: ${test.name}`);
            try {
                const response = await fetch(`/tasks/get-my-tasks-paginated?${test.params}`);
                const data = await response.json();

                if (data.success && data.data) {
                    console.log(`✅ Получено задач: ${data.data.length}`);

                    // Ищем задачу #258367
                    const targetTask = data.data.find(task => task.id == 258367);
                    if (targetTask) {
                        console.log(`✅ Задача #258367 найдена в "${test.name}":`);
                        console.log(`  - Статус: "${targetTask.status_name}" (ID: ${targetTask.status_id})`);
                    } else {
                        console.log(`❌ Задача #258367 не найдена в "${test.name}"`);
                    }
                } else {
                    console.log(`❌ Ошибка в "${test.name}":`, data);
                }
            } catch (error) {
                console.error(`❌ Ошибка в "${test.name}":`, error);
            }
        }
    };

                window.forceRefreshStyles = function() {
        console.log('🔄 Принудительное обновление стилей...');

        // Обновляем все приоритеты
        const priorityBadges = document.querySelectorAll('.priority-badge');
        console.log(`📊 Найдено ${priorityBadges.length} приоритетов для обновления`);

        priorityBadges.forEach((badge, index) => {
            const priority = badge.textContent;
            console.log(`🔍 Приоритет ${index + 1}: "${priority}"`);

            badge.className = 'priority-badge';

            if (priority.toLowerCase().includes('срочный') || priority.toLowerCase().includes('urgent') || priority.toLowerCase().includes('высокий') || priority.toLowerCase().includes('high')) {
                badge.classList.add('priority-high');
                badge.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
                badge.style.color = 'white';
                console.log(`🔴 Приоритет "${priority}" -> КРАСНЫЙ`);
            } else if (priority.toLowerCase().includes('низкий') || priority.toLowerCase().includes('low')) {
                badge.classList.add('priority-low');
                badge.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                badge.style.color = 'white';
                console.log(`🟢 Приоритет "${priority}" -> ЗЕЛЕНЫЙ`);
            } else {
                badge.classList.add('priority-normal');
                badge.style.background = 'linear-gradient(135deg, #3b82f6, #2563eb)';
                badge.style.color = 'white';
                console.log(`🔵 Приоритет "${priority}" -> СИНИЙ`);
            }
        });

        console.log(`✅ Обновлено ${priorityBadges.length} приоритетов`);
    };

        window.limitClosedTasks = function() {
        console.log('🔒 Ограничение задач в колонке "Закрыто"...');

        const closedColumn = document.querySelector('[data-status-id="5"]');
        if (closedColumn) {
            const cards = closedColumn.querySelectorAll('.kanban-card');
            console.log(`📊 Найдено ${cards.length} задач в колонке "Закрыто"`);

            if (cards.length > 5) {
                // Удаляем лишние карточки (оставляем только первые 5)
                for (let i = 5; i < cards.length; i++) {
                    cards[i].remove();
                    console.log(`🗑️ Удалена лишняя карточка ${i + 1}`);
                }

                // Обновляем счетчик
                const countElement = closedColumn.parentElement.querySelector('.kanban-column-count');
                if (countElement) {
                    countElement.textContent = '5';
                }

                console.log('✅ Колонка "Закрыто" ограничена до 5 задач');
            } else if (cards.length < 5) {
                console.log(`⚠️ В колонке "Закрыто" только ${cards.length} задач, нужно загрузить больше`);
                // Попробуем загрузить больше завершенных задач
                window.kanbanManager.loadMoreCompletedTasks();
            }
        } else {
            console.log('⚠️ Колонка "Закрыто" не найдена');
        }
    };

                window.applyAllFixes = function() {
        console.log('🔧 Применение всех исправлений...');

        // 1. Обновляем стили приоритетов
        forceRefreshStyles();

        // 2. Ограничиваем задачи в колонке "Закрыто"
        limitClosedTasks();

        // 3. Принудительно обновляем высоту колонок
        const collapsedColumns = document.querySelectorAll('.kanban-column.collapsed');
        collapsedColumns.forEach(column => {
            column.style.minHeight = 'auto';
            column.style.height = 'auto';
        });

        // 4. Исправляем drag & drop
        fixDragAndDrop();

        console.log('✅ Все исправления применены');
    };

            window.fixDragAndDrop = function() {
        console.log('🎯 Исправление Drag & Drop...');

        // Принудительно устанавливаем draggable для всех карточек
        const cards = document.querySelectorAll('.kanban-card');
        console.log(`📊 Найдено ${cards.length} карточек для исправления`);

        cards.forEach((card, index) => {
            const taskId = card.getAttribute('data-task-id');
            card.setAttribute('draggable', 'true');
            card.style.cursor = 'grab';

            // Удаляем все старые обработчики
            const newCard = card.cloneNode(true);
            card.parentNode.replaceChild(newCard, card);

            // Добавляем простые обработчики для тестирования
            newCard.addEventListener('dragstart', function(e) {
                console.log(`🎯 Drag start для карточки ${taskId}`);
                e.dataTransfer.setData('text/plain', taskId);
                newCard.style.opacity = '0.5';
            });

            newCard.addEventListener('dragend', function(e) {
                console.log(`✅ Drag end для карточки ${taskId}`);
                newCard.style.opacity = '1';
            });

            console.log(`✅ Карточка ${taskId} настроена для drag & drop`);
        });

        // Настраиваем зоны сброса
        const dropZones = document.querySelectorAll('.kanban-column-content');
        console.log(`📊 Найдено ${dropZones.length} зон сброса`);

        dropZones.forEach((zone, index) => {
            // Удаляем старые обработчики
            const newZone = zone.cloneNode(true);
            zone.parentNode.replaceChild(newZone, zone);

            // Добавляем простые обработчики для тестирования
            newZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                newZone.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
            });

                        newZone.addEventListener('drop', function(e) {
                e.preventDefault();
                const taskId = e.dataTransfer.getData('text/plain');
                const statusId = newZone.getAttribute('data-status-id');
                console.log(`🎯 Drop задачи ${taskId} в зону ${index + 1} (статус: ${statusId})`);
                newZone.style.backgroundColor = '';

                // Находим карточку задачи
                const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
                if (taskCard) {
                    // Показываем индикатор загрузки
                    taskCard.classList.add('updating');

                    // Обновляем статус задачи
                    if (window.kanbanManager && window.kanbanManager.updateTaskStatus) {
                        window.kanbanManager.updateTaskStatus(taskId, statusId).then(success => {
                            if (success) {
                                // Перемещаем карточку в новую колонку
                                window.kanbanManager.moveCardWithAnimation(taskCard, newZone);

                                // Обновляем счетчики
                                window.kanbanManager.updateColumnCounts();

                                // Показываем уведомление об успехе
                                const columnTitle = newZone.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();
                                window.kanbanManager.showSuccessMessage(`Задача #${taskId} перемещена в статус "${columnTitle}"`);

                                console.log(`✅ Задача #${taskId} успешно перемещена в статус ${statusId}`);
                            } else {
                                // Возвращаем карточку на место при ошибке
                                window.kanbanManager.showErrorMessage(`Ошибка обновления задачи #${taskId}`);
                                console.error(`❌ Ошибка обновления статуса задачи #${taskId}`);
                            }

                            // Убираем индикатор загрузки
                            taskCard.classList.remove('updating');
                        });
                    }
                } else {
                    console.error(`❌ Карточка задачи ${taskId} не найдена`);
                }
            });

            newZone.addEventListener('dragenter', function(e) {
                e.preventDefault();
                newZone.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
            });

            newZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                newZone.style.backgroundColor = '';
            });

            console.log(`✅ Зона сброса ${index + 1} настроена`);
        });

        console.log('✅ Drag & Drop исправлен с простыми обработчиками');
    };

            window.checkCurrentState = function() {
        console.log('🔍 Проверка текущего состояния...');

        // Проверяем колонку "Закрыто"
        const closedColumn = document.querySelector('[data-status-id="5"]');
        if (closedColumn) {
            const cards = closedColumn.querySelectorAll('.kanban-card');
            console.log(`📊 Колонка "Закрыто": ${cards.length} задач`);
        }

        // Проверяем приоритеты
        const priorityBadges = document.querySelectorAll('.priority-badge');
        console.log(`🎨 Найдено ${priorityBadges.length} приоритетов:`);
        priorityBadges.forEach((badge, index) => {
            const text = badge.textContent;
            const classes = badge.className;
            const style = badge.style.background;
            console.log(`  ${index + 1}. "${text}" -> классы: "${classes}", стиль: "${style}"`);
        });

        // Проверяем сворачивание
        const collapsedColumns = document.querySelectorAll('.kanban-column.collapsed');
        console.log(`📏 Свернутых колонок: ${collapsedColumns.length}`);

        // Проверяем drag & drop
        const draggableCards = document.querySelectorAll('.kanban-card[draggable="true"]');
        const dropZones = document.querySelectorAll('.kanban-column-content');
        console.log(`🎯 Drag & Drop: ${draggableCards.length} перетаскиваемых карточек, ${dropZones.length} зон сброса`);

        return {
            closedTasks: closedColumn ? closedColumn.querySelectorAll('.kanban-card').length : 0,
            priorityBadges: priorityBadges.length,
            collapsedColumns: collapsedColumns.length,
            draggableCards: draggableCards.length,
            dropZones: dropZones.length
        };
    };

        window.diagnoseDragAndDrop = function() {
        console.log('🔍 Диагностика Drag & Drop...');

        // Проверяем все карточки
        const allCards = document.querySelectorAll('.kanban-card');
        console.log(`📊 Всего карточек: ${allCards.length}`);

        allCards.forEach((card, index) => {
            const draggable = card.getAttribute('draggable');
            const taskId = card.getAttribute('data-task-id');
            const cursor = card.style.cursor;

            console.log(`  Карточка ${index + 1}: ID=${taskId}, draggable=${draggable}, cursor=${cursor}`);
        });

        // Проверяем зоны сброса
        const allZones = document.querySelectorAll('.kanban-column-content');
        console.log(`📊 Всего зон сброса: ${allZones.length}`);

        allZones.forEach((zone, index) => {
            const statusId = zone.getAttribute('data-status-id');
            const columnTitle = zone.closest('.kanban-column')?.querySelector('.kanban-column-title')?.textContent?.trim();

            console.log(`  Зона ${index + 1}: statusId=${statusId}, title="${columnTitle}"`);
        });

        // Проверяем обработчики событий
        console.log('🔍 Проверка обработчиков событий...');

        const testCard = allCards[0];
        if (testCard) {
            const events = getEventListeners ? getEventListeners(testCard) : 'getEventListeners недоступен';
            console.log(`  Обработчики для первой карточки:`, events);
        }

        return {
            totalCards: allCards.length,
            totalZones: allZones.length,
            draggableCards: document.querySelectorAll('.kanban-card[draggable="true"]').length
        };
    };

    window.resetDragAndDrop = function() {
        console.log('🔄 Полный сброс и восстановление Drag & Drop...');

        // Удаляем все обработчики событий
        const allCards = document.querySelectorAll('.kanban-card');
        const allZones = document.querySelectorAll('.kanban-column-content');

        console.log(`🗑️ Удаляем обработчики с ${allCards.length} карточек и ${allZones.length} зон...`);

        // Клонируем и заменяем все карточки для удаления обработчиков
        allCards.forEach(card => {
            const newCard = card.cloneNode(true);
            card.parentNode.replaceChild(newCard, card);
        });

        // Клонируем и заменяем все зоны сброса
        allZones.forEach(zone => {
            const newZone = zone.cloneNode(true);
            zone.parentNode.replaceChild(newZone, zone);
        });

        console.log('✅ Все обработчики удалены');

        // Теперь применяем новый drag & drop
        setTimeout(() => {
            fixDragAndDrop();
        }, 100);

        return 'Drag & Drop сброшен и восстановлен';
    };

    window.findSpecificTask = async function(taskId = 258367) {
        console.log(`🔍 Поиск конкретной задачи #${taskId}...`);

        try {
            // Пробуем разные варианты запросов
            const queries = [
                { name: 'Прямой поиск по ID', url: `/tasks/api/task/${taskId}` },
                { name: 'Все задачи без фильтров', url: '/tasks/get-my-tasks-paginated?length=10000&start=0&force_load=1' },
                { name: 'Задачи с вашим ID', url: `/tasks/get-my-tasks-paginated?length=10000&start=0&force_load=1&assigned_to=${encodeURIComponent('Varslavan Yury')}` },
                { name: 'Задачи в статусе 9', url: '/tasks/get-my-tasks-paginated?length=10000&start=0&force_load=1&status=9' }
            ];

            for (const query of queries) {
                console.log(`\n📋 ${query.name}:`);
                try {
                    const response = await fetch(query.url);
                    const data = await response.json();

                                    if (data.success && data.data) {
                    // Проверяем, является ли data.data массивом или объектом
                    if (Array.isArray(data.data)) {
                        console.log(`✅ Получено задач: ${data.data.length}`);

                        // Ищем задачу в массиве
                        const targetTask = data.data.find(task => task.id == taskId);
                        if (targetTask) {
                            console.log(`✅ Задача #${taskId} найдена:`);
                            console.log(`  - ID: ${targetTask.id}`);
                            console.log(`  - Subject: ${targetTask.subject}`);
                            console.log(`  - Status: "${targetTask.status_name}" (ID: ${targetTask.status_id})`);
                            console.log(`  - Priority: ${targetTask.priority_name}`);
                            console.log(`  - Project: ${targetTask.project_name}`);
                            console.log(`  - Assigned to: ${targetTask.assigned_to_name}`);
                            console.log(`  - Created: ${targetTask.created_on}`);
                            console.log(`  - Updated: ${targetTask.updated_on}`);
                            return targetTask;
                        } else {
                            console.log(`❌ Задача #${taskId} не найдена в массиве`);
                        }
                    } else {
                        // data.data - это объект с одной задачей
                        console.log(`✅ Получена задача:`, data.data);

                        if (data.data.id == taskId) {
                            console.log(`✅ Задача #${taskId} найдена:`);
                            console.log(`  - ID: ${data.data.id}`);
                            console.log(`  - Subject: ${data.data.subject}`);
                            console.log(`  - Status: "${data.data.status_name}" (ID: ${data.data.status_id})`);
                            console.log(`  - Priority: ${data.data.priority_name}`);
                            console.log(`  - Project: ${data.data.project_name}`);
                            console.log(`  - Assigned to: ${data.data.assigned_to_name}`);
                            console.log(`  - Created: ${data.data.created_on}`);
                            console.log(`  - Updated: ${data.data.updated_on}`);
                            return data.data;
                        } else {
                            console.log(`❌ Задача #${taskId} не найдена (получена задача #${data.data.id})`);
                        }
                    }
                } else {
                    console.log(`❌ Ошибка API:`, data);
                }
                } catch (error) {
                    console.error(`❌ Ошибка запроса:`, error);
                }
            }

            console.log(`\n❌ Задача #${taskId} не найдена ни в одном запросе`);
            return null;

        } catch (error) {
            console.error('❌ Общая ошибка:', error);
            return null;
        }
    };

    window.expandAllColumns = function() {
        console.log('📋 Разворачиваем все колонки');
        const allColumns = document.querySelectorAll('.kanban-column');
        allColumns.forEach(column => column.classList.remove('collapsed'));
    };

    window.collapseAllColumns = function() {
        console.log('📋 Сворачиваем все колонки');
        const allColumns = document.querySelectorAll('.kanban-column');
        allColumns.forEach(column => column.classList.add('collapsed'));
    };
}

// Запускаем инициализацию
initKanbanManager();
