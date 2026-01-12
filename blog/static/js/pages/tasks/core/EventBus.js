/**
 * EventBus - Система событий для связи между компонентами
 * Реализует паттерн Observer для слабой связанности модулей
 */
class EventBus {
  constructor() {
    this.events = new Map();
    this.debugMode = false;
  }

  /**
   * Подписка на событие
   * @param {string} event - Название события
   * @param {Function} callback - Функция обработчик
   * @param {Object} context - Контекст выполнения (this)
   */
  on(event, callback, context = null) {
    if (!this.events.has(event)) {
      this.events.set(event, []);
    }

    const listener = {
      callback,
      context,
      id: this.generateId()
    };

    this.events.get(event).push(listener);

    if (this.debugMode) {
      console.log(`[EventBus] Подписка на событие: ${event}`, listener);
    }

    // Возвращаем функцию для отписки
    return () => this.off(event, listener.id);
  }

  /**
   * Отписка от события
   * @param {string} event - Название события
   * @param {string} listenerId - ID слушателя
   */
  off(event, listenerId) {
    if (!this.events.has(event)) return;

    const listeners = this.events.get(event);
    const index = listeners.findIndex(listener => listener.id === listenerId);

    if (index !== -1) {
      listeners.splice(index, 1);

      if (this.debugMode) {
        console.log(`[EventBus] Отписка от события: ${event}`, listenerId);
      }
    }
  }

  /**
   * Эмиссия события
   * @param {string} event - Название события
   * @param {*} data - Данные события
   */
  emit(event, data = null) {
    if (!this.events.has(event)) {
      if (this.debugMode) {
        console.warn(`[EventBus] Нет слушателей для события: ${event}`);
      }
      return;
    }

    const listeners = this.events.get(event);

    if (this.debugMode) {
      console.log(`[EventBus] Эмиссия события: ${event}`, data, `(${listeners.length} слушателей)`);
    }

    listeners.forEach(listener => {
      try {
        if (listener.context) {
          listener.callback.call(listener.context, data);
        } else {
          listener.callback(data);
        }
      } catch (error) {
        console.error(`[EventBus] Ошибка в обработчике события ${event}:`, error);
      }
    });
  }

  /**
   * Одноразовая подписка на событие
   * @param {string} event - Название события
   * @param {Function} callback - Функция обработчик
   * @param {Object} context - Контекст выполнения
   */
  once(event, callback, context = null) {
    const unsubscribe = this.on(event, (data) => {
      callback.call(context, data);
      unsubscribe();
    }, context);

    return unsubscribe;
  }

  /**
   * Очистка всех событий
   */
  clear() {
    this.events.clear();

    if (this.debugMode) {
      console.log('[EventBus] Все события очищены');
    }
  }

  /**
   * Получение списка активных событий
   */
  getActiveEvents() {
    const activeEvents = {};

    this.events.forEach((listeners, event) => {
      activeEvents[event] = listeners.length;
    });

    return activeEvents;
  }

  /**
   * Включение/выключение режима отладки
   */
  setDebugMode(enabled) {
    this.debugMode = enabled;
    console.log(`[EventBus] Режим отладки: ${enabled ? 'включен' : 'выключен'}`);
  }

  /**
   * Генерация уникального ID
   */
  generateId() {
    return `listener_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
  module.exports = EventBus;
} else {
  window.EventBus = EventBus;
}
