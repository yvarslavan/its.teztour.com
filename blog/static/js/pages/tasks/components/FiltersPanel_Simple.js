/**
 * FiltersPanel_Simple - Упрощенная версия компонента панели фильтров
 * Автономная версия без зависимостей
 */
class FiltersPanel_Simple {
  constructor() {
    this.eventBus = window.eventBus;
    this.loadingManager = window.loadingManager;
    this.panelElement = null;
    this.isInitialized = false;
    this.currentFilters = {};
    this.debouncedSearch = null;

    // Задержка для гарантии готовности DOM и глобальных переменных
    setTimeout(() => this.init(), 200);
  }

  async init() {
    try {
      console.log('[FiltersPanel] 🚀 Инициализация панели фильтров...');

      // Проверяем наличие панели
      this.panelElement = document.querySelector('.filters-container');
      if (!this.panelElement) {
        throw new Error('Панель .filters-container не найдена');
      }

      // Настраиваем debounced поиск
      this.debouncedSearch = this.debounce(this.performSearch.bind(this), 500);

      // Настраиваем обработчики событий
      this._setupEventListeners();

      // Загружаем фильтры
      await this.loadFilters();

      // Инициализируем состояние фильтров
      this._initializeFilterState();

      this.isInitialized = true;
      console.log('[FiltersPanel] ✅ Панель фильтров инициализирована');

      // Уведомляем о готовности
      this.eventBus.emit('filters:initialized');

    } catch (error) {
      console.error('[FiltersPanel] ❌ Ошибка инициализации:', error);
      this.eventBus.emit('filters:error', { error: error.message });
      throw error;
    }
  }

