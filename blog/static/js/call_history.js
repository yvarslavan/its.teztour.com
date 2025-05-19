/**
 * Модуль для управления журналом звонков
 */
(function() {
    // Глобальные переменные
    let callsData = [];
    let lastUpdateTime = null;
    let isLoading = false;

    /**
     * Загружает историю звонков с сервера
     */
    async function fetchCallHistory() {
        // Отображаем состояние загрузки
        isLoading = true;
        updateStatusMessage('Загрузка журнала звонков...', 'loading');

        // Избегаем слишком частых запросов - добавляем проверку последнего обновления
        const now = new Date();
        if (lastUpdateTime && (now - lastUpdateTime) < 10000) { // Минимум 10 секунд между запросами
            console.log('Слишком частое обновление, ожидаем...');
            updateStatusMessage('Данные обновлены недавно', 'info', false);
            isLoading = false;
            return;
        }

        try {
            let response;
            let data;
            let calls = []; // Добавляем переменную для хранения массива звонков
            let errorMessage = '';

            // Пытаемся получить реальные данные
            try {
                // Добавляем параметр для обхода кэша
                const timestamp = new Date().getTime();
                response = await fetch(`/api/moscow-calls?_=${timestamp}`);

                if (!response.ok) {
                    throw new Error(`Ошибка при получении звонков (${response.status})`);
                }

                data = await response.json();

                // Извлекаем массив звонков из ответа API
                if (data && data.success && Array.isArray(data.calls)) {
                    calls = data.calls;
                    console.log('Успешно получены данные звонков:', calls);
                } else {
                    console.log('Получен пустой список звонков или неверный формат данных');
                    calls = [];
                }
            } catch (apiError) {
                console.warn('Ошибка доступа к API звонков:', apiError);
                errorMessage = apiError.message || 'Ошибка при получении журнала звонков';
                calls = []; // Пустой массив в случае ошибки
            }

            // Сохраняем данные
            callsData = calls;
            lastUpdateTime = new Date();

            // Отображаем данные
            displayCallHistory(calls); // Передаем массив calls вместо data

            // Обновляем сообщение о статусе
            if (errorMessage) {
                updateStatusMessage(`Ошибка: ${errorMessage}`, 'error', false);
            } else {
                const formattedTime = lastUpdateTime.toLocaleTimeString();
                updateStatusMessage(`Данные обновлены в ${formattedTime}`, 'success', false);
            }
        } catch (error) {
            console.error('Ошибка при получении журнала звонков:', error);
            updateStatusMessage(`Ошибка: ${error.message}`, 'error');

            // Отображаем пустой журнал с сообщением об ошибке
            displayCallHistory([]);
        } finally {
            // Убираем состояние загрузки
            isLoading = false;
        }
    }

    /**
     * Отображает историю звонков на странице
     */
    function displayCallHistory(calls) {
        const container = document.querySelector('.calls-list');
        if (!container) {
            console.error('Контейнер для отображения звонков не найден');
            return;
        }

        // Очищаем контейнер
        container.innerHTML = '';

        // Создаем заголовок таблицы
        const header = document.createElement('div');
        header.className = 'calls-header';
        header.innerHTML = `
            <div class="call-phone-header">Номер телефона</div>
            <div class="call-operator-header">Оператор</div>
            <div class="call-time-header">Время</div>
        `;
        container.appendChild(header);

        // Проверяем наличие данных
        if (!calls || calls.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'no-calls-message';
            emptyMessage.innerHTML = `
                <i class="fas fa-phone-slash"></i>
                <p>Журнал звонков пуст</p>
            `;
            container.appendChild(emptyMessage);
            return;
        }

        // Добавляем отладочный вывод
        console.log('Отображаем звонки:', calls);

        // Создаем элементы для каждого звонка
        calls.forEach(call => {
            const callItem = document.createElement('div');
            callItem.className = 'call-item';

            // Определяем, есть ли карточка клиента и информация об обзвоне
            const hasClientCard = call.card_id && call.card_id !== '0';
            const hasAgencyInfo = call.pp_id && call.pp_id !== '0';

            // Формируем HTML для элемента звонка
            callItem.innerHTML = `
                <div class="call-phone">
                    <span class="${call.phone_number ? 'phone-number' : 'unknown-number'}">
                        ${call.phone_number || 'Номер не определен'}
                    </span>
                    <div class="call-actions">
                        ${hasClientCard ? `
                            <button class="client-card-badge" onclick="showClientCard('${call.card_id}')">
                                <i class="fas fa-id-card"></i> Карта клиента
                            </button>
                        ` : ''}
                        ${hasAgencyInfo ? `
                            <button class="agency-info-btn" onclick="showAgencyInfo('${call.pp_id}')">
                                <i class="fas fa-building"></i> Информация об обзвоне
                            </button>
                        ` : ''}
                    </div>
                </div>
                <div class="call-operator">${call.operator || 'Не назначен'}</div>
                <div class="call-time">${call.time || ''}</div>
            `;

            container.appendChild(callItem);
        });
    }

    /**
     * Обновляет сообщение о статусе загрузки
     */
    function updateStatusMessage(message, type = 'info', isFallbackData = false) {
        const statusElement = document.getElementById('callsStatusMessage');
        if (!statusElement) {
            // Создаем элемент статуса, если его нет
            const accordionContent = document.querySelector('.calls-panel .accordion-content');
            if (accordionContent) {
                const statusMessage = document.createElement('div');
                statusMessage.id = 'callsStatusMessage';
                statusMessage.className = 'status-message';

                // Вставляем перед списком звонков
                const callsList = accordionContent.querySelector('.calls-list');
                if (callsList) {
                    accordionContent.insertBefore(statusMessage, callsList);
                } else {
                    accordionContent.appendChild(statusMessage);
                }

                updateStatusMessage(message, type, isFallbackData);
                return;
            }
            return;
        }

        // Удаляем предыдущие классы типов
        statusElement.classList.remove('status-error', 'status-success', 'status-loading', 'status-info', 'status-demo-data');

        // Устанавливаем новый тип
        statusElement.classList.add(`status-${type}`);

        if (isFallbackData) {
            statusElement.classList.add('status-demo-data');
            message += ' (демонстрационные данные)';
        }

        // Обновляем сообщение
        statusElement.textContent = message;

        // Показываем элемент
        statusElement.style.display = 'block';
    }

    /**
     * Показывает уведомление о необходимости подключения VPN
     */
    function showVpnNotification(context = 'general') {
        // Используем общую функцию из модуля finesse_agents.js, если она доступна
        if (window.showVpnNotification) {
            window.showVpnNotification(context);
            return;
        }

        // Резервная реализация, если основная функция недоступна
        // (код резервной реализации аналогичен функции в finesse_agents.js)
        // ...
    }

    /**
     * Инициализация модуля
     */
    function init() {
        // Проверяем, был ли модуль уже инициализирован
        if (window.callHistoryInitialized) {
            console.log('Модуль журнала звонков уже инициализирован');
            return;
        }

        // Помечаем модуль как инициализированный
        window.callHistoryInitialized = true;

        // Загружаем историю звонков при инициализации
        setTimeout(fetchCallHistory, 500);

        // Добавляем кнопку обновления
        addRefreshButton();

        console.log('Модуль журнала звонков инициализирован');
    }

    /**
     * Добавляет кнопку обновления журнала звонков
     */
    function addRefreshButton() {
        const accordionHeader = document.querySelector('.calls-panel .accordion-header');
        if (!accordionHeader) return;

        // Проверяем, нет ли уже кнопки
        if (accordionHeader.querySelector('.refresh-calls-btn')) return;

        // Создаем кнопку
        const refreshButton = document.createElement('button');
        refreshButton.className = 'refresh-calls-btn';
        refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshButton.setAttribute('title', 'Обновить журнал звонков');
        refreshButton.style.marginLeft = '10px';
        refreshButton.style.background = 'transparent';
        refreshButton.style.border = 'none';
        refreshButton.style.color = 'white';
        refreshButton.style.cursor = 'pointer';

        // Добавляем обработчик
        refreshButton.addEventListener('click', function(e) {
            e.stopPropagation(); // Предотвращаем срабатывание клика по аккордеону
            if (!isLoading) {
                fetchCallHistory();
                // Добавляем анимацию вращения
                this.querySelector('i').classList.add('fa-spin');
                setTimeout(() => {
                    this.querySelector('i').classList.remove('fa-spin');
                }, 1000);
            }
        });

        // Вставляем кнопку в заголовок перед иконкой
        const icon = accordionHeader.querySelector('.accordion-icon');
        if (icon) {
            accordionHeader.insertBefore(refreshButton, icon);
        } else {
            accordionHeader.appendChild(refreshButton);
        }
    }

    // Перемещаем функции форматирования и отображения модальных окон в глобальную область
    function formatClientData(client) {
        return `
            <div class="client-info">
                <div class="client-info-row">
                    <div class="client-info-label">Имя клиента:</div>
                    <div class="client-info-value">${client.client_name || 'Не указано'}</div>
                </div>
                <div class="client-info-row">
                    <div class="client-info-label">Город:</div>
                    <div class="client-info-value">${client.client_city || 'Не указано'}</div>
                </div>
                <div class="client-info-row">
                    <div class="client-info-label">Менеджер:</div>
                    <div class="client-info-value">${client.manager_name || 'Не указано'}</div>
                </div>
                <div class="client-info-row">
                    <div class="client-info-label">Метро:</div>
                    <div class="client-info-value">${client.metro_name || 'Не указано'}</div>
                </div>
                <div class="client-info-row">
                    <div class="client-info-label">Страна:</div>
                    <div class="client-info-value">${client.country_name || 'Не указано'}</div>
                </div>
            </div>
        `;
    }

    function formatAgencyData(agencyData) {
        if (!agencyData || agencyData.length === 0) {
            return '<div class="error-message"><i class="fas fa-exclamation-circle"></i><p>Информация об обзвоне не найдена</p></div>';
        }

        // Добавляем отладочный вывод
        console.log('Форматирование данных агентства:', agencyData);

        // Создаем HTML для всех записей
        return agencyData.map(agency => `
            <div class="agency-info">
                <div class="agency-info-row">
                    <div class="agency-info-label">Агентство:</div>
                    <div class="agency-info-value">${agency.agency_name || 'Не указано'}</div>
                </div>
                <div class="agency-info-row">
                    <div class="agency-info-label">Результат звонка:</div>
                    <div class="agency-info-value">${agency.call_result_text || 'Не указано'}</div>
                </div>
                <div class="agency-info-row">
                    <div class="agency-info-label">Страна:</div>
                    <div class="agency-info-value">${agency.client_country || 'Не указано'}</div>
                </div>
                <div class="agency-info-row">
                    <div class="agency-info-label">Метро:</div>
                    <div class="agency-info-value">${agency.metro || 'Не указано'}</div>
                </div>
                <div class="agency-info-row">
                    <div class="agency-info-label">Менеджер:</div>
                    <div class="agency-info-value">${agency.manager_name || 'Не указано'}</div>
                </div>
                <div class="agency-info-row">
                    <div class="agency-info-label">Дата и время:</div>
                    <div class="agency-info-value">${agency.datetime || 'Не указано'}</div>
                </div>
            </div>
            <hr class="agency-divider">
        `).join('');
    }

    // Делаем функции доступными глобально
    window.showClientCard = function(cardId) {
        const modal = document.getElementById('clientCardModal');
        const contentDiv = document.getElementById('clientCardContent');

        contentDiv.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Загрузка данных...</div>';
        modal.style.display = 'block';

        fetch(`/api/client-card/${cardId}`)
            .then(response => response.json())
            .then(data => {
                if (data.client) {
                    contentDiv.innerHTML = formatClientData(data.client);
                } else {
                    contentDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i><p>Данные о клиенте не найдены</p></div>';
                }
            })
            .catch(error => {
                contentDiv.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i><p>Ошибка при загрузке данных: ${error.message}</p></div>`;
            });
    };

    window.showAgencyInfo = function(ppId) {
        const modal = document.getElementById('agencyInfoModal');
        const contentDiv = document.getElementById('agencyInfoContent');

        contentDiv.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Загрузка данных...</div>';
        modal.style.display = 'block';

        console.log(`Запрашиваем данные об обзвоне для pp_id: ${ppId}`);

        // Возвращаем локальный URL
        fetch(`/api/call-agency-data/${ppId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin' // Важно для работы с сессиями
        })
        .then(response => {
            console.log('Получен ответ от сервера:', response.status);
            return response.json().then(data => {
                if (!response.ok) {
                    // Если сервер вернул ошибку, включаем информацию из ответа в сообщение об ошибке
                    throw new Error(data.error || `HTTP error! status: ${response.status}`);
                }
                return data;
            });
        })
        .then(data => {
            console.log('Получены данные:', data);
            if (data && data.agency_data && data.agency_data.length > 0) {
                console.log('Форматируем данные для отображения:', data.agency_data);
                contentDiv.innerHTML = formatAgencyData(data.agency_data);
            } else {
                console.log('Данные отсутствуют или пустые:', data);
                contentDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i><p>Информация об обзвоне не найдена</p></div>';
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке данных:', error);
            contentDiv.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-triangle"></i><p>Ошибка при загрузке данных: ${error.message}</p></div>`;
        });
    };

    // Функции закрытия модальных окон
    window.closeClientCard = function() {
        document.getElementById('clientCardModal').style.display = 'none';
    };

    window.closeAgencyInfo = function() {
        document.getElementById('agencyInfoModal').style.display = 'none';
    };

    // Запускаем инициализацию после загрузки DOM
    document.addEventListener('DOMContentLoaded', init);

    // Экспортируем функцию для внешнего вызова
    window.fetchCallHistory = fetchCallHistory;
})();
