/**
 * StatisticsPanel_Simple - Упрощенная версия компонента панели статистики
 * Автономная версия без зависимостей
 */
class StatisticsPanel_Simple {
  constructor() {
    this.eventBus = window.eventBus;
    this.loadingManager = window.loadingManager;
    this.panelElement = null;
    this.isInitialized = false;
    this.currentStats = {};

    // Задержка для гарантии готовности DOM и глобальных переменных
    setTimeout(() => this.init(), 100);
  }

  async init() {
    try {
      console.log('[StatisticsPanel] 🚀 Инициализация панели статистики...');

      // Проверяем наличие панели
      this.panelElement = document.getElementById('statisticsCards');
      if (!this.panelElement) {
        throw new Error('Панель #statisticsCards не найдена');
      }

      // Настраиваем обработчики событий
      this._setupEventListeners();

      // Загружаем начальную статистику
      await this.loadStatistics();

      this.isInitialized = true;
      console.log('[StatisticsPanel] ✅ Панель статистики инициализирована');

      // Уведомляем о готовности
      this.eventBus.emit('statistics:initialized');

    } catch (error) {
      console.error('[StatisticsPanel] ❌ Ошибка инициализации:', error);
      this.eventBus.emit('statistics:error', { error: error.message });
      throw error;
    }
  }

  _setupEventListeners() {
    // Слушаем события от других компонентов
    this.eventBus.on('table:dataLoaded', (data) => {
      this.updateFromTableData(data);
    });

    this.eventBus.on('filters:changed', () => {
      this.loadStatistics();
    });

    this.eventBus.on('statistics:refresh', () => {
      this.loadStatistics();
    });
  }

  async loadStatistics() {
    try {
      console.log('[StatisticsPanel] 📊 Загрузка расширенной статистики с реальными данными...');
      console.log('[StatisticsPanel] 🔥 ОТЛАДКА: Вызываем /tasks/api/statistics-extended');

      this.loadingManager.show('Загрузка статистики...');

      // ИСПРАВЛЕНИЕ: Используем новый API endpoint с реальными данными
      const response = await fetch('/tasks/api/statistics-extended');
      console.log('[StatisticsPanel] 🔥 ОТЛАДКА: Ответ получен, статус:', response.status);

      const data = await response.json();
      console.log('[StatisticsPanel] 🔥 ОТЛАДКА: Данные из API:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      this.currentStats = data;
      this.renderStatistics(data);

      this.eventBus.emit('statistics:loaded', data);

      console.log('[StatisticsPanel] ✅ Расширенная статистика загружена:', data);

    } catch (error) {
      console.error('[StatisticsPanel] ❌ Ошибка загрузки статистики:', error);
      this.showError('Ошибка загрузки статистики: ' + error.message);
      this.eventBus.emit('statistics:error', { error: error.message });
    } finally {
      this.loadingManager.hide();
    }
  }

  renderStatistics(data) {
    console.log('[StatisticsPanel_Simple] Рендеринг статистики:', data);

    const container = document.getElementById('statisticsCards');
    if (!container) {
      console.error('[StatisticsPanel_Simple] Контейнер statisticsCards не найден');
      return;
    }

    // Градиентные конфигурации для каждого типа карточки
    const cardConfigs = {
      total: {
        gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        icon: 'fas fa-tasks',
        iconColor: '#667eea',
        title: 'Всего задач'
      },
      new: {
        gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        icon: 'fas fa-plus-circle',
        iconColor: '#4facfe',
        title: 'Новые'
      },
      progress: {
        gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
        icon: 'fas fa-clock',
        iconColor: '#43e97b',
        title: 'В работе'
      },
      closed: {
        gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        icon: 'fas fa-check-circle',
        iconColor: '#fa709a',
        title: 'Завершенные'
      }
    };

    // Функция создания карточки с реальными данными изменений
    const createCard = (type, value, change = null) => {
      const config = cardConfigs[type];
      if (!config) return '';

      const changeText = change ? change : (type === 'progress' ? 'без изменений' : '+0 сегодня');
      const changeIcon = change && change.includes('+') ? 'fas fa-arrow-up' :
                        change && change.includes('-') ? 'fas fa-arrow-down' : 'fas fa-arrow-right';
      const changeColor = change && change.includes('+') ? '#10b981' :
                         change && change.includes('-') ? '#ef4444' : '#64748b';

      return `
        <div class="stat-card ${type}" style="
          background: white;
          border-radius: 16px;
          padding: 1.5rem;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
          border: 1px solid rgba(0, 0, 0, 0.05);
          position: relative;
          overflow: hidden;
          min-height: 140px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          transition: all 0.3s ease;
        ">
          <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; background: ${config.gradient};"></div>
          <div class="stat-header" style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <i class="${config.icon}" style="font-size: 1.5rem; color: ${config.iconColor}; opacity: 0.8;"></i>
            <h3 style="font-size: 0.9rem; font-weight: 600; color: #64748b; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">${config.title}</h3>
          </div>
          <div class="stat-value" style="font-size: 2.5rem; font-weight: 700; color: #1e293b; margin: 0; line-height: 1;">${value}</div>
          <div class="stat-change" style="font-size: 0.85rem; margin-top: 0.5rem; display: flex; align-items: center; gap: 0.25rem; color: ${changeColor};">
            <i class="${changeIcon}"></i>
            ${changeText}
          </div>
        </div>
      `;
    };

    // ИСПРАВЛЕНИЕ: Получаем реальные изменения из API данных вместо захардкоженных значений
    const getTotalChange = () => {
      if (data.changes && data.changes.total) {
        return data.changes.total.week_text;
      }
      return 'без изменений за неделю';
    };

    const getNewChange = () => {
      if (data.changes && data.changes.new) {
        return data.changes.new.today_text;
      }
      return 'без новых сегодня';
    };

    const getProgressChange = () => {
      if (data.changes && data.changes.progress) {
        return data.changes.progress.today_text;
      }
      return 'без изменений';
    };

    const getClosedChange = () => {
      console.log('[StatisticsPanel] 🔥 ОТЛАДКА getClosedChange:');
      console.log('  data:', data);
      console.log('  data.changes:', data.changes);
      console.log('  data.changes.closed:', data.changes ? data.changes.closed : 'НЕТ');

      if (data.changes && data.changes.closed) {
        console.log('  today_text:', data.changes.closed.today_text);
        return data.changes.closed.today_text;
      }
      console.log('  FALLBACK: без завершений сегодня');
      return 'без завершений сегодня';
    };

    // Генерируем HTML для всех карточек с реальными данными
    const cardsHTML = `
      ${createCard('total', data.total_tasks || 0, getTotalChange())}
      ${createCard('new', data.new_tasks || 0, getNewChange())}
      ${createCard('progress', data.in_progress_tasks || 0, getProgressChange())}
      ${createCard('closed', data.closed_tasks || 0, getClosedChange())}
    `;

    // Обновляем содержимое контейнера
    container.innerHTML = cardsHTML;

    // Добавляем hover эффекты
    const cards = container.querySelectorAll('.stat-card');
    cards.forEach(card => {
      card.addEventListener('mouseenter', () => {
        card.style.transform = 'translateY(-4px)';
        card.style.boxShadow = '0 8px 40px rgba(0, 0, 0, 0.12)';
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'translateY(0)';
        card.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.08)';
      });
    });

    console.log('[StatisticsPanel_Simple] Статистика отрендерена успешно');
  }

