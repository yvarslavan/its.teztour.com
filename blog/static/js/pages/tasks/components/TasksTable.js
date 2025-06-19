/**
 * TasksTable - Компонент таблицы задач
 * Инкапсулирует логику DataTables с сохранением всей функциональности
 */
class TasksTable {
    constructor(eventBus, loadingManager, tasksAPI) {
        this.eventBus = eventBus;
        this.loadingManager = loadingManager;
        this.tasksAPI = tasksAPI;

        this.dataTable = null;
        this.tableElement = null;
        this.isInitialized = false;
        this.isFirstLoad = true;

        // Настройки по умолчанию
        this.defaultOptions = {
            processing: true,
            serverSide: true,
            searching: true,
            searchDelay: 1000,
            deferLoading: 1,
            pageLength: 25,
            lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
            language: {
                url: '/static/js/datatables/ru.json'
            }
        };

        // Привязываем методы к контексту
        this.handleTableDraw = this.handleTableDraw.bind(this);
        this.handleAjaxData = this.handleAjaxData.bind(this);
        this.handleDataSrc = this.handleDataSrc.bind(this);
        this.handleError = this.handleError.bind(this);
    }

    /**
     * Инициализация таблицы
     */
    async init(tableSelector = '#tasksTable') {
        try {
            this.tableElement = $(tableSelector);

            if (this.tableElement.length === 0) {
                throw new Error(`Таблица ${tableSelector} не найдена`);
            }

            // Проверяем, не инициализирована ли уже таблица
            if ($.fn.DataTable.isDataTable(tableSelector)) {
                console.log('[TasksTable] ⚠️ Таблица уже инициализирована, получаем существующий экземпляр');
                this.dataTable = this.tableElement.DataTable();
                this.isInitialized = true;
                this._setupEventListeners();
                return this.dataTable;
            }

            console.log('[TasksTable] 🚀 Инициализация таблицы задач...');

            // Показываем загрузку
            this.loadingManager.show('table', 'Инициализация таблицы...');

            // Настройка событий перед инициализацией
            this._setupPreInitEvents();

            // Создаем DataTable
            this.dataTable = this.tableElement.DataTable({
                ...this.defaultOptions,
                ajax: {
                    url: "/tasks/get-my-tasks-paginated",
                    type: "GET",
                    data: this.handleAjaxData,
                    dataSrc: this.handleDataSrc,
                    error: this.handleError
                },
                columns: this._getColumnConfig(),
                initComplete: (settings, json) => {
                    this._handleInitComplete(settings, json);
                }
            });

            // Делаем таблицу глобально доступной для совместимости
            window.tasksDataTable = this.dataTable;
            window.tasksTable = this;

            this.isInitialized = true;
            this._setupEventListeners();

            console.log('[TasksTable] ✅ Таблица успешно инициализирована');
            this.eventBus.emit('table:initialized', { table: this.dataTable });

            return this.dataTable;

        } catch (error) {
            console.error('[TasksTable] ❌ Ошибка инициализации:', error);
            this.loadingManager.hide('table');
            this.eventBus.emit('table:error', { error: error.message });
            throw error;
        }
    }

    /**
     * Обновление данных таблицы
     */
    refresh() {
        if (!this.isInitialized || !this.dataTable) {
            console.warn('[TasksTable] Таблица не инициализирована');
            return;
        }

        console.log('[TasksTable] 🔄 Обновление данных таблицы');
        this.loadingManager.show('table', 'Обновление данных...');
        this.dataTable.ajax.reload();
    }

    /**
     * Применение фильтров
     */
    applyFilters(filters = {}) {
        if (!this.isInitialized || !this.dataTable) {
            console.warn('[TasksTable] Таблица не инициализирована');
            return;
        }

        console.log('[TasksTable] 🔍 Применение фильтров:', filters);

        // Сохраняем текущие фильтры
        this.currentFilters = { ...filters };

        // Перезагружаем данные
        this.refresh();
    }

    /**
     * Поиск в таблице
     */
    search(searchTerm) {
        if (!this.isInitialized || !this.dataTable) {
            console.warn('[TasksTable] Таблица не инициализирована');
            return;
        }

        console.log('[TasksTable] 🔍 Поиск:', searchTerm);
        this.dataTable.search(searchTerm).draw();
    }

    /**
     * Получение текущих данных
     */
    getCurrentData() {
        if (!this.isInitialized || !this.dataTable) {
            return [];
        }

        return this.dataTable.rows().data().toArray();
    }

