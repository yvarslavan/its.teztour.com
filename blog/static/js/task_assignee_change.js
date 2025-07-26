/**
 * JavaScript для изменения исполнителя задачи на странице детализации
 * Работает с API endpoints: GET /tasks/api/users и PUT /tasks/api/task/<id>/assignee
 */

class TaskAssigneeChanger {
    constructor(taskId) {
        this.taskId = taskId;
        this.currentAssigneeId = null;
        this.isLoading = false;
        this.init();
    }

    /**
     * Инициализация компонента
     */
    init() {
        this.loadCurrentAssignee();
        this.bindEvents();
    }

    /**
     * Загрузка текущего исполнителя
     */
    async loadCurrentAssignee() {
        try {
            // Получаем информацию о задаче для определения текущего исполнителя
            const response = await fetch(`/tasks/api/task/${this.taskId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.currentAssigneeId = data.data.assigned_to_id;
                this.renderAssigneeSelector(data.data.assigned_to_name, data.data.assigned_to_id);
            } else {
                this.showError('Не удалось загрузить информацию о задаче: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка загрузки исполнителя:', error);
            this.showError('Ошибка загрузки исполнителя. Попробуйте обновить страницу.');
        }
    }

    /**
     * Отрисовка селектора исполнителя
     */
    async renderAssigneeSelector(currentAssigneeName, currentAssigneeId) {
        const assigneeContainer = document.getElementById('task-assignee-container');
        if (!assigneeContainer) {
            console.error('Контейнер для исполнителя не найден');
            return;
        }

        try {
            this.showLoading(true);

            // Загружаем список доступных пользователей
            const usersResponse = await fetch('/tasks/api/users', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const usersData = await usersResponse.json();

            if (!usersData.success) {
                this.showError('Не удалось загрузить список пользователей: ' + usersData.error);
                return;
            }

            // Создаем HTML для изменения исполнителя
            const assigneeHTML = `
                <div class="task-assignee-changer">
                    <div class="current-assignee">
                        <label class="form-label">Текущий исполнитель:</label>
                        <div class="user-avatar">
                            <div class="avatar-circle assigned">${currentAssigneeName ? currentAssigneeName[0].toUpperCase() : 'U'}</div>
                            <span class="user-name">${currentAssigneeName || 'Не назначен'}</span>
                        </div>
                    </div>

                    <div class="assignee-change-form mt-3">
                        <label class="form-label">Изменить исполнителя:</label>
                        <div class="row">
                            <div class="col-md-6">
                                <select class="form-select" id="new-assignee-select">
                                    <option value="">Выберите нового исполнителя</option>
                                    <option value="">Снять назначение</option>
                                    ${usersData.users.map(user =>
                                        `<option value="${user.id}" ${user.id === currentAssigneeId ? 'disabled' : ''}>${user.name}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div class="col-md-6">
                                <button type="button" class="btn btn-primary" id="change-assignee-btn" disabled>
                                    <i class="fas fa-user-edit"></i> Изменить исполнителя
                                </button>
                            </div>
                        </div>

                        <div class="mt-3">
                            <label class="form-label">Комментарий (необязательно):</label>
                            <textarea class="form-control" id="assignee-comment" rows="3"
                                      placeholder="Добавьте комментарий к изменению исполнителя..."></textarea>
                        </div>
                    </div>
                </div>
            `;

            assigneeContainer.innerHTML = assigneeHTML;

        } catch (error) {
            console.error('Ошибка загрузки пользователей:', error);
            this.showError('Ошибка загрузки списка пользователей. Попробуйте обновить страницу.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Привязка событий
     */
    bindEvents() {
        document.addEventListener('change', (event) => {
            if (event.target.id === 'new-assignee-select') {
                this.handleAssigneeSelectChange(event);
            }
        });

        document.addEventListener('click', (event) => {
            if (event.target.id === 'change-assignee-btn') {
                this.handleAssigneeChange(event);
            }
        });
    }

    /**
     * Обработка изменения выбора исполнителя
     */
    handleAssigneeSelectChange(event) {
        const newAssigneeSelect = document.getElementById('new-assignee-select');
        const changeAssigneeBtn = document.getElementById('change-assignee-btn');

        if (newAssigneeSelect && changeAssigneeBtn) {
            changeAssigneeBtn.disabled = !newAssigneeSelect.value;
        }
    }

    /**
     * Обработка изменения исполнителя
     */
    async handleAssigneeChange(event) {
        if (this.isLoading) return;

        const newAssigneeSelect = document.getElementById('new-assignee-select');
        const commentField = document.getElementById('assignee-comment');

        if (!newAssigneeSelect || !newAssigneeSelect.value) {
            this.showError('Выберите нового исполнителя');
            return;
        }

        const newAssigneeId = newAssigneeSelect.value === '' ? null : parseInt(newAssigneeSelect.value);
        const comment = commentField ? commentField.value.trim() : '';

        // Подтверждение изменения
        const selectedAssigneeText = newAssigneeSelect.options[newAssigneeSelect.selectedIndex].text;
        const confirmMessage = newAssigneeId
            ? `Вы действительно хотите назначить исполнителем "${selectedAssigneeText}"?`
            : 'Вы действительно хотите снять назначение исполнителя?';

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            this.showLoading(true);

            const response = await fetch(`/tasks/api/task/${this.taskId}/assignee`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'include',
                body: JSON.stringify({
                    assignee_id: newAssigneeId,
                    comment: comment
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess(data.message);
                this.updateCurrentAssignee(newAssigneeId, data.new_assignee_name);
                this.resetForm();

                // Обновляем страницу через 2 секунды для отображения изменений
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
            } else {
                this.showError('Ошибка изменения исполнителя: ' + data.error);
            }
        } catch (error) {
            console.error('Ошибка изменения исполнителя:', error);
            this.showError('Произошла ошибка при изменении исполнителя. Попробуйте еще раз.');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Обновление отображения текущего исполнителя
     */
    updateCurrentAssignee(newAssigneeId, newAssigneeName) {
        const currentAssigneeDisplay = document.querySelector('.current-assignee .user-name');
        const currentAssigneeAvatar = document.querySelector('.current-assignee .avatar-circle');

        if (currentAssigneeDisplay) {
            currentAssigneeDisplay.textContent = newAssigneeName || 'Не назначен';
        }

        if (currentAssigneeAvatar) {
            currentAssigneeAvatar.textContent = newAssigneeName ? newAssigneeName[0].toUpperCase() : 'U';
        }
    }

    /**
     * Сброс формы
     */
    resetForm() {
        const newAssigneeSelect = document.getElementById('new-assignee-select');
        const assigneeComment = document.getElementById('assignee-comment');
        const changeAssigneeBtn = document.getElementById('change-assignee-btn');

        if (newAssigneeSelect) newAssigneeSelect.value = '';
        if (assigneeComment) assigneeComment.value = '';
        if (changeAssigneeBtn) changeAssigneeBtn.disabled = true;
    }

    /**
     * Показ/скрытие индикатора загрузки
     */
    showLoading(show) {
        const assigneeContainer = document.getElementById('task-assignee-container');
        if (!assigneeContainer) return;

        if (show) {
            assigneeContainer.innerHTML = `
                <div class="loading-placeholder">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Обновление исполнителя...</span>
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
    // Пробуем разные форматы URL
    const pathParts = window.location.pathname.split('/');

    // Формат: /tasks/my-tasks/12345
    let taskIdIndex = pathParts.findIndex(part => part === 'my-tasks') + 1;
    if (taskIdIndex > 0 && pathParts[taskIdIndex]) {
        return parseInt(pathParts[taskIdIndex]);
    }

    // Формат: /tasks/12345
    taskIdIndex = pathParts.findIndex(part => part === 'tasks') + 1;
    if (taskIdIndex > 0 && pathParts[taskIdIndex] && !isNaN(pathParts[taskIdIndex])) {
        return parseInt(pathParts[taskIdIndex]);
    }

    // Формат: /task/12345
    taskIdIndex = pathParts.findIndex(part => part === 'task') + 1;
    if (taskIdIndex > 0 && pathParts[taskIdIndex] && !isNaN(pathParts[taskIdIndex])) {
        return parseInt(pathParts[taskIdIndex]);
    }

    // Пробуем найти число в URL
    const urlMatch = window.location.pathname.match(/\/(\d+)(?:\/|$)/);
    if (urlMatch) {
        return parseInt(urlMatch[1]);
    }

    console.warn('Не удалось определить ID задачи из URL:', window.location.pathname);
    return null;
}

/**
 * Инициализация компонента изменения исполнителя
 */
function initTaskAssigneeChanger() {
    const taskId = getTaskIdFromUrl();
    if (taskId) {
        console.log('Инициализация TaskAssigneeChanger для задачи:', taskId);
        new TaskAssigneeChanger(taskId);
    } else {
        console.warn('TaskAssigneeChanger: ID задачи не найден в URL');
        // Показываем сообщение пользователю, если контейнер существует
        const assigneeContainer = document.getElementById('task-assignee-container');
        if (assigneeContainer) {
            assigneeContainer.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Не удалось определить ID задачи. Обновите страницу.</span>
                </div>
            `;
        }
    }
}

// Запускаем инициализацию при загрузке страницы
document.addEventListener('DOMContentLoaded', initTaskAssigneeChanger);
