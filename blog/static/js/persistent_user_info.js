/**
 * Модуль для защиты и отображения информации о пользователе
 * в шапке сайта с защитой от удаления
 */
(function() {
    // Добавляем стили для элементов пользователя в шапке
    function addCustomStyles() {
        // Проверяем, нет ли уже добавленных стилей
        if (document.getElementById('persistent-user-styles')) {
            return;
        }

        // Создаем элемент стиля
        const styleElement = document.createElement('style');
        styleElement.id = 'persistent-user-styles';
        styleElement.setAttribute('data-persistent', 'true');

        // Добавляем стили
        styleElement.textContent = `
            /* --- Enhanced Header Styles --- */
            header {
                /* Slightly more vibrant gradient */
                background: linear-gradient(to right, #00a896, #90c63e);
                border-bottom: 3px solid #007a6e; /* Accent border */
                position: relative; /* For potential absolute positioning inside */
                overflow: hidden; /* Hide overflow from pseudo-elements */
            }

            /* Optional: Subtle background pattern */
            /* header::before {
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"><path fill="%23ffffff" fill-opacity="0.05" d="M0 40 L40 0 H20 L0 20 M40 40 V20 L20 40"></path></svg>');
                opacity: 0.5;
                z-index: 0;
            } */

            header .header-content {
                position: relative; /* Ensure content is above pseudo-elements */
                z-index: 1;
                display: flex;
                justify-content: space-between;
                align-items: center;
                /* Add more padding for a spacious look */
                padding: 20px 25px;
            }

            /* Title adjustments */
             .header-title-block { /* Wrapper for title and subtitle */
                 display: flex;
                 align-items: center;
                 gap: 15px; /* Space between icon and text */
             }

            .header-title-block i.header-icon { /* Optional Icon */
                 font-size: 28px; /* Adjust icon size */
                 color: rgba(255, 255, 255, 0.8);
            }

            .header-title {
                font-size: 26px; /* Slightly larger title */
                font-weight: 700;
                margin: 0;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1); /* Subtle text shadow */
            }

            .header-subtitle {
                font-size: 14px;
                opacity: 0.85; /* Slightly less transparent */
                margin-top: 3px;
            }

            /* Finesse Mention */
            .finesse-mention {
                 font-size: 11px;
                 font-weight: 500;
                 color: rgba(255, 255, 255, 0.7);
                 background-color: rgba(0, 0, 0, 0.1);
                 padding: 3px 8px;
                 border-radius: 4px;
                 margin-left: 10px;
                 vertical-align: middle;
            }
             .finesse-mention i {
                 margin-right: 4px;
             }

            /* Actions alignment */
            header .header-actions {
                display: flex;
                align-items: center;
                justify-content: flex-end; /* Keep to the right */
                gap: 15px; /* Space between action elements */
                flex-shrink: 0; /* Prevent shrinking on smaller screens */
            }

            /* Date Display */
            #current-date-display {
                color: white;
                font-size: 0.9em;
                opacity: 0.9;
                white-space: nowrap;
                padding: 8px 12px;
                background-color: rgba(0, 0, 0, 0.1); /* Subtle background */
                border-radius: 6px;
            }

            /* Operator Info Block */
            #operator-header-info {
                display: flex;
                align-items: center;
                /* Adjusted gradient */
                background: linear-gradient(135deg, #1aa882, #138496);
                border-radius: 6px;
                padding: 8px 15px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2); /* Slightly enhanced shadow */
                transition: all 0.3s ease;
                color: white; /* Ensure text is white */
            }
            #operator-header-info:hover {
                 background: linear-gradient(135deg, #20c997, #17a2b8); /* Lighter on hover */
                 box-shadow: 0 4px 8px rgba(0,0,0,0.25);
                 transform: translateY(-1px); /* Slight lift */
            }

            #operator-name-display {
                font-weight: 600;
                margin-right: 12px;
                font-size: 0.95em;
            }

            #operator-status-display {
                display: flex;
                align-items: center;
                font-size: 0.85em;
                opacity: 0.9;
            }

            #operator-status-indicator {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 6px;
                border: 1px solid rgba(0, 0, 0, 0.1);
                flex-shrink: 0;
            }

            /* Status color classes remain the same */
            .status-ready { background-color: #28a745; }
            .status-not-ready { background-color: #dc3545; }
            .status-logout { background-color: #6c757d; }
            .status-talking { background-color: #ffc107; }

            /* Logout Button */
            #persistent-logout-button {
                background-color: rgba(255, 255, 255, 0.15); /* Slightly lighter background */
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2); /* Subtle border */
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 0.9em;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            #persistent-logout-button:hover {
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.4);
                box-shadow: 0 2px 5px rgba(0,0,0,0.15);
                transform: translateY(-1px); /* Slight lift */
            }
            #persistent-logout-button i {
                margin-right: 6px;
            }

             /* Responsive adjustments if needed */
             @media (max-width: 992px) {
                 header .header-content {
                     flex-direction: column;
                     align-items: flex-start;
                     gap: 15px;
                 }
                 header .header-actions {
                     width: 100%;
                     justify-content: space-between; /* Space out actions */
                 }
             }
             @media (max-width: 768px) {
                #current-date-display {
                     order: -1; /* Move date first on small screens */
                 }
             }

            /* --- End of Enhanced Header Styles --- */
        `;

        // Добавляем стили в head
        document.head.appendChild(styleElement);
    }

    // Функция для обновления информации о пользователе в шапке
    function updateUserInfo() {
        // Получаем данные авторизации
        const isAuthenticated = window.finesseAuth && window.finesseAuth.isAuthenticated;
        const userData = window.finesseAuth && window.finesseAuth.userData;

        // Находим или создаем элементы для отображения информации
        let operatorInfo = document.getElementById('operator-header-info');
        let operatorName = document.getElementById('operator-name-display');
        let operatorStatus = document.getElementById('operator-status-display');
        let statusIndicator = document.getElementById('operator-status-indicator');
        let logoutButton = document.getElementById('persistent-logout-button');
        let dateDisplay = document.getElementById('current-date-display'); // Раскомментировано объявление
        let finesseMention = document.querySelector('.finesse-mention'); // Finesse mention

        // --- Date Display (Always Visible) --- DEPRECATED since new header has its own date
        /*
        // let dateDisplay = document.getElementById('current-date-display'); // Закомментировано здесь, т.к. объявлено выше
        if (!dateDisplay) {
            dateDisplay = document.createElement('div');
// ... existing code ...
        // const today = new Date();
        // const months = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'];
        // dateDisplay.textContent = `Сегодня: ${today.getDate()} ${months[today.getMonth()]} ${today.getFullYear()}`;
        // dateDisplay.style.display = 'block'; // Тоже закомментируем, чтобы не пытаться отобразить
        */

        // --- Add Finesse Mention to Title Block ---
        const titleBlock = document.querySelector('.header-content > div:first-child'); // Assuming first div contains title/subtitle
        if (titleBlock && !finesseMention) {
             finesseMention = document.createElement('span');
             finesseMention.className = 'finesse-mention';
             finesseMention.setAttribute('data-persistent', 'true'); // Protect it
             finesseMention.innerHTML = '<i class="fas fa-headset"></i> Cisco Finesse';
             // Append after the title/subtitle block or within it
             const subtitle = titleBlock.querySelector('.header-subtitle');
             if(subtitle) {
                subtitle.appendChild(finesseMention); // Append to subtitle
             } else {
                 titleBlock.appendChild(finesseMention); // Or append to title block
             }
        }
        // Ensure it's visible
        if (finesseMention) {
            finesseMention.style.display = 'inline-block';
            // Potentially update text or icon based on Finesse connection status from finesse_profile.js if needed

            // --- Начало добавленного кода ---
            // Делаем элемент кликабельным, если он еще не инициализирован
            if (!finesseMention.dataset.clickableInitialized) {
                finesseMention.style.cursor = 'pointer';
                finesseMention.title = 'Перейти в Cisco Finesse'; // Добавляем подсказку

                // --- Начало добавленных стилей для заметности и кликабельности ---
                finesseMention.style.display = 'inline-flex'; // Для лучшего контроля над содержимым
                finesseMention.style.alignItems = 'center';
                finesseMention.style.padding = '6px 14px'; // Немного увеличим отступы
                finesseMention.style.borderRadius = '18px'; // Более скругленные углы
                finesseMention.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                finesseMention.style.transition = 'transform 0.2s ease-out, box-shadow 0.2s ease-out, background-color 0.2s ease-out';
                // Предполагаем, что базовый цвет текста и фона задается классом .finesse-mention
                // и они достаточно контрастны. Если нет, можно добавить:
                // finesseMention.style.color = 'white';
                // finesseMention.style.backgroundColor = '#28a745'; // Пример основного зеленого

                const originalBgColor = getComputedStyle(finesseMention).backgroundColor;
                // Яркий зеленый для ховера, который хорошо сочетается с белым текстом
                const hoverBgColor = '#34d399'; // Яркий изумрудно-зеленый (Tailwind green-400)

                finesseMention.addEventListener('mouseover', () => {
                    finesseMention.style.transform = 'translateY(-2px)';
                    finesseMention.style.boxShadow = '0 5px 10px rgba(0,0,0,0.15)';
                    if (originalBgColor !== hoverBgColor) { // Изменяем фон, только если он отличается
                       finesseMention.style.backgroundColor = hoverBgColor;
                    }
                });

                finesseMention.addEventListener('mouseout', () => {
                    finesseMention.style.transform = 'translateY(0)';
                    finesseMention.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                    finesseMention.style.backgroundColor = originalBgColor; // Восстанавливаем оригинальный фон
                });
                // --- Конец добавленных стилей ---

                finesseMention.addEventListener('click', () => {
                    window.open('https://uccx1.teztour.com:8445/desktop/container/?locale=en_US', '_blank', 'noopener,noreferrer');
                });

                finesseMention.dataset.clickableInitialized = 'true'; // Помечаем как инициализированный
                console.log('Элемент finesse-mention сделан кликабельным и стилизован в persistent_user_info.js');
            }
            // --- Конец добавленного кода ---
        }

        // --- User Info Block (Only if Authenticated) ---
        if (isAuthenticated && userData) {
            if (!operatorInfo) {
                operatorInfo = document.createElement('div');
                operatorInfo.id = 'operator-header-info';
                operatorInfo.setAttribute('data-persistent', 'true');

                operatorName = document.createElement('div');
                operatorName.id = 'operator-name-display';
                operatorName.setAttribute('data-persistent', 'true');

                operatorStatus = document.createElement('div');
                operatorStatus.id = 'operator-status-display';
                operatorStatus.setAttribute('data-persistent', 'true');

                statusIndicator = document.createElement('div');
                statusIndicator.id = 'operator-status-indicator';
                statusIndicator.setAttribute('data-persistent', 'true');

                operatorStatus.appendChild(statusIndicator);
                operatorInfo.appendChild(operatorName);
                operatorInfo.appendChild(operatorStatus);

                // Находим место для вставки (в header actions)
                const headerActions = document.querySelector('header .header-actions');
                if (headerActions) {
                    // Insert before date or at the start if date is not there yet
                    headerActions.insertBefore(operatorInfo, dateDisplay || headerActions.firstChild);
                } else {
                     // Fallback (less ideal)
                     document.body.insertBefore(operatorInfo, document.body.firstChild);
                }
            }

            // --- Operator Info Update ---
            operatorName.textContent = userData.firstName
                ? `${userData.firstName} ${userData.lastName || ''}`
                : userData.loginId || 'Оператор';

            // --- Status Update ---
            const state = userData.state || 'LOGOUT';
            statusIndicator.classList.remove('status-ready', 'status-not-ready', 'status-logout', 'status-talking');
            let statusClass = 'status-logout';
            let statusText = 'Logout';
            switch (state) {
                case 'READY': statusClass = 'status-ready'; statusText = 'Ready'; break;
                case 'NOT_READY': statusClass = 'status-not-ready'; statusText = 'Not Ready'; break;
                case 'TALKING': statusClass = 'status-talking'; statusText = 'Talking'; break;
            }
            statusIndicator.classList.add(statusClass);
            while (operatorStatus.childNodes.length > 1) { // Keep only the indicator
                operatorStatus.removeChild(operatorStatus.lastChild);
            }
            operatorStatus.appendChild(document.createTextNode(statusText));
            operatorInfo.style.display = 'flex'; // Ensure visible

            // --- Logout Button ---
            if (!logoutButton) {
                logoutButton = document.createElement('button');
                logoutButton.id = 'persistent-logout-button';
                logoutButton.setAttribute('data-persistent', 'true');
                logoutButton.innerHTML = '<i class="fas fa-sign-out-alt"></i> Выход';

                // Находим место для вставки кнопки выхода (в конец header actions)
                const headerActions = document.querySelector('header .header-actions');
                if (headerActions) {
                    headerActions.appendChild(logoutButton);
                } else if (operatorInfo && operatorInfo.parentNode) {
                     // Fallback
                     operatorInfo.parentNode.insertBefore(logoutButton, operatorInfo.nextSibling);
                }

                // Добавляем обработчик для кнопки выхода
                logoutButton.addEventListener('click', function() {
                    if (window.finesseAuth && typeof window.finesseAuth.logout === 'function') {
                        window.finesseAuth.logout();
                    } else {
                        // Резервный механизм выхода
                        localStorage.removeItem('finesseToken');
                        localStorage.removeItem('finesseUserData');
                        window.location.reload();
                    }
                });
            }
             logoutButton.style.display = 'flex'; // Ensure visible

        } else {
            // Если пользователь не авторизован, скрываем информацию
            if (operatorInfo) {
                operatorInfo.style.display = 'none';
            }
            // Скрываем кнопку выхода
            if (logoutButton) {
                logoutButton.style.display = 'none';
            }
        }
    }

    // Защита от удаления элементов с data-persistent="true"
    function protectElements() {
        // Сохраняем оригинальный метод remove
        const originalRemove = Element.prototype.remove;

        // Переопределяем метод remove
        Element.prototype.remove = function() {
            if (this.getAttribute && this.getAttribute('data-persistent') === 'true') {
                console.warn('Попытка удалить защищенный элемент:', this);
                return; // Предотвращаем удаление
            }

            // Вызываем оригинальный метод для не защищенных элементов
            originalRemove.apply(this, arguments);
        };

        // Сохраняем оригинальный сеттер innerHTML
        const originalInnerHTMLDescriptor = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');

        // Переопределяем сеттер innerHTML
        Object.defineProperty(Element.prototype, 'innerHTML', {
            set: function(html) {
                // Сохраняем защищенные элементы
                const protectedElements = Array.from(this.querySelectorAll('[data-persistent="true"]'));

                // Вызываем оригинальный сеттер
                originalInnerHTMLDescriptor.set.call(this, html);

                // Восстанавливаем защищенные элементы, если они были удалены
                // Check if the current element still exists in the DOM
                if (document.body.contains(this)) {
                    protectedElements.forEach(el => {
                        // Check if the element exists and is not already in the right place
                        if (el && !this.contains(el)) {
                             // Try to re-insert smartly, e.g., in header actions
                             const headerActions = document.querySelector('header .header-actions');
                             if (headerActions) {
                                 if (el.id === 'operator-header-info' || el.id === 'current-date-display' || el.id === 'persistent-logout-button') {
                                      // Re-insert logic might be needed here if elements are strictly ordered
                                      // For simplicity, just append if not present
                                      if (!headerActions.contains(el)) headerActions.appendChild(el);
                                 } else if (el.classList.contains('finesse-mention')) {
                                     const titleBlock = document.querySelector('.header-content > div:first-child .header-subtitle') || document.querySelector('.header-content > div:first-child');
                                     if (titleBlock && !titleBlock.contains(el)) {
                                         titleBlock.appendChild(el);
                                     }
                                 } else {
                                     // Fallback append to the original parent if possible
                                     if (!this.contains(el)) this.appendChild(el);
                                 }
                             } else {
                                 // Fallback append if header not found
                                 if (!this.contains(el)) this.appendChild(el);
                             }
                        }
                    });
                     // Ensure correct order/visibility after potential innerHTML change
                     updateUserInfo(); // Re-run update to fix order/visibility
                }
            },
            get: originalInnerHTMLDescriptor.get
        });
    }

    // Инициализация модуля
    function init() {
        // Добавляем стили
        addCustomStyles();

        // Защищаем элементы от удаления
        protectElements();

        // Обновляем информацию о пользователе
        updateUserInfo();

        // Устанавливаем интервал для обновления информации
        setInterval(updateUserInfo, 3000);

        // Слушаем события авторизации
        document.addEventListener('finesseAuthSuccess', updateUserInfo);
        document.addEventListener('finesseLogout', updateUserInfo);
        document.addEventListener('finesseStateUpdate', updateUserInfo);

        // Добавляем функцию проверки токена
        async function checkTokenValidity() {
            if (window.finesseAuth && window.finesseAuth.isAuthenticated && window.finesseAuth.token) {
                try {
                    const response = await fetch('/finesse/check-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({ token: window.finesseAuth.token })
                    });

                    const data = await response.json();

                    if (!data.valid) {
                        console.warn('Токен недействителен, выполняем выход');
                        if (window.finesseAuth.logout) {
                            window.finesseAuth.logout();
                        }
                    }
                } catch (error) {
                    console.error('Ошибка при проверке токена:', error);
                }
            }
        }

        // Проверяем токен каждые 5 минут
        setInterval(checkTokenValidity, 5 * 60 * 1000);

        // Update date periodically (e.g., every minute to catch day change, though overkill)
        setInterval(() => {
            const dateDisp = document.getElementById('current-date-display'); // Используем новое имя для элемента даты в шапке
            if (dateDisp) {
                 // Этот блок больше не должен обновлять старый dateDisplay, если он не существует.
                 // Вместо этого, новая дата в шапке обновляется в contact_center_moscow.html
                 // const today = new Date();
                 // const months = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря'];
                 // dateDisp.textContent = `Сегодня: ${today.getDate()} ${months[today.getMonth()]} ${today.getFullYear()}`;
            }
             // Ensure Finesse mention is visible
             const finesseMention = document.querySelector('.finesse-mention');
             if (finesseMention) finesseMention.style.display = 'inline-block';
        }, 60 * 1000); // Update every minute
    }

    // Запускаем инициализацию после загрузки DOM
    document.addEventListener('DOMContentLoaded', init);

    // Экспортируем API для взаимодействия с другими модулями
    window.persistentUserInfo = {
        update: updateUserInfo
    };
})();
