/**
 * TasksAPI - Сервис для работы с API задач
 * Инкапсулирует все AJAX запросы и обработку данных
 */
class TasksAPI {
    constructor() {
        this.baseUrl = window.location.origin;
        this.cache = new Map();
        this.requestQueue = new Map();
    }

    /**
     * Получение списка задач с фильтрацией и пагинацией
     */
    async getTasks(params = {}) {
        const cacheKey = this._getCacheKey('tasks', params);

        // Проверяем кэш
        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 30000) { // 30 секунд
                return cached.data;
            }
        }

        // Проверяем очередь запросов (предотвращаем дублирование)
        if (this.requestQueue.has(cacheKey)) {
            return this.requestQueue.get(cacheKey);
        }

        const requestPromise = this._makeRequest('/tasks/api/tasks', {
            method: 'GET',
            params: {
                page: params.page || 1,
                per_page: params.perPage || 25,
                search: params.search || '',
                status_filter: params.statusFilter || '',
                priority_filter: params.priorityFilter || '',
                assigned_to_filter: params.assignedToFilter || '',
                project_filter: params.projectFilter || '',
                sort_by: params.sortBy || 'updated_on',
                sort_order: params.sortOrder || 'desc'
            }
        });

        this.requestQueue.set(cacheKey, requestPromise);

        try {
            const result = await requestPromise;

            // Кэшируем результат
            this.cache.set(cacheKey, {
                data: result,
                timestamp: Date.now()
            });

            return result;
        } finally {
            this.requestQueue.delete(cacheKey);
        }
    }

    /**
     * Получение статистики задач
     */
    async getStatistics(params = {}) {
        const cacheKey = this._getCacheKey('statistics', params);

        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 60000) { // 1 минута
                return cached.data;
            }
        }

        const result = await this._makeRequest('/tasks/api/statistics', {
            method: 'GET',
            params: params
        });

        this.cache.set(cacheKey, {
            data: result,
            timestamp: Date.now()
        });

        return result;
    }

    /**
     * Получение деталей задачи
     */
    async getTaskDetail(taskId) {
        const cacheKey = `task_detail_${taskId}`;

        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 120000) { // 2 минуты
                return cached.data;
            }
        }

        const result = await this._makeRequest(`/tasks/api/task/${taskId}`, {
            method: 'GET'
        });

        this.cache.set(cacheKey, {
            data: result,
            timestamp: Date.now()
        });

        return result;
    }

    /**
     * Получение списка проектов
     */
    async getProjects() {
        const cacheKey = 'projects';

        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 300000) { // 5 минут
                return cached.data;
            }
        }

        const result = await this._makeRequest('/tasks/api/projects', {
            method: 'GET'
        });

        this.cache.set(cacheKey, {
            data: result,
            timestamp: Date.now()
        });

        return result;
    }

    /**
     * Получение списка пользователей
     */
    async getUsers() {
        const cacheKey = 'users';

        if (this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < 300000) { // 5 минут
                return cached.data;
            }
        }

        const result = await this._makeRequest('/tasks/api/users', {
            method: 'GET'
        });

        this.cache.set(cacheKey, {
            data: result,
            timestamp: Date.now()
        });

        return result;
    }

    /**
     * Обновление задачи
     */
    async updateTask(taskId, data) {
        const result = await this._makeRequest(`/tasks/api/task/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(data),
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Очищаем кэш для этой задачи
        this._clearTaskCache(taskId);

        return result;
    }

    /**
     * Экспорт задач
     */
    async exportTasks(format = 'csv', params = {}) {
        const exportParams = new URLSearchParams({
            format: format,
            ...params
        });

        const response = await fetch(`${this.baseUrl}/tasks/api/export?${exportParams}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`Export failed: ${response.status} ${response.statusText}`);
        }

        return {
            blob: await response.blob(),
            filename: this._getFilenameFromResponse(response)
        };
    }

    /**
     * Очистка кэша
     */
    clearCache(pattern = null) {
        if (pattern) {
            for (const key of this.cache.keys()) {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                }
            }
        } else {
            this.cache.clear();
        }
    }

    /**
     * Приватные методы
     */
    async _makeRequest(url, options = {}) {
        const { params, ...fetchOptions } = options;

        let fullUrl = `${this.baseUrl}${url}`;

        if (params && Object.keys(params).length > 0) {
            const searchParams = new URLSearchParams();
            for (const [key, value] of Object.entries(params)) {
                if (value !== null && value !== undefined && value !== '') {
                    searchParams.append(key, value);
                }
            }
            fullUrl += `?${searchParams.toString()}`;
        }

        const defaultHeaders = {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        };

        const response = await fetch(fullUrl, {
            ...fetchOptions,
            headers: {
                ...defaultHeaders,
                ...fetchOptions.headers
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }

        return await response.text();
    }

    _getCacheKey(endpoint, params) {
        const sortedParams = Object.keys(params || {}).sort().reduce((result, key) => {
            result[key] = params[key];
            return result;
        }, {});

        return `${endpoint}_${JSON.stringify(sortedParams)}`;
    }

    _clearTaskCache(taskId) {
        const keysToDelete = [];
        for (const key of this.cache.keys()) {
            if (key.includes('tasks') || key.includes(`task_detail_${taskId}`)) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => this.cache.delete(key));
    }

    _getFilenameFromResponse(response) {
        const contentDisposition = response.headers.get('content-disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                return filenameMatch[1].replace(/['"]/g, '');
            }
        }
        return `tasks_export_${new Date().toISOString().slice(0, 10)}.csv`;
    }
}

// Экспорт для ES6 модулей
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TasksAPI;
} else if (typeof window !== 'undefined') {
    window.TasksAPI = TasksAPI;
}
