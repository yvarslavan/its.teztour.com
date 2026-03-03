        // Функции для работы с модальными окнами
        function showClientCard(buttonElement) {
            console.log('Button element:', buttonElement);
            const callId = buttonElement.dataset.callId;
            const modal = document.getElementById('clientCardModal');
            const contentDiv = document.getElementById('clientCardContent');

            // Показываем спиннер загрузки
            contentDiv.innerHTML = '<div class="finesse-loading">Загрузка данных...</div>';
            modal.style.display = 'flex';

            // Добавляем логирование ID звонка
            console.log('Запрос карточки клиента для Call ID из data-атрибута:', callId);

            // Запрос данных с сервера
            fetch(`/api/client-card/call/${callId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Ошибка HTTP: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data && data.success && data.client_data) {
                        // Формируем содержимое карточки клиента, используя data.client_data
                        const clientData = data.client_data;
                        let html = `
                            <div class="client-card">
                                <div class="client-info">
                                    <h3>${clientData.client_name || 'Имя не указано'}</h3>
                                    <div class="client-phone">${clientData.phone || 'Телефон не указан'}</div>
                                    <div class="client-details">
                                        <p><strong>Email:</strong> ${clientData.email || 'Не указан'}</p>
                                        <p><strong>Город:</strong> ${clientData.client_city || 'Не указан'}</p>
                                        <p><strong>Менеджер:</strong> ${clientData.manager_name || 'Не указан'}</p>
                                        <p><strong>Метро:</strong> ${clientData.metro_name || 'Не указано'}</p>
                                        <p><strong>Страна:</strong> ${clientData.country_name || 'Не указана'}</p>
                                        <p><strong>Реклама:</strong> ${clientData.ad_name || 'Не указана'}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                        contentDiv.innerHTML = html;
                    } else {
                        // Если данные не найдены или success: false
                        contentDiv.innerHTML = `
                            <div class="error-message">
                                <i class="fas fa-exclamation-circle"></i>
                                <p>Информация о клиенте не найдена</p>
                            </div>
                        `;
                    }
                })
                .catch(error => {
                    // В случае ошибки
                    contentDiv.innerHTML = `
                        <div class="error-message">
                            <i class="fas fa-exclamation-triangle"></i>
                            <p>Ошибка при загрузке данных: ${error.message}</p>
                        </div>
                    `;
                    console.error('Ошибка при загрузке карточки клиента:', error);
                });
        }

        function closeClientCard() {
            const modal = document.getElementById('clientCardModal');
            modal.style.display = 'none';
        }

        function closeAgencyInfo() {
            const modal = document.getElementById('agencyInfoModal');
            // Плавно скрываем модальное окно с анимацией затухания
            modal.style.opacity = '0';
            setTimeout(() => {
                modal.style.display = 'none';
                // Сбрасываем прозрачность для следующего открытия
                modal.style.opacity = '';
            }, 200); // Соответствует времени анимации в CSS
        }

        function hideVpnNotification() {
            const notification = document.getElementById('vpnNotification');
            notification.style.display = 'none';
        }

        // Обработчики событий
        document.addEventListener('DOMContentLoaded', function() {
            // Установка текущей даты в заголовке журнала звонков
            const dateSpan = document.getElementById('currentCallLogDate');
            if (dateSpan) {
                const today = new Date();
                const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
                dateSpan.textContent = `Сегодня: ${today.toLocaleDateString('ru-RU', options)}`;
            }

            // Установка текущей даты в главном хедере
            const headerDateSpan = document.getElementById('headerCurrentDate');
            if (headerDateSpan) {
                const today = new Date();
                // Формат: "Сегодня: 15 мая 2025"
                const options = { day: 'numeric', month: 'long', year: 'numeric' };
                headerDateSpan.textContent = `Сегодня: ${today.toLocaleDateString('ru-RU', options)}`;
            }

            // Компактный профиль в шапке: синхронизация с Finesse авторизацией
            const loginButton = document.querySelector('header .header-actions .login-btn');
            const userControls = document.querySelector('.user-session-controls');
            const userMenuToggle = document.getElementById('userMenuToggle');
            const userDropdownMenu = document.getElementById('userDropdownMenu');
            const usernameDisplay = document.getElementById('usernameDisplay');
            const userDropdownName = document.getElementById('userDropdownName');
            const userAvatar = document.getElementById('userAvatar');

            function getDisplayName(userData) {
                if (!userData) return 'Оператор';
                if (userData.displayName) return userData.displayName;
                const fullName = `${userData.firstName || ''} ${userData.lastName || ''}`.trim();
                return fullName || userData.loginId || userData.username || 'Оператор';
            }

            function getInitials(name) {
                const normalized = (name || '').trim();
                if (!normalized) return 'OP';
                const parts = normalized.split(/\s+/).filter(Boolean);
                if (parts.length === 1) {
                    return parts[0].slice(0, 2).toUpperCase();
                }
                return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
            }

            function syncHeaderUserControls() {
                const finesseReady = window.finesseAuth && window.finesseAuth.isAuthenticated;
                const userData = window.finesseAuth && window.finesseAuth.userData;

                if (finesseReady && userData) {
                    const displayName = getDisplayName(userData);
                    if (loginButton) loginButton.style.display = 'none';
                    if (userControls) userControls.style.display = 'block';
                    if (usernameDisplay) usernameDisplay.textContent = displayName;
                    if (userDropdownName) userDropdownName.textContent = displayName;
                    if (userAvatar) userAvatar.textContent = getInitials(displayName);
                } else {
                    if (loginButton) loginButton.style.display = 'inline-flex';
                    if (userControls) {
                        userControls.style.display = 'none';
                        userControls.classList.remove('open');
                    }
                }
            }

            if (userMenuToggle && userControls) {
                userMenuToggle.addEventListener('click', function(event) {
                    event.stopPropagation();
                    const isOpen = userControls.classList.toggle('open');
                    userMenuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
                });
            }

            if (userDropdownMenu) {
                userDropdownMenu.addEventListener('click', function(event) {
                    event.stopPropagation();
                });
            }

            document.addEventListener('click', function() {
                if (userControls) userControls.classList.remove('open');
                if (userMenuToggle) userMenuToggle.setAttribute('aria-expanded', 'false');
            });

            document.addEventListener('finesseAuthSuccess', syncHeaderUserControls);
            document.addEventListener('finesseLogout', syncHeaderUserControls);
            setTimeout(syncHeaderUserControls, 500);

            // Инициализация аккордеона
            const accordionHeaders = document.querySelectorAll('.accordion-header');
            accordionHeaders.forEach(header => {
                 // --- Ищем родительский panel для текущего header ---
                 const panel = header.closest('.accordion-panel');
                 if (!panel) return; // Пропускаем, если не нашли панель

                 // --- Находим контент и иконку внутри этой панели ---
                 const content = panel.querySelector('.accordion-content');
                 const icon = header.querySelector('.accordion-icon');

                 if (!content || !icon) return; // Пропускаем, если нет контента или иконки

                header.addEventListener('click', function() {
                    // Переключаем класс 'active' на родительской панели
                    panel.classList.toggle('active');

                    // Убираем прямое управление max-height и overflow
                    /*
                    if (content.style.maxHeight) {
                        content.style.maxHeight = null;
                        icon.classList.remove('fa-chevron-up');
                        icon.classList.add('fa-chevron-down');
                    } else {
                        content.style.maxHeight = content.scrollHeight + "px";
                        icon.classList.remove('fa-chevron-down');
                        icon.classList.add('fa-chevron-up');
                    }
                    */
                });
            });

            // Открываем панель журнала звонков по умолчанию
            const callsPanel = document.querySelector('.calls-panel');
            if (callsPanel) {
                 callsPanel.classList.add('active');
                 // Стиль max-height теперь управляется CSS через класс 'active'
                 // const content = callsPanel.querySelector('.accordion-content');
                 // const icon = callsPanel.querySelector('.accordion-header .accordion-icon');
                 // if(content) content.style.maxHeight = content.scrollHeight + "px";
                 // if(icon) {
                 //    icon.classList.remove('fa-chevron-down');
                 //    icon.classList.add('fa-chevron-up');
                 // }
            }
            // Закрываем панель аналитики по умолчанию
            const analyticsPanel = document.getElementById('analyticsPanel');
            if (analyticsPanel) {
                analyticsPanel.classList.remove('active');
            }

            // Скрываем статус-бар после начальной загрузки страницы
            const statusBar = document.getElementById('callsStatusBar');
            if (statusBar) {
                statusBar.style.display = 'none'; // Скрываем по умолчанию
            }

            // Привязываем кнопку обновления
            const refreshBtn = document.querySelector('.refresh-calls-btn');

            if (refreshBtn) {
                refreshBtn.addEventListener('click', function(e) {
                    e.stopPropagation(); // Предотвращаем срабатывание клика по аккордеону

                    // Получаем текущую выбранную дату
                    const selectedDate = document.getElementById('callLogDatePicker').value;

                    // Показываем анимацию вращения на кнопке
                    const icon = this.querySelector('i');
                    if (icon) icon.classList.add('fa-spin');

                    // Вызываем функцию обновления таблицы с текущей датой
                    updateTableForDate(selectedDate);
                    // Также обновляем статистику операторов для этой даты
                    fetchOperatorStats(selectedDate);

                    // Убираем анимацию вращения через некоторое время (например, 1 секунду)
                    // Это нужно, так как updateTableForDate асинхронная
                    setTimeout(() => {
                        if (icon) icon.classList.remove('fa-spin');
                    }, 1000);
                });
            }

            // Проверяем наличие функции обновления уведомлений
            if (typeof updateNotificationCount === 'function') {
                // Проверяем, авторизован ли пользователь
                const isLoggedIn = Boolean(window.finesseAuth && window.finesseAuth.isAuthenticated);
                if (isLoggedIn) {
                    // Вызываем функцию только если пользователь авторизован
                    updateNotificationCount();
                }
            }

            // Добавляем логику фильтрации журнала звонков СЮДА
            const phoneSearchInput = document.getElementById('phoneSearch');
            const operatorFilterInput = document.getElementById('operatorSelect'); // <<< ИЗМЕНЕНО: Используем ID select'а
            const callsTableBody = document.querySelector('.calls-table tbody');
            let noCallsRow = callsTableBody && callsTableBody.querySelector('.no-calls-message')
                ? callsTableBody.querySelector('.no-calls-message').closest('tr')
                : null;
            // <<< ДОБАВЛЕНО: Находим кнопку очистки оператора >>>
            const clearOperatorBtn = document.getElementById('clearOperatorFilter');

            function syncNoCallsRowReference() {
                if (!callsTableBody) {
                    noCallsRow = null;
                    return;
                }
                const noCallsCell = callsTableBody.querySelector('.no-calls-message');
                noCallsRow = noCallsCell ? noCallsCell.closest('tr') : null;
            }

            function formatOperatorInitials(operatorName) {
                const normalized = (operatorName || '').trim();
                if (!normalized || normalized === '-') return 'OP';
                const parts = normalized.split(/\s+/).filter(Boolean);
                if (parts.length === 1) {
                    return parts[0].slice(0, 2).toUpperCase();
                }
                return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
            }

            function buildOperatorCellContent(operatorName) {
                const displayName = (operatorName || '-').trim() || '-';
                const wrapper = document.createElement('div');
                wrapper.className = 'operator-person';

                const avatar = document.createElement('span');
                avatar.className = 'operator-avatar-badge';
                avatar.textContent = formatOperatorInitials(displayName);
                wrapper.appendChild(avatar);

                const text = document.createElement('span');
                text.className = 'operator-name-text';
                text.textContent = displayName;
                wrapper.appendChild(text);

                return wrapper;
            }

            function enhanceOperatorCells() {
                if (!callsTableBody) return;
                const rows = callsTableBody.querySelectorAll('tr');
                rows.forEach(row => {
                    if (row === noCallsRow || !row.cells || !row.cells[2]) return;
                    const operatorCell = row.cells[2];
                    if (operatorCell.querySelector('.operator-person')) return;
                    const operatorName = operatorCell.textContent.trim();
                    operatorCell.textContent = '';
                    operatorCell.appendChild(buildOperatorCellContent(operatorName));
                });
            }

            // <<< ДОБАВЛЕНО: Функция для заполнения выпадающего списка операторов >>>
            function populateOperatorFilter(rows) {
                if (!operatorFilterInput || !clearOperatorBtn) return;
                syncNoCallsRowReference();
                const operators = new Set();
                rows.forEach(row => {
                    if (row === noCallsRow || !row.cells[2]) return; // Пропускаем строку "нет звонков" и проверяем наличие ячейки
                    const operatorNameElement = row.cells[2].querySelector('.operator-name-text');
                    const operatorName = operatorNameElement ? operatorNameElement.textContent.trim() : row.cells[2].textContent.trim();
                    if (operatorName && operatorName !== '-') { // Добавляем только если имя не пустое и не '-'
                        operators.add(operatorName);
                    }
                });

                // Сохраняем текущее выбранное значение
                const currentSelectedValue = operatorFilterInput.value;

                // Очищаем текущие опции (кроме первой "Все операторы")
                while (operatorFilterInput.options.length > 1) {
                    operatorFilterInput.remove(1);
                }

                // Сортируем имена операторов
                const sortedOperators = Array.from(operators).sort();

                // Добавляем новые опции
                sortedOperators.forEach(opName => {
                    const option = document.createElement('option');
                    option.value = opName;
                    option.textContent = opName;
                    operatorFilterInput.appendChild(option);
                });

                // Восстанавливаем ранее выбранное значение, если оно все еще есть в списке
                if (Array.from(operatorFilterInput.options).some(opt => opt.value === currentSelectedValue)) {
                    operatorFilterInput.value = currentSelectedValue;
                } else {
                    operatorFilterInput.value = ""; // Сбрасываем на "Все операторы" если старого значения нет
                }
                 // Показываем/скрываем кнопку очистки в зависимости от выбора
                 clearOperatorBtn.style.display = operatorFilterInput.value ? 'inline' : 'none';
            }

            function filterCalls() {
                if (!callsTableBody) return;
                syncNoCallsRowReference();
                const phoneFilter = phoneSearchInput.value.toLowerCase().trim();
                const operatorFilter = operatorFilterInput.value; // <<< ИЗМЕНЕНО: Получаем value из select'а
                let visibleRows = 0;
                const rows = Array.from(callsTableBody.querySelectorAll('tr')); // Преобразуем в массив для populateOperatorFilter

                rows.forEach(row => {
                    if (row === noCallsRow) return;
                    const phoneCell = row.cells[0];
                    const operatorCell = row.cells[2];
                    // <<< ИЗМЕНЕНО: Убедимся что ячейки существуют перед доступом к ним >>>
                    if (!phoneCell || !operatorCell) {
                        row.style.display = 'none'; // Скрыть строку, если структура нарушена
                        return;
                    }
                    const phoneNumber = phoneCell.querySelector('.phone-number') ? phoneCell.querySelector('.phone-number').textContent.toLowerCase().trim() : '';
                    const operatorNameElement = operatorCell.querySelector('.operator-name-text');
                    const operatorName = operatorNameElement ? operatorNameElement.textContent.trim() : operatorCell.textContent.trim();

                    const phoneMatch = phoneNumber.includes(phoneFilter);
                    // <<< ИЗМЕНЕНО: Сравниваем с выбранным оператором или показываем, если фильтр пуст ("Все операторы") >>>
                    const operatorMatch = !operatorFilter || operatorName === operatorFilter;

                    if (phoneMatch && operatorMatch) {
                        row.style.display = '';
                        visibleRows++;
                    } else {
                        row.style.display = 'none';
                    }
                });
                if (noCallsRow) {
                     noCallsRow.style.display = visibleRows === 0 ? '' : 'none';
                }

                // <<< УДАЛЕНО: populateOperatorFilter теперь вызывается после загрузки данных >>>
                // populateOperatorFilter(rows); // Обновляем список операторов после каждой фильтрации
            }

            if (phoneSearchInput && operatorFilterInput && callsTableBody && clearOperatorBtn) {
                phoneSearchInput.addEventListener('input', filterCalls);
                operatorFilterInput.addEventListener('change', () => { // <<< ИЗМЕНЕНО: Слушаем 'change' для select'а
                    filterCalls();
                    // Показываем/скрываем кнопку очистки при изменении select'а
                    clearOperatorBtn.style.display = operatorFilterInput.value ? 'inline' : 'none';
                });
            } else {
                 console.error("Элементы для фильтрации звонков (select, clear button) не найдены!");
            }

            // --- Логика для кнопок очистки фильтров ---
            function setupClearButton(inputId, clearBtnId) {
                const input = document.getElementById(inputId); // Может быть input или select
                const clearBtn = document.getElementById(clearBtnId);

                if (!input || !clearBtn) return;

                // Показать/скрыть кнопку при вводе (для text input)
                if (input.tagName.toLowerCase() === 'input') {
                    input.addEventListener('input', () => {
                        clearBtn.style.display = input.value ? 'inline' : 'none';
                    });
                }
                // Для select, показ/скрытие управляется в 'change' и populateOperatorFilter

                // Очистка поля при клике на кнопку
                clearBtn.addEventListener('click', () => {
                    if (input.tagName.toLowerCase() === 'select') {
                         input.value = ''; // Сброс select на "Все операторы"
                    } else {
                         input.value = ''; // Очистка input
                    }
                    clearBtn.style.display = 'none';
                    // Генерируем событие input или change, чтобы обновить фильтрацию
                    const eventType = input.tagName.toLowerCase() === 'select' ? 'change' : 'input';
                    input.dispatchEvent(new Event(eventType, { bubbles: true }));
                });
            }

            setupClearButton('phoneSearch', 'clearPhoneSearch');
            setupClearButton('operatorSelect', 'clearOperatorFilter'); // <<< ИЗМЕНЕНО: Используем ID select'а
            // --- Конец логики для кнопок очистки ---

            // --- Логика для выбора даты ---
            const datePicker = document.getElementById('callLogDatePicker');
            const dateDisplaySpan = document.getElementById('currentCallLogDate');
            const callsCountSpan = document.getElementById('callsCountDisplay')?.querySelector('span'); // Получаем span внутри div
            const operatorStatsContainer = document.getElementById('operatorStatsContainer'); // Получаем контейнер статистики
            const kpiKnownCallsValue = document.getElementById('kpiKnownCallsValue');
            const kpiKnownCallsRatio = document.getElementById('kpiKnownCallsRatio');
            const analyticsReportDateDisplay = document.getElementById('analyticsReportDate'); // Переименовываем для ясности
            const analyticsDatePicker = document.getElementById('analyticsDatePicker'); // Новый календарь для аналитики

            function emitCallLogUpdated(calls, dateString, error = '') {
                document.dispatchEvent(new CustomEvent('moscowCallLogUpdated', {
                    detail: {
                        calls: Array.isArray(calls) ? calls : [],
                        date: dateString || '',
                        error: error || ''
                    }
                }));
            }

            function updateCallsKpi(calls) {
                const totalCalls = Array.isArray(calls) ? calls.length : 0;
                const knownCalls = Array.isArray(calls)
                    ? calls.filter(call => call.phone_number && call.phone_number !== 'None' && String(call.phone_number).toLowerCase() !== 'unknown').length
                    : 0;
                const knownRatio = totalCalls > 0 ? Math.round((knownCalls / totalCalls) * 100) : 0;

                if (callsCountSpan) callsCountSpan.textContent = String(totalCalls);
                if (kpiKnownCallsValue) kpiKnownCallsValue.textContent = String(knownCalls);
                if (kpiKnownCallsRatio) kpiKnownCallsRatio.textContent = `${knownRatio}% от общего объема`;
            }

            // Устанавливаем сегодняшнюю дату по умолчанию
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0'); // Месяцы 0-11
            const dd = String(today.getDate()).padStart(2, '0');
            const todayString = `${yyyy}-${mm}-${dd}`;
            if (datePicker) {
                datePicker.value = todayString;
            }

            function updateTableForDate(dateString) {
                console.log('[updateTableForDate] LOG 1: Function called with dateString:', dateString);
                if (!callsTableBody) {
                    console.error('[updateTableForDate] LOG ERROR: callsTableBody element not found. Main log will not load.');
                    return;
                }
                console.log('[updateTableForDate] LOG 2: callsTableBody found:', callsTableBody);

                // Показываем загрузку ТОЛЬКО для основного журнала
                callsTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;"><i class="fas fa-spinner fa-spin"></i> Загрузка основного журнала...</td></tr>';
                console.log('[updateTableForDate] LOG 3: Loading spinner set for main log.');

                const apiUrl = `/api/moscow-calls?date=${dateString}`;
                console.log(`[updateTableForDate] LOG 4: Preparing to fetch from URL: ${apiUrl}`);

                fetch(apiUrl)
                    .then(response => {
                        console.log('[updateTableForDate] LOG 5: Fetch response received. Status:', response.status, 'Ok:', response.ok);
                        if (!response.ok) {
                            // Попытка получить текст ошибки из тела ответа
                            return response.text().then(text => {
                                console.error(`[updateTableForDate] LOG ERROR: Network response was not ok. Status: ${response.status}, Response text: ${text}`);
                                throw new Error(`Ошибка сети: ${response.status}. Детали: ${text || 'Нет деталей'}`);
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('[updateTableForDate] LOG 6: JSON data parsed successfully:', data);
                        callsTableBody.innerHTML = ''; // Очищаем tbody
                        let callCount = 0;

                        if (data && data.success && data.calls && data.calls.length > 0) {
                            console.log('[updateTableForDate] LOG 7A: Data is successful and calls exist. Count:', data.calls.length);
                            callCount = data.calls.length;
                            // ... (код для заполнения таблицы звонков) ...
                            data.calls.forEach(call => {
                                const row = document.createElement('tr');
                                const phoneCell = document.createElement('td');
                                const phoneSpan = document.createElement('span');
                                phoneSpan.className = `phone-number ${!call.phone_number || call.phone_number === 'None' ? 'unknown-number' : ''}`;
                                if (call.phone_number && call.phone_number !== 'None') {
                                    phoneSpan.textContent = call.phone_number;
                                } else {
                                    phoneSpan.innerHTML = '<span class="phone-unknown-label">Телефон не определен</span>';
                                }
                                phoneCell.appendChild(phoneSpan);
                                const buttonsDiv = document.createElement('div');
                                if (call.has_client_card) {
                                    const clientBtn = document.createElement('button');
                                    clientBtn.className = 'action-btn client-card-btn';
                                    clientBtn.innerHTML = '<i class="fas fa-id-card"></i>Карта клиента';
                                    clientBtn.dataset.callId = call.id;
                                    clientBtn.onclick = () => showClientCard(clientBtn);
                                    buttonsDiv.appendChild(clientBtn);
                                }
                                if (call.pp_id) {
                                    const infoBtn = document.createElement('button');
                                    infoBtn.className = 'action-btn agency-info-btn';
                                    infoBtn.title = 'Информация об обзвоне';
                                    infoBtn.innerHTML = '<i class="fas fa-info-circle"></i>Инфо';
                                    infoBtn.onclick = () => showAgencyInfo(call.pp_id);
                                    buttonsDiv.appendChild(infoBtn);
                                }
                                phoneCell.appendChild(buttonsDiv);
                                row.appendChild(phoneCell);
                                const timeCell = document.createElement('td');
                                timeCell.textContent = call.time || '-';
                                row.appendChild(timeCell);
                                const operatorCell = document.createElement('td');
                                operatorCell.appendChild(buildOperatorCellContent(call.operator || '-'));
                                row.appendChild(operatorCell);
                                const resultCell = document.createElement('td');
                                const resultSpan = document.createElement('span');
                                resultSpan.className = 'call-result-badge';
                                switch (call.result) {
                                    case 0: resultSpan.classList.add('result-failed'); break;
                                    case 1: resultSpan.classList.add('result-success'); break;
                                    case 2: resultSpan.classList.add('result-dropped'); break;
                                    case 3: resultSpan.classList.add('result-no-internet'); break;
                                    case 4: case 5: case 6: resultSpan.classList.add('result-failed'); break;
                                    default: resultSpan.classList.add('result-unknown');
                                }
                                resultSpan.textContent = call.call_result_text || '-';
                                resultCell.appendChild(resultSpan);
                                row.appendChild(resultCell);
                                const typeCell = document.createElement('td');
                                typeCell.textContent = call.call_type_text || '-';
                                row.appendChild(typeCell);
                                callsTableBody.appendChild(row);
                            });

                            const allRows = Array.from(callsTableBody.querySelectorAll('tr'));
                            populateOperatorFilter(allRows);
                            console.log('[updateTableForDate] LOG 7B: Attempting to render analytics. Calls data:', data.calls, 'Selected date:', dateString);
                            if (typeof renderDailyAnalyticsReport === 'function') {
                                renderDailyAnalyticsReport(data.calls, dateString);
                            }
                            updateCallsKpi(data.calls);
                            enhanceOperatorCells();
                            filterCalls();
                            emitCallLogUpdated(data.calls, dateString);
                        } else {
                            console.log('[updateTableForDate] LOG 8: No calls data or success:false for main log. Selected date:', dateString, 'Data received:', data);
                            const emptyRow = document.createElement('tr');
                            emptyRow.innerHTML = `<td colspan="5" class="no-calls-message"><i class="fas fa-phone-slash"></i><p>Журнал звонков пуст за ${new Date(dateString + 'T00:00:00').toLocaleDateString('ru-RU')}</p></td>`;
                            callsTableBody.appendChild(emptyRow);
                            updateCallsKpi([]);
                            const allRows = Array.from(callsTableBody.querySelectorAll('tr'));
                            populateOperatorFilter(allRows);
                            syncNoCallsRowReference();
                            filterCalls();
                            emitCallLogUpdated([], dateString);
                            // ОТСЮДА УБРАН ВЫЗОВ clearAnalyticsReport
                        }

                        if (callsCountSpan) callsCountSpan.textContent = String(callCount);
                        if (dateDisplaySpan) {
                             const selectedDateObj = new Date(dateString + 'T00:00:00');
                             const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
                             dateDisplaySpan.textContent = selectedDateObj.toLocaleDateString('ru-RU', options);
                        }
                        // ОТСЮДА УБРАНО ОБНОВЛЕНИЕ analyticsReportDateSpan
                    })
                    .catch(error => {
                        console.error('[updateTableForDate] LOG 9: Error during fetch promise chain for main log:', error.message, error);
                        callsTableBody.innerHTML = `<tr><td colspan="5" class="error-message"><i class="fas fa-exclamation-triangle"></i> Ошибка загрузки: ${error.message}</td></tr>`;
                        if (callsCountSpan) callsCountSpan.textContent = '0';
                        if (kpiKnownCallsValue) kpiKnownCallsValue.textContent = '0';
                        if (kpiKnownCallsRatio) kpiKnownCallsRatio.textContent = 'Нет данных';
                        if (dateDisplaySpan) dateDisplaySpan.textContent = 'Ошибка загрузки даты';
                        if (operatorFilterInput) {
                            operatorFilterInput.value = '';
                            while (operatorFilterInput.options.length > 1) {
                                operatorFilterInput.remove(1);
                            }
                        }
                        if (clearOperatorBtn) clearOperatorBtn.style.display = 'none';
                        syncNoCallsRowReference();
                        emitCallLogUpdated([], dateString, error.message);
                        // ОТСЮДА УБРАНО ОБНОВЛЕНИЕ analyticsReportDateSpan И ВЫЗОВ showErrorInAnalyticsReport
                    });
            }

            // --- Новая функция для загрузки статистики операторов ---
            function fetchOperatorStats(dateString) {
                if (!operatorStatsContainer) return;

                // Показываем загрузку
                operatorStatsContainer.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка статистики...';

                fetch(`/api/moscow-operator-stats?date=${dateString}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Ошибка сети: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        operatorStatsContainer.innerHTML = '';
                        if (data.success && data.stats && data.stats.length > 0) {
                            const topStats = [...data.stats]
                                .sort((a, b) => (b.call_count || 0) - (a.call_count || 0))
                                .slice(0, 4);

                            const maxValue = topStats[0]?.call_count || 1;
                            const statsList = document.createElement('div');
                            statsList.className = 'kpi-leaders-list';

                            topStats.forEach(stat => {
                                const row = document.createElement('div');
                                row.className = 'kpi-leader-row';

                                const name = document.createElement('span');
                                name.className = 'kpi-leader-name';
                                name.textContent = stat.operator_name || 'Оператор';
                                name.title = stat.operator_name || 'Оператор';
                                row.appendChild(name);

                                const count = document.createElement('span');
                                count.className = 'kpi-leader-count';
                                count.textContent = String(stat.call_count || 0);
                                row.appendChild(count);

                                const bar = document.createElement('div');
                                bar.className = 'kpi-leader-bar';
                                const fill = document.createElement('span');
                                fill.style.width = `${Math.max(8, Math.round(((stat.call_count || 0) / maxValue) * 100))}%`;
                                bar.appendChild(fill);
                                row.appendChild(bar);

                                statsList.appendChild(row);
                            });

                            operatorStatsContainer.appendChild(statsList);
                        } else if (data.success) {
                            operatorStatsContainer.innerHTML = '<span style="font-size: 12px; color: #6b7280;">Статистики за день нет</span>';
                        } else {
                            throw new Error(data.error || 'Неизвестная ошибка при получении статистики');
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка загрузки статистики операторов:', error);
                        operatorStatsContainer.innerHTML = `<span style="font-size: 12px; color: #dc2626;" title="${error.message}"><i class="fas fa-exclamation-triangle"></i> Ошибка загрузки</span>`;
                    });
            }

            // --- Новая функция для загрузки и отображения АНАЛИТИКИ ---
            function fetchAndRenderAnalytics(dateString) {
                console.log('[fetchAndRenderAnalytics] Called for date:', dateString);
                if (!document.getElementById('dailySummaryStats') || !document.getElementById('operatorDetailsTableContainer') || !document.getElementById('callTypeAnalysisTableContainer')) {
                    console.error('[fetchAndRenderAnalytics] Analytics container elements not found.');
                    return;
                }

                // Показываем спиннеры в секциях аналитики
                document.getElementById('dailySummaryStats').innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Загрузка общей статистики...</p>';
                document.getElementById('operatorDetailsTableContainer').innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Загрузка статистики по операторам...</p>';
                document.getElementById('callTypeAnalysisTableContainer').innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Загрузка анализа по типам звонков...</p>';

                if (analyticsReportDateDisplay) {
                    const dateObj = new Date(dateString + 'T00:00:00');
                    const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
                    analyticsReportDateDisplay.textContent = dateObj.toLocaleDateString('ru-RU', options);
                } else {
                    console.warn('[fetchAndRenderAnalytics] analyticsReportDateDisplay element not found.');
                }

                const apiUrl = `/api/moscow-calls?date=${dateString}`;
                console.log(`[fetchAndRenderAnalytics] Fetching analytics data from: ${apiUrl}`);

                fetch(apiUrl)
                    .then(response => {
                        console.log('[fetchAndRenderAnalytics] Fetch response status:', response.status);
                        if (!response.ok) {
                            return response.text().then(text => {
                                throw new Error(`Ошибка сети при загрузке аналитики: ${response.status}. ${text}`);
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('[fetchAndRenderAnalytics] Data received:', data);
                        if (data && data.success && data.calls) {
                            renderDailyAnalyticsReport(data.calls, dateString);
                        } else {
                            console.warn('[fetchAndRenderAnalytics] No calls data or success:false. Clearing analytics.');
                            clearAnalyticsReport(dateString);
                        }
                    })
                    .catch(error => {
                        console.error('[fetchAndRenderAnalytics] Error:', error.message);
                        showErrorInAnalyticsReport(error.message);
                        if (analyticsReportDateDisplay) {
                            analyticsReportDateDisplay.textContent = 'Ошибка!';
                        }
                    });
            }

            // Загружаем статистику операторов для сегодняшней даты при загрузке страницы
            fetchOperatorStats(todayString);
            // Вызываем первоначальное обновление таблицы основного журнала для сегодняшней даты
            console.log('[DOMContentLoaded] LOG_INIT: About to call updateTableForDate for todayString:', todayString);
            updateTableForDate(todayString);

            // Инициализация и первоначальная загрузка для КАЛЕНДАРЯ АНАЛИТИКИ
            if (analyticsDatePicker) {
                analyticsDatePicker.value = todayString;
                console.log('[DOMContentLoaded] LOG_INIT_ANALYTICS: About to call fetchAndRenderAnalytics for todayString:', todayString);
                fetchAndRenderAnalytics(todayString); // Первоначальная загрузка аналитики

                analyticsDatePicker.addEventListener('change', function() {
                    console.log('[analyticsDatePicker] Date changed to:', this.value);
                    fetchAndRenderAnalytics(this.value);
                });

                // Предотвращаем сворачивание аккордеона при клике на календарь
                analyticsDatePicker.addEventListener('click', function(event) {
                    event.stopPropagation();
                });
            } else {
                console.warn('[DOMContentLoaded] analyticsDatePicker element not found!');
            }

            if (datePicker) {
                 datePicker.addEventListener('change', function() {
                     updateTableForDate(this.value);
                     fetchOperatorStats(this.value); // Вызываем загрузку статистики при смене даты
                 });
            }

            // <<< ДОБАВЛЕНО: Вызов populateOperatorFilter при начальной загрузке страницы >>>
             const initialRows = Array.from(callsTableBody.querySelectorAll('tr'));
             syncNoCallsRowReference();
             populateOperatorFilter(initialRows);
             enhanceOperatorCells();
             const initialCallsForKpi = initialRows
                .filter(row => row !== noCallsRow && row.cells && row.cells[0])
                .map(row => {
                    const phoneElement = row.cells[0].querySelector('.phone-number');
                    const isUnknown = !phoneElement || phoneElement.classList.contains('unknown-number');
                    return { phone_number: isUnknown ? null : phoneElement.textContent.trim() };
                });
             updateCallsKpi(initialCallsForKpi);

        }); // Конец основного DOMContentLoaded
        console.log('[DOMContentLoaded] LOG_END: All event listeners and initial calls set up.');

    console.log('ANALYTICS SCRIPT BLOCK - VERSION_CHECK_001 LOADED'); // TEST LOG
    // Глобальная переменная для хранения данных для аналитики, чтобы не передавать их везде
    let callsDataForAnalytics = [];

    // Добавляем функцию для перенаправления на Яндекс Карты
    function openInYandexMaps(address) {
        if (!address || address === '-') return;

        // Кодируем адрес для URL
        const encodedAddress = encodeURIComponent(address);

        // Формируем URL для Яндекс Карт
        const yandexMapsUrl = `https://yandex.ru/maps/?text=${encodedAddress}`;

        // Открываем в новой вкладке
        window.open(yandexMapsUrl, '_blank');
    }

    // <<< НАЧАЛО ИЗМЕНЕНИЯ: Возвращаем функцию formatAgencyData >>>
    function formatAgencyData(agencyDataArray) { // Переименован параметр для ясности
        if (!agencyDataArray || agencyDataArray.length === 0) {
            return '<div class="error-message"><i class="fas fa-exclamation-circle"></i><p>Информация об обзвоне не найдена</p></div>';
        }

        const agencyData = agencyDataArray[0]; // Берем первую запись, как и раньше

        // Логика отображения, почти полностью взятая из showAgencyDetails
        let html = '<div class="agency-info-card" style="text-align: left;">';

        const displayValue = (value, defaultValue = '-') => value !== null && value !== undefined && value !== '' ? value : defaultValue;
        const displayBool = (value) => value ? 'Да' : 'Нет';

        // ID и Названия
        html += `<div class="info-row"><i class="fas fa-hashtag info-icon hashtag"></i><span class="info-label">ID Агентства:</span><span class="info-value">${displayValue(agencyData.agency_db_id)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-building info-icon agency"></i><span class="info-label">Название:</span><span class="info-value"><strong>${displayValue(agencyData.agency_name_ru)}</strong></span></div>`;
        html += `<div class="info-row"><i class="fas fa-language info-icon globe"></i><span class="info-label">Название (англ.):</span><span class="info-value"><strong>${displayValue(agencyData.agency_name_en)}</strong></span></div>`;

        // Адрес (кликабельный)
        const address = displayValue(agencyData.agency_address);
        if (address !== '-') {
            html += `<div class="info-row">
                        <i class="fas fa-map-marker-alt info-icon map-marker-alt"></i>
                        <span class="info-label">Адрес:</span>
                        <span class="info-value">
                            <a href="javascript:void(0)"
                               class="map-link"
                               onclick="openInYandexMaps('${address.replace(/'/g, "\\'")}')">
                                ${address}
                                <i class="fas fa-external-link-alt map-link-icon"></i>
                            </a>
                        </span>
                     </div>`;
        } else {
            html += `<div class="info-row"><i class="fas fa-map-marker-alt info-icon map-marker-alt"></i><span class="info-label">Адрес:</span><span class="info-value">-</span></div>`;
        }

        // Город, Метро, Район, Зона, Регион
        html += `<div class="info-row"><i class="fas fa-city info-icon city"></i><span class="info-label">Город:</span><span class="info-value">${displayValue(agencyData.city_name)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-subway info-icon metro"></i><span class="info-label">Метро:</span><span class="info-value">${displayValue(agencyData.agency_metro_name)}</span></div>`; // Используем agency_metro_name
        html += `<div class="info-row"><i class="fas fa-map-signs info-icon map-signs"></i><span class="info-label">Район города:</span><span class="info-value">${displayValue(agencyData.district_name)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-map info-icon map"></i><span class="info-label">Зона:</span><span class="info-value">${displayValue(agencyData.area_name)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-globe-europe info-icon map"></i><span class="info-label">Регион:</span><span class="info-value">${displayValue(agencyData.region_name_from_db)}</span></div>`;

        // Информация о времени и режиме
        html += `<div class="info-row"><i class="fas fa-clock info-icon clock"></i><span class="info-label">Часовой пояс (смещение от Мск):</span><span class="info-value">${displayValue(agencyData.time_zone)}</span></div>`;
        // html += `<div class="info-row"><i class="far fa-calendar-alt info-icon calendar-alt"></i><span class="info-label">Режим работы ID:</span><span class="info-value">${displayValue(agencyData.time_rezhim_id)}</span></div>`; // Закомментировано

        // Булевы флаги
        html += `<div class="info-row"><i class="fas fa-user-check info-icon user-check"></i><span class="info-label">Англ. туристы:</span><span class="info-value">${displayBool(agencyData.english)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-ticket-alt info-icon ticket-alt"></i><span class="info-label">Продажа билетов:</span><span class="info-value">${displayBool(agencyData.tickets)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-ban info-icon ban"></i><span class="info-label">"Станция не задана":</span><span class="info-value">${displayBool(agencyData.station_not_set)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-random info-icon random"></i><span class="info-label">"Перекл. на Мск":</span><span class="info-value">${displayBool(agencyData.switch_msk_agency)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-credit-card info-icon credit-card"></i><span class="info-label">Прием банк. карт:</span><span class="info-value">${displayBool(agencyData.bank_card)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-plane-departure info-icon plane-departure"></i><span class="info-label">Туры в Стамбул:</span><span class="info-value">${displayBool(agencyData.stambul)}</span></div>`;
        html += `<div class="info-row"><i class="fas fa-skiing info-icon skiing"></i><span class="info-label">Туры в Австрию:</span><span class="info-value">${displayBool(agencyData.austria)}</span></div>`;

        // Комментарий (Как пройти)
        const commentText = displayValue(agencyData.agency_comment);
        const trimmedComment = commentText !== '-' ? commentText.trim() : '-';
        if (trimmedComment && trimmedComment !== '-') {
            html += `<div class="info-row">
                        <i class="fas fa-directions info-icon directions"></i>
                        <span class="info-label">Как пройти:</span>
                        <span class="info-value">
                            <div style="max-height: 150px; overflow-y: auto; white-space: pre-line; word-break: break-word; padding-right: 5px;">
                                ${trimmedComment}
                            </div>
                        </span>
                     </div>`;
        } else {
             html += `<div class="info-row"><i class="fas fa-directions info-icon"></i><span class="info-label">Как пройти:</span><span class="info-value">-</span></div>`;
        }

        // Телефоны (детализированные)
        if (agencyData.telephones_detailed && agencyData.telephones_detailed.length > 0) {
            let phonesHtml = agencyData.telephones_detailed.map(tel => {
                let phoneEntry = `<i class="fas fa-phone-alt info-icon" style="margin-right: 5px; font-size: 0.9em;"></i>${displayValue(tel.number)}`;
                if (tel.comment && tel.comment !== "NULL") {
                    phoneEntry += ` <small style="color: #555;">(${displayValue(tel.comment)})</small>`;
                }
                // Добавляем отображение режима работы для телефона
                if (tel.work_schedule) {
                    phoneEntry += '<div style="font-size: 0.8em; margin-left: 25px; color: #666;">';
                    const schedule = tel.work_schedule;
                    // Простая группировка для Пн-Пт, если время совпадает
                    let weekdaysSchedule = '';
                    if (schedule.monday && schedule.monday === schedule.tuesday && schedule.monday === schedule.wednesday && schedule.monday === schedule.thursday && schedule.monday === schedule.friday) {
                        weekdaysSchedule = `Пн-Пт: ${schedule.monday}`;
                        phoneEntry += `${weekdaysSchedule}<br>`;
                    } else {
                        if(schedule.monday) phoneEntry += `Пн: ${schedule.monday}<br>`;
                        if(schedule.tuesday) phoneEntry += `Вт: ${schedule.tuesday}<br>`;
                        if(schedule.wednesday) phoneEntry += `Ср: ${schedule.wednesday}<br>`;
                        if(schedule.thursday) phoneEntry += `Чт: ${schedule.thursday}<br>`;
                        if(schedule.friday) phoneEntry += `Пт: ${schedule.friday}<br>`;
                    }
                    if (schedule.saturday) {
                        phoneEntry += `Сб: ${schedule.saturday}<br>`;
                    }
                    if (schedule.sunday) {
                        phoneEntry += `Вс: ${schedule.sunday}`;
                    }
                    // Убираем последний <br> если он есть и за ним ничего нет
                    if (phoneEntry.endsWith('<br>')) {
                        phoneEntry = phoneEntry.slice(0, -4);
                    }
                    phoneEntry += '</div>';
                }
                return phoneEntry;
            }).join('<br style="margin-bottom: 8px; margin-top: 3px;">'); // Увеличим немного отступ между записями о телефонах
            html += `<div class="info-row"><i class="fas fa-phone-square-alt info-icon operator"></i><span class="info-label">Телефоны:</span><span class="info-value">${phonesHtml}</span></div>`;
        } else {
            html += `<div class="info-row"><i class="fas fa-phone-slash info-icon"></i><span class="info-label">Телефоны:</span><span class="info-value">-</span></div>`;
        }

        // Информация о звонке (специфична для formatAgencyData)
        let resultIconClass = 'result-neutral';
        if (agencyData.result === 0) resultIconClass = 'result-success'; // Дозвон
        else if ([ -1, 1, 4, 5].includes(agencyData.result)) resultIconClass = 'result-fail'; // Ошибка, занято, бросили, тишина

        html += `<hr style="margin: 15px 0;">
                 <div class="info-row">
                    <i class="fas fa-phone-alt info-icon ${resultIconClass}"></i>
                    <span class="info-label">Результат звонка:</span>
                    <span class="info-value">${agencyData.call_result_text || '-'}</span>
                </div>
                 <div class="info-row">
                    <i class="fas fa-user-tie info-icon client"></i>
                    <span class="info-label">Клиент (из обзвона):</span>
                    <span class="info-value">${agencyData.client_name || '-'}</span>
                </div>
                <div class="info-row">
                    <i class="fas fa-globe-americas info-icon country"></i>
                    <span class="info-label">Страна (из обзвона):</span>
                    <span class="info-value">${agencyData.client_country || '-'}</span>
                </div>
                <div class="info-row">
                    <i class="fas fa-subway info-icon metro"></i>
                    <span class="info-label">Метро (из обзвона):</span>
                    <span class="info-value">${agencyData.client_metro || '-'}</span>
                </div>
                <div class="info-row">
                    <i class="fas fa-user-tag info-icon manager"></i>
                    <span class="info-label">Менеджер (из обзвона):</span>
                    <span class="info-value">${agencyData.client_manager || '-'}</span>
                </div>
                 <div class="info-row">
                    <i class="fas fa-headset info-icon operator"></i>
                    <span class="info-label">Оператор (звонка):</span>
                    <span class="info-value">${agencyData.call_operator_name || '-'}</span>
                </div>
                 <div class="info-row">
                    <i class="far fa-calendar-alt info-icon datetime"></i>
                    <span class="info-label">Дата и время звонка:</span>
                    <span class="info-value">${agencyData.call_datetime || '-'}</span>
                </div>`;

        html += '</div>'; // Закрываем .agency-info-card
        return html;
    }
    // <<< КОНЕЦ ИЗМЕНЕНИЯ >>>

    // Функция для отображения информации об агентстве (из Журнала звонков)
    function showAgencyInfo(ppId) {
        const modal = document.getElementById('agencyInfoModal');
        const contentDiv = document.getElementById('agencyInfoContent');
        const titleSpan = modal.querySelector('.finesse-modal-title');

        // Обновляем заголовок модального окна, используя иконку
        titleSpan.innerHTML = '<i class="fas fa-building header-icon"></i> Информация об агентстве (из Журнала)';

        contentDiv.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Загрузка данных...</div>';
        // Плавно показываем модальное окно
        modal.style.display = 'flex'; // Используем flex для центрирования
        setTimeout(() => {
             modal.style.opacity = '1';
        }, 10); // Небольшая задержка для срабатывания transition

        fetch(`/api/call-agency-data/${ppId}`)
            .then(response => {
                if (!response.ok) {
                    // Попытаемся прочитать текст ошибки, если это не JSON
                    return response.text().then(text => {
                        throw new Error(`Ошибка сервера: ${response.status} - ${text || 'Без дополнительной информации'}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.agency_data) {
                    // Используем новую функцию для форматирования
                    contentDiv.innerHTML = formatAgencyData(data.agency_data);
                    // Обновляем заголовок модального окна с названием агентства, если оно есть
                    const agencyName = data.agency_data[0]?.agency_name_ru;
                    if (agencyName) {
                         titleSpan.innerHTML = `<i class="fas fa-building header-icon"></i> ${agencyName}`;
                    }
                } else {
                    contentDiv.innerHTML = `<div class="error-message">${data.error || 'Информация не найдена'}</div>`;
                    titleSpan.innerHTML = '<i class="fas fa-exclamation-triangle header-icon"></i> Ошибка загрузки';
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке информации об агентстве:', error);
                contentDiv.innerHTML = `<div class="error-message">Ошибка: ${error.message}</div>`;
                titleSpan.innerHTML = '<i class="fas fa-exclamation-triangle header-icon"></i> Ошибка загрузки';
            });
    }

    // --- Функции для Справочника Агентств ---
    const agencySearchInput = document.getElementById('agencySearchInput');
    const agenciesTableBody = document.getElementById('agenciesTableBody');
    const agenciesCountDisplay = document.getElementById('agenciesCountDisplay').querySelector('span');
    const agenciesStatusBar = document.getElementById('agenciesStatusBar');
    const clearAgencySearchBtn = document.getElementById('clearAgencySearch');
    const refreshAgenciesBtn = document.getElementById('refreshAgenciesBtn');
    const agencyDirectoryInfoSpan = document.getElementById('agencyDirectoryInfoSpan');
    let agencyDataCache = []; // Кэш для данных справочника
    let isCacheHoldingFullList = false; // <--- НОВЫЙ ФЛАГ
    let fetchAgenciesController = null; // Для отмены предыдущего запроса

    function showLoadingAgencies(message = "Загрузка справочника агентств...") {
        agenciesStatusBar.style.display = 'block';
        agenciesStatusBar.innerHTML = `<i class="fas fa-spinner fa-spin status-icon"></i><span class="status-message">${message}</span>`;
        agenciesTableBody.innerHTML = ''; // Очищаем таблицу на время загрузки
        agenciesCountDisplay.textContent = 'Найдено: 0';
    }

    function hideLoadingAgencies() {
        agenciesStatusBar.style.display = 'none';
    }

    function renderAgenciesTable(agencies) {
        agenciesTableBody.innerHTML = ''; // Очищаем перед рендерингом
        if (agencies.length === 0) {
            const noResultsRow = `<tr><td colspan="7" style="text-align:center; padding: 20px;"><i class="fas fa-search-minus" style="font-size: 1.5em; margin-bottom: 10px;"></i><p>Агентства не найдены по вашему запросу.</p></td></tr>`;
            agenciesTableBody.innerHTML = noResultsRow;
            agenciesCountDisplay.textContent = 'Найдено: 0';
            return;
        }

        agencies.forEach(agency => {
            const row = document.createElement('tr');

            // Ячейка для Названия (RU + EN)
            const nameCell = row.insertCell();
            let nameHtml = '';
            if (agency.NAME_RU) {
                nameHtml += `<strong>${agency.NAME_RU}</strong>`;
            } else {
                nameHtml += '<strong>-</strong>'; // Если нет русского названия
            }
            if (agency.NAME_EN) {
                nameHtml += `<br><small style="color: #555;">${agency.NAME_EN}</small>`;
            }
            nameCell.innerHTML = nameHtml; // Убрана иконка fas fa-building

            // Ячейка для Адреса
            row.insertCell().textContent = agency.ADDRESS || '-';
            // Ячейка для Города
            row.insertCell().textContent = agency.CITY_NAME || '-';
            // Ячейка для Метро
            row.insertCell().textContent = agency.METRO_STATION_NAME || '-';

            // Ячейка для Телефонов
            const phonesCell = row.insertCell();
            let phonesDisplay = '-';
            // Эндпоинт /api/agencies сейчас возвращает telephone_1_number
            // Поэтому TELEPHONES_DETAILED не будет доступно здесь без доработки Python кода
            if (agency.telephone_1_number) {
                phonesDisplay = agency.telephone_1_number;
            }
            phonesCell.innerHTML = phonesDisplay;

            // Ячейка для Района
            row.insertCell().textContent = agency.DISTRICT_NAME || '-';

            // Ячейка для Действий
            const actionsCell = row.insertCell();
            actionsCell.innerHTML = `
                <button class="action-btn agency-detail-btn" title="Подробная информация об агентстве" onclick="showAgencyDetails(${agency.ID_TR})" style="background-color: #e0f2ff; color: #004085; border-color: #b8daff;">
                    <i class="fas fa-eye"></i>Подробнее...
                </button>
            `;

            agenciesTableBody.appendChild(row);
        });
        agenciesCountDisplay.textContent = `Найдено: ${agencies.length}`;
    }

    function filterAgencies() {
        const query = agencySearchInput.value.toLowerCase().trim();
        clearAgencySearchBtn.style.display = query ? 'inline' : 'none';

        if (!query) {
            renderAgenciesTable(agencyDataCache); // Показываем все из кэша, если запрос пуст
            return;
        }

        const filteredAgencies = agencyDataCache.filter(agency => {
            const queryLower = query.toLowerCase(); // Кэшируем значение в нижнем регистре
            return (agency.NAME_RU && agency.NAME_RU.toLowerCase().includes(queryLower)) ||
                   (agency.NAME_EN && agency.NAME_EN.toLowerCase().includes(queryLower)) || // Добавлен поиск по NAME_EN
                   (agency.ADDRESS && agency.ADDRESS.toLowerCase().includes(queryLower)) ||
                   (agency.CITY_NAME && agency.CITY_NAME.toLowerCase().includes(queryLower)) ||
                   (agency.METRO_STATION_NAME && agency.METRO_STATION_NAME.toLowerCase().includes(queryLower)) ||
                   (agency.DISTRICT_NAME && agency.DISTRICT_NAME.toLowerCase().includes(queryLower)) ||
                   (agency.ALL_TELEPHONES_CONCAT && agency.ALL_TELEPHONES_CONCAT.toLowerCase().includes(queryLower)); // Поиск по всем конкатенированным телефонам
        });
        renderAgenciesTable(filteredAgencies);
    }

    function fetchAgencies(forceRefresh = false, searchTerm = '') {
        console.log(`[fetchAgencies] Called. forceRefresh: ${forceRefresh}, searchTerm: '${searchTerm}', isCacheHoldingFullList: ${isCacheHoldingFullList}`);
        if (fetchAgenciesController) {
            fetchAgenciesController.abort();
        }
        fetchAgenciesController = new AbortController();
        const signal = fetchAgenciesController.signal;

        // Используем кэш только если он содержит ПОЛНЫЙ список, не требуется принудительное обновление и нет поискового запроса
        if (isCacheHoldingFullList && !forceRefresh && !searchTerm) {
            console.log('[fetchAgencies] Using FULL LIST cache. Cache size:', agencyDataCache.length);
            renderAgenciesTable(agencyDataCache);
            const cachedTimestamp = localStorage.getItem('agencyCacheTimestamp');
            agencyDirectoryInfoSpan.textContent = cachedTimestamp ? `Данные от ${cachedTimestamp}` : 'Данные из кэша (полный список)';
            return;
        }

        showLoadingAgencies(searchTerm ? "Поиск агентств..." : (forceRefresh ? "Принудительное обновление..." : "Загрузка справочника..."));

        let apiUrl = '/api/agencies';
        if (searchTerm) {
            apiUrl += `?search=${encodeURIComponent(searchTerm)}`;
        }

        fetch(apiUrl, { signal })
            .then(response => {
                console.log(`[fetchAgencies] API response status for ${apiUrl}: ${response.status}`);
                if (!response.ok) throw new Error(`HTTP error ${response.status}`);
                return response.json();
            })
            .then(data => {
                fetchAgenciesController = null;
                hideLoadingAgencies();
                if (data.success && data.agencies) {
                    console.log('[fetchAgencies] Data received from API. Count:', data.agencies.length);
                    agencyDataCache = data.agencies;
                    if (!searchTerm) { // Это был запрос на полный список
                        isCacheHoldingFullList = true;
                        const timestamp = new Date().toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
                        localStorage.setItem('agencyCacheTimestamp', timestamp);
                        agencyDirectoryInfoSpan.textContent = `Данные обновлены: ${timestamp}`;
                    } else { // Это был запрос с фильтром
                        isCacheHoldingFullList = false;
                        agencyDirectoryInfoSpan.textContent = 'Результаты поиска';
                    }
                    renderAgenciesTable(agencyDataCache);
                } else {
                    agenciesTableBody.innerHTML = `<tr><td colspan="7" class="error-message">${data.error || 'Не удалось загрузить справочник'}</td></tr>`;
                    agencyDirectoryInfoSpan.textContent = 'Ошибка загрузки';
                    isCacheHoldingFullList = false; // Сбрасываем флаг при ошибке данных
                }
            })
            .catch(error => {
                fetchAgenciesController = null;
                if (error.name === 'AbortError') {
                    console.log('Fetch agencies aborted');
                    return;
                }
                hideLoadingAgencies();
                console.error('Ошибка при загрузке справочника агентств:', error);
                agenciesTableBody.innerHTML = `<tr><td colspan="7" class="error-message">Ошибка: ${error.message}</td></tr>`;
                agencyDirectoryInfoSpan.textContent = 'Ошибка загрузки';
                isCacheHoldingFullList = false; // Сбрасываем флаг при ошибке сети/обработки
            });
    }

    function showAgencyDetails(agencyId) {
        const modal = document.getElementById('agencyDetailModal');
        const contentDiv = document.getElementById('agencyDetailContent');
        const titleSpan = modal.querySelector('.finesse-modal-title');

        // Reset title and show loading spinner
        titleSpan.innerHTML = '<i class="fas fa-building header-icon"></i> Информация об агентстве';
        contentDiv.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Загрузка детальной информации...</div>';
        modal.style.display = 'flex';
        setTimeout(() => { modal.style.opacity = '1'; }, 10); // For smooth appearance

        fetch(`/api/agency-details/${agencyId}`)
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.error || `Ошибка HTTP: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success && data.agency_details) {
                    contentDiv.innerHTML = formatDetailedAgencyData(data.agency_details);
                    // Используем data.agency_details.name (или NAME_RU если сервер его так отдает после всех преобразований)
                    // По текущей структуре get_agency_details отдает 'name' для русского названия
                    const agencyName = data.agency_details.name || data.agency_details.NAME_RU;
                    if (agencyName) {
                        titleSpan.innerHTML = `<i class="fas fa-building header-icon"></i> ${agencyName}`;
                    } else {
                        titleSpan.innerHTML = '<i class="fas fa-building header-icon"></i> Детали агентства';
                    }
                } else {
                    contentDiv.innerHTML = `<div class="error-message">${data.error || 'Не удалось загрузить детали агентства.'}</div>`;
                    titleSpan.innerHTML = '<i class="fas fa-exclamation-triangle header-icon"></i> Ошибка данных';
                }
            })
            .catch(error => {
                console.error('Ошибка при загрузке деталей агентства:', error);
                contentDiv.innerHTML = `<div class="error-message">Ошибка при загрузке: ${error.message}</div>`;
                titleSpan.innerHTML = '<i class="fas fa-exclamation-triangle header-icon"></i> Ошибка загрузки';
            });
    }

    function formatDetailedAgencyData(agency) {
        let html = '<div class="agency-info-card" style="text-align: left;">';
        const displayValue = (value, defaultValue = '-') => value !== null && value !== undefined && value !== '' ? value : defaultValue;
        const displayBool = (value) => value ? 'Да' : 'Нет';

        html += `<div class="info-row"><i class="fas fa-hashtag info-icon hashtag"></i><span class="info-label">ID (ID_TR):</span><span class="info-value">${displayValue(agency.id)}</span></div>`; // Было agency.ID_TR
        html += `<div class="info-row"><i class="fas fa-building info-icon agency"></i><span class="info-label">Название (RU):</span><span class="info-value"><strong>${displayValue(agency.name)}</strong></span></div>`; // Было agency.NAME_RU
        html += `<div class="info-row"><i class="fas fa-language info-icon globe"></i><span class="info-label">Название (EN):</span><span class="info-value"><strong>${displayValue(agency.english_name)}</strong></span></div>`; // Было agency.NAME_EN

        const address = displayValue(agency.adres); // Было agency.ADDRESS
        if (address !== '-') {
             html += `<div class="info-row">
                        <i class="fas fa-map-marker-alt info-icon map-marker-alt"></i>
                        <span class="info-label">Адрес:</span>
                        <span class="info-value">
                            <a href="javascript:void(0)"
                               class="map-link"
                               onclick="openInYandexMaps('${address.replace(/'/g, "\\'")}')">
                                ${address}
                                <i class="fas fa-external-link-alt map-link-icon"></i>
                            </a>
                        </span>
                     </div>`;
        } else {
            html += `<div class="info-row"><i class="fas fa-map-marker-alt info-icon map-marker-alt"></i><span class="info-label">Адрес:</span><span class="info-value">-</span></div>`;
        }

        html += `<div class="info-row"><i class="fas fa-city info-icon city"></i><span class="info-label">Город:</span><span class="info-value">${displayValue(agency.city_name)}</span></div>`; // Было agency.CITY_NAME
        html += `<div class="info-row"><i class="fas fa-subway info-icon metro"></i><span class="info-label">Метро:</span><span class="info-value">${displayValue(agency.metro_name)}</span></div>`; // Было agency.METRO_STATION_NAME
        html += `<div class="info-row"><i class="fas fa-map-signs info-icon map-signs"></i><span class="info-label">Район города:</span><span class="info-value">${displayValue(agency.district_name)}</span></div>`; // Было agency.DISTRICT_NAME
        html += `<div class="info-row"><i class="fas fa-map info-icon map"></i><span class="info-label">Зона:</span><span class="info-value">${displayValue(agency.area_name)}</span></div>`; // Было agency.AREA_NAME
        html += `<div class="info-row"><i class="fas fa-globe-europe info-icon map"></i><span class="info-label">Регион:</span><span class="info-value">${displayValue(agency.region_name_from_db || agency.region_name)}</span></div>`;

        html += `<div class="info-row"><i class="fas fa-clock info-icon clock"></i><span class="info-label">Часовой пояс (смещение):</span><span class="info-value">${displayValue(agency.time_zone)}</span></div>`; // Было agency.TIME_ZONE

        html += `<div class="info-row"><i class="fas fa-user-check info-icon user-check"></i><span class="info-label">Англ. туристы:</span><span class="info-value">${displayBool(agency.english)}</span></div>`; // Было agency.ENGLISH
        html += `<div class="info-row"><i class="fas fa-ticket-alt info-icon ticket-alt"></i><span class="info-label">Продажа билетов:</span><span class="info-value">${displayBool(agency.tickets)}</span></div>`; // Было agency.TICKETS
        html += `<div class="info-row"><i class="fas fa-ban info-icon ban"></i><span class="info-label">"Станция не задана":</span><span class="info-value">${displayBool(agency.station_not_set)}</span></div>`; // Было agency.STATION_NOT_SET
        html += `<div class="info-row"><i class="fas fa-random info-icon random"></i><span class="info-label">"Перекл. на Мск":</span><span class="info-value">${displayBool(agency.switch_msk_agency)}</span></div>`; // Было agency.SWITCH_MSK_AGENCY
        html += `<div class="info-row"><i class="fas fa-credit-card info-icon credit-card"></i><span class="info-label">Прием банк. карт:</span><span class="info-value">${displayBool(agency.bank_card)}</span></div>`; // Было agency.BANK_CARD
        html += `<div class="info-row"><i class="fas fa-plane-departure info-icon plane-departure"></i><span class="info-label">Туры в Стамбул:</span><span class="info-value">${displayBool(agency.stambul)}</span></div>`; // Было agency.STAMBUL
        html += `<div class="info-row"><i class="fas fa-skiing info-icon skiing"></i><span class="info-label">Туры в Австрию:</span><span class="info-value">${displayBool(agency.austria)}</span></div>`; // Было agency.AUSTRIA

        const commentText = displayValue(agency.comment); // Уже исправлено
        const trimmedComment = commentText !== '-' ? commentText.trim() : '-';
        if (trimmedComment && trimmedComment !== '-') {
             html += `<div class="info-row">
                        <i class="fas fa-directions info-icon directions"></i>
                        <span class="info-label">Как пройти:</span>
                        <span class="info-value">
                            <div style="max-height: 150px; overflow-y: auto; white-space: pre-line; word-break: break-word; padding-right: 5px;">
                                ${trimmedComment}
                            </div>
                        </span>
                     </div>`;
        } else {
             html += `<div class="info-row"><i class="fas fa-directions info-icon"></i><span class="info-label">Как пройти:</span><span class="info-value">-</span></div>`;
        }


        if (agency.telephones && agency.telephones.length > 0) { // Исправлено с agency.TELEPHONES_DETAILED
            let phonesHtml = agency.telephones.map(tel => {
                let phoneEntry = `<i class="fas fa-phone-alt info-icon" style="margin-right: 5px; font-size: 0.9em;"></i>${displayValue(tel.number)}`;
                if (tel.comment && tel.comment !== "NULL") {
                    phoneEntry += ` <small style="color: #555;">(${displayValue(tel.comment)})</small>`;
                }
                // Добавляем отображение режима работы для телефона
                if (tel.work_schedule) {
                    phoneEntry += '<div style="font-size: 0.8em; margin-left: 25px; color: #666;">';
                    const schedule = tel.work_schedule;
                    // Простая группировка для Пн-Пт, если время совпадает
                    let weekdaysSchedule = '';
                    if (schedule.monday && schedule.monday === schedule.tuesday && schedule.monday === schedule.wednesday && schedule.monday === schedule.thursday && schedule.monday === schedule.friday) {
                        weekdaysSchedule = `Пн-Пт: ${schedule.monday}`;
                        phoneEntry += `${weekdaysSchedule}<br>`;
                    } else {
                        if(schedule.monday) phoneEntry += `Пн: ${schedule.monday}<br>`;
                        if(schedule.tuesday) phoneEntry += `Вт: ${schedule.tuesday}<br>`;
                        if(schedule.wednesday) phoneEntry += `Ср: ${schedule.wednesday}<br>`;
                        if(schedule.thursday) phoneEntry += `Чт: ${schedule.thursday}<br>`;
                        if(schedule.friday) phoneEntry += `Пт: ${schedule.friday}<br>`;
                    }
                    if (schedule.saturday) {
                        phoneEntry += `Сб: ${schedule.saturday}<br>`;
                    }
                    if (schedule.sunday) {
                        phoneEntry += `Вс: ${schedule.sunday}`;
                    }
                    // Убираем последний <br> если он есть и за ним ничего нет
                    if (phoneEntry.endsWith('<br>')) {
                        phoneEntry = phoneEntry.slice(0, -4);
                    }
                    phoneEntry += '</div>';
                }
                return phoneEntry;
            }).join('<br style="margin-bottom: 8px; margin-top: 3px;">');
            html += `<div class="info-row"><i class="fas fa-phone-square-alt info-icon operator"></i><span class="info-label">Телефоны:</span><span class="info-value">${phonesHtml}</span></div>`;
        } else {
            html += `<div class="info-row"><i class="fas fa-phone-slash info-icon"></i><span class="info-label">Телефоны:</span><span class="info-value">-</span></div>`;
        }

        html += '</div>'; // Закрываем .agency-info-card
        return html;
    }


    function closeAgencyDetailModal() {
        const modal = document.getElementById('agencyDetailModal');
        modal.style.opacity = '0';
        setTimeout(() => {
            modal.style.display = 'none';
            modal.style.opacity = '';
        }, 200);
    }


    // Инициализация справочника при загрузке DOM
    document.addEventListener('DOMContentLoaded', function() {
        // Загрузка справочника (использует кэш или фетчит)
        fetchAgencies(); // Первоначальная загрузка без поискового запроса

        if (agencySearchInput) {
            agencySearchInput.addEventListener('input', function() {
                const query = this.value.trim();
                console.log(`[Input Event] Query: '${query}'`); // DEBUG
                clearAgencySearchBtn.style.display = query ? 'inline' : 'none';
                // Вызываем fetchAgencies с поисковым запросом (даже если он пустой,
                // fetchAgencies теперь корректно обработает это и загрузит полный список или из кэша)
                fetchAgencies(false, query); // Вызываем fetchAgencies с поисковым запросом
            });
        }
        if (clearAgencySearchBtn) {
            clearAgencySearchBtn.addEventListener('click', () => {
                agencySearchInput.value = '';
                clearAgencySearchBtn.style.display = 'none';
                fetchAgencies(false, ''); // Изменено с filterAgencies()
            });
        }
        if (refreshAgenciesBtn) {
            refreshAgenciesBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const icon = refreshAgenciesBtn.querySelector('i');
                if (icon) icon.classList.add('fa-spin');
                fetchAgencies(true); // Принудительное обновление
                setTimeout(() => {
                    if (icon) icon.classList.remove('fa-spin');
                }, 1500); // Даем время на загрузку
            });
        }
    });
     // --- Конец функций для Справочника Агентств ---

    // --- Начало Аналитики звонков ---
    function renderDailyAnalyticsReport(calls, dateString) {
        console.log('[renderDailyAnalyticsReport] Called with calls:', calls, 'and date:', dateString);
        callsDataForAnalytics = calls; // Сохраняем данные глобально для этой функции

        const generalStatsContainer = document.getElementById('dailySummaryStats');
        const operatorDetailsContainer = document.getElementById('operatorDetailsTableContainer');
        const callTypeAnalysisContainer = document.getElementById('callTypeAnalysisTableContainer');

        if (!generalStatsContainer || !operatorDetailsContainer || !callTypeAnalysisContainer) {
            console.error('Один или несколько контейнеров для аналитики не найдены!');
            return;
        }

        // Обновляем дату в заголовке панели аналитики
        const analyticsReportDateDisplay = document.getElementById('analyticsReportDate');
        if (analyticsReportDateDisplay) {
            const dateObj = new Date(dateString + 'T00:00:00'); // Гарантируем правильный парсинг даты
            const options = { day: '2-digit', month: '2-digit', year: 'numeric' };
            analyticsReportDateDisplay.textContent = dateObj.toLocaleDateString('ru-RU', options);
        }


        if (!calls || calls.length === 0) {
            const noDataMessage = `<p style="text-align:center; color:#6c757d;"><i class="fas fa-info-circle"></i> Нет данных для анализа за выбранный день.</p>`;
            generalStatsContainer.innerHTML = noDataMessage;
            operatorDetailsContainer.innerHTML = noDataMessage;
            callTypeAnalysisContainer.innerHTML = noDataMessage;
            return;
        }

        // 1. Общая статистика
        renderGeneralStats(calls, generalStatsContainer);

        // 2. Детализация по операторам
        renderOperatorDetails(calls, operatorDetailsContainer);

        // 3. Анализ результативности по типам звонков
        renderCallTypeAnalysis(calls, callTypeAnalysisContainer);
    }

    function clearAnalyticsReport(dateString) {
        const generalStatsContainer = document.getElementById('dailySummaryStats');
        const operatorDetailsContainer = document.getElementById('operatorDetailsTableContainer');
        const callTypeAnalysisContainer = document.getElementById('callTypeAnalysisTableContainer');
        const analyticsReportDateDisplay = document.getElementById('analyticsReportDate');

        const dateObj = new Date(dateString + 'T00:00:00');
        const formattedDate = dateObj.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
        const noDataMessage = `<p style="text-align:center; color:#6c757d;"><i class="fas fa-info-circle"></i> Нет данных для анализа за ${formattedDate}.</p>`;

        if (generalStatsContainer) generalStatsContainer.innerHTML = noDataMessage;
        if (operatorDetailsContainer) operatorDetailsContainer.innerHTML = noDataMessage;
        if (callTypeAnalysisContainer) callTypeAnalysisContainer.innerHTML = noDataMessage;
        if (analyticsReportDateDisplay) analyticsReportDateDisplay.textContent = formattedDate;
    }

    function showErrorInAnalyticsReport(errorMessage) {
        const generalStatsContainer = document.getElementById('dailySummaryStats');
        const operatorDetailsContainer = document.getElementById('operatorDetailsTableContainer');
        const callTypeAnalysisContainer = document.getElementById('callTypeAnalysisTableContainer');
        const analyticsReportDateDisplay = document.getElementById('analyticsReportDate');

        const errorHtml = `<p style="text-align:center; color:#dc3545;"><i class="fas fa-exclamation-triangle"></i> Ошибка загрузки аналитики: ${errorMessage}</p>`;

        if (generalStatsContainer) generalStatsContainer.innerHTML = errorHtml;
        if (operatorDetailsContainer) operatorDetailsContainer.innerHTML = errorHtml;
        if (callTypeAnalysisContainer) callTypeAnalysisContainer.innerHTML = errorHtml;
        if (analyticsReportDateDisplay) analyticsReportDateDisplay.textContent = 'Ошибка!';
    }


    function renderGeneralStats(calls, container) {
        const totalCalls = calls.length;
        const successfulCalls = calls.filter(call => call.result === 1).length; // Успешный результат = 1
        const failedCalls = calls.filter(call => call.result === 0 || call.result === 4 || call.result === 5 || call.result === 6).length; // Неуспешный результат (добавим разные коды)
        const droppedCalls = calls.filter(call => call.result === 2).length; // Клиент положил трубку = 2
        const noInternetCalls = calls.filter(call => call.result === 3).length; // Нет интернета = 3

        let html = '<ul>';
        html += `<li>Общее количество звонков: <strong>${totalCalls}</strong></li>`;
        html += `<li>Успешных звонков (дозвон): <strong>${successfulCalls}</strong> (${((successfulCalls / totalCalls) * 100 || 0).toFixed(1)}%)</li>`;
        html += `<li>Неуспешных звонков (недозвон/занято/тишина): <strong>${failedCalls}</strong> (${((failedCalls / totalCalls) * 100 || 0).toFixed(1)}%)</li>`;
        html += `<li>Клиент положил трубку: <strong>${droppedCalls}</strong> (${((droppedCalls / totalCalls) * 100 || 0).toFixed(1)}%)</li>`;
        if (noInternetCalls > 0) { // Показываем только если были такие звонки
             html += `<li>"Нет интернета": <strong>${noInternetCalls}</strong> (${((noInternetCalls / totalCalls) * 100 || 0).toFixed(1)}%)</li>`;
        }
        html += '</ul>';
        container.innerHTML = html;
    }

    function renderOperatorDetails(calls, container) {
        const operatorStats = {};
        calls.forEach(call => {
            const operator = call.operator || 'Неизвестный оператор';
            if (!operatorStats[operator]) {
                operatorStats[operator] = { total: 0, successful: 0, failed: 0, dropped: 0, noInternet: 0 };
            }
            operatorStats[operator].total++;
            if (call.result === 1) operatorStats[operator].successful++;
            else if (call.result === 0 || call.result === 4 || call.result === 5 || call.result === 6) operatorStats[operator].failed++;
            else if (call.result === 2) operatorStats[operator].dropped++;
            else if (call.result === 3) operatorStats[operator].noInternet++;
        });

        let tableHtml = '<table class="analytics-table">';
        tableHtml += '<thead><tr><th>Оператор</th><th>Всего звонков</th><th>Успешных</th><th>Неуспешных</th><th>Сброшено клиентом</th><th>"Нет интернета"</th><th>% Успеха</th></tr></thead><tbody>';

        for (const operator in operatorStats) {
            const stats = operatorStats[operator];
            const successRate = ((stats.successful / stats.total) * 100 || 0).toFixed(1);
            tableHtml += `<tr>
                <td>${operator}</td>
                <td>${stats.total}</td>
                <td>${stats.successful}</td>
                <td>${stats.failed}</td>
                <td>${stats.dropped}</td>
                <td>${stats.noInternet > 0 ? stats.noInternet : '-'}</td>
                <td>
                    <div class="percentage-bar-container" title="${successRate}%">
                        <div class="percentage-bar success" style="width: ${successRate}%;"></div>
                    </div>
                    <span class="percentage-text">${successRate}%</span>
                </td>
            </tr>`;
        }
        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    }

    function renderCallTypeAnalysis(calls, container) {
        const callTypeStats = {};
        calls.forEach(call => {
            const type = call.call_type_text || 'Неизвестный тип';
            if (!callTypeStats[type]) {
                callTypeStats[type] = { total: 0, successful: 0, failed: 0, dropped: 0, noInternet: 0 };
            }
            callTypeStats[type].total++;
            if (call.result === 1) callTypeStats[type].successful++;
            else if (call.result === 0 || call.result === 4 || call.result === 5 || call.result === 6) callTypeStats[type].failed++;
            else if (call.result === 2) callTypeStats[type].dropped++;
            else if (call.result === 3) callTypeStats[type].noInternet++;
        });

        let tableHtml = '<table class="analytics-table">';
        tableHtml += '<thead><tr><th>Тип звонка</th><th>Всего</th><th>Успешных</th><th>Неуспешных</th><th>Сброшено</th><th>"Нет интернета"</th><th>% Успеха</th></tr></thead><tbody>';

        for (const type in callTypeStats) {
            const stats = callTypeStats[type];
            const successRate = ((stats.successful / stats.total) * 100 || 0).toFixed(1);
             // Определяем класс для прогресс-бара в зависимости от успешности
            let barClass = 'success'; // Зеленый по умолчанию
            if (successRate < 30) barClass = 'failed'; // Красный, если < 30%
            else if (successRate < 60) barClass = 'dropped'; // Желтый, если < 60%

            tableHtml += `<tr>
                <td>${type}</td>
                <td>${stats.total}</td>
                <td>${stats.successful}</td>
                <td>${stats.failed}</td>
                <td>${stats.dropped}</td>
                <td>${stats.noInternet > 0 ? stats.noInternet : '-'}</td>
                <td>
                     <div class="percentage-bar-container" title="${successRate}%">
                        <div class="percentage-bar ${barClass}" style="width: ${successRate}%;"></div>
                    </div>
                    <span class="percentage-text">${successRate}%</span>
                </td>
            </tr>`;
        }
        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    }
    // --- Конец Аналитики звонков ---

    // --- Начало Динамики звонков по месяцам (Chart.js) ---
    let monthlyCallsChartInstance = null; // Для хранения экземпляра диаграммы

    // Вспомогательная функция для получения названия месяца
    function getMonthName(monthNumber, type = 'short') {
        const date = new Date();
        date.setMonth(monthNumber - 1); // месяцы в JS 0-индексированные
        const locale = 'ru-RU';
        if (type === 'full') {
            return date.toLocaleString(locale, { month: 'long' });
        }
        return date.toLocaleString(locale, { month: 'short' });
    }

    function renderMonthlyCallsChart(data) {
        const chartContainer = document.getElementById('monthlyCallsChartContainer');
        const chartLoadingStatus = document.getElementById('chartLoadingStatus');
        const chartStatsSummaryContainer = document.getElementById('chartStatsSummary');
        const yearlyMonthlyStatsTableContainer = document.getElementById('yearlyMonthlyStatsTable');

        if (!chartContainer || !chartLoadingStatus || !chartStatsSummaryContainer || !yearlyMonthlyStatsTableContainer) {
            console.error("Элементы для диаграммы или статистики по месяцам не найдены.");
            if(chartLoadingStatus) chartLoadingStatus.innerHTML = '<p style="color:red;">Ошибка: Не найдены все необходимые HTML элементы для диаграммы.</p>';
            return;
        }

        if (!data || data.length === 0) {
            chartLoadingStatus.innerHTML = '<p style="color:#6c757d;"><i class="fas fa-info-circle"></i> Нет данных для построения диаграммы.</p>';
            chartContainer.style.display = 'none';
            chartStatsSummaryContainer.innerHTML = '';
            yearlyMonthlyStatsTableContainer.innerHTML = '';
            return;
        }

        chartContainer.style.display = 'block';
        chartLoadingStatus.style.display = 'none';

        // Используем getMonthName и item.count
        const labels = data.map(item => `${getMonthName(item.month, 'short')} ${item.year}`);
        const totalCalls = data.map(item => item.count); // Используем item.count

        const canvas = document.getElementById('monthlyCallsChart');
        // Рассчитываем минимальную ширину для канваса, чтобы столбцы не были слишком узкими
        const minBarWidth = 45; // Увеличено с 30 до 45
        const calculatedWidth = labels.length * minBarWidth;
        canvas.style.width = `${calculatedWidth}px`;
        // Высота задается через родительский контейнер (40vh), Chart.js подстроится
        // canvas.style.height = '300px'; // или фиксированная высота если vh не подходит

        const ctx = canvas.getContext('2d');

        if (monthlyCallsChartInstance) {
            monthlyCallsChartInstance.destroy();
        }

        monthlyCallsChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Всего звонков',
                    data: totalCalls,
                    backgroundColor: 'rgba(144, 238, 144, 0.6)', // Мягкий светло-зеленый
                    borderColor: 'rgba(34, 139, 34, 0.8)', // Темно-зеленый для контура
                    borderWidth: 1,
                    borderRadius: 5, // Скругление углов
                    borderSkipped: false // Применяем скругление ко всем углам
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Количество звонков'
                        }
                    },
                    x: {
                         title: {
                            display: true,
                            text: 'Месяц и Год'
                        }
                        // Убираем объект ticks, чтобы Chart.js использовал autoSkip по умолчанию
                        // ticks: {
                        //     autoSkip: false,
                        //     maxRotation: 60,
                        //     minRotation: 60,
                        // }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Динамика общего количества звонков по месяцам' // Обновлен заголовок
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                    }
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const chartElement = elements[0];
                        const index = chartElement.index;
                        const year = data[index].year;
                        const month = data[index].month;
                        console.log(`Клик по: ${getMonthName(data[index].month, 'short')} ${year} (Месяц: ${month})`);
                    }
                }
            }
        });

        // Прокрутка к текущему году
        const currentYear = new Date().getFullYear();
        let currentYearIndex = -1;
        for(let i = 0; i < data.length; i++) {
            if(data[i].year === currentYear) {
                currentYearIndex = i;
                break;
            }
        }
        if (currentYearIndex !== -1) {
            // Примерная позиция для прокрутки. Точное позиционирование может потребовать chart.scales.x.getPixelForValue
            // Это более простой подход, который должен работать для большинства случаев
            const scrollPosition = currentYearIndex * minBarWidth - (chartContainer.clientWidth / 2) + (minBarWidth / 2);
            chartContainer.scrollLeft = Math.max(0, scrollPosition);
        }

        renderChartStatsSummary(data, chartStatsSummaryContainer);
        renderYearlyMonthlyTable(data, yearlyMonthlyStatsTableContainer);
    }

    function renderChartStatsSummary(data, container) {
        if (!data || data.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:#6c757d;"><i class="fas fa-info-circle"></i> Нет данных для сводной статистики.</p>';
            return;
        }

        let minYear = Infinity, maxYear = -Infinity;
        let minMonthInMinYear = 12, maxMonthInMaxYear = 1;
        let totalCalls = 0;
        let peakCalls = -1, peakYear = 0, peakMonth = 0;
        let minCalls = Infinity, minYearA = 0, minMonthA = 0;
        const callsByYearMonth = {}; // Для подсчета за последние 12 мес

        data.forEach(item => {
            const year = parseInt(item.year, 10);
            const month = parseInt(item.month, 10);
            const count = parseInt(item.count, 10);

            totalCalls += count;

            if (year < minYear) {
                minYear = year;
                minMonthInMinYear = month;
            } else if (year === minYear && month < minMonthInMinYear) {
                minMonthInMinYear = month;
            }

            if (year > maxYear) {
                maxYear = year;
                maxMonthInMaxYear = month;
            } else if (year === maxYear && month > maxMonthInMaxYear) {
                maxMonthInMaxYear = month;
            }

            if (count > peakCalls) {
                peakCalls = count;
                peakYear = year;
                peakMonth = month;
            }
            // Для минимальной активности, учитываем только если были звонки
            if (count > 0 && count < minCalls) {
                minCalls = count;
                minYearA = year;
                minMonthA = month;
            }

            if (!callsByYearMonth[year]) callsByYearMonth[year] = {};
            callsByYearMonth[year][month] = count;
        });

        const numberOfMonthsWithData = data.length;
        const averageCallsPerMonth = numberOfMonthsWithData > 0 ? (totalCalls / numberOfMonthsWithData).toFixed(0) : 0;

        // Звонки за последние 12 месяцев
        let callsLast12Months = 0;
        const currentDate = new Date();
        let currentScanYear = currentDate.getFullYear();
        let currentScanMonth = currentDate.getMonth() + 1; // JS month is 0-indexed

        for (let i = 0; i < 12; i++) {
            if (callsByYearMonth[currentScanYear] && callsByYearMonth[currentScanYear][currentScanMonth]) {
                callsLast12Months += callsByYearMonth[currentScanYear][currentScanMonth];
            }
            currentScanMonth--;
            if (currentScanMonth === 0) {
                currentScanMonth = 12;
                currentScanYear--;
            }
        }

        const analysisPeriodStart = `${getMonthName(minMonthInMinYear, 'short')} ${minYear} г.`;
        const analysisPeriodEnd = `${getMonthName(maxMonthInMaxYear, 'short')} ${maxYear} г.`;
        const peakActivity = `${getMonthName(peakMonth, 'full')} ${peakYear} г. (${peakCalls} звонков)`;
        const minActivity = minCalls !== Infinity ? `${getMonthName(minMonthA, 'full')} ${minYearA} г. (${minCalls} звонков)` : '-';

        let html = `<ul style="list-style-type: none; padding-left: 0; font-size: 0.9em;">
                        <li><strong>Период анализа:</strong> ${analysisPeriodStart} - ${analysisPeriodEnd}</li>
                        <li><strong>Общее количество звонков:</strong> ${totalCalls.toLocaleString('ru-RU')}</li>
                        <li><strong>Среднее количество звонков в месяц:</strong> ${parseFloat(averageCallsPerMonth).toLocaleString('ru-RU')}</li>
                        <li><strong>Месяц пиковой активности:</strong> ${peakActivity}</li>
                        <li><strong>Месяц минимальной активности:</strong> ${minActivity}</li>
                        <li><strong>Звонков за последние 12 месяцев:</strong> ${callsLast12Months.toLocaleString('ru-RU')}</li>
                    </ul>`;
        container.innerHTML = html;
    }

    function renderYearlyMonthlyTable(data, container) {
        if (!data || data.length === 0) {
            container.innerHTML = '<p style="text-align:center; color:#6c757d;"><i class="fas fa-info-circle"></i> Нет данных для таблицы по годам и месяцам.</p>';
            return;
        }

        // 1. Подготовка данных
        const statsByYear = {};
        let minYear = Infinity;
        let maxYear = -Infinity;

        data.forEach(item => {
            const year = parseInt(item.year, 10);
            const month = parseInt(item.month, 10);
            const count = parseInt(item.count, 10);

            minYear = Math.min(minYear, year);
            maxYear = Math.max(maxYear, year);

            if (!statsByYear[year]) {
                statsByYear[year] = { total: 0 }; // Инициализируем общую сумму за год
                for (let m = 1; m <= 12; m++) {
                    statsByYear[year][m] = 0; // Инициализируем все месяцы нулями
                }
            }
            statsByYear[year][month] = count;
            statsByYear[year].total += count;
        });

        // 2. Создание заголовка таблицы
        const monthHeaders = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
        let tableHtml = '<table class="analytics-table calls-table" style="margin-top:10px;">'; // Добавил класс calls-table для консистентности
        tableHtml += '<thead><tr><th>Год</th>';
        monthHeaders.forEach(mh => tableHtml += `<th>${mh}</th>`);
        tableHtml += '<th>Итого за год</th></tr></thead><tbody>';

        // 3. Формирование строк таблицы (от самого нового года к старому)
        const sortedYears = Object.keys(statsByYear).sort((a, b) => b - a); // Сортировка годов по убыванию

        sortedYears.forEach(year => {
            tableHtml += `<tr><td style="font-weight: bold;">${year}</td>`;
            for (let m = 1; m <= 12; m++) {
                const countForMonth = statsByYear[year][m];
                tableHtml += `<td>${countForMonth > 0 ? countForMonth : '-'}</td>`;
            }
            tableHtml += `<td style="font-weight: bold;">${statsByYear[year].total > 0 ? statsByYear[year].total : '-'}</td></tr>`;
        });

        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
    }


    function fetchMonthlyCallDynamics() {
        const chartLoadingStatus = document.getElementById('chartLoadingStatus');
        if (chartLoadingStatus) {
            chartLoadingStatus.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка данных для диаграммы...';
            chartLoadingStatus.style.display = 'block'; // Показываем при начале загрузки
        }
        const chartContainer = document.getElementById('monthlyCallsChartContainer');
        if(chartContainer) chartContainer.style.display = 'none'; // Скрываем контейнер на время загрузки


        fetch('/api/moscow-calls-monthly-stats')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP error ${response.status}`);
                return response.json();
            })
            .then(data => {
                if (data.success && data.stats) { // Изменено data.dynamics на data.stats
                    renderMonthlyCallsChart(data.stats); // Изменено data.dynamics на data.stats
                } else {
                    console.error("Ошибка при получении данных для диаграммы:", data.error);
                    if(chartLoadingStatus) chartLoadingStatus.innerHTML = `<p style="color:red;">Ошибка: ${data.error || 'Не удалось загрузить данные'}</p>`;
                    if(chartContainer) chartContainer.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Критическая ошибка при загрузке данных для диаграммы:', error);
                if(chartLoadingStatus) chartLoadingStatus.innerHTML = `<p style="color:red;">Критическая ошибка: ${error.message}</p>`;
                if(chartContainer) chartContainer.style.display = 'none';
            });
    }

    document.addEventListener('DOMContentLoaded', function() {
        // Находим панель "Динамика звонков по месяцам"
        const monthlyDynamicsPanel = document.getElementById('monthlyDynamicsPanel');
        let chartDataLoaded = false; // Флаг, чтобы избежать повторной загрузки

        if (monthlyDynamicsPanel) {
            const header = monthlyDynamicsPanel.querySelector('.accordion-header');
            if (header) {
                header.addEventListener('click', function() {
                    // Панель будет переключать класс 'active' сама по себе
                    // Загружаем данные только если панель стала активной И данные еще не загружены
                    if (monthlyDynamicsPanel.classList.contains('active') && !chartDataLoaded) {
                        fetchMonthlyCallDynamics();
                        chartDataLoaded = true; // Устанавливаем флаг, что данные (попытка) загружены
                    }
                });
            }

            // Если панель изначально активна (например, если убрать data-collapsed), загружаем данные сразу
            // В текущей конфигурации, она закрыта по умолчанию, так что это не сработает.
            // if (monthlyDynamicsPanel.classList.contains('active') && !chartDataLoaded) {
            //     fetchMonthlyCallDynamics();
            //     chartDataLoaded = true;
            // }
        }
    });
    // --- Конец Динамики звонков по месяцам ---
