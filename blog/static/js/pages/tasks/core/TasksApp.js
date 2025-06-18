/**
 * TasksApp - Главный контроллер приложения задач
 * Координирует работу всех компонентов и сервисов
 */
class TasksApp {
  constructor(config = {}) {
    this.config = {
      debug: false,
      autoInit: true,
      preserveTaskNavigation: true, // НЕ ИЗМЕНЯЕМ навигацию по задачам
      ...config
    };

    this.components = new Map();
    this.services = new Map();
    this.state = {
      initialized: false,
      loading: false,
      error: null,
      data: {
        tasks: [],
        filters: {},
        statistics: {},
        currentFilters: {}
      }
    };

    this.eventBus = new EventBus();
    this.loadingManager = new LoadingManager(this.eventBus);

    if (this.config.debug) {
      this.eventBus.setDebugMode(true);
      console.log('[TasksApp] Режим отладки включен');
    }

    this.init();
  }

  /**
   * Инициализация приложения
   */
  async init() {
    try {
      console.log('[TasksApp] Начало инициализации...');

      this.loadingManager.show('initial', 'Инициализация приложения...');

      // Инициализируем сервисы
      await this.initializeServices();

      // Инициализируем компоненты
      await this.initializeComponents();

      // Привязываем события
      this.bindEvents();

      // Загружаем начальные данные
      if (this.config.autoInit) {
        await this.loadInitialData();
      }

      this.state.initialized = true;
      this.loadingManager.hide('initial');

      // Эмитим событие готовности
      this.eventBus.emit('app:ready', this.state);

      console.log('[TasksApp] Инициализация завершена успешно');

    } catch (error) {
      this.handleError('Ошибка инициализации приложения', error);
      this.loadingManager.hideAll();
    }
  }

  /**
   * Инициализация сервисов
   */
  async initializeServices() {
    // Используем созданный TasksAPI
    if (typeof TasksAPI !== 'undefined') {
      this.services.set('api', new TasksAPI());
    } else {
      // Fallback для динамического импорта
      const { TasksAPI } = await import('../services/TasksAPI.js');
      this.services.set('api', new TasksAPI());
    }

    console.log('[TasksApp] Сервисы инициализированы');
  }

  /**
   * Инициализация компонентов
   */
  async initializeComponents() {
    // Получаем API сервис
    const tasksAPI = this.getService('api');

    // Создаем экземпляры компонентов с правильными зависимостями
    if (typeof StatisticsPanel !== 'undefined') {
      this.components.set('statistics', new StatisticsPanel(this.eventBus, this.loadingManager, tasksAPI));
    }

    if (typeof FiltersPanel !== 'undefined') {
      this.components.set('filters', new FiltersPanel(this.eventBus, this.loadingManager, tasksAPI));
    }

    if (typeof TasksTable !== 'undefined') {
      this.components.set('table', new TasksTable(this.eventBus, this.loadingManager, tasksAPI));
    }

    this.components.set('loading', this.loadingManager);

    console.log('[TasksApp] Компоненты инициализированы');
  }

  /**
   * Привязка событий
   */
  bindEvents() {
    // События фильтрации
    this.eventBus.on('filters:changed', this.handleFiltersChanged, this);
    this.eventBus.on('filters:reset', this.handleFiltersReset, this);

    // События таблицы
    this.eventBus.on('table:refresh', this.handleTableRefresh, this);
    this.eventBus.on('table:sort', this.handleTableSort, this);
    this.eventBus.on('table:page', this.handleTablePage, this);

    // События задач - СОХРАНЯЕМ СУЩЕСТВУЮЩУЮ ЛОГИКУ
    this.eventBus.on('task:click', this.handleTaskClick, this);
    this.eventBus.on('task:view', this.handleTaskView, this);

    // События статистики
    this.eventBus.on('statistics:refresh', this.handleStatisticsRefresh, this);
    this.eventBus.on('statistics:filter', this.handleStatisticsFilter, this);

    // События загрузки
    this.eventBus.on('loading:start', this.handleLoadingStart, this);
    this.eventBus.on('loading:end', this.handleLoadingEnd, this);

    // Глобальные события
    window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
    window.addEventListener('error', this.handleGlobalError.bind(this));

    console.log('[TasksApp] События привязаны');
  }

  /**
   * Загрузка начальных данных
   */
  async loadInitialData() {
    try {
      console.log('[TasksApp] Загрузка начальных данных...');

      // Инициализируем компоненты в правильном порядке
      const filtersComponent = this.getComponent('filters');
      const tableComponent = this.getComponent('table');
      const statisticsComponent = this.getComponent('statistics');

      // 1. Сначала фильтры (нужны для таблицы)
      if (filtersComponent && typeof filtersComponent.init === 'function') {
        await filtersComponent.init();
      }

      // 2. Затем таблица (основной компонент)
      if (tableComponent && typeof tableComponent.init === 'function') {
        await tableComponent.init();
      }

      // 3. Статистика (может зависеть от данных таблицы)
      if (statisticsComponent && typeof statisticsComponent.init === 'function') {
        await statisticsComponent.init();
      }

      console.log('[TasksApp] Начальные данные загружены');

    } catch (error) {
      this.handleError('Ошибка загрузки начальных данных', error);
    }
  }

