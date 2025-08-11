/**
 * Основное приложение для страницы "Мои задачи в Redmine"
 * Реализует все функции согласно документации tasks_my_tasks_documentation.md
 */

const MyTasksApp = {
    // Конфигурация
    config: {
        apiEndpoints: {
            tasks: '/tasks/get-my-tasks-paginated',
            statistics: '/tasks/get-my-tasks-statistics-optimized',
            filters: '/tasks/get-my-tasks-filters-optimized'
        },
        tableId: 'tasksTable',
        loadingSpinnerId: 'loading-spinner',
        defaultPageSize: 25
    },

    // Состояние приложения
    state: {
        isInitialized: false,
        dataTable: null,
        isReturn: false,          // Возврат со страницы детали?
        showSpinnerFirstLoad: true, // Нужно ли показывать спиннер при первой загрузке
        filtersLoaded: false,
        statisticsLoaded: false,
        currentFilters: {
            status: '',
            project: '',
            priority: ''
        }
    },

    // Инициализация приложения
    init: function() {
        console.log('🚀 Инициализация MyTasksApp');

        if (this.state.isInitialized) {
            console.log('⚠️ MyTasksApp уже инициализирован');
            return;
        }

        // Определяем, вернулся ли пользователь со страницы детали
        this.state.isReturn = sessionStorage.getItem('return_from_task_id') !== null;
        this.state.showSpinnerFirstLoad = !this.state.isReturn; // если возврат — спиннер не нужен

        console.log('🔄 Логика спиннера:', {
            isReturn: this.state.isReturn,
            showSpinnerFirstLoad: this.state.showSpinnerFirstLoad,
            returnId: sessionStorage.getItem('return_from_task_id')
        });

        // Спиннер уже управляется ранним скриптом в template
        // Здесь только логируем состояние

        this.initializeDataTable();
        this.loadFilters();
        this.loadStatistics();
        this.bindEventListeners();
        this.initializeTooltips();

        this.state.isInitialized = true;
        console.log('✅ MyTasksApp инициализирован успешно');
    },

    // Показать спинер загрузки
    showLoadingSpinner: function() {
        const spinner = document.getElementById(this.config.loadingSpinnerId);
        if (spinner) {
            console.log('🟢 Показываем спиннер');
            spinner.classList.add('show');
        } else {
            console.warn('⚠️ Спиннер не найден:', this.config.loadingSpinnerId);
        }
    },

    // Скрыть спинер загрузки
    hideLoadingSpinner: function() {
        const spinner = document.getElementById(this.config.loadingSpinnerId);
        if (spinner) {
            console.log('🔴 Скрываем спиннер');
            spinner.classList.remove('show');
        } else {
            console.warn('⚠️ Спиннер не найден:', this.config.loadingSpinnerId);
        }
    },

    // Инициализация DataTable
    initializeDataTable: function() {
        console.log('📊 Инициализация DataTable');

        // Проверяем наличие jQuery и DataTables
        if (typeof $ === "undefined" || typeof $.fn.dataTable === "undefined") {
            console.error('❌ jQuery или DataTables не загружены');
            console.error('jQuery available:', typeof $);
            console.error('DataTables available:', typeof $.fn?.dataTable);
            this.hideLoadingSpinner();
            this.showError('Ошибка инициализации: необходимые библиотеки не загружены. Перезагрузите страницу.');
            return;
        }

        const tableElement = document.getElementById(this.config.tableId);
        if (!tableElement) {
            console.error('❌ Таблица не найдена:', this.config.tableId);
            this.showError('Ошибка инициализации: таблица не найдена');
            return;
        }

        // Конфигурация DataTable
        const dataTableConfig = {
            processing: true,
            serverSide: true,
            ajax: {
                url: this.config.apiEndpoints.tasks,
                type: 'GET',
                data: (params) => {
                    // Добавляем параметры фильтрации
                    if (this.state.currentFilters.status) {
                        params.status_id = [this.state.currentFilters.status];
                    }
                    if (this.state.currentFilters.project) {
                        params.project_id = [this.state.currentFilters.project];
                    }
                    if (this.state.currentFilters.priority) {
                        params.priority_id = [this.state.currentFilters.priority];
                    }

                    console.log('📤 Параметры запроса DataTables:', params);
                    return params;
                },
                error: (xhr, error, code) => {
                    console.error('❌ Ошибка загрузки данных DataTables:', {xhr, error, code});
                    this.hideLoadingSpinner();
                    this.showError(`Ошибка загрузки данных: ${error}`);
                }
            },
            columns: [
                {
                    data: 'id',
                    name: 'id',
                    title: 'ID',
                    className: 'col-id-cell',
                    width: '70px',
                    responsivePriority: 1,
                    render: (data, type, row) => {
                        if (type === 'display') {
                            return `<div class="task-id-container">
                                        <a href="/tasks/my-tasks/${data}" class="task-id-link" target="_blank" rel="noopener noreferrer" title="Открыть задачу #${data} в новой вкладке">
                                            <span class="task-id-number">#${data}</span>
                                        </a>
                                    </div>`;
                        }
                        return data;
                    }
                },
                {
                    data: 'easy_email_to',
                    name: 'easy_email_to',
                    title: 'Email',
                    className: 'col-email-cell',
                    responsivePriority: 4,
                    render: (data) => {
                        if (!data || data === '-') {
                            return `<div class="email-container">
                                        <span class="email-placeholder">
                                            <i class="fas fa-envelope-open text-muted"></i>
                                            <span class="text-muted">Не указан</span>
                                        </span>
                                    </div>`;
                        }
                        const truncatedEmail = data.length > 25 ? data.substring(0, 25) + '...' : data;
                        const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data);

                        if (isValidEmail) {
                            return `<div class="email-container">
                                        <i class="fas fa-envelope text-primary"></i>
                                        <a href="mailto:${this.escapeHtml(data)}" class="email-link" title="Написать письмо: ${this.escapeHtml(data)}">
                                            <span class="email-text">${this.escapeHtml(truncatedEmail)}</span>
                                        </a>
                                    </div>`;
                        } else {
                            return `<div class="email-container">
                                        <i class="fas fa-envelope text-primary"></i>
                                        <span class="email-text" title="${this.escapeHtml(data)}">${this.escapeHtml(truncatedEmail)}</span>
                                    </div>`;
                        }
                    }
                },
                {
                    data: 'subject',
                    name: 'subject',
                    title: 'Тема задачи',
                    className: 'col-subject-cell',
                    responsivePriority: 2,
                    render: (data, type, row) => {
                        const subjectHtml = this.escapeHtml(data);
                        const projectHtml = this.escapeHtml(row.project_name || 'Без проекта');

                        // HTML-структура, которая соответствует CSS из 'tasks_modern_ui.css'
                        const taskTitleHtml = `<a class="task-title" href="/tasks/my-tasks/${row.id}" title="${subjectHtml}">${subjectHtml}</a>`;
                        const projectNameHtml = `<div class="project-name">
                                                   <i class="fas fa-folder-open"></i>
                                                   <span>${projectHtml}</span>
                                                 </div>`;

                        return `<div class="task-title-container">
                                    ${taskTitleHtml}
                                    ${projectNameHtml}
                                </div>`;
                    }
                },
                {
                    data: 'status_name',
                    name: 'status',
                    title: 'Статус',
                    className: 'col-status-cell',
                    responsivePriority: 3,
                    render: (data) => {
                        const statusInfo = this.getStatusInfo(data);
                        return `<div class="status-container">
                                    <div class="status-indicator-modern ${statusInfo.class}"
                                         data-status="${this.escapeHtml(data || 'N/A')}"
                                         title="${statusInfo.tooltip || this.escapeHtml(data || 'N/A')}">
                                        <div class="status-icon">
                                            <i class="${statusInfo.icon}"></i>
                                        </div>
                                        <span class="status-text">${this.escapeHtml(statusInfo.shortName || data || 'N/A')}</span>
                                        <div class="status-tooltip">${statusInfo.tooltip || this.escapeHtml(data || 'N/A')}</div>
                                    </div>
                                </div>`;
                    }
                },
                {
                    data: 'priority_name',
                    name: 'priority',
                    title: 'Приоритет',
                    className: 'col-priority-cell',
                    responsivePriority: 5,
                    render: (data) => {
                        const priorityInfo = this.getPriorityInfo(data);
                        return `<div class="priority-container">
                                    <span class="priority-badge-redesigned ${priorityInfo.class}">
                                        <i class="${priorityInfo.icon} priority-icon"></i>
                                        <span class="priority-text">${this.escapeHtml(data || 'N/A')}</span>
                                    </span>
                                </div>`;
                    }
                },
                {
                    data: 'created_on',
                    name: 'created_on',
                    title: 'Создана',
                    className: 'col-created-cell',
                    responsivePriority: 7,
                    render: (data) => {
                        return `<div class="date-container">
                                    <i class="fas fa-calendar-plus date-icon"></i>
                                    <span class="date-text">${this.formatDate(data)}</span>
                                </div>`;
                    }
                },
                {
                    data: 'updated_on',
                    name: 'updated_on',
                    title: 'Обновлена',
                    className: 'col-updated-cell',
                    responsivePriority: 6,
                    render: (data) => {
                        const formattedDateTime = this.formatDateTime(data);
                        const timezoneInfo = this.getTimezoneInfo();
                        const tooltipText = `Точное время последнего обновления: ${formattedDateTime}\nВременная зона: ${timezoneInfo.timezone} (UTC${timezoneInfo.offset})`;

                        return `<div class="date-container">
                                    <i class="fas fa-calendar-check date-icon"></i>
                                    <span class="date-text" title="${tooltipText}">${formattedDateTime}</span>
                                </div>`;
                    }
                }
            ],
            order: [[6, 'desc']], // Сортировка по дате обновления (убывание)
            pageLength: this.config.defaultPageSize,
            lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
            responsive: {
                details: {
                    display: $.fn.dataTable.Responsive.display.childRowImmediate,
                    type: 'none',
                    target: ''
                }
            },
            scrollX: false,
            autoWidth: false,
            columnDefs: [
                {
                    targets: '_all',
                    className: 'dt-body-nowrap'
                }
            ],
            language: {
                "processing": "🚀 Загрузка данных...",
                "search": "Поиск:",
                "lengthMenu": "Показать _MENU_ записей",
                "info": "Записи с _START_ до _END_ из _TOTAL_ записей",
                "infoEmpty": "Записи с 0 до 0 из 0 записей",
                "infoFiltered": "(отфильтровано из _MAX_ записей)",
                "infoPostFix": "",
                "loadingRecords": "Загрузка записей...",
                "zeroRecords": "Записи отсутствуют",
                "emptyTable": "В таблице отсутствуют данные",
                "paginate": {
                    "first": "Первая",
                    "previous": "Предыдущая",
                    "next": "Следующая",
                    "last": "Последняя"
                },
                "aria": {
                    "sortAscending": ": активировать для сортировки столбца по возрастанию",
                    "sortDescending": ": активировать для сортировки столбца по убыванию"
                },
                "select": {
                    "rows": {
                        "_": "Выбрано %d строк",
                        "0": "Кликните по строке для выбора",
                        "1": "Выбрана %d строка"
                    }
                }
            },
            drawCallback: () => {
                console.log('✅ DataTable перерисована');
            },
            initComplete: () => {
                console.log('✅ DataTable инициализирована');

                // Скрываем спиннер после полной инициализации
                this.hideLoadingSpinner();

                // Настраиваем плейсхолдер для поиска
                this.setupSearchPlaceholder();

                // Логируем информацию о временной зоне для отладки
                const timezoneInfo = this.getTimezoneInfo();
                console.log('🕐 Информация о временной зоне клиента:', timezoneInfo);
            }
        };

        /*
         * ⬅️ Восстановление страницы пагинации ещё до создания DataTable.
         */
        const savedPage = sessionStorage.getItem('return_from_task_page');
        if (savedPage !== null) {
            dataTableConfig.displayStart = parseInt(savedPage, 10) * this.config.defaultPageSize;
            dataTableConfig.processing = !this.state.isReturn;
        }

        // Инициализируем DataTable
        try {
            this.state.dataTable = $(tableElement).DataTable(dataTableConfig);
            console.log('✅ DataTable создана успешно');
        } catch (error) {
            console.error('❌ Ошибка создания DataTable:', error);
            this.hideLoadingSpinner();
            this.showError('Ошибка инициализации таблицы');
        }

        // После каждого draw управляем состоянием (подсветка строки + пагинация)
        $(tableElement).on('draw.dt', () => {
            this.highlightReturnRow(); // Восстанавливаем подсветку при возврате
            this.highlightPagination();
        });

        // Перехватываем клики по ссылкам задач, чтобы сохранить контекст (ID и страница)
        $(tableElement).on('click', '.task-id-link, .task-title', (e) => {
            const taskId = $(e.currentTarget).closest('tr').find('.task-id-number').text().replace('#','');
            sessionStorage.setItem('return_from_task_id', taskId);
            // Сохраняем текущую страницу DataTable
            const currentPage = this.state.dataTable.page();
            sessionStorage.setItem('return_from_task_page', currentPage);

            // Сохраняем текущий режим просмотра
            const currentView = document.querySelector('.view-toggle-btn.active')?.dataset.view || 'list';
            sessionStorage.setItem('return_from_task_view', currentView);
            console.log(`[MyTasksApp] 💾 Сохранен режим просмотра при переходе в детали: ${currentView}`);
        });
    },

    // Загрузка фильтров
    loadFilters: function() {
        console.log('🔄 Загрузка фильтров');

        fetch(this.config.apiEndpoints.filters)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('✅ Фильтры загружены:', data);
                this.populateFilters(data);
                this.state.filtersLoaded = true;
            })
            .catch(error => {
                console.error('❌ Ошибка загрузки фильтров:', error);
                this.showError('Ошибка загрузки фильтров');
            });
    },

    // Заполнение селектов фильтров
    populateFilters: function(data) {
        // Статусы
        if (data.statuses && Array.isArray(data.statuses)) {
            const statusSelect = document.getElementById('status-filter');
            if (statusSelect) {
                statusSelect.innerHTML = '<option value="">Все статусы</option>';
                data.statuses.forEach(status => {
                    const option = document.createElement('option');
                    option.value = status.id;
                    option.textContent = status.name;
                    statusSelect.appendChild(option);
                });
            }
        }

        // Проекты
        if (data.projects && Array.isArray(data.projects)) {
            const projectSelect = document.getElementById('project-filter');
            if (projectSelect) {
                projectSelect.innerHTML = '<option value="">Все проекты</option>';
                data.projects.forEach(project => {
                    const option = document.createElement('option');
                    option.value = project.id;
                    option.textContent = project.name;
                    projectSelect.appendChild(option);
                });
            }
        }

        // Приоритеты
        if (data.priorities && Array.isArray(data.priorities)) {
            const prioritySelect = document.getElementById('priority-filter');
            if (prioritySelect) {
                prioritySelect.innerHTML = '<option value="">Все приоритеты</option>';
                data.priorities.forEach(priority => {
                    const option = document.createElement('option');
                    option.value = priority.id;
                    option.textContent = priority.name;
                    prioritySelect.appendChild(option);
                });
            }
        }

        console.log('✅ Фильтры заполнены');
    },

    // Загрузка статистики
    loadStatistics: function() {
        console.log('🔄 Загрузка статистики');

        fetch(this.config.apiEndpoints.statistics)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('✅ Статистика загружена:', data);
                this.updateStatistics(data);
                this.state.statisticsLoaded = true;
            })
            .catch(error => {
                console.error('❌ Ошибка загрузки статистики:', error);
                this.showError('Ошибка загрузки статистики');
            });
    },

    // Обновление карточек статистики
    updateStatistics: function(data) {
        console.log('📊 Обновление статистики с данными:', data);

        // Обновляем основные значения
        this.updateElementText('total-tasks-summary', data.total_tasks || 0);
        this.updateElementText('total-tasks', data.total_tasks || 0);
        this.updateElementText('open-tasks', data.open_tasks || 0);
        this.updateElementText('completed-tasks', data.completed_tasks || 0);
        this.updateElementText('in-progress-tasks', data.in_progress_tasks || 0);

        // Обновляем детализацию для карточки "Всего задач"
        this.updateElementText('total-open', data.open_tasks || 0);
        this.updateElementText('total-in-progress', data.in_progress_tasks || 0);
        this.updateElementText('total-completed', data.completed_tasks || 0);

        // Обновляем детализацию статусов
        if (data.status_counts && data.detailed_breakdown) {
            this.updateDetailedStatistics(data.status_counts, data.detailed_breakdown);
        } else if (data.statistics && data.statistics.breakdown_details) {
            // Альтернативный формат данных
            this.updateDetailedStatisticsNew(data.statistics.breakdown_details, data.status_counts);
        }

        console.log('✅ Статистика обновлена');
    },

    // Обновление детализированной статистики (старый формат)
    updateDetailedStatistics: function(statusCounts, breakdown) {
        // Открытые задачи
        if (breakdown && breakdown.open_statuses) {
            this.populateStatusDetails('open-details-content', breakdown.open_statuses, statusCounts);
        }

        // Завершённые задачи (обратная совместимость)
        if (breakdown && breakdown.closed_statuses) {
            this.populateStatusDetails('completed-details-content', breakdown.closed_statuses, statusCounts);
        }

        // В работе (обратная совместимость)
        if (breakdown && breakdown.paused_statuses) {
            this.populateStatusDetails('in-progress-details-content', breakdown.paused_statuses, statusCounts);
        }

        // Новый формат
        if (breakdown && breakdown.completed_statuses) {
            this.populateStatusDetails('completed-details-content', breakdown.completed_statuses, statusCounts);
        }

        if (breakdown && breakdown.in_progress_statuses) {
            this.populateStatusDetails('in-progress-details-content', breakdown.in_progress_statuses, statusCounts);
        }
    },

    // Обновление детализированной статистики (новый формат)
    updateDetailedStatisticsNew: function(breakdownDetails, statusCounts) {
        console.log('📊 Обновление детализации (новый формат):', breakdownDetails);

        // Открытые задачи
        if (breakdownDetails.open) {
            this.populateStatusDetailsFromArray('open-details-content', breakdownDetails.open);
        }

        // Завершённые задачи
        if (breakdownDetails.completed) {
            this.populateStatusDetailsFromArray('completed-details-content', breakdownDetails.completed);
        }

        // В работе
        if (breakdownDetails.in_progress) {
            this.populateStatusDetailsFromArray('in-progress-details-content', breakdownDetails.in_progress);
        }
    },

    // Вспомогательная функция для заполнения деталей статусов (по именам)
    populateStatusDetails: function(containerId, statuses, statusCounts) {
        const container = document.getElementById(containerId);
        if (!container || !statuses) return;

        container.innerHTML = '';
        statuses.forEach(status => {
            const count = statusCounts[status] || 0;
            if (count > 0) {
                const item = document.createElement('div');
                item.className = 'detail-item';
                item.innerHTML = `
                    <span class="detail-label">${this.escapeHtml(status)}:</span>
                    <span class="detail-value">${count}</span>
                `;
                container.appendChild(item);
            }
        });
    },

    // Вспомогательная функция для заполнения деталей статусов (из массива объектов)
    populateStatusDetailsFromArray: function(containerId, statusArray) {
        const container = document.getElementById(containerId);
        if (!container || !statusArray) return;

        container.innerHTML = '';
        statusArray.forEach(statusObj => {
            if (statusObj.count > 0) {
                const item = document.createElement('div');
                item.className = 'detail-item';
                item.innerHTML = `
                    <span class="detail-label">${this.escapeHtml(statusObj.name)}:</span>
                    <span class="detail-value">${statusObj.count}</span>
                `;
                container.appendChild(item);
            }
        });
    },

    // Привязка событий
    bindEventListeners: function() {
        console.log('🔗 Привязка событий');

        // Фильтры
        const statusFilter = document.getElementById('status-filter');
        const projectFilter = document.getElementById('project-filter');
        const priorityFilter = document.getElementById('priority-filter');

        if (statusFilter) {
            statusFilter.addEventListener('change', (e) => this.handleFilterChange('status', e.target.value));
        }
        if (projectFilter) {
            projectFilter.addEventListener('change', (e) => this.handleFilterChange('project', e.target.value));
        }
        if (priorityFilter) {
            priorityFilter.addEventListener('change', (e) => this.handleFilterChange('priority', e.target.value));
        }

        // Кнопки очистки фильтров
        document.addEventListener('click', (e) => {
            if (e.target.closest('.clear-filter-btn')) {
                const button = e.target.closest('.clear-filter-btn');
                this.clearFilter(button.id);
            }
        });

        // Глобальная кнопка разворачивания
        const globalToggleBtn = document.getElementById('globalToggleBtn');
        if (globalToggleBtn) {
            globalToggleBtn.addEventListener('click', () => this.toggleAllDetails());
        }

        // Кнопки детализации карточек
        document.addEventListener('click', (e) => {
            if (e.target.closest('.toggle-details-btn')) {
                const button = e.target.closest('.toggle-details-btn');
                const target = button.getAttribute('data-target');
                this.toggleCardDetails(target);
            }
        });

        // Кнопка сброса фильтров
        const resetBtn = document.getElementById('reset-filters-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetAllFilters());
        }

        // Кнопка повтора при ошибке
        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.retry());
        }

        console.log('✅ События привязаны');
    },

    // Обработка изменения фильтров
    handleFilterChange: function(filterType, value) {
        console.log(`🔄 Изменен фильтр ${filterType}:`, value);

        this.state.currentFilters[filterType] = value;

        // Показываем/скрываем кнопку очистки
        const clearBtn = document.getElementById(`clear-${filterType}-filter`);
        if (clearBtn) {
            clearBtn.style.display = value ? 'block' : 'none';
        }

        // Перезагружаем таблицу
        if (this.state.dataTable) {
            this.state.dataTable.ajax.reload();
        }

        // Обновляем статистику (если нужно)
        this.loadStatistics();
    },

    // Очистка фильтра
    clearFilter: function(buttonId) {
        console.log('🧹 Очистка фильтра:', buttonId);

        const filterType = buttonId.replace('clear-', '').replace('-filter', '');
        const select = document.getElementById(`${filterType}-filter`);
        const clearBtn = document.getElementById(buttonId);

        if (select) {
            select.value = '';
            this.handleFilterChange(filterType, '');
        }

        if (clearBtn) {
            clearBtn.style.display = 'none';
        }
    },

    // Сброс всех фильтров
    resetAllFilters: function() {
        console.log('🔄 Сброс всех фильтров');

        this.state.currentFilters = {
            status: '',
            project: '',
            priority: ''
        };

        // Очищаем селекты
        ['status-filter', 'project-filter', 'priority-filter'].forEach(id => {
            const select = document.getElementById(id);
            if (select) select.value = '';
        });

        // Скрываем кнопки очистки
        ['clear-status-filter', 'clear-project-filter', 'clear-priority-filter'].forEach(id => {
            const btn = document.getElementById(id);
            if (btn) btn.style.display = 'none';
        });

        // Перезагружаем таблицу
        if (this.state.dataTable) {
            this.state.dataTable.ajax.reload();
        }

        // Обновляем статистику
        this.loadStatistics();
    },

    // Переключение детализации карточки
    toggleCardDetails: function(targetId) {
        const details = document.getElementById(targetId);
        const button = document.querySelector(`[data-target="${targetId}"]`);

        if (details && button) {
            const isVisible = details.style.display !== 'none';
            details.style.display = isVisible ? 'none' : 'block';

            const icon = button.querySelector('i');
            const span = button.querySelector('span');

            if (icon && span) {
                if (isVisible) {
                    icon.className = 'fas fa-chevron-down';
                    span.textContent = 'Детализация';
                } else {
                    icon.className = 'fas fa-chevron-up';
                    span.textContent = 'Свернуть';
                }
            }
        }
    },

    // Переключение всех деталей
    toggleAllDetails: function() {
        const detailsElements = document.querySelectorAll('.card-details');
        const globalBtn = document.getElementById('globalToggleBtn');

        if (!detailsElements.length || !globalBtn) return;

        const firstVisible = detailsElements[0].style.display !== 'none';
        const newDisplay = firstVisible ? 'none' : 'block';

        detailsElements.forEach(details => {
            details.style.display = newDisplay;
        });

        // Обновляем кнопки детализации
        document.querySelectorAll('.toggle-details-btn').forEach(btn => {
            const icon = btn.querySelector('i');
            const span = btn.querySelector('span');

            if (icon && span) {
                if (firstVisible) {
                    icon.className = 'fas fa-chevron-down';
                    span.textContent = 'Детализация';
                } else {
                    icon.className = 'fas fa-chevron-up';
                    span.textContent = 'Свернуть';
                }
            }
        });

        // Обновляем глобальную кнопку
        const globalIcon = globalBtn.querySelector('i');
        const globalSpan = globalBtn.querySelector('span');

        if (globalIcon && globalSpan) {
            if (firstVisible) {
                globalIcon.className = 'fas fa-expand-alt';
                globalSpan.textContent = 'Развернуть все';
            } else {
                globalIcon.className = 'fas fa-compress-alt';
                globalSpan.textContent = 'Свернуть все';
            }
        }
    },

    // Повторная попытка
    retry: function() {
        console.log('🔄 Повторная попытка загрузки');
        this.hideError();
        this.showLoadingSpinner();

        // Перезагружаем все данные
        if (this.state.dataTable) {
            this.state.dataTable.ajax.reload();
        }
        this.loadFilters();
        this.loadStatistics();
    },

    // Показать ошибку
    showError: function(message) {
        const errorState = document.getElementById('error-state');
        const errorMessage = document.getElementById('error-message');

        if (errorState) {
            errorState.style.display = 'block';
        }
        if (errorMessage) {
            errorMessage.textContent = message;
        }

        // Скрываем таблицу и другие элементы
        const tableContainer = document.querySelector('.table-container');
        if (tableContainer) {
            tableContainer.style.display = 'none';
        }
    },

    // Скрыть ошибку
    hideError: function() {
        const errorState = document.getElementById('error-state');
        if (errorState) {
            errorState.style.display = 'none';
        }

        // Показываем таблицу
        const tableContainer = document.querySelector('.table-container');
        if (tableContainer) {
            tableContainer.style.display = 'block';
        }
    },

    // Утилиты
    updateElementText: function(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        }
    },

    // Функция для экранирования HTML
    escapeHtml: function(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.toString().replace(/[&<>"']/g, function(m) { return map[m]; });
    },

    // Подсветка строки при возврате (без автоматической прокрутки)
    highlightReturnRow: function() {
        const returnId = sessionStorage.getItem('return_from_task_id');

        if (!returnId || returnId.trim() === '' || isNaN(returnId)) {
            return;
        }

        const tableApi = this.state.dataTable;
        if (!tableApi) {
            return;
        }

        // Ищем строку с нужным ID
        const $row = $(tableApi.rows({ page: 'current' }).nodes()).filter(function() {
            const $this = $(this);
            const idFromNumber = $this.find('.task-id-number').text().replace('#','');
            const idFromLink = $this.find('.task-id-link').text().replace('#','');
            const idFromAny = $this.find('[class*="task-id"]').text().replace('#','');

            return idFromNumber === returnId || idFromLink === returnId || idFromAny === returnId;
        });

        if ($row.length && $row.is(':visible')) {
            // Убираем прошлое выделение
            $(tableApi.rows().nodes()).removeClass('return-selected');

            // Добавляем класс
            $row.addClass('return-selected');

            // Очищаем ключ после подсветки
            sessionStorage.removeItem('return_from_task_id');
        }
    },

    formatDate: function(dateString) {
        if (!dateString) return '-';

        try {
            const date = new Date(dateString);
            const now = new Date();
            const diffTime = Math.abs(now - date);
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            // Если дата сегодня - показываем только время
            if (diffDays === 0) {
                return date.toLocaleString('ru-RU', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }

            // Если дата в этом году - показываем без года
            if (date.getFullYear() === now.getFullYear()) {
                return date.toLocaleDateString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit'
                });
            }

            // Иначе показываем полную дату
            return date.toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: '2-digit'
            });
        } catch (error) {
            console.warn('Ошибка форматирования даты:', error);
            return dateString;
        }
    },

    // Форматирование даты и времени для поля "Обновлена"
    formatDateTime: function(dateString) {
        if (!dateString) return '-';

        try {
            // Создаем объект Date из строки
            // JavaScript автоматически обрабатывает UTC и ISO строки
            let date;

            // Если строка содержит 'T' или 'Z', это ISO формат
            if (dateString.includes('T') || dateString.includes('Z')) {
                date = new Date(dateString);
            } else {
                // Если это строка в формате "YYYY-MM-DD HH:MM:SS", обрабатываем как UTC
                date = new Date(dateString + (dateString.includes(' ') ? ' UTC' : ''));
            }

            // Проверяем валидность даты
            if (isNaN(date.getTime())) {
                console.warn('Невалидная дата:', dateString);
                return dateString;
            }

            // Форматируем в формате "дд.мм.гггг чч:мм"
            // Используем локальное время клиента для корректного отображения
            const day = String(date.getDate()).padStart(2, '0');
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const year = date.getFullYear();
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');

            return `${day}.${month}.${year} ${hours}:${minutes}`;
        } catch (error) {
            console.warn('Ошибка форматирования даты и времени:', error);
            return dateString;
        }
    },

    // Получение информации о временной зоне клиента
    getTimezoneInfo: function() {
        try {
            const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const offset = new Date().getTimezoneOffset();
            const offsetHours = Math.floor(Math.abs(offset) / 60);
            const offsetMinutes = Math.abs(offset) % 60;
            const offsetSign = offset <= 0 ? '+' : '-';

            return {
                timezone: timezone,
                offset: `${offsetSign}${String(offsetHours).padStart(2, '0')}:${String(offsetMinutes).padStart(2, '0')}`,
                offsetMinutes: offset
            };
        } catch (error) {
            console.warn('Ошибка получения информации о временной зоне:', error);
            return {
                timezone: 'Unknown',
                offset: '+00:00',
                offsetMinutes: 0
            };
        }
    },

    getStatusInfo: function(statusName) {
        if (!statusName) {
            return {
                class: 'status-default',
                icon: 'fas fa-question-circle',
                shortName: 'N/A',
                tooltip: 'Статус не определен'
            };
        }

        const statusLower = statusName.toLowerCase();

        // 🆕 Новая
        if (statusLower === 'новая' || statusLower === 'new') {
            return {
                class: 'status-new',
                icon: 'fas fa-star',
                shortName: 'Новая',
                tooltip: 'Новая задача ожидает обработки'
            };
        }

        // 🔄 В работе
        if (statusLower === 'в работе' || statusLower === 'in progress') {
            return {
                class: 'status-in-progress',
                icon: 'fas fa-cog',
                shortName: 'В работе',
                tooltip: 'Задача находится в процессе выполнения'
            };
        }

        // ✅ Закрыта
        if (statusLower === 'закрыта' || statusLower === 'closed') {
            return {
                class: 'status-closed',
                icon: 'fas fa-check-circle',
                shortName: 'Закрыта',
                tooltip: 'Задача закрыта'
            };
        }

        // ❌ Отклонена
        if (statusLower === 'отклонена' || statusLower === 'rejected') {
            return {
                class: 'status-rejected',
                icon: 'fas fa-times-circle',
                shortName: 'Отклонена',
                tooltip: 'Задача отклонена'
            };
        }

        // ✅ Выполнена
        if (statusLower === 'выполнена' || statusLower === 'resolved' || statusLower === 'done') {
            return {
                class: 'status-closed',
                icon: 'fas fa-check-circle',
                shortName: 'Выполнена',
                tooltip: 'Задача выполнена'
            };
        }

        // 📋 Запрошено уточнение
        if (statusLower === 'запрошено уточнение' || statusLower.includes('уточнение')) {
            return {
                class: 'status-waiting',
                icon: 'fas fa-question-circle',
                shortName: 'Уточнение',
                tooltip: 'Запрошено уточнение по задаче'
            };
        }

        // ⏸️ Приостановлена
        if (statusLower === 'приостановлена' || statusLower === 'paused') {
            return {
                class: 'status-waiting',
                icon: 'fas fa-pause-circle',
                shortName: 'Приостановлена',
                tooltip: 'Задача приостановлена'
            };
        }

        // 🧪 Протестирована
        if (statusLower === 'протестирована' || statusLower === 'tested') {
            return {
                class: 'status-testing',
                icon: 'fas fa-check-double',
                shortName: 'Протестирована',
                tooltip: 'Задача протестирована'
            };
        }

        // 🔄 Перенаправлена
        if (statusLower === 'перенаправлена' || statusLower === 'redirected') {
            return {
                class: 'status-in-progress',
                icon: 'fas fa-share',
                shortName: 'Перенаправлена',
                tooltip: 'Задача перенаправлена'
            };
        }

        // 📝 На согласовании
        if (statusLower === 'на согласовании' || statusLower.includes('согласован')) {
            return {
                class: 'status-waiting',
                icon: 'fas fa-handshake',
                shortName: 'На согласовании',
                tooltip: 'Задача на согласовании'
            };
        }

        // ❄️ Заморожена
        if (statusLower === 'заморожена' || statusLower === 'frozen') {
            return {
                class: 'status-waiting',
                icon: 'fas fa-snowflake',
                shortName: 'Заморожена',
                tooltip: 'Задача заморожена'
            };
        }

        // 📂 Открыта
        if (statusLower === 'открыта' || statusLower === 'open') {
            return {
                class: 'status-new',
                icon: 'fas fa-folder-open',
                shortName: 'Открыта',
                tooltip: 'Задача открыта'
            };
        }

        // 🔍 На тестировании
        if (statusLower === 'на тестировании' || statusLower.includes('тестирован')) {
            return {
                class: 'status-testing',
                icon: 'fas fa-flask',
                shortName: 'На тестировании',
                tooltip: 'Задача на тестировании'
            };
        }

        // 📋 В очереди
        if (statusLower === 'в очереди' || statusLower === 'queued') {
            return {
                class: 'status-new',
                icon: 'fas fa-list-ol',
                shortName: 'В очереди',
                tooltip: 'Задача в очереди на выполнение'
            };
        }

        // Статус по умолчанию
        return {
            class: 'status-default',
            icon: 'fas fa-info-circle',
            shortName: statusName.length > 10 ? statusName.substring(0, 10) + '...' : statusName,
            tooltip: `Статус: ${statusName}`
        };
    },

    getPriorityInfo: function(priorityName) {
        if (!priorityName) return { class: 'priority-default', icon: 'fas fa-question' };

        const priorityLower = priorityName.toLowerCase();

        if (priorityLower.includes('низк') || priorityLower.includes('low')) {
            return { class: 'priority-low', icon: 'fas fa-arrow-down' };
        }
        if (priorityLower.includes('обычн') || priorityLower.includes('normal') ||
            priorityLower.includes('средн') || priorityLower.includes('нормальн')) {
            return { class: 'priority-normal', icon: 'fas fa-circle' };
        }
        if (priorityLower.includes('высок') || priorityLower.includes('high')) {
            return { class: 'priority-high', icon: 'fas fa-arrow-up' };
        }
        if (priorityLower.includes('критич') || priorityLower.includes('critical') ||
            priorityLower.includes('срочн') || priorityLower.includes('urgent')) {
            return { class: 'priority-critical', icon: 'fas fa-exclamation-triangle' };
        }

        return { class: 'priority-default', icon: 'fas fa-question' };
    },

    // Настройка плейсхолдера для поиска
    setupSearchPlaceholder: function() {
        const searchInput = document.querySelector('.dataTables_filter input');
        if (searchInput) {
            searchInput.placeholder = 'Поиск по ID, теме, описанию...';
            searchInput.setAttribute('aria-label', 'Поиск задач');
        }
    },

    // Выделяем активную страницу пагинации доп.классом и автопрокручиваем номер
    highlightPagination: function() {
        const tableApi = this.state.dataTable;
        if (!tableApi) return;

        const currentPage = tableApi.page();
        const $paginateContainer = $('.dataTables_paginate');
        if (!$paginateContainer.length) return;

        $paginateContainer.find('.paginate_button').removeClass('active-page');
        $paginateContainer.find('.paginate_button').each(function() {
            const pageNum = parseInt($(this).text(), 10) - 1; // zero-based
            if (pageNum === currentPage) {
                $(this).addClass('active-page');
            }
        });
    },

    // Инициализация tooltips с защитой от зависания
    initializeTooltips: function() {
        console.log('🎯 Инициализация tooltips для MyTasksApp');

        // Принудительно очищаем все существующие tooltips перед инициализацией
        if (typeof window.emergencyHideTooltips === 'function') {
            window.emergencyHideTooltips();
        }

        // Инициализируем KanbanTooltips если доступен
        if (typeof window.KanbanTooltips !== 'undefined') {
            try {
                if (!this.tooltipManager) {
                    this.tooltipManager = new window.KanbanTooltips();
                }

                // Очищаем предыдущую инициализацию
                if (this.tooltipManager.cleanup) {
                    this.tooltipManager.cleanup();
                }

                // Инициализируем заново
                this.tooltipManager.init();
                console.log('✅ KanbanTooltips инициализированы успешно');
            } catch (error) {
                console.warn('⚠️ Ошибка при инициализации KanbanTooltips:', error);
            }
        }

        // Добавляем обработчик для предотвращения зависания tooltips при быстром движении мыши
        let tooltipHideTimeout;
        document.addEventListener('mouseleave', () => {
            clearTimeout(tooltipHideTimeout);
            tooltipHideTimeout = setTimeout(() => {
                if (this.tooltipManager && this.tooltipManager.hideAllTooltips) {
                    this.tooltipManager.hideAllTooltips();
                }
            }, 500);
        });

        // Принудительно скрываем tooltips при скролле
        window.addEventListener('scroll', () => {
            if (this.tooltipManager && this.tooltipManager.hideTooltip) {
                this.tooltipManager.hideTooltip();
            }
        }, { passive: true });

        console.log('✅ Tooltips защита от зависания настроена');
    }
};

// Экспортируем для глобального использования
window.MyTasksApp = MyTasksApp;
