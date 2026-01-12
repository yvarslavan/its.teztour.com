/**
 * LoadingManager - Единый менеджер состояний загрузки
 * Устраняет проблему дублирования спинеров и обеспечивает централизованное управление
 */
class LoadingManager {
  constructor(eventBus = null) {
    this.eventBus = eventBus;
    this.activeLoaders = new Set();
    this.containers = new Map();
    this.templates = new Map();

    // Типы состояний загрузки
    this.STATES = {
      INITIAL: 'initial',
      TABLE: 'table',
      STATISTICS: 'statistics',
      FILTERS: 'filters',
      SEARCH: 'search'
    };

    this.init();
  }

  /**
   * Инициализация менеджера
   */
  init() {
    this.setupContainers();
    this.setupTemplates();
    this.bindEvents();
  }

  /**
   * Настройка контейнеров для разных типов загрузки
   */
  setupContainers() {
    // Основной полноэкранный спинер
    this.containers.set(this.STATES.INITIAL, {
      selector: '#loading-spinner',
      type: 'overlay'
    });

    // Спинер для таблицы
    this.containers.set(this.STATES.TABLE, {
      selector: '#tasksTable_wrapper',
      type: 'inline'
    });

    // Спинер для статистики
    this.containers.set(this.STATES.STATISTICS, {
      selector: '.status-breakdown-dashboard',
      type: 'inline'
    });

    // Спинер для фильтров
    this.containers.set(this.STATES.FILTERS, {
      selector: '.filters-section',
      type: 'inline'
    });

    // Спинер для поиска
    this.containers.set(this.STATES.SEARCH, {
      selector: '.search-container',
      type: 'inline'
    });
  }

  /**
   * Настройка шаблонов загрузки
   */
  setupTemplates() {
    // Шаблон полноэкранного спинера
    this.templates.set('overlay', (message) => `
      <div class="loading-overlay" data-loading-type="overlay">
        <div class="loading-content">
          <div class="loading-spinner">
            <i class="fas fa-cog fa-spin loading-icon"></i>
          </div>
          <div class="loading-text">
            <h3>${message}</h3>
            <p>Пожалуйста, подождите...</p>
          </div>
        </div>
      </div>
    `);

    // Шаблон inline спинера
    this.templates.set('inline', (message) => `
      <div class="loading-inline" data-loading-type="inline">
        <div class="loading-spinner-small">
          <i class="fas fa-spinner fa-spin loading-icon-small"></i>
        </div>
        <span class="loading-message">${message}</span>
      </div>
    `);

    // Шаблон DataTables спинера
    this.templates.set('datatable', (message) => `
      <div class="dt-processing" data-loading-type="datatable">
        <div class="dt-processing-content">
          <i class="fas fa-spinner fa-spin"></i>
          <span>${message}</span>
        </div>
      </div>
    `);
  }

  /**
   * Показать состояние загрузки
   * @param {string} state - Тип состояния загрузки
   * @param {string} message - Сообщение для отображения
   * @param {Object} options - Дополнительные опции
   */
  show(state, message = 'Загрузка...', options = {}) {
    // Предотвращаем дублирование
    if (this.activeLoaders.has(state)) {
      console.warn(`[LoadingManager] Состояние ${state} уже активно`);
      return false;
    }

    const containerConfig = this.containers.get(state);
    if (!containerConfig) {
      console.error(`[LoadingManager] Неизвестное состояние: ${state}`);
      return false;
    }

    try {
      this.activeLoaders.add(state);
      this.renderLoader(state, message, containerConfig, options);

      // Эмитим событие через EventBus
      if (this.eventBus) {
        this.eventBus.emit('loading:start', { state, message });
      }

      console.log(`[LoadingManager] Показан спинер: ${state} - ${message}`);
      return true;

    } catch (error) {
      console.error(`[LoadingManager] Ошибка показа спинера ${state}:`, error);
      this.activeLoaders.delete(state);
      return false;
    }
  }

