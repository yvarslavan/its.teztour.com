/**
 * Валидаторы для данных задач
 */
class TaskValidators {
    /**
     * Валидация ID задачи
     */
    static isValidTaskId(taskId) {
        return taskId && (typeof taskId === 'number' || /^\d+$/.test(taskId));
    }

    /**
     * Валидация статуса задачи
     */
    static isValidStatus(status) {
        const validStatuses = [
            'new', 'in_progress', 'resolved', 'feedback',
            'closed', 'rejected', 'assigned', 'testing'
        ];
        return validStatuses.includes(status);
    }

    /**
     * Валидация приоритета
     */
    static isValidPriority(priority) {
        const validPriorities = ['low', 'normal', 'high', 'urgent', 'immediate'];
        return validPriorities.includes(priority);
    }

    /**
     * Валидация поискового запроса
     */
    static isValidSearchQuery(query) {
        if (!query || typeof query !== 'string') return false;

        // Минимум 2 символа, максимум 100
        return query.trim().length >= 2 && query.trim().length <= 100;
    }

    /**
     * Валидация номера страницы
     */
    static isValidPage(page) {
        const pageNum = parseInt(page);
        return !isNaN(pageNum) && pageNum > 0 && pageNum <= 10000;
    }

    /**
     * Валидация размера страницы
     */
    static isValidPerPage(perPage) {
        const validSizes = [10, 25, 50, 100];
        return validSizes.includes(parseInt(perPage));
    }

    /**
     * Валидация даты
     */
    static isValidDate(dateString) {
        if (!dateString) return false;

        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }

    /**
     * Валидация диапазона дат
     */
    static isValidDateRange(startDate, endDate) {
        if (!this.isValidDate(startDate) || !this.isValidDate(endDate)) {
            return false;
        }

        return new Date(startDate) <= new Date(endDate);
    }

    /**
     * Санитизация HTML контента
     */
    static sanitizeHtml(html) {
        if (!html || typeof html !== 'string') return '';

        // Простая санитизация - удаляем опасные теги
        const dangerousTags = /<script[^>]*>.*?<\/script>/gi;
        const dangerousAttributes = /on\w+="[^"]*"/gi;

        return html
            .replace(dangerousTags, '')
            .replace(dangerousAttributes, '')
            .trim();
    }

    /**
     * Валидация email
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Валидация URL
     */
    static isValidUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }
}

/**
 * Утилиты для форматирования данных
 */
class TaskFormatters {
    /**
     * Форматирование даты
     */
    static formatDate(dateString, options = {}) {
        if (!dateString) return '';

        const date = new Date(dateString);
        if (isNaN(date)) return dateString;

        const defaultOptions = {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        };

        return date.toLocaleDateString('ru-RU', { ...defaultOptions, ...options });
    }

    /**
     * Форматирование относительного времени
     */
    static formatRelativeTime(dateString) {
        if (!dateString) return '';

        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'только что';
        if (diffMins < 60) return `${diffMins} мин. назад`;
        if (diffHours < 24) return `${diffHours} ч. назад`;
        if (diffDays < 7) return `${diffDays} дн. назад`;

        return this.formatDate(dateString, { year: 'numeric', month: 'short', day: 'numeric' });
    }

    /**
     * Форматирование размера файла
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Обрезка текста
     */
    static truncateText(text, maxLength = 100) {
        if (!text || text.length <= maxLength) return text;

        return text.substring(0, maxLength).trim() + '...';
    }

    /**
     * Форматирование статуса
     */
    static formatStatus(status) {
        const statusMap = {
            'new': 'Новая',
            'in_progress': 'В работе',
            'resolved': 'Решена',
            'feedback': 'Обратная связь',
            'closed': 'Закрыта',
            'rejected': 'Отклонена',
            'assigned': 'Назначена',
            'testing': 'Тестирование'
        };

        return statusMap[status] || status;
    }

    /**
     * Форматирование приоритета
     */
    static formatPriority(priority) {
        const priorityMap = {
            'low': 'Низкий',
            'normal': 'Обычный',
            'high': 'Высокий',
            'urgent': 'Срочный',
            'immediate': 'Немедленный'
        };

        return priorityMap[priority] || priority;
    }
}

// Экспорт для ES6 модулей и глобального использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TaskValidators, TaskFormatters };
} else if (typeof window !== 'undefined') {
    window.TaskValidators = TaskValidators;
    window.TaskFormatters = TaskFormatters;
}
