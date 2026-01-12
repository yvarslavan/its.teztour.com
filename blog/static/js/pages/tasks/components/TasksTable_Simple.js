/**
 * TasksTable_Simple - Упрощенная версия компонента таблицы задач
 * Автономная версия без зависимостей с поддержкой бесконечной прокрутки
 * ИСПРАВЛЕНО: Улучшена инициализация и обработка зависимостей
 */
class TasksTable_Simple {
  constructor() {
    // ИСПРАВЛЕНИЕ: Создаем собственные зависимости если они отсутствуют
    this.eventBus = window.eventBus || this.createEventBus();
    this.loadingManager = window.loadingManager || this.createLoadingManager();

    this.tableElement = null;
    this.isInitialized = false;
    this.currentData = [];
    this.currentPage = 1;
    this.pageSize = 25;
    this.totalRecords = 0;
    this.isLoading = false;
    this.hasMoreData = true;
    this.currentFilters = {};
    this.initializationAttempts = 0;
    this.maxInitializationAttempts = 5;

    console.log('[TasksTable] 🚀 Конструктор вызван, планируем инициализацию...');

    // ИСПРАВЛЕНИЕ: Более надежная инициализация с проверками
    this.scheduleInitialization();
  }

  // ИСПРАВЛЕНИЕ: Создаем собственный EventBus если отсутствует
  createEventBus() {
    console.log('[TasksTable] 🔧 Создаем собственный EventBus');
    return {
      listeners: {},
      on: function(event, callback) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(callback);
      },
      emit: function(event, data) {
        if (this.listeners[event]) {
          this.listeners[event].forEach(callback => {
            try {
              callback(data);
            } catch (error) {
              console.error('[EventBus] Ошибка в callback:', error);
            }
          });
        }
      }
    };
  }

  // ИСПРАВЛЕНИЕ: Создаем собственный LoadingManager если отсутствует
  createLoadingManager() {
    console.log('[TasksTable] 🔧 Создаем собственный LoadingManager');
    return {
      show: (message) => {
        console.log('[TasksTable] 🔄 Показываем загрузку:', message);
        let loadingDiv = document.getElementById('tasks-loading-indicator');
        if (!loadingDiv) {
          loadingDiv = document.createElement('div');
          loadingDiv.id = 'tasks-loading-indicator';
          loadingDiv.style.cssText = `
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1); z-index: 1000;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          `;
          document.body.appendChild(loadingDiv);
        }
        loadingDiv.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${message || 'Загрузка...'}`;
        loadingDiv.style.display = 'block';
      },
      hide: () => {
        const loadingDiv = document.getElementById('tasks-loading-indicator');
        if (loadingDiv) {
          loadingDiv.style.display = 'none';
        }
      }
    };
  }

  // ИСПРАВЛЕНИЕ: Планируем инициализацию с проверками готовности
  scheduleInitialization() {
    const attemptInitialization = () => {
      this.initializationAttempts++;
      console.log(`[TasksTable] 🔄 Попытка инициализации ${this.initializationAttempts}/${this.maxInitializationAttempts}`);

      // Проверяем готовность DOM
      if (document.readyState === 'loading') {
        console.log('[TasksTable] ⏳ DOM еще загружается, ждем...');
        document.addEventListener('DOMContentLoaded', () => {
          setTimeout(attemptInitialization, 100);
        });
        return;
      }

      // Проверяем наличие таблицы
      this.tableElement = document.getElementById('tasksTable');
      if (!this.tableElement) {
        if (this.initializationAttempts < this.maxInitializationAttempts) {
          console.log('[TasksTable] ⏳ Таблица не найдена, повторная попытка через 500мс...');
          setTimeout(attemptInitialization, 500);
          return;
        } else {
          console.error('[TasksTable] ❌ Таблица #tasksTable не найдена после всех попыток');
          this.showError('Таблица задач не найдена на странице');
          return;
        }
      }

      // Инициализируем
      this.init().catch(error => {
        console.error('[TasksTable] ❌ Ошибка инициализации:', error);
        if (this.initializationAttempts < this.maxInitializationAttempts) {
          setTimeout(attemptInitialization, 1000);
        }
      });
    };

    // Начинаем попытки инициализации
    setTimeout(attemptInitialization, 100);
  }

  async init() {
    try {
      console.log('[TasksTable] 🚀 Начинаем инициализацию таблицы задач...');

      if (this.isInitialized) {
        console.log('[TasksTable] ✅ Таблица уже инициализирована');
        return;
      }

      // Настраиваем обработчики событий
      this._setupEventListeners();

      // Настраиваем прокрутку
      this._setupScrollListener();

      this.isInitialized = true;
      console.log('[TasksTable] ✅ Таблица задач инициализирована успешно');

      // ИСПРАВЛЕНИЕ: Автоматически загружаем данные при инициализации
      console.log('[TasksTable] 🔄 Загружаем начальные данные...');
      await this.loadTasks();

      // Уведомляем о готовности
      this.eventBus.emit('table:initialized', {
        component: 'TasksTable_Simple',
        timestamp: new Date().toISOString()
      });

    } catch (error) {
      console.error('[TasksTable] ❌ Ошибка инициализации:', error);
      this.showError('Ошибка инициализации таблицы: ' + error.message);
      this.eventBus.emit('table:error', { error: error.message });
      throw error;
    }
  }

  _setupEventListeners() {
    console.log('[TasksTable] 🔧 Настройка обработчиков событий...');

    // Слушаем события от других компонентов
    this.eventBus.on('filters:changed', (data) => {
      console.log('[TasksTable] 🔍 Получено событие filters:changed:', data);
      this.applyFilters(data.filters);
    });

    this.eventBus.on('search:changed', (data) => {
      console.log('[TasksTable] 🔍 Получено событие search:changed:', data);
      this.search(data.searchTerm);
    });

    this.eventBus.on('table:refresh', () => {
      console.log('[TasksTable] 🔄 Получено событие table:refresh');
      this.refresh();
    });
  }

  _setupScrollListener() {
    console.log('[TasksTable] 🔧 Настройка прокрутки...');

    const container = document.getElementById('tasks-table-container') ||
                     document.querySelector('.table-responsive') ||
                     this.tableElement?.parentElement;

    if (container) {
      container.addEventListener('scroll', () => {
        if (this.isLoading || !this.hasMoreData) return;

        const scrollTop = container.scrollTop;
        const scrollHeight = container.scrollHeight;
        const clientHeight = container.clientHeight;

        // Загружаем новые данные когда пользователь прокрутил на 80% вниз
        if (scrollTop + clientHeight >= scrollHeight * 0.8) {
          console.log('[TasksTable] 📜 Достигнут порог прокрутки, загружаем еще данные...');
          this.loadMoreTasks();
        }
      });
      console.log('[TasksTable] ✅ Прокрутка настроена для контейнера:', container.id || container.className);
    } else {
      console.warn('[TasksTable] ⚠️ Контейнер для прокрутки не найден');
    }
  }

  async loadTasks(resetData = true) {
    console.log('[TasksTable] 📡 loadTasks вызван, resetData:', resetData);

    if (resetData) {
      this.currentPage = 1;
      this.currentData = [];
      this.hasMoreData = true;
    }

    return this.loadMoreTasks();
  }

  async loadMoreTasks() {
    if (this.isLoading || !this.hasMoreData) {
      console.log('[TasksTable] ⏭️ Пропускаем загрузку: isLoading=', this.isLoading, 'hasMoreData=', this.hasMoreData);
      return;
    }

    try {
      console.log('[TasksTable] 📡 Загрузка задач, страница:', this.currentPage);

      this.isLoading = true;
      if (this.currentPage === 1) {
        this.loadingManager.show('Загрузка задач...');
      }

      // Собираем параметры запроса
      const params = {
        start: (this.currentPage - 1) * this.pageSize,
        length: this.pageSize,
        ...this.currentFilters
      };

      // ИСПРАВЛЕНИЕ: Более надежное получение значений фильтров
      const searchInput = document.getElementById('searchInput');
      const statusFilter = document.getElementById('statusFilter');
      const projectFilter = document.getElementById('projectFilter');
      const priorityFilter = document.getElementById('priorityFilter');

      if (searchInput?.value?.trim()) {
        params.search = searchInput.value.trim();
        console.log('[TasksTable] 🔍 Добавлен поиск:', params.search);
      }
      if (statusFilter?.value && statusFilter.value !== '') {
        params.status_filter = statusFilter.value;
        console.log('[TasksTable] 🔍 Добавлен фильтр статуса:', params.status_filter);
      }
      if (projectFilter?.value && projectFilter.value !== '') {
        params.project_filter = projectFilter.value;
        console.log('[TasksTable] 🔍 Добавлен фильтр проекта:', params.project_filter);
      }
      if (priorityFilter?.value && priorityFilter.value !== '') {
        params.priority_filter = priorityFilter.value;
        console.log('[TasksTable] 🔍 Добавлен фильтр приоритета:', params.priority_filter);
      }

      console.log('[TasksTable] 📡 Параметры запроса:', params);

      const response = await fetch('/tasks/api/tasks?' + new URLSearchParams(params));

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('[TasksTable] 📡 Ответ API:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      const newTasks = data.data || [];
      this.totalRecords = data.recordsTotal || 0;

      console.log('[TasksTable] 📊 Получено задач:', newTasks.length, 'Всего в системе:', this.totalRecords);

      if (this.currentPage === 1) {
        this.currentData = newTasks;
      } else {
        this.currentData = [...this.currentData, ...newTasks];
      }

      // Проверяем, есть ли еще данные
      this.hasMoreData = newTasks.length === this.pageSize && this.currentData.length < this.totalRecords;

      this.renderTable(this.currentData, this.currentPage === 1);
      this.currentPage++;

      this.eventBus.emit('table:dataLoaded', {
        data: this.currentData,
        total: this.totalRecords,
        page: this.currentPage - 1,
        hasMoreData: this.hasMoreData
      });

      console.log('[TasksTable] ✅ Загружено задач:', newTasks.length, 'Всего в таблице:', this.currentData.length);

    } catch (error) {
      console.error('[TasksTable] ❌ Ошибка загрузки данных:', error);
      this.showError('Ошибка загрузки задач: ' + error.message);
      this.eventBus.emit('table:error', { error: error.message });
    } finally {
      this.isLoading = false;
      this.loadingManager.hide();
    }
  }

  renderTable(data, clearTable = true) {
    console.log('[TasksTable] 🎨 Рендеринг таблицы, данных:', data?.length, 'очистка:', clearTable);

    const tbody = this.tableElement.querySelector('tbody');
    if (!tbody) {
      console.error('[TasksTable] ❌ tbody не найден в таблице');
      return;
    }

    if (clearTable) {
      tbody.innerHTML = '';
    }

    if (!data || data.length === 0) {
      if (clearTable) {
        tbody.innerHTML = `
          <tr>
            <td colspan="8" class="text-center" style="padding: 2rem; color: #6b7280;">
              <i class="fas fa-inbox" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
              Нет задач для отображения
            </td>
          </tr>
        `;
      }
      return;
    }

    // ИСПРАВЛЕНИЕ: Улучшенный рендеринг строк с обработкой ошибок и добавлением колонки "Отправитель"
    const rowsHTML = data.map(task => {
      try {
        return `
          <tr data-task-id="${task.id || 'unknown'}" style="transition: background-color 0.2s ease;">
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0;">
              <a href="/tasks/my-tasks/${task.id || 'unknown'}" class="task-link"
                 style="color: #667eea; font-weight: 600; text-decoration: none;"
                 data-task-id="${task.id || 'unknown'}">
                #${task.id || 'N/A'}
              </a>
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #374151;">
              ${this.escapeHtml(task.subject) || 'Без темы'}
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0;">
              <span class="badge badge-status" style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; background: #dbeafe; color: #1e40af;">
                ${this.escapeHtml(task.status_name) || 'Неизвестно'}
              </span>
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #374151;">
              ${this.escapeHtml(task.project_name) || 'Неизвестно'}
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0;">
              <span class="badge badge-priority" style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; background: #fef3c7; color: #92400e;">
                ${this.escapeHtml(task.priority_name) || 'Обычный'}
              </span>
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #374151;">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="fas fa-envelope" style="color: #6b7280; font-size: 0.8rem;"></i>
                <span style="font-size: 0.9rem;">${this.escapeHtml(task.easy_email_to) || 'Не указан'}</span>
              </div>
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #6b7280;">
              ${task.created_on ? new Date(task.created_on).toLocaleDateString('ru-RU') : '-'}
            </td>
            <td style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #6b7280;">
              ${task.updated_on ? new Date(task.updated_on).toLocaleDateString('ru-RU') : '-'}
            </td>
          </tr>
        `;
      } catch (error) {
        console.error('[TasksTable] ❌ Ошибка рендеринга задачи:', task, error);
        return `
          <tr>
            <td colspan="8" style="padding: 0.75rem; border-bottom: 1px solid #e2e8f0; color: #dc3545;">
              ⚠️ Ошибка отображения задачи
            </td>
          </tr>
        `;
      }
    }).join('');

    if (clearTable) {
      tbody.innerHTML = rowsHTML;
    } else {
      tbody.insertAdjacentHTML('beforeend', rowsHTML);
    }

    // Добавляем индикатор загрузки если есть еще данные
    if (this.hasMoreData && !clearTable) {
      const loadingRow = document.createElement('tr');
      loadingRow.innerHTML = `
        <td colspan="8" class="text-center" style="padding: 1rem;">
          <i class="fas fa-spinner fa-spin"></i> Загрузка...
        </td>
      `;
      tbody.appendChild(loadingRow);
    }

    // Привязываем события клика
    this.bindRowEvents();

    console.log('[TasksTable] ✅ Таблица отрендерена, строк:', tbody.querySelectorAll('tr[data-task-id]').length);
  }

  // ИСПРАВЛЕНИЕ: Добавляем метод для экранирования HTML
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  bindRowEvents() {
    const rows = this.tableElement.querySelectorAll('tbody tr[data-task-id]');
    rows.forEach(row => {
      // Добавляем hover эффект
      row.addEventListener('mouseenter', () => {
        row.style.backgroundColor = '#f8fafc';
      });

      row.addEventListener('mouseleave', () => {
        row.style.backgroundColor = '';
      });

      row.addEventListener('click', (e) => {
        // Если клик по ссылке задачи, позволяем стандартную навигацию
        if (e.target.classList.contains('task-link') || e.target.closest('.task-link')) {
          return; // Позволяем стандартную навигацию по href
        }

        const taskId = row.dataset.taskId;
        this.eventBus.emit('task:click', { taskId });
      });
    });

    // Дополнительно привязываем обработчики для ссылок задач
    const taskLinks = this.tableElement.querySelectorAll('.task-link');
    taskLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const taskId = link.dataset.taskId || link.getAttribute('href').split('/').pop();
        console.log('[TasksTable] 🔗 Переход к задаче:', taskId);

        // Позволяем стандартную навигацию
        // Можно добавить дополнительную логику здесь при необходимости
      });
    });
  }

  applyFilters(filters) {
    console.log('[TasksTable] 🔍 Применение фильтров:', filters);
    this.currentFilters = filters;
    this.loadTasks(true);
  }

  search(searchTerm) {
    console.log('[TasksTable] 🔍 Поиск:', searchTerm);
    this.currentFilters.search = searchTerm;
    this.loadTasks(true);
  }

  refresh() {
    console.log('[TasksTable] 🔄 Обновление таблицы');
    this.loadTasks(true);
  }

  showError(message) {
    const tbody = this.tableElement.querySelector('tbody');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger" style="padding: 2rem; color: #dc3545;">⚠️ ${message}</td></tr>`;
    }
  }

  // Методы для совместимости с TasksApp
  clearFilters() {
    console.log('[TasksTable] 🧹 Очистка фильтров');
    this.currentFilters = {};
    this.loadTasks(true);
  }

  destroy() {
    console.log('[TasksTable] 🗑️ Очистка ресурсов');
    this.isInitialized = false;
    this.currentData = [];
    this.currentFilters = {};
  }
}

// Экспорт для использования
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TasksTable_Simple;
} else {
  window.TasksTable_Simple = TasksTable_Simple;
}