    /**
     * Обработчик данных AJAX запроса
     */
    handleAjaxData(d) {
        console.log('[TasksTable] 🔄 Формирование AJAX запроса');

        // Добавляем сортировку
        const orderColumnIndex = d.order[0].column;
        const orderColumnName = d.columns[orderColumnIndex].data;
        const orderDir = d.order[0].dir;

        // Получаем текущие значения фильтров
        const statusFilter = $('#status-filter').val();
        const projectFilter = $('#project-filter').val();
        const priorityFilter = $('#priority-filter').val();

        const params = {
            // Стандартные параметры DataTables
            draw: d.draw,
            start: d.start,
            length: d.length,
            ['search[value]']: d.search.value,

            // Сортировка
            ['order[0][column]']: orderColumnIndex,
            ['order[0][dir]']: orderDir,
            ['columns[' + orderColumnIndex + '][data]']: orderColumnName,

            // Фильтры
            status_id: statusFilter || '',
            project_id: projectFilter || '',
            priority_id: priorityFilter || '',

            // Дополнительные фильтры по имени
            status_name: $('#status-filter option:selected').text() || '',
            project_name: $('#project-filter option:selected').text() || '',
            priority_name: $('#priority-filter option:selected').text() || '',

            // Параметр для принудительной загрузки данных при первом запросе
            force_load: this.isFirstLoad ? '1' : '0',

            // Дополнительные фильтры из компонента
            ...this.currentFilters
        };

        console.log('[TasksTable] 📊 Параметры запроса:', params);
        return params;
    }

    /**
     * Обработчик источника данных
     */
    handleDataSrc(json) {
        console.log('[TasksTable] 📥 Данные получены:', json);

        // Скрываем загрузку
        this.loadingManager.hide('table');

        // Сбрасываем флаг первой загрузки
        if (this.isFirstLoad) {
            console.log('[TasksTable] ✅ Первая загрузка выполнена');
            this.isFirstLoad = false;
        }

        // Уведомляем о получении данных
        this.eventBus.emit('table:dataLoaded', {
            data: json.data,
            recordsTotal: json.recordsTotal,
            recordsFiltered: json.recordsFiltered
        });

        return json.data;
    }

    /**
     * Обработчик ошибок AJAX
     */
    handleError(xhr, error, thrown) {
        console.error('[TasksTable] ❌ Ошибка загрузки данных:', error, thrown, xhr.responseText);

        this.loadingManager.hide('table');

        const errorMessage = 'Ошибка загрузки данных. Попробуйте перезагрузить страницу.';
        this.eventBus.emit('table:error', {
            error: errorMessage,
            details: { xhr, error, thrown }
        });
    }

    /**
     * Обработчик отрисовки таблицы
     */
    handleTableDraw() {
        console.log('[TasksTable] 🎨 Обработка отрисовки таблицы');

        // Улучшаем строки таблицы
        this._enhanceTableRows();

        // Уведомляем о перерисовке
        this.eventBus.emit('table:drawn');
    }

    /**
     * Настройка событий перед инициализацией
     */
    _setupPreInitEvents() {
        this.tableElement.on('draw.dt', this.handleTableDraw);
    }

    /**
     * Настройка слушателей событий
     */
    _setupEventListeners() {
        // Слушаем события от других компонентов
        this.eventBus.on('filters:changed', (data) => {
            this.applyFilters(data.filters);
        });

        this.eventBus.on('search:changed', (data) => {
            this.search(data.searchTerm);
        });

        this.eventBus.on('table:refresh', () => {
            this.refresh();
        });
    }

    /**
     * Обработчик завершения инициализации
     */
    _handleInitComplete(settings, json) {
        console.log('[TasksTable] ✅ Инициализация завершена');

        // Перемещаем элементы UI для лучшего отображения
        this._moveUIElements();

        // Скрываем загрузку
        this.loadingManager.hide('table');

        // Уведомляем о завершении инициализации
        this.eventBus.emit('table:initComplete', { settings, json });

        // Для совместимости с существующим кодом
        $(document).trigger('datatables-initialized');
    }

    /**
     * Перемещение элементов UI
     */
    _moveUIElements() {
        // Перемещаем стандартные элементы DataTables в наши контейнеры
        const moveElement = (source, target) => {
            const $source = $(source);
            const $target = $(target);
            if ($source.length && $target.length) {
                $source.appendTo($target);
            }
        };

        moveElement('#tasksTable_filter', '#searchBoxContainer');
        moveElement('#tasksTable_length', '#lengthContainer');
        moveElement('#tasksTable_info', '#tasksInfoContainer');
        moveElement('#tasksTable_paginate', '#tasksPaginationContainer');
    }

    /**
     * Улучшение строк таблицы
     */
    _enhanceTableRows() {
        // Добавляем обработчики кликов для номеров задач
        this.tableElement.find('.task-id-link').off('click').on('click', function(e) {
            e.preventDefault();
            const taskId = $(this).text().replace('#', '');
            const url = $(this).attr('href');

            console.log('[TasksTable] 🔗 Клик по задаче:', taskId);

            // Открываем задачу (сохраняем оригинальную логику)
            window.location.href = url;
        });

        // Добавляем hover эффекты
        this.tableElement.find('tbody tr').off('mouseenter mouseleave').on({
            mouseenter: function() {
                $(this).addClass('table-row-hover');
            },
            mouseleave: function() {
                $(this).removeClass('table-row-hover');
            }
        });
    }

