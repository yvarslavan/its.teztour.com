/**
 * JavaScript для изменения приоритета задачи на странице детализации
 * Работает с API endpoints: GET /tasks/api/task/<id>/priorities и PUT /tasks/api/task/<id>/priority
 */

class TaskPriorityChanger {
    constructor(taskId) {
        this.taskId = taskId;
        this.currentPriorityId = null;
        this.isLoading = false;
        this.init();
    }

    /**
     * Инициализация компонента
     */
    init() {
        this.loadAvailablePriorities();
        this.bindEvents();
    }

    /**
     * Загрузка доступных приоритетов для задачи
     */
    async loadAvailablePriorities() {
        try {
            this.showLoading(true);

            const response = await fetch(`/tasks/api/task/${this.taskId}/priorities`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.currentPriorityId = data.current_priority ? data.current_priority.id : null;
                this.renderPrioritySelector(data.current_priority, data.available_priorities);
            } else {
                this.showError('Не удалось загрузить доступные приоритеты: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки приоритетов:', error);
            this.showError('Ошибка загрузки приоритетов. Попробуйте обновить страницу.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Отрисовка селектора приоритета
     */
    renderPrioritySelector(currentPriority, availablePriorities) {
        const priorityContainer = document.getElementById('task-priority-container');
        if (!priorityContainer) {
            console.error('Контейнер для приоритета не найден');
            return;
        }

        // Создаем HTML для изменения приоритета
        const priorityHTML = `
            <div class="task-priority-changer">
                <div class="current-priority">
                    <label class="form-label">Текущий приоритет:</label>
                    <span class="priority-badge priority-${currentPriority ? currentPriority.id : 'none'}" id="current-priority-display">
                        ${currentPriority ? currentPriority.name : 'Не установлен'}
                    </span>
                </div>

                <div class="priority-change-form mt-3">
                    <label class="form-label">Изменить приоритет:</label>
                    <div class="row">
                        <div class="col-md-6">
                            <select class="form-select" id="new-priority-select">
                                <option value="">Выберите новый приоритет</option>
                                ${availablePriorities.map(priority =>
                                    `<option value="${priority.id}">${priority.name}</option>`
                                ).join('')}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <button type="button" class="btn btn-primary" id="change-priority-btn" disabled>
                                <i class="fas fa-sync-alt"></i> Изменить приоритет
                            </button>
                        </div>
                    </div>

                    <div class="mt-3">
                        <label class="form-label">Комментарий (необязательно):</label>
                        <textarea class="form-control" id="priority-comment" rows="3"
                                  placeholder="Добавьте комментарий к изменению приоритета..."></textarea>
                    </div>
                </div>
            </div>
        `;

        priorityContainer.innerHTML = priorityHTML;
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        document.addEventListener('change', (event) => {
            if (event.target.id === 'new-priority-select') {
                this.handlePrioritySelectChange(event);
            }
        });

        document.addEventListener('click', (event) => {
            if (event.target.id === 'change-priority-btn') {
                this.handlePriorityChange(event);
            }
        });
    }

    /**
     * Обработка изменения выбора приоритета
     */
    handlePrioritySelectChange(event) {
        const newPrioritySelect = document.getElementById('new-priority-select');
        const changePriorityBtn = document.getElementById('change-priority-btn');

        if (newPrioritySelect && changePriorityBtn) {
            changePriorityBtn.disabled = !newPrioritySelect.value;
        }
    }

    /**
     * Обработка изменения приоритета
     */
    async handlePriorityChange(event) {
        if (this.isLoading) return;

        const newPrioritySelect = document.getElementById('new-priority-select');
        const commentField = document.getElementById('priority-comment');

        if (!newPrioritySelect || !newPrioritySelect.value) {
            this.showError('Выберите новый приоритет');
            return;
        }

        const newPriorityId = parseInt(newPrioritySelect.value);
        const comment = commentField ? commentField.value.trim() : '';

        // Подтверждение изменения
        const selectedPriorityText = newPrioritySelect.options[newPrioritySelect.selectedIndex].text;
        const confirmMessage = `Вы действительно хотите изменить приоритет задачи на "${selectedPriorityText}"?`;

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            this.showLoading(true);

            const response = await fetch(`/tasks/api/task/${this.taskId}/priority`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include',
                body: JSON.stringify({
                    priority_id: newPriorityId,
                    comment: comment
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(data.message);
                this.updateCurrentPriority(data.new_priority_id, data.new_priority_name);
                this.resetForm();

                // Обновляем страницу через 2 секунды для отображения изменений
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showError('Ошибка изменения приоритета: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка изменения приоритета:', error);
            this.showError('Произошла ошибка при изменении приоритета. Попробуйте еще раз.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Обновление отображения текущего приоритета
     */
    updateCurrentPriority(newPriorityId, newPriorityName) {
        const currentPriorityDisplay = document.getElementById('current-priority-display');
        if (currentPriorityDisplay) {
            currentPriorityDisplay.textContent = newPriorityName;
            currentPriorityDisplay.className = `priority-badge priority-${newPriorityId}`;
        }
    }

    /**
     * Сброс формы
     */
    resetForm() {
        const newPrioritySelect = document.getElementById('new-priority-select');
        const priorityComment = document.getElementById('priority-comment');
        const changePriorityBtn = document.getElementById('change-priority-btn');

        if (newPrioritySelect) newPrioritySelect.value = '';
        if (priorityComment) priorityComment.value = '';
        if (changePriorityBtn) changePriorityBtn.disabled = true;
    }

    /**
     * Показ/скрытие индикатора загрузки
     */
    showLoading(show) {
        const priorityContainer = document.getElementById('task-priority-container');
        if (!priorityContainer) return;

        if (show) {
            priorityContainer.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Обновление приоритета...</span>
                </div>
            `;
        }
    }

    /**
     * Показ ошибки
     */
    showError(message) {
        this.showAlert(message, 'error');
    }

    /**
     * Показ успешного сообщения
     */
    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    /**
     * Показ уведомления
     */
    showAlert(message, type) {
        // Создаем элемент уведомления
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Добавляем уведомление в начало страницы
        const container = document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);

        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

/**
 * Функция для получения ID задачи из URL
 */
function getTaskIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    const taskIdIndex = pathParts.findIndex(part => part === 'my-tasks') + 1;
    return pathParts[taskIdIndex] ? parseInt(pathParts[taskIdIndex]) : null;
}

/**
 * Инициализация компонента изменения приоритета
 */
function initTaskPriorityChanger() {
    const taskId = getTaskIdFromUrl();
    if (taskId) {
        new TaskPriorityChanger(taskId);
    }
}

// Запускаем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', initTaskPriorityChanger);