  /**
   * Инициализация таблицы
   */
  async initializeTable() {
    try {
      this.loadingManager.show('table', 'Загрузка задач...');

      const tableComponent = this.getComponent('table');
      await tableComponent.initialize();

      this.loadingManager.hide('table');

    } catch (error) {
      this.loadingManager.hide('table');
      this.handleError('Ошибка инициализации таблицы', error);
    }
  }

  /**
   * Обработчики событий
   */

  handleFiltersChanged(data) {
    console.log('[TasksApp] Фильтры изменены:', data);

    this.updateState({
      data: {
        ...this.state.data,
        currentFilters: data.filters
      }
    });

    // Обновляем таблицу с новыми фильтрами
    this.getComponent('table').applyFilters(data.filters);

    // Обновляем статистику
    this.refreshStatistics();
  }

  handleFiltersReset() {
    console.log('[TasksApp] Сброс фильтров');

    this.updateState({
      data: {
        ...this.state.data,
        currentFilters: {}
      }
    });

    this.getComponent('table').clearFilters();
    this.getComponent('filters').reset();
    this.refreshStatistics();
  }

  handleTableRefresh() {
    console.log('[TasksApp] Обновление таблицы');
    this.getComponent('table').refresh();
  }

  handleTableSort(data) {
    console.log('[TasksApp] Сортировка таблицы:', data);
    // Логика сортировки обрабатывается компонентом таблицы
  }

  handleTablePage(data) {
    console.log('[TasksApp] Переход на страницу:', data);
    // Логика пагинации обрабатывается компонентом таблицы
  }

  // КРИТИЧНО: НЕ ИЗМЕНЯЕМ логику перехода к задачам
  handleTaskClick(data) {
    if (this.config.preserveTaskNavigation) {
      // Используем существующую логику навигации
      if (data.taskId) {
        window.location.href = `/tasks/my-tasks/${data.taskId}`;
      }
    }
    console.log('[TasksApp] Клик по задаче (навигация сохранена):', data);
  }

  handleTaskView(data) {
    console.log('[TasksApp] Просмотр задачи:', data);
    // Дополнительная логика просмотра (аналитика, логирование)
  }

  handleStatisticsRefresh() {
    console.log('[TasksApp] Обновление статистики');
    this.refreshStatistics();
  }

  handleStatisticsFilter(data) {
    console.log('[TasksApp] Фильтрация по статистике:', data);

    // Применяем фильтр из статистики
    const filters = { status: data.status };
    this.getComponent('filters').applyFilters(filters);
  }

  handleLoadingStart(data) {
    this.updateState({ loading: true });
  }

  handleLoadingEnd(data) {
    // Если нет активных загрузок
    if (this.loadingManager.getActiveCount() === 0) {
      this.updateState({ loading: false });
    }
  }

  handleBeforeUnload(event) {
    // Очистка ресурсов перед выгрузкой страницы
    this.cleanup();
  }

  handleGlobalError(event) {
    this.handleError('Глобальная ошибка', event.error);
  }

  /**
   * Вспомогательные методы
   */

  async refreshStatistics() {
    try {
      this.loadingManager.show('statistics', 'Обновление статистики...');

      const statisticsData = await this.getService('api').getStatistics(
        this.state.data.currentFilters
      );

      this.updateState({
        data: {
          ...this.state.data,
          statistics: statisticsData
        }
      });

      this.getComponent('statistics').update(statisticsData);
      this.loadingManager.hide('statistics');

    } catch (error) {
      this.loadingManager.hide('statistics');
      this.handleError('Ошибка обновления статистики', error);
    }
  }

  updateState(newState) {
    this.state = { ...this.state, ...newState };
    this.eventBus.emit('state:updated', this.state);
  }

  getComponent(name) {
    const component = this.components.get(name);
    if (!component) {
      throw new Error(`Компонент ${name} не найден`);
    }
    return component;
  }

  getService(name) {
    const service = this.services.get(name);
    if (!service) {
      throw new Error(`Сервис ${name} не найден`);
    }
    return service;
  }

  handleError(message, error) {
    console.error(`[TasksApp] ${message}:`, error);

    this.updateState({
      error: {
        message,
        error: error?.message || error,
        timestamp: new Date().toISOString()
      }
    });

    this.eventBus.emit('app:error', { message, error });

    // Показываем уведомление пользователю
    this.showErrorNotification(message);
  }

  showErrorNotification(message) {
    // Интеграция с системой уведомлений
    if (window.notificationManager) {
      window.notificationManager.showError(message);
    } else {
      // Fallback
      console.error(`Ошибка: ${message}`);
    }
  }

  cleanup() {
    console.log('[TasksApp] Очистка ресурсов...');

    // Очищаем события
    this.eventBus.clear();

    // Скрываем все спинеры
    this.loadingManager.hideAll();

    // Очищаем компоненты
    this.components.forEach(component => {
      if (component.destroy) {
        component.destroy();
      }
    });

    this.components.clear();
    this.services.clear();
  }

  /**
   * Публичные методы для внешнего API
   */

  // Получение текущего состояния
  getState() {
    return { ...this.state };
  }

  // Принудительное обновление
  async refresh() {
    await this.loadInitialData();
  }

  // Применение фильтров извне
  applyFilters(filters) {
    this.eventBus.emit('filters:changed', { filters });
  }

  // Сброс фильтров
  resetFilters() {
    this.eventBus.emit('filters:reset');
  }

  // Получение компонента для внешнего использования
  getComponentInstance(name) {
    return this.getComponent(name);
  }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TasksApp;
} else {
  window.TasksApp = TasksApp;
}
