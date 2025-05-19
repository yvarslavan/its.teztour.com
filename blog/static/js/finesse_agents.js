/**
 * Модуль для управления отображением статусов операторов Cisco Finesse
 */
(function() {
    // Глобальная переменная для хранения статусов операторов
    let agentsData = [];
    let lastUpdateTime = null;
    let isLoading = false;

    /**
     * Загружает статусы операторов с сервера
     */
    async function fetchAgentStatuses() {
        console.log('[fetchAgentStatuses] Вызвана функция'); // <<< Лог 1: Начало вызова
        // Отображаем состояние загрузки
        isLoading = true;
        updateStatusMessage('Загрузка статусов операторов...', 'loading');

        // Отображаем анимацию на кнопке обновления
        const refreshBtn = document.getElementById('refreshAgentsBtn');
        if (refreshBtn) {
            refreshBtn.classList.add('loading');
        }

        try {
            let response;
            let data;
            let authorized = false;
            let errorMessage = '';

            // Проверяем авторизацию
            if (window.finesseAuth && window.finesseAuth.isAuthenticated) {
                try {
                    // Получаем данные через авторизованный маршрут
                    response = await fetch('/finesse/agents/status', {
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        credentials: 'include'
                    });

                    if (response.ok) {
                        data = await response.json();
                        authorized = true;
                    } else {
                        errorMessage = `Ошибка при получении статусов (${response.status})`;
                        // Проверяем на 401, чтобы показать уведомление о правах
                        if (response.status === 401) {
                            showVpnNotification('Ошибка авторизации', 'У вас нет прав на просмотр статусов операторов в Cisco Finesse. Обратитесь к администратору.');
                        }
                        throw new Error(errorMessage);
                    }
                } catch (authError) {
                    console.error('Ошибка авторизованного доступа:', authError);
                    // Проверяем наличие ошибки сети, что может указывать на проблемы с VPN
                    if (authError.message && (authError.message.includes('Failed to fetch') || authError.message.includes('Network Error') )) {
                        errorMessage = 'Ошибка сетевого соединения. Проверьте подключение VPN Cisco AnyConnect.';
                        showVpnNotification(); // Показываем стандартное VPN уведомление
                    } else {
                        errorMessage = authError.message || 'Ошибка авторизованного доступа';
                        // Если это не 401 и не сеть, показываем общую ошибку
                        if (response && response.status !== 401) {
                           showVpnNotification('Ошибка доступа к Finesse', errorMessage);
                        }
                    }
                    throw new Error(errorMessage);
                }
            } else {
                 // Если пользователь не авторизован, ничего не делаем или показываем сообщение
                updateStatusMessage('Требуется авторизация для просмотра статусов', 'info');
                return; // Выходим, так как нет смысла делать запрос без токена
            }

            // Если мы дошли сюда, значит авторизованный запрос был успешен
            // Логируем полученные данные перед обработкой
            console.log('Сырые данные операторов от API:', JSON.stringify(data, null, 2));

            // Сохраняем данные
            agentsData = data;
            lastUpdateTime = new Date();

            console.log('[fetchAgentStatuses] Успех. Вызов displayAgentStatuses'); // <<< Лог 2: Перед успехом
            // Отображаем данные
            displayAgentStatuses(data);

            // Обновляем сообщение о статусе
            const formattedTime = lastUpdateTime.toLocaleTimeString();
            updateStatusMessage(`Данные обновлены в ${formattedTime}`, 'success'); // Убираем isPublicApi

            // Обновляем текст внизу панели
            const refreshStatusElement = document.querySelector('#agentsPanelContainer .refresh-status');
            if (refreshStatusElement) {
                refreshStatusElement.textContent = `Обновлено: ${formattedTime}`;
            }

        } catch (error) { // Перехватываем ошибки из блока try
            console.error('Ошибка при получении статусов операторов:', error);
            updateStatusMessage(`Ошибка: ${error.message}`, 'error');

            // Убираем анимацию вращения
            const refreshIcon = document.querySelector('.refresh-button i');
            if (refreshIcon) refreshIcon.classList.remove('fa-spin');

            // Показываем сообщение об ошибке с учетом кода 401
            errorMessage = `Ошибка при получении статусов: ${error.message || 'Неизвестная ошибка'}`;
            if (error.message && error.message.includes('(401)')) {
                errorMessage = 'Ошибка авторизации (401): У вас нет прав на просмотр статусов операторов в Cisco Finesse. Обратитесь к администратору.';
            }
            console.warn('[fetchAgentStatuses] Ошибка. Вызов showError:', errorMessage); // <<< Лог 3: Перед ошибкой
            showError(errorMessage);
        } finally {
            // Убираем состояние загрузки
            isLoading = false;

            // Убираем анимацию с кнопки обновления
            const refreshBtn = document.getElementById('refreshAgentsBtn');
            if (refreshBtn) {
                refreshBtn.classList.remove('loading');
            }
        }
    }

    /**
     * Отображает статусы операторов на странице
     */
    function displayAgentStatuses(agents) {
        // Получаем контейнер для отображения операторов
        const container = document.getElementById('agentsContainer');
        if (!container) {
            console.error('Контейнер для отображения операторов не найден');
            return;
        }

        // Очищаем контейнер
        container.innerHTML = '';

        // Проверяем наличие данных
        if (!agents || agents.length === 0) {
            container.innerHTML = '<div class="empty-message">Нет доступных данных об операторах</div>';
            return;
        }

        // Группируем операторов по командам (Teams), если доступно
        const agentsByTeam = {};

        agents.forEach(agent => {
            const team = agent.team || 'Без команды';
            if (!agentsByTeam[team]) {
                agentsByTeam[team] = [];
            }
            agentsByTeam[team].push(agent);
        });

        // Создаем элементы для каждой команды и операторов в ней
        Object.keys(agentsByTeam).sort().forEach(team => {
            // Создаем обертку для группы команды (заголовок + операторы)
            const teamGroup = document.createElement('div');
            teamGroup.className = 'team-group';

            // Создаем заголовок для команды
            const teamHeader = document.createElement('div');
            teamHeader.className = 'team-header';
            teamHeader.innerHTML = `
                ${team}
                <i class="fas fa-chevron-down team-accordion-icon"></i>
            `;
            teamGroup.appendChild(teamHeader);

            // Создаем контейнер для операторов команды
            const teamContainer = document.createElement('div');
            teamContainer.className = 'team-container';
            // По умолчанию контейнер скрыт (будет управляться через CSS/JS)
            teamContainer.style.maxHeight = '0';
            teamContainer.style.overflow = 'hidden';
            teamContainer.style.transition = 'max-height 0.3s ease-out';

            // Добавляем обработчик клика на заголовок команды
            teamHeader.addEventListener('click', function() {
                teamGroup.classList.toggle('active');
                const icon = this.querySelector('.team-accordion-icon');
                if (teamGroup.classList.contains('active')) {
                    teamContainer.style.maxHeight = teamContainer.scrollHeight + 'px';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    teamContainer.style.maxHeight = '0';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            });

            // Создаем карточки для каждого оператора
            agentsByTeam[team].forEach(agent => {
                // Создаем карточку оператора
                const card = document.createElement('div');
                card.className = 'agent-card';

                // Получаем информацию о статусе
                let statusClass = '';
                let statusText = '';

                switch (agent.status) {
                    case 'READY':
                        statusClass = 'status-ready';
                        statusText = 'Ready';
                        break;
                    case 'NOT_READY':
                        statusClass = 'status-not-ready';
                        statusText = 'Not Ready';
                        break;
                    case 'TALKING':
                        statusClass = 'status-talking';
                        statusText = 'Talking';
                        break;
                    case 'WORK':
                    case 'WORK_READY':
                        statusClass = 'status-work';
                        statusText = 'Work';
                        break;
                    default:
                        statusClass = 'status-logout';
                        statusText = 'Logout';
                }

                // Заполняем карточку
                card.innerHTML = `
                    <div class="agent-name">
                        <span class="agent-status ${statusClass}"></span>
                        ${agent.displayName || agent.username || 'Неизвестный оператор'}
                    </div>
                    <div class="agent-details">
                        <div class="agent-status-text">${statusText}</div>
                        <div class="agent-phone">
                            <i class="fas fa-phone"></i> ${agent.extension || 'не указан'}
                        </div>
                    </div>
                `;

                // Добавляем карточку в контейнер команды
                teamContainer.appendChild(card);
            });

            teamGroup.appendChild(teamContainer);
            container.appendChild(teamGroup); // Добавляем всю группу в основной контейнер
        });
    }

    /**
     * Обновляет сообщение о статусе загрузки
     */
    function updateStatusMessage(message, type = 'info') {
        const statusElement = document.getElementById('agentsStatusMessage');
        if (!statusElement) {
            return;
        }

        // Удаляем предыдущие классы типов
        statusElement.classList.remove('status-error', 'status-success', 'status-loading', 'status-info');

        // Устанавливаем новый тип
        statusElement.classList.add(`status-${type}`);

        // Обновляем сообщение
        statusElement.textContent = message;

        // Показываем элемент
        statusElement.style.display = 'block';
    }

    /**
     * Показывает сообщение об ошибке в панели статусов
     */
    function showError(message) {
        updateStatusMessage(message, 'error');
    }

    /**
     * Создает UI элементы для отображения операторов
     */
    function createAgentsUI() {
        // Создаем основной контейнер
        const container = document.createElement('div');
        container.className = 'supervisor-panel accordion-panel';
        container.id = 'agentsPanelContainer';

        // Добавляем атрибут для скрытия, если пользователь не авторизован
        if (!window.finesseAuth || !window.finesseAuth.isAuthenticated) {
            container.style.display = 'none';
        }

        // Создаем заголовок
        const header = document.createElement('div');
        header.className = 'accordion-header';
        header.innerHTML = `
            <span>Список операторов Cisco Finesse</span>
            <i class="fas fa-chevron-down accordion-icon"></i>
        `;
        container.appendChild(header);

        // Создаем контент аккордеона
        const content = document.createElement('div');
        content.className = 'accordion-content';
        container.appendChild(content);

        // Добавляем сообщение о статусе
        const statusMessage = document.createElement('div');
        statusMessage.id = 'agentsStatusMessage';
        statusMessage.className = 'status-message';
        statusMessage.style.display = 'none';
        content.appendChild(statusMessage);

        // Создаем контейнер для карточек операторов
        const agentsContainer = document.createElement('div');
        agentsContainer.id = 'agentsContainer';
        agentsContainer.className = 'agents-container';
        content.appendChild(agentsContainer);

        // Добавляем контейнер для кнопки обновления
        const refreshContainer = document.createElement('div');
        refreshContainer.className = 'refresh-container';
        content.appendChild(refreshContainer);

        // Добавляем информацию о последнем обновлении
        const refreshStatus = document.createElement('div');
        refreshStatus.className = 'refresh-status';
        refreshStatus.textContent = 'Данные не загружены';
        refreshContainer.appendChild(refreshStatus);

        // Добавляем кнопку обновления
        const refreshButton = document.createElement('button');
        refreshButton.id = 'refreshAgentsBtn';
        refreshButton.className = 'refresh-button';
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshButton.setAttribute('title', 'Обновить статусы операторов');

        // Добавляем обработчик для кнопки обновления
        refreshButton.addEventListener('click', function() {
            if (!isLoading) {
                fetchAgentStatuses();
            }
        });

        refreshContainer.appendChild(refreshButton);

        // Навешиваем обработчик клика на заголовок аккордеона
        header.addEventListener('click', function() {
            container.classList.toggle('active');
        });

        // Добавляем контейнер на страницу
        const contentArea = document.querySelector('.container');
        if (contentArea) {
            // Находим место для вставки контейнера (после шапки, но перед журналом звонков)
            const callsPanel = document.querySelector('.calls-panel');
            if (callsPanel) {
                contentArea.insertBefore(container, callsPanel);
            } else {
                contentArea.appendChild(container);
            }
        } else {
            document.body.appendChild(container);
        }

        // Раскрываем аккордеон по умолчанию
        container.classList.add('active');

        // Возвращаем созданный контейнер
        return container;
    }

    /**
     * Защита элементов от удаления
     */
    function protectRefreshButton() {
        // Получаем кнопку обновления
        const refreshBtn = document.getElementById('refreshAgentsBtn');
        if (!refreshBtn) {
            return;
        }

        // Добавляем атрибут для защиты
        refreshBtn.setAttribute('id', 'tez_protected_refresh_btn');

        // Используем MutationObserver для защиты кнопки от удаления
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.removedNodes.length) {
                    // Проверяем, была ли удалена наша кнопка
                    const wasRemoved = Array.from(mutation.removedNodes).some(node => {
                        return node.id === 'tez_protected_refresh_btn' ||
                               (node.querySelector && node.querySelector('#tez_protected_refresh_btn'));
                    });

                    if (wasRemoved) {
                        console.warn('Кнопка обновления статусов была удалена. Восстанавливаем...');

                        // Восстанавливаем кнопку
                        const container = document.querySelector('.refresh-container');
                        if (container && !document.getElementById('tez_protected_refresh_btn')) {
                            const newBtn = document.createElement('button');
                            newBtn.id = 'tez_protected_refresh_btn';
                            newBtn.className = 'refresh-button';
                            newBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
                            newBtn.setAttribute('title', 'Обновить статусы операторов');

                            // Добавляем обработчик
                            newBtn.addEventListener('click', function() {
                                if (!isLoading) {
                                    fetchAgentStatuses();
                                }
                            });

                            container.appendChild(newBtn);
                        }
                    }
                }
            });
        });

        // Запускаем наблюдение за документом
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Инициализация модуля
     */
    function init() {
        // Создаем UI элементы для отображения операторов
        createAgentsUI();

        // Защищаем кнопку обновления от удаления
        protectRefreshButton();

        // Если пользователь авторизован, загружаем статусы операторов
        if (window.finesseAuth && window.finesseAuth.isAuthenticated) {
            // Загружаем статусы с небольшой задержкой
            setTimeout(fetchAgentStatuses, 500);
        } else {
            // Показываем сообщение о необходимости авторизации
            updateStatusMessage('Выполните вход Finesse для просмотра статусов', 'info');

            // Слушаем событие успешной авторизации
            document.addEventListener('finesseAuthSuccess', function() {
                // Загружаем статусы после успешной авторизации
                setTimeout(fetchAgentStatuses, 500);
            });
        }
    }

    // Запускаем инициализацию после загрузки DOM
    document.addEventListener('DOMContentLoaded', init);

    // Экспортируем функцию для внешнего вызова
    window.fetchAgentStatuses = fetchAgentStatuses;

    /**
     * Показывает уведомление о необходимости подключения VPN
     */
    function showVpnNotification(title, message) {
        // Проверяем, нет ли уже показанного уведомления
        if (document.getElementById('vpn-notification')) {
            return;
        }

        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.id = 'vpn-notification';
        notification.className = 'vpn-notification';
        notification.innerHTML = `
            <div class="vpn-notification-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${title}</span>
                <button class="vpn-close-btn">&times;</button>
            </div>
            <div class="vpn-notification-body">
                <p>${message}</p>
            </div>
        `;

        // Добавляем стили для уведомления
        const style = document.createElement('style');
        style.textContent = `
            .vpn-notification {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 380px;
                background-color: #fff3cd;
                border: 1px solid #ffeeba;
                border-left: 4px solid #ffc107;
                border-radius: 4px;
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
                z-index: 1050;
                overflow: hidden;
                animation: slideIn 0.3s;
            }

            .vpn-notification-header {
                padding: 12px 15px;
                background-color: rgba(255, 193, 7, 0.2);
                display: flex;
                align-items: center;
                border-bottom: 1px solid #ffeeba;
            }

            .vpn-notification-header i {
                color: #856404;
                margin-right: 10px;
            }

            .vpn-notification-header span {
                flex: 1;
                font-weight: 600;
                color: #856404;
            }

            .vpn-close-btn {
                background: none;
                border: none;
                color: #856404;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                line-height: 1;
            }

            .vpn-notification-body {
                padding: 15px;
                color: #856404;
            }

            .vpn-notification-body p {
                margin-top: 0;
                margin-bottom: 10px;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }
        `;

        // Добавляем стили и уведомление в DOM
        document.head.appendChild(style);
        document.body.appendChild(notification);

        // Добавляем обработчик для закрытия уведомления
        const closeBtn = notification.querySelector('.vpn-close-btn');
        closeBtn.addEventListener('click', function() {
            notification.style.animation = 'slideOut 0.3s forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        });

        // Автоматически скрываем уведомление через 30 секунд
        setTimeout(() => {
            if (document.body.contains(notification)) {
                notification.style.animation = 'slideOut 0.3s forwards';
                setTimeout(() => {
                    if (document.body.contains(notification)) {
                        notification.remove();
                    }
                }, 300);
            }
        }, 30000);
    }

    // Добавьте в конец файла, внутри замыкания
    window.showVpnNotification = showVpnNotification;
})();
