/**
 * DashboardManager.js - Управление различными типами дашбордов
 * v1.0.0
 */

class DashboardManager {
    constructor() {
        this.currentView = 'list';
        this.dashboards = {
            kanban: null,
            analytics: null,
            priority: null,
            projects: null
        };

        this.init();
    }

    init() {
        console.log('[DashboardManager] 🚀 Инициализация менеджера дашбордов');
        this.setupEventListeners();
        this.loadDashboardData();
        this.restoreViewFromURL();
    }

    setupEventListeners() {
        // Переключение между видами
        document.addEventListener('click', (e) => {
            if (e.target.closest('.view-toggle-btn')) {
                const btn = e.target.closest('.view-toggle-btn');
                const view = btn.dataset.view;
                this.switchView(view);
            }
        });

        // Drag & Drop для Kanban
        this.setupKanbanDragDrop();
    }

    restoreViewFromURL() {
        // Проверяем URL параметры для восстановления режима просмотра
        const urlParams = new URLSearchParams(window.location.search);
        const viewParam = urlParams.get('view');

        console.log(`[DashboardManager] 🔍 Проверка восстановления режима просмотра`);
        console.log(`[DashboardManager] 📋 URL параметры:`, Object.fromEntries(urlParams.entries()));
        console.log(`[DashboardManager] 💾 sessionStorage:`, Object.fromEntries(Object.entries(sessionStorage)));

        if (viewParam && ['list', 'kanban'].includes(viewParam)) {
            console.log(`[DashboardManager] 🔄 Восстанавливаем режим просмотра из URL: ${viewParam}`);

            // Небольшая задержка для полной загрузки DOM
            setTimeout(() => {
                this.switchView(viewParam);
            }, 100);
        } else {
            // Проверяем сохраненный режим в sessionStorage
            const savedView = sessionStorage.getItem('return_from_task_view');
            console.log(`[DashboardManager] 🔍 Сохраненный режим из sessionStorage: ${savedView}`);

            if (savedView && ['list', 'kanban'].includes(savedView)) {
                console.log(`[DashboardManager] 🔄 Восстанавливаем режим просмотра из sessionStorage: ${savedView}`);

                setTimeout(() => {
                    this.switchView(savedView);
                }, 100);
            } else {
                console.log(`[DashboardManager] ⚠️ Режим просмотра не найден, используем 'list' по умолчанию`);
            }
        }
    }

    switchView(view) {
        console.log(`[DashboardManager] 🔄 Переключение на вид: ${view}`);

        // Обновляем активную кнопку
        const allButtons = document.querySelectorAll('.view-toggle-btn');
        console.log(`[DashboardManager] 🔍 Найдено кнопок переключения: ${allButtons.length}`);

        allButtons.forEach(btn => {
            btn.classList.remove('active');
            console.log(`[DashboardManager] 🔧 Убрана активность с кнопки: ${btn.dataset.view}`);
        });

        const targetButton = document.querySelector(`[data-view="${view}"]`);
        if (targetButton) {
            targetButton.classList.add('active');
            console.log(`[DashboardManager] ✅ Установлена активность на кнопку: ${view}`);
        } else {
            console.error(`[DashboardManager] ❌ Кнопка для вида не найдена: ${view}`);
        }

        // Скрываем/показываем соответствующие секции
        this.toggleDashboardSections(view);

        this.currentView = view;

        // Сохраняем режим просмотра в sessionStorage
        sessionStorage.setItem('return_from_task_view', view);
        console.log(`[DashboardManager] 💾 Сохранен режим просмотра: ${view}`);
    }

