/**
 * JavaScript для изменения статуса задачи на странице детализации
 * Работает с API endpoints: GET /tasks/api/task/<id>/statuses и PUT /tasks/api/task/<id>/status
 */

class TaskStatusChanger {
    constructor(taskId) {
        this.taskId = taskId;
        this.currentStatusId = null;
        this.isLoading = false;
        this.init();
    }

    /**
     * Инициализация компонента
     */
    init() {
        this.loadAvailableStatuses();
        this.bindEvents();
    }

    /**
     * Загрузка доступных статусов для задачи
     */
    async loadAvailableStatuses() {
        try {
            this.showLoading(true);

            const response = await fetch(`/tasks/api/task/${this.taskId}/statuses`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.currentStatusId = data.current_status.id;
                this.renderStatusSelector(data.current_status, data.available_statuses);
            } else {
                this.showError('Не удалось загрузить доступные статусы: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки статусов:', error);
            this.showError('Ошибка загрузки статусов. Попробуйте обновить страницу.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Отрисовка селектора статуса
     */
    renderStatusSelector(currentStatus, availableStatuses) {
        const statusContainer = document.getElementById('task-status-container');
        if (!statusContainer) {
            console.error('Контейнер для статуса не найден');
            return;
        }

        // Создаем HTML для изменения статуса
        const statusHTML = `
            <div class="task-status-changer">
                <div class="current-status">
                    <label class="form-label">Текущий статус:</label>
                    <span class="status-badge status-${currentStatus.id}" id="current-status-display">
                        ${currentStatus.name}
                    </span>
                </div>

                <div class="status-change-form mt-3">
                    <label class="form-label">Изменить статус:</label>
                    <div class="row">
                        <div class="col-md-6">
                            <select class="form-select" id="new-status-select">
                                <option value="">Выберите новый статус</option>
                                ${availableStatuses.map(status =>
                                    `<option value="${status.id}">${status.name}</option>`
                                ).join('')}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <button type="button" class="btn btn-primary" id="change-status-btn" disabled>
                                <i class="fas fa-sync-alt"></i> Изменить статус
                            </button>
                        </div>
                    </div>

                    <div class="mt-3">
                        <label class="form-label">Комментарий (необязательно):</label>
                        <textarea class="form-control" id="status-comment" rows="3"
                                  placeholder="Добавьте комментарий к изменению статуса..."></textarea>
                    </div>
                </div>
            </div>
        `;

        statusContainer.innerHTML = statusHTML;
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        // Используем делегирование событий, так как элементы создаются динамически
        document.addEventListener('change', (e) => {
            if (e.target.id === 'new-status-select') {
                this.handleStatusSelectChange(e);
            }
        });

        document.addEventListener('click', (e) => {
            if (e.target.id === 'change-status-btn') {
                this.handleStatusChange(e);
            }
        });
    }

    /**
     * Обработка изменения выбора статуса
     */
    handleStatusSelectChange(event) {
        const newStatusId = event.target.value;
        const changeButton = document.getElementById('change-status-btn');

        if (changeButton) {
            changeButton.disabled = !newStatusId || newStatusId === this.currentStatusId.toString();
        }
    }

    /**
     * Обработка изменения статуса
     */
    async handleStatusChange(event) {
        if (this.isLoading) return;

        const newStatusSelect = document.getElementById('new-status-select');
        const commentField = document.getElementById('status-comment');

        if (!newStatusSelect || !newStatusSelect.value) {
            this.showError('Выберите новый статус');
            return;
        }

        const newStatusId = parseInt(newStatusSelect.value);
        const comment = commentField ? commentField.value.trim() : '';

        // Подтверждение изменения
        const selectedStatusText = newStatusSelect.options[newStatusSelect.selectedIndex].text;
        const confirmMessage = `Вы действительно хотите изменить статус задачи на "${selectedStatusText}"?`;

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            this.showLoading(true);

            const response = await fetch(`/tasks/api/task/${this.taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    status_id: newStatusId,
                    comment: comment
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(data.message);
                this.updateCurrentStatus(data.new_status_id, data.new_status_name);
                this.resetForm();

                // Обновляем страницу через 2 секунды для отображения изменений
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showError('Ошибка изменения статуса: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка изменения статуса:', error);
            this.showError('Произошла ошибка при изменении статуса. Попробуйте еще раз.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Обновление отображения текущего статуса
     */
    updateCurrentStatus(newStatusId, newStatusName) {
        const currentStatusDisplay = document.getElementById('current-status-display');
        if (currentStatusDisplay) {
            currentStatusDisplay.textContent = newStatusName;
            currentStatusDisplay.className = `status-badge status-${newStatusId}`;
        }

        this.currentStatusId = newStatusId;
    }

    /**
     * Сброс формы
     */
    resetForm() {
        const newStatusSelect = document.getElementById('new-status-select');
        const commentField = document.getElementById('status-comment');
        const changeButton = document.getElementById('change-status-btn');

        if (newStatusSelect) newStatusSelect.value = '';
        if (commentField) commentField.value = '';
        if (changeButton) changeButton.disabled = true;
    }

    /**
     * Показать индикатор загрузки
     */
    showLoading(show) {
        this.isLoading = show;
        const changeButton = document.getElementById('change-status-btn');
        const newStatusSelect = document.getElementById('new-status-select');

        if (changeButton) {
            if (show) {
                changeButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Изменение...';
                changeButton.disabled = true;
            } else {
                changeButton.innerHTML = '<i class="fas fa-sync-alt"></i> Изменить статус';
                changeButton.disabled = !newStatusSelect || !newStatusSelect.value;
            }
        }

        if (newStatusSelect) {
            newStatusSelect.disabled = show;
        }
    }

    /**
     * Показать сообщение об ошибке
     */
    showError(message) {
        // Используем существующий механизм уведомлений или создаем простое уведомление
        if (typeof showNotification === 'function') {
            showNotification(message, 'error');
        } else {
            // Простое уведомление через alert или создание элемента
            this.showAlert(message, 'danger');
        }
    }

    /**
     * Показать сообщение об успехе
     */
    showSuccess(message) {
        if (typeof showNotification === 'function') {
            showNotification(message, 'success');
        } else {
            this.showAlert(message, 'success');
        }
    }

    /**
     * Показать alert уведомление
     */
    showAlert(message, type) {
        const alertHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        const container = document.getElementById('task-status-container');
        if (container) {
            const alertElement = document.createElement('div');
            alertElement.innerHTML = alertHTML;
            container.insertBefore(alertElement.firstElementChild, container.firstChild);

            // Автоматически скрыть через 5 секунд
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) {
                    alert.remove();
                }
            }, 5000);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Получаем ID задачи из URL или data-атрибута
    const taskId = getTaskIdFromUrl();

    if (taskId) {
        window.taskStatusChanger = new TaskStatusChanger(taskId);
    }
});

/**
 * Получение ID задачи из URL
 */
function getTaskIdFromUrl() {
    // Предполагаем URL вида: /tasks/my-tasks/123
    const pathParts = window.location.pathname.split('/');
    const taskIdIndex = pathParts.findIndex(part => part === 'my-tasks') + 1;

    if (taskIdIndex > 0 && taskIdIndex < pathParts.length) {
        const taskId = parseInt(pathParts[taskIdIndex]);
        return isNaN(taskId) ? null : taskId;
    }

    return null;
}
