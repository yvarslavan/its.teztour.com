/**
 * Виджет статуса сетевого соединения для встраивания на различные страницы
 */
(function() {
    // Настройки
    const updateIntervalMs = 30000; // Обновление каждые 30 секунд
    let updateInterval = null;

    /**
     * Создает HTML-разметку виджета
     */
    function createWidgetHTML() {
        const widget = document.createElement('div');
        widget.className = 'network-status-widget';
        widget.id = 'networkStatusWidget';

        widget.innerHTML = `
            <div class="widget-header">
                <i class="fas fa-network-wired"></i>
                <span>Состояние сети</span>
            </div>
            <div class="widget-body">
                <div class="status-indicators" id="statusIndicators">
                    <div class="status-indicator-item">
                        <span class="indicator-name">Finesse:</span>
                        <span class="indicator-value" id="finesseStatus">
                            <i class="fas fa-spinner fa-spin"></i>
                        </span>
                    </div>
                </div>
                <a href="/network-monitor" class="widget-details-link">
                    Подробнее <i class="fas fa-chevron-right"></i>
                </a>
            </div>
        `;

        // Добавляем стили
        addWidgetStyles();

        return widget;
    }

    /**
     * Добавляет стили виджета в документ
     */
    function addWidgetStyles() {
        // Проверяем, добавлены ли уже стили
        if (document.getElementById('network-widget-styles')) {
            return;
        }

        const styleElement = document.createElement('style');
        styleElement.id = 'network-widget-styles';

        styleElement.textContent = `
            .network-status-widget {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 15px;
                overflow: hidden;
            }

            .widget-header {
                background-color: #f8f9fa;
                padding: 10px 15px;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 500;
            }

            .widget-body {
                padding: 12px 15px;
            }

            .status-indicators {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-bottom: 10px;
            }

            .status-indicator-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 14px;
            }

            .indicator-name {
                color: #555;
            }

            .indicator-value {
                display: flex;
                align-items: center;
                gap: 5px;
            }

            .indicator-value.excellent { color: #28a745; }
            .indicator-value.good { color: #17a2b8; }
            .indicator-value.average { color: #ffc107; }
            .indicator-value.poor { color: #dc3545; }
            .indicator-value.disconnected { color: #6c757d; }

            .indicator-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
            }

            .indicator-dot.excellent { background-color: #28a745; }
            .indicator-dot.good { background-color: #17a2b8; }
            .indicator-dot.average { background-color: #ffc107; }
            .indicator-dot.poor { background-color: #dc3545; }
            .indicator-dot.disconnected { background-color: #6c757d; }

            .widget-details-link {
                display: block;
                text-align: right;
                font-size: 13px;
                color: #007bff;
                text-decoration: none;
            }

            .widget-details-link:hover {
                text-decoration: underline;
            }
        `;

        document.head.appendChild(styleElement);
    }

    /**
     * Обновляет статусы соединения в виджете
     */
    async function updateWidgetStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            if (data.status === 'ok') {
                updateStatusIndicators(data.targets);
            }
        } catch (error) {
            console.error('Failed to update widget status:', error);
        }
    }

    /**
     * Обновляет индикаторы статуса в виджете
     */
    function updateStatusIndicators(targets) {
        const statusTexts = {
            'excellent': 'Отличное',
            'good': 'Хорошее',
            'average': 'Среднее',
            'poor': 'Плохое',
            'disconnected': 'Отключено'
        };

        // Обновляем каждый индикатор
        for (const [targetName, targetData] of Object.entries(targets)) {
            const indicator = document.getElementById(`${targetName}Status`);

            if (indicator) {
                const statusClass = targetData.status;
                const pingTime = targetData.time_ms;
                const statusText = statusTexts[statusClass] || 'Неизвестно';

                indicator.className = `indicator-value ${statusClass}`;
                indicator.innerHTML = `
                    <span class="indicator-dot ${statusClass}"></span>
                    <span>${pingTime > 0 ? pingTime + ' мс' : 'Нет связи'}</span>
                `;

                // Добавляем всплывающую подсказку
                indicator.setAttribute('title', `${statusText} - Обновлено: ${targetData.timestamp}`);
            }
        }
    }

    /**
     * Инициализирует виджет и вставляет его в указанный элемент
     */
    function initWidget(containerSelector) {
        const container = document.querySelector(containerSelector);

        if (!container) {
            console.error(`Container element not found: ${containerSelector}`);
            return;
        }

        // Создаем и вставляем виджет
        const widget = createWidgetHTML();
        container.appendChild(widget);

        // Выполняем начальное обновление
        updateWidgetStatus();

        // Устанавливаем интервал для периодического обновления
        updateInterval = setInterval(updateWidgetStatus, updateIntervalMs);
    }

    // Экспортируем API виджета
    window.networkStatusWidget = {
        init: initWidget,
        update: updateWidgetStatus
    };
})();