    /**
     * Конфигурация колонок
     */
    _getColumnConfig() {
        return [
            {
                data: 'id',
                render: (data, type, row) => {
                    return type === 'display'
                        ? `<a href="/tasks/my-tasks/${data}" class="task-id-link" target="_blank" rel="noopener noreferrer" title="Открыть задачу #${data} в новой вкладке">#${data}</a>`
                        : data;
                },
                orderable: true,
                searchable: true,
                className: 'task-id-column'
            },
            {
                data: 'subject',
                render: (data, type, row) => {
                    if (type === 'display') {
                        const subject = this._escapeHtml(data || '');
                        const project = this._escapeHtml(row.project_name || 'Без проекта');
                        return `<div class="task-subject">${subject}</div><div class="task-project">${project}</div>`;
                    }
                    return data;
                },
                orderable: true,
                searchable: true,
                className: 'task-subject-column'
            },
            {
                data: 'status_name',
                render: (data, type, row) => {
                    if (type === 'display') {
                        const statusInfo = this._getStatusInfo(data);
                        const statusText = this._escapeHtml(data || 'N/A');
                        return `<div class="status-badge ${statusInfo.class}" data-status="${statusText}">
                                    <i class="${statusInfo.icon}"></i>
                                    <span>${statusText}</span>
                                </div>`;
                    }
                    return data;
                },
                orderable: true,
                className: 'task-status-column'
            },
            {
                data: 'priority_name',
                render: (data, type, row) => {
                    if (type === 'display') {
                        const priorityInfo = this._getPriorityInfo(data);
                        const priorityText = this._escapeHtml(data || 'N/A');
                        return `<div class="priority-badge ${priorityInfo.class}" data-priority="${priorityText}">
                                    <i class="${priorityInfo.icon}"></i>
                                    <span>${priorityText}</span>
                                </div>`;
                    }
                    return data;
                },
                orderable: true,
                className: 'task-priority-column'
            },
            {
                data: 'easy_email_to',
                render: (data, type, row) => {
                    if (type === 'display') {
                        if (!data) {
                            return 'Не назначена';
                        }

                        // Проверяем валидность email
                        const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data);

                        if (isValidEmail) {
                            return `<a href="mailto:${this._escapeHtml(data)}" class="email-link" title="Написать письмо: ${this._escapeHtml(data)}">${this._escapeHtml(data)}</a>`;
                        } else {
                            return this._escapeHtml(data);
                        }
                    }
                    return data;
                },
                orderable: true,
                searchable: true,
                className: 'task-assignee-column'
            },
            {
                data: 'updated_on',
                render: (data, type, row) => {
                    if (type === 'display') {
                        return this._formatDate(data);
                    }
                    return data;
                },
                orderable: true,
                className: 'task-updated-column'
            },
            {
                data: 'created_on',
                render: (data, type, row) => {
                    if (type === 'display') {
                        return this._formatDate(data);
                    }
                    return data;
                },
                orderable: true,
                className: 'task-created-column'
            },
            {
                data: 'start_date',
                render: (data, type, row) => {
                    if (type === 'display') {
                        return this._formatDate(data, true);
                    }
                    return data;
                },
                orderable: true,
                className: 'task-start-column'
            }
        ];
    }

    /**
     * Утилиты для рендеринга
     */
    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    _formatDate(dateString, isStartDate = false) {
        if (!dateString) return isStartDate ? 'Не указана' : 'Никогда';

        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString;
        }
    }

    _getStatusInfo(status) {
        const statusMap = {
            'Новая': { class: 'status-new', icon: 'fas fa-plus-circle' },
            'В работе': { class: 'status-in-progress', icon: 'fas fa-play-circle' },
            'Решена': { class: 'status-resolved', icon: 'fas fa-check-circle' },
            'Обратная связь': { class: 'status-feedback', icon: 'fas fa-comment-dots' },
            'Закрыта': { class: 'status-closed', icon: 'fas fa-times-circle' },
            'Отклонена': { class: 'status-rejected', icon: 'fas fa-ban' },
            'Назначена': { class: 'status-assigned', icon: 'fas fa-user-check' },
            'Тестирование': { class: 'status-testing', icon: 'fas fa-vials' }
        };

        return statusMap[status] || { class: 'status-default', icon: 'fas fa-circle' };
    }

    _getPriorityInfo(priority) {
        const priorityMap = {
            'Низкий': { class: 'priority-low', icon: 'fas fa-arrow-down' },
            'Обычный': { class: 'priority-normal', icon: 'fas fa-minus' },
            'Высокий': { class: 'priority-high', icon: 'fas fa-arrow-up' },
            'Срочный': { class: 'priority-urgent', icon: 'fas fa-exclamation' },
            'Немедленный': { class: 'priority-immediate', icon: 'fas fa-exclamation-triangle' }
        };

        return priorityMap[priority] || { class: 'priority-default', icon: 'fas fa-circle' };
    }

    /**
     * Очистка ресурсов
     */
    destroy() {
        if (this.dataTable) {
            this.tableElement.off('draw.dt', this.handleTableDraw);
            this.dataTable.destroy();
            this.dataTable = null;
        }

        this.isInitialized = false;
        console.log('[TasksTable] 🗑️ Компонент очищен');
    }
}

// Экспорт для ES6 модулей и глобального использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TasksTable;
} else if (typeof window !== 'undefined') {
    window.TasksTable = TasksTable;
}