    toggleDashboardSections(view) {
        console.log(`[DashboardManager] 🔄 Переключение секций на вид: ${view}`);

        const sections = {
            'list': ['.table-container'],
            'kanban': ['.kanban-board'],
            'analytics': ['.analytics-dashboard'],
            'priority': ['.priority-dashboard'],
            'projects': ['.projects-dashboard']
        };

        // Скрываем все секции
        Object.values(sections).flat().forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.style.display = 'none';
                console.log(`[DashboardManager] 👁️ Скрыта секция: ${selector}`);
            } else {
                console.log(`[DashboardManager] ⚠️ Секция не найдена: ${selector}`);
            }
        });

        // Показываем нужную секцию
        sections[view]?.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.style.display = 'block';
                console.log(`[DashboardManager] ✅ Показана секция: ${selector}`);
            } else {
                console.error(`[DashboardManager] ❌ Секция не найдена: ${selector}`);
            }
        });
    }

    async loadDashboardData() {
        try {
            console.log('[DashboardManager] 📊 Загрузка данных для дашбордов');

            // Пока отключаем загрузку несуществующих API endpoints
            // await Promise.all([
            //     this.loadKanbanData(),
            //     this.loadAnalyticsData(),
            //     this.loadPriorityData(),
            //     this.loadProjectsData()
            // ]);

        } catch (error) {
            console.error('[DashboardManager] ❌ Ошибка загрузки данных:', error);
        }
    }

    async loadKanbanData() {
        try {
            const response = await fetch('/api/tasks/kanban-data');
            const data = await response.json();

            this.renderKanbanBoard(data);

        } catch (error) {
            console.error('[DashboardManager] ❌ Ошибка загрузки Kanban данных:', error);
        }
    }

    async loadAnalyticsData() {
        try {
            const response = await fetch('/api/tasks/analytics-data');
            const data = await response.json();

            this.renderAnalyticsDashboard(data);

        } catch (error) {
            console.error('[DashboardManager] ❌ Ошибка загрузки аналитических данных:', error);
        }
    }

    async loadPriorityData() {
        try {
            const response = await fetch('/api/tasks/priority-data');
            const data = await response.json();

            this.renderPriorityDashboard(data);

        } catch (error) {
            console.error('[DashboardManager] ❌ Ошибка загрузки данных приоритетов:', error);
        }
    }

    async loadProjectsData() {
        try {
            const response = await fetch('/api/tasks/projects-data');
            const data = await response.json();

            this.renderProjectsDashboard(data);

        } catch (error) {
            console.error('[DashboardManager] ❌ Ошибка загрузки данных проектов:', error);
        }
    }

    renderKanbanBoard(data) {
        const kanbanContainer = document.querySelector('.kanban-columns');
        if (!kanbanContainer) return;

        // Очищаем существующие карточки
        document.querySelectorAll('.task-cards').forEach(container => {
            container.innerHTML = '';
        });

        // Заполняем колонки задачами
        Object.entries(data.columns).forEach(([status, tasks]) => {
            const column = document.querySelector(`[data-status="${status}"]`);
            if (!column) return;

            const taskCards = column.querySelector('.task-cards');
            const taskCount = column.querySelector('.task-count');

            // Обновляем счетчик
            taskCount.textContent = tasks.length;

            // Создаем карточки задач
            tasks.forEach(task => {
                const taskCard = this.createTaskCard(task);
                taskCards.appendChild(taskCard);
            });
        });

        console.log('[DashboardManager] ✅ Kanban доска обновлена');
    }

    createTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.draggable = true;
        card.dataset.taskId = task.id;

        card.innerHTML = `
            <div class="task-card-header">
                <span class="task-id">#${task.id}</span>
                <span class="task-priority priority-${task.priority.toLowerCase()}">${task.priority}</span>
            </div>
            <div class="task-card-body">
                <h4 class="task-title">${task.subject}</h4>
                <p class="task-project">${task.project}</p>
            </div>
            <div class="task-card-footer">
                <span class="task-assignee">${task.assignee}</span>
                <span class="task-date">${task.updated_on}</span>
            </div>
        `;

        return card;
    }

    renderAnalyticsDashboard(data) {
        // Рендерим графики и метрики
        this.renderTimelineChart(data.timeline);
        this.renderProjectsChart(data.projects);
        this.renderMetrics(data.metrics);
    }

    renderTimelineChart(data) {
        const canvas = document.getElementById('tasksTimelineChart');
        if (!canvas) return;

        // Здесь будет код для создания графика
        console.log('[DashboardManager] 📈 График временной шкалы обновлен');
    }

    renderProjectsChart(data) {
        const canvas = document.getElementById('projectsChart');
        if (!canvas) return;

        // Здесь будет код для создания графика проектов
        console.log('[DashboardManager] 📊 График проектов обновлен');
    }

    renderMetrics(metrics) {
        const metricsContainer = document.querySelector('.metrics-card');
        if (!metricsContainer) return;

        // Обновляем метрики
        Object.entries(metrics).forEach(([key, value]) => {
            const metricElement = metricsContainer.querySelector(`[data-metric="${key}"]`);
            if (metricElement) {
                metricElement.textContent = value;
            }
        });
    }

    renderPriorityDashboard(data) {
        const priorityGrid = document.querySelector('.priority-grid');
        if (!priorityGrid) return;

        // Обновляем карточки приоритетов
        Object.entries(data.priorities).forEach(([priority, tasks]) => {
            const card = priorityGrid.querySelector(`.priority-card.${priority}`);
            if (!card) return;

            const countElement = card.querySelector('.priority-count');
            if (countElement) {
                countElement.textContent = tasks.length;
            }

            // Обновляем список задач
            const tasksContainer = card.querySelector('.priority-tasks');
            if (tasksContainer) {
                tasksContainer.innerHTML = '';
                tasks.slice(0, 3).forEach(task => {
                    const taskElement = document.createElement('div');
                    taskElement.className = 'priority-task-item';
                    taskElement.innerHTML = `
                        <span class="task-title">${task.subject}</span>
                        <span class="task-id">#${task.id}</span>
                    `;
                    tasksContainer.appendChild(taskElement);
                });
            }
        });
    }

    renderProjectsDashboard(data) {
        const projectsGrid = document.querySelector('.projects-grid');
        if (!projectsGrid) return;

        projectsGrid.innerHTML = '';

        // Создаем карточки проектов
        data.projects.forEach(project => {
            const projectCard = document.createElement('div');
            projectCard.className = 'project-card';

            const progressPercent = Math.round((project.completed / project.total) * 100);

            projectCard.innerHTML = `
                <div class="project-header">
                    <h3>${project.name}</h3>
                    <span class="project-progress">${progressPercent}%</span>
                </div>
                <div class="project-stats">
                    <div class="stat-item">
                        <span class="stat-label">Активные задачи</span>
                        <span class="stat-value">${project.active}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Завершённые</span>
                        <span class="stat-value">${project.completed}</span>
                    </div>
                </div>
                <div class="project-progress-bar">
                    <div class="progress-fill" style="width: ${progressPercent}%"></div>
                </div>
            `;

            projectsGrid.appendChild(projectCard);
        });
    }

    setupKanbanDragDrop() {
        const kanbanColumns = document.querySelectorAll('.kanban-column');

        kanbanColumns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                column.classList.add('drag-over');
            });

            column.addEventListener('dragleave', (e) => {
                column.classList.remove('drag-over');
            });

            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('drag-over');

                const taskCard = document.querySelector('.task-card.dragging');
                if (taskCard) {
                    const newStatus = column.dataset.status;
                    this.moveTask(taskCard.dataset.taskId, newStatus);
                    column.querySelector('.task-cards').appendChild(taskCard);
                }
            });
        });

        // Drag & Drop для карточек задач
        document.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('task-card')) {
                e.target.classList.add('dragging');
            }
        });

        document.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('task-card')) {
                e.target.classList.remove('dragging');
            }
        });
    }

    async moveTask(taskId, newStatus) {
        try {
            const response = await fetch(`/api/tasks/${taskId}/status`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                console.log(`[DashboardManager] ✅ Задача ${taskId} перемещена в статус ${newStatus}`);
            } else {
                console.error(`[DashboardManager] ❌ Ошибка перемещения задачи ${taskId}`);
            }
        } catch (error) {
            console.error('[DashboardManager] ❌ Ошибка перемещения задачи:', error);
        }
    }

    // Методы для обновления данных в реальном времени
    updateDashboardData() {
        this.loadDashboardData();
    }

    // Метод для экспорта данных
    exportDashboardData(type) {
        console.log(`[DashboardManager] 📤 Экспорт данных дашборда: ${type}`);
        // Здесь будет логика экспорта
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});