  _setupEventListeners() {
    // Поиск
    const searchInput = this.panelElement.querySelector('#searchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.debouncedSearch(e.target.value);
      });
    }

    // Фильтры
    const statusFilter = this.panelElement.querySelector('#statusFilter');
    if (statusFilter) {
      statusFilter.addEventListener('change', () => this.applyFilters());
    }

    const projectFilter = this.panelElement.querySelector('#projectFilter');
    if (projectFilter) {
      projectFilter.addEventListener('change', () => this.applyFilters());
    }

    const priorityFilter = this.panelElement.querySelector('#priorityFilter');
    if (priorityFilter) {
      priorityFilter.addEventListener('change', () => this.applyFilters());
    }

    // Кнопка сброса
    const resetButton = this.panelElement.querySelector('#clearFilters');
    if (resetButton) {
      resetButton.addEventListener('click', () => this.resetAllFilters());
    }
  }

  async loadFilters() {
    try {
      console.log('[FiltersPanel] 📋 Загрузка фильтров...');

      // Загружаем проекты
      const projectsResponse = await fetch('/tasks/api/projects');
      const projectsData = await projectsResponse.json();

      if (projectsData.success && projectsData.projects) {
        this.populateProjectFilter(projectsData.projects);
      }

      // Загружаем статусы
      const statusesResponse = await fetch('/tasks/api/statuses');
      const statusesData = await statusesResponse.json();

      if (statusesData.success && statusesData.statuses) {
        this.populateStatusFilter(statusesData.statuses);
      }

      // Загружаем приоритеты
      const prioritiesResponse = await fetch('/tasks/api/priorities');
      const prioritiesData = await prioritiesResponse.json();

      if (prioritiesData.success && prioritiesData.priorities) {
        this.populatePriorityFilter(prioritiesData.priorities);
      }

      console.log('[FiltersPanel] ✅ Фильтры загружены');

    } catch (error) {
      console.error('[FiltersPanel] ❌ Ошибка загрузки фильтров:', error);
    }
  }

  populateProjectFilter(projects) {
    const projectFilter = this.panelElement.querySelector('#projectFilter');
    if (!projectFilter) return;

    projectFilter.innerHTML = '<option value="">Все проекты</option>' +
      projects.map(project =>
        `<option value="${project.id}">${project.name}</option>`
      ).join('');
  }

  populateStatusFilter(statuses) {
    const statusFilter = this.panelElement.querySelector('#statusFilter');
    if (!statusFilter) return;

    statusFilter.innerHTML = '<option value="">Все статусы</option>' +
      statuses.map(status =>
        `<option value="${status.id}">${status.name}</option>`
      ).join('');
  }

  populatePriorityFilter(priorities) {
    const priorityFilter = this.panelElement.querySelector('#priorityFilter');
    if (!priorityFilter) return;

    priorityFilter.innerHTML = '<option value="">Все приоритеты</option>' +
      priorities.map(priority =>
        `<option value="${priority.id}">${priority.name}</option>`
      ).join('');
  }

  applyFilters() {
    const filters = this.getCurrentFilters();
    this.currentFilters = filters;

    console.log('[FiltersPanel] 🔍 Применение фильтров:', filters);
    this.eventBus.emit('filters:changed', { filters });
  }

  getCurrentFilters() {
    const searchInput = this.panelElement.querySelector('#searchInput');
    const statusFilter = this.panelElement.querySelector('#statusFilter');
    const projectFilter = this.panelElement.querySelector('#projectFilter');
    const priorityFilter = this.panelElement.querySelector('#priorityFilter');

    return {
      search: searchInput ? searchInput.value.trim() : '',
      status_filter: statusFilter ? statusFilter.value : '',
      project_filter: projectFilter ? projectFilter.value : '',
      priority_filter: priorityFilter ? priorityFilter.value : ''
    };
  }

  performSearch(searchTerm) {
    console.log('[FiltersPanel] 🔍 Поиск:', searchTerm);
    this.eventBus.emit('search:changed', { searchTerm });
  }

  resetAllFilters() {
    console.log('[FiltersPanel] 🧹 Сброс всех фильтров');

    // Очищаем все поля
    const searchInput = this.panelElement.querySelector('#searchInput');
    if (searchInput) searchInput.value = '';

    const statusFilter = this.panelElement.querySelector('#statusFilter');
    if (statusFilter) statusFilter.value = '';

    const projectFilter = this.panelElement.querySelector('#projectFilter');
    if (projectFilter) projectFilter.value = '';

    const priorityFilter = this.panelElement.querySelector('#priorityFilter');
    if (priorityFilter) priorityFilter.value = '';

    this.currentFilters = {};
    this.eventBus.emit('filters:reset');
  }

  _initializeFilterState() {
    // Инициализируем состояние фильтров
    this.resetAllFilters();
  }

  // Утилита debounce
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Методы для совместимости с TasksApp
  clearFilters() {
    console.log('[FiltersPanel] 🧹 Очистка фильтров');
    this.resetAllFilters();
  }

  getFilters() {
    return this.getCurrentFilters();
  }

  setFilters(filters) {
    console.log('[FiltersPanel] 📝 Установка фильтров:', filters);

    if (filters.search !== undefined) {
      const searchInput = this.panelElement.querySelector('#searchInput');
      if (searchInput) searchInput.value = filters.search;
    }

    if (filters.status_filter !== undefined) {
      const statusFilter = this.panelElement.querySelector('#statusFilter');
      if (statusFilter) statusFilter.value = filters.status_filter;
    }

    if (filters.project_filter !== undefined) {
      const projectFilter = this.panelElement.querySelector('#projectFilter');
      if (projectFilter) projectFilter.value = filters.project_filter;
    }

    if (filters.priority_filter !== undefined) {
      const priorityFilter = this.panelElement.querySelector('#priorityFilter');
      if (priorityFilter) priorityFilter.value = filters.priority_filter;
    }

    this.currentFilters = filters;
  }

  destroy() {
    console.log('[FiltersPanel] 🗑️ Очистка ресурсов');
    this.isInitialized = false;
    this.currentFilters = {};
  }
}

// Экспорт для использования
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FiltersPanel_Simple;
} else {
  window.FiltersPanel_Simple = FiltersPanel_Simple;
}