  renderDetailedBreakdown(statusCounts) {
    const container = document.getElementById('statusBreakdown');
    if (!container) return;

    // Создаем детальную разбивку
    const detailsHTML = Object.entries(statusCounts).map(([status, count]) => `
      <div class="status-item">
        <span class="status-name">${status}</span>
        <span class="status-count">${count}</span>
      </div>
    `).join('');

    container.innerHTML = detailsHTML;
  }

  updateFromTableData(tableData) {
    // Обновляем статистику на основе данных таблицы
    const stats = {
      total_tasks: tableData.total || 0,
      new_tasks: 0,
      in_progress_tasks: 0,
      closed_tasks: 0
    };

    // Подсчитываем статистику из данных таблицы
    if (tableData.data) {
      tableData.data.forEach(task => {
        const status = (task.status_name || '').toLowerCase();
        if (status.includes('новая') || status.includes('new')) {
          stats.new_tasks++;
        } else if (status.includes('работе') || status.includes('progress')) {
          stats.in_progress_tasks++;
        } else if (status.includes('закрыт') || status.includes('closed')) {
          stats.closed_tasks++;
        }
      });
    }

    this.currentStats = stats;
    this.renderStatistics(stats);
  }

  showError(message) {
    const cardsContainer = this.panelElement;
    if (cardsContainer) {
      cardsContainer.innerHTML = `
        <div class="stat-card error">
          <div class="text-center text-danger">
            <i class="fas fa-exclamation-triangle"></i>
            <p>${message}</p>
          </div>
        </div>
      `;
    }
  }

  // Методы для совместимости с TasksApp
  update(data) {
    console.log('[StatisticsPanel] 🔄 Обновление статистики');
    if (data) {
      this.currentStats = data;
      this.renderStatistics(data);
    } else {
      this.loadStatistics();
    }
  }

  refresh() {
    console.log('[StatisticsPanel] 🔄 Обновление статистики');
    this.loadStatistics();
  }

  destroy() {
    console.log('[StatisticsPanel] 🗑️ Очистка ресурсов');
    this.isInitialized = false;
    this.currentStats = {};
  }
}

// Экспорт для использования
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StatisticsPanel_Simple;
} else {
  window.StatisticsPanel_Simple = StatisticsPanel_Simple;
}