  /**
   * Скрыть состояние загрузки
   * @param {string} state - Тип состояния загрузки
   */
  hide(state) {
    if (!this.activeLoaders.has(state)) {
      console.warn(`[LoadingManager] Состояние ${state} не активно`);
      return false;
    }

    try {
      this.activeLoaders.delete(state);
      this.removeLoader(state);

      // Эмитим событие через EventBus
      if (this.eventBus) {
        this.eventBus.emit('loading:end', { state });

        // Если все спинеры скрыты
        if (this.activeLoaders.size === 0) {
          this.eventBus.emit('loading:complete');
        }
      }

      console.log(`[LoadingManager] Скрыт спинер: ${state}`);
      return true;

    } catch (error) {
      console.error(`[LoadingManager] Ошибка скрытия спинера ${state}:`, error);
      return false;
    }
  }

  /**
   * Принудительное скрытие всех спинеров
   */
  hideAll() {
    const activeStates = Array.from(this.activeLoaders);

    activeStates.forEach(state => {
      this.hide(state);
    });

    // Дополнительная очистка для старых спинеров
    this.cleanupLegacySpinners();

    console.log('[LoadingManager] Все спинеры принудительно скрыты');
  }

  /**
   * Рендеринг спинера
   */
  renderLoader(state, message, containerConfig, options) {
    const container = document.querySelector(containerConfig.selector);
    if (!container) {
      throw new Error(`Контейнер не найден: ${containerConfig.selector}`);
    }

    const templateType = options.templateType || containerConfig.type;
    const template = this.templates.get(templateType);

    if (!template) {
      throw new Error(`Шаблон не найден: ${templateType}`);
    }

    // Создаем элемент спинера
    const loaderElement = document.createElement('div');
    loaderElement.className = `loading-container loading-${state}`;
    loaderElement.innerHTML = template(message);
    loaderElement.setAttribute('data-loading-state', state);

    // Вставляем спинер в зависимости от типа
    if (containerConfig.type === 'overlay') {
      document.body.appendChild(loaderElement);
    } else {
      // Для inline спинеров добавляем в начало контейнера
      container.insertBefore(loaderElement, container.firstChild);
      container.classList.add('loading-active');
    }

    // Анимация появления
    requestAnimationFrame(() => {
      loaderElement.classList.add('loading-visible');
    });
  }

  /**
   * Удаление спинера
   */
  removeLoader(state) {
    const loaderElements = document.querySelectorAll(`[data-loading-state="${state}"]`);

    loaderElements.forEach(element => {
      element.classList.add('loading-hiding');

      // Удаляем элемент после анимации
      setTimeout(() => {
        if (element.parentNode) {
          element.parentNode.removeChild(element);
        }
      }, 300);
    });

    // Убираем класс loading-active с контейнеров
    const containerConfig = this.containers.get(state);
    if (containerConfig && containerConfig.type !== 'overlay') {
      const container = document.querySelector(containerConfig.selector);
      if (container) {
        container.classList.remove('loading-active');
      }
    }
  }

  /**
   * Очистка старых спинеров (совместимость)
   */
  cleanupLegacySpinners() {
    // Список селекторов старых спинеров для очистки
    const legacySelectors = [
      '.loading-overlay',
      '.dt-processing',
      '#loading-spinner',
      '.spinner-overlay',
      '.loading-indicator'
    ];

    legacySelectors.forEach(selector => {
      const elements = document.querySelectorAll(selector);
      elements.forEach(element => {
        if (!element.hasAttribute('data-loading-state')) {
          element.style.display = 'none';
          element.style.visibility = 'hidden';
          element.style.opacity = '0';
        }
      });
    });
  }

  /**
   * Привязка событий
   */
  bindEvents() {
    // Слушаем события DataTables для интеграции
    document.addEventListener('processing.dt', (e) => {
      const isProcessing = e.detail?.processing;

      if (isProcessing) {
        this.show(this.STATES.TABLE, '🚀 Загрузка данных...');
      } else {
        this.hide(this.STATES.TABLE);
      }
    });

    // Обработка ошибок
    window.addEventListener('error', () => {
      // При критических ошибках скрываем все спинеры
      setTimeout(() => this.hideAll(), 1000);
    });
  }

  /**
   * Получение активных состояний
   */
  getActiveStates() {
    return Array.from(this.activeLoaders);
  }

  /**
   * Проверка активности состояния
   */
  isActive(state) {
    return this.activeLoaders.has(state);
  }

  /**
   * Получение количества активных спинеров
   */
  getActiveCount() {
    return this.activeLoaders.size;
  }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LoadingManager;
} else {
  window.LoadingManager = LoadingManager;
}
