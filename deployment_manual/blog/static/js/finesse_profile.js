/**
 * Модуль для управления профилем пользователя Finesse
 * Отвечает за авторизацию, вход и выход пользователя
 */
(function() {
    // Глобальный объект для хранения данных авторизации
    window.finesseAuth = {
        isAuthenticated: false,
        userData: null,
        token: null,

        // Сохраняем состояние авторизации в localStorage
        saveAuth(token, userData) {
            localStorage.setItem('finesseToken', token);
            localStorage.setItem('finesseUserData', JSON.stringify(userData));
            this.isAuthenticated = true;
            this.userData = userData;
            this.token = token;

            // Создаем и отправляем событие успешной авторизации
            const authEvent = new CustomEvent('finesseAuthSuccess', {
                detail: { userData }
            });
            document.dispatchEvent(authEvent);
        },

        // Загружаем состояние авторизации из localStorage
        loadAuth() {
            const token = localStorage.getItem('finesseToken');
            const userDataStr = localStorage.getItem('finesseUserData');

            if (token && userDataStr) {
                try {
                    const userData = JSON.parse(userDataStr);
                    this.isAuthenticated = true;
                    this.userData = userData;
                    this.token = token;
                    return true;
                } catch (e) {
                    console.error('Ошибка при загрузке данных пользователя:', e);
                    this.clearAuth();
                }
            }
            return false;
        },

        // Очищаем состояние авторизации
        clearAuth() {
            localStorage.removeItem('finesseToken');
            localStorage.removeItem('finesseUserData');
            this.isAuthenticated = false;
            this.userData = null;
            this.token = null;

            // Создаем и отправляем событие выхода
            const logoutEvent = new CustomEvent('finesseLogout');
            document.dispatchEvent(logoutEvent);
        },

        // Выполняем вход пользователя
        async login(username, password) {
            try {
                // Проверяем состояние соединения с Finesse
                const healthCheck = await fetch('/finesse/health-check');
                const healthStatus = await healthCheck.json();

                if (healthStatus.status !== 'ok') {
                    throw new Error(healthStatus.message || 'Сервис Finesse недоступен');
                }

                // Формируем базовую аутентификацию
                const authHeader = 'Basic ' + btoa(`${username}:${password}`);

                // Проверяем сессию с Finesse
                const response = await fetch('/finesse/session', {
                    method: 'GET',
                    headers: {
                        'Authorization': authHeader,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'include'
                });

                if (!response.ok) {
                    throw new Error('Ошибка авторизации. Проверьте имя пользователя и пароль.');
                }

                const data = await response.json();

                if (data.authenticated) {
                    // Сохраняем данные авторизации
                    this.saveAuth(data.token, data.user);

                    // Запрашиваем текущее состояние агента
                    this.updateAgentState();

                    return { success: true, message: 'Авторизация успешна' };
                } else {
                    throw new Error(data.error || 'Ошибка авторизации');
                }
            } catch (error) {
                console.error('Ошибка при авторизации:', error);
                return { success: false, message: error.message };
            }
        },

        // Выполняем выход пользователя
        logout() {
            this.clearAuth();
            // Перезагружаем страницу или обновляем интерфейс
            window.location.reload();
        },

        // Обновляем состояние агента
        async updateAgentState() {
            if (!this.isAuthenticated || !this.token) {
                return null;
            }

            try {
                const response = await fetch('/finesse/agent/state', {
                    headers: {
                        'X-Session-Token': this.token,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) {
                    // Если получили 401, то токен недействителен
                    if (response.status === 401) {
                        this.clearAuth();
                        return null;
                    }
                    throw new Error('Ошибка при получении статуса агента');
                }

                const data = await response.json();

                if (data.success) {
                    // Обновляем статус агента в userData
                    if (!this.userData) this.userData = {};
                    this.userData.state = data.state;
                    this.userData.stateChangeTime = data.stateChangeTime;

                    // Сохраняем обновленные данные
                    localStorage.setItem('finesseUserData', JSON.stringify(this.userData));

                    // Отправляем событие обновления статуса
                    const stateEvent = new CustomEvent('finesseStateUpdate', {
                        detail: { state: data.state, stateChangeTime: data.stateChangeTime }
                    });
                    document.dispatchEvent(stateEvent);

                    return data.state;
                }
            } catch (error) {
                console.error('Ошибка при обновлении статуса агента:', error);
            }

            return null;
        },

        // Изменяем состояние агента
        async changeState(newState) {
            if (!this.isAuthenticated || !this.token) {
                return { success: false, message: 'Необходима авторизация' };
            }

            try {
                const response = await fetch('/finesse/agent/state', {
                    method: 'POST',
                    headers: {
                        'X-Session-Token': this.token,
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ state: newState })
                });

                if (!response.ok) {
                    // Если получили 401, то токен недействителен
                    if (response.status === 401) {
                        this.clearAuth();
                        return { success: false, message: 'Сессия истекла, требуется повторная авторизация' };
                    }
                    throw new Error('Ошибка при изменении статуса агента');
                }

                const data = await response.json();

                if (data.success) {
                    // Обновляем статус агента сразу после успешного изменения
                    this.updateAgentState();
                    return { success: true, message: 'Статус успешно изменен' };
                } else {
                    return { success: false, message: data.error || 'Не удалось изменить статус' };
                }
            } catch (error) {
                console.error('Ошибка при изменении статуса агента:', error);
                return { success: false, message: error.message };
            }
        }
    };

    // Функция для создания модального окна авторизации
    function createLoginModal() {
        // Проверяем, существует ли уже модальное окно
        if (document.getElementById('finesseLoginModal')) {
            return document.getElementById('finesseLoginModal'); // Возвращаем существующее окно
        }

        // Добавляем стили для модального окна, если их еще нет
        if (!document.getElementById('finesse-modal-styles')) {
            const style = document.createElement('style');
            style.id = 'finesse-modal-styles';
            style.textContent = `
                .finesse-modal {
                    display: none; /* Скрыто по умолчанию */
                    position: fixed;
                    z-index: 1050;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    background-color: rgba(0, 0, 0, 0.5); /* Полупрозрачный фон */
                    animation: fadeInModal 0.3s;
                }

                .finesse-modal-content {
                    background-color: #fefefe;
                    margin: 10% auto; /* Центрирование по вертикали и горизонтали */
                    padding: 0; /* Убираем внутренние отступы */
                    border: 1px solid #888;
                    width: 90%; /* Адаптивная ширина */
                    max-width: 400px; /* Максимальная ширина */
                    border-radius: 8px; /* Скругленные углы */
                    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2),0 6px 20px 0 rgba(0,0,0,0.19);
                    overflow: hidden; /* Скрываем выходящий контент */
                    animation: slideInModal 0.4s cubic-bezier(0.25, 0.8, 0.25, 1); /* Анимация появления */
                }

                .finesse-modal-header {
                    padding: 15px 20px; /* Увеличенные отступы */
                    background-color: #007bff; /* Цвет из Bootstrap */
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #dee2e6;
                }

                .finesse-modal-title {
                    margin: 0;
                    font-size: 1.3em; /* Увеличенный размер шрифта */
                    font-weight: 500; /* Средняя насыщенность */
                }

                .finesse-close-btn {
                    color: white; /* Белый цвет иконки */
                    float: right;
                    font-size: 28px;
                    font-weight: bold;
                    background: none;
                    border: none;
                    cursor: pointer;
                    opacity: 0.8; /* Немного прозрачности */
                    transition: opacity 0.2s ease-in-out; /* Плавный переход */
                }

                .finesse-close-btn:hover,
                .finesse-close-btn:focus {
                    opacity: 1; /* Полная непрозрачность при наведении */
                    text-decoration: none;
                }

                .finesse-modal-body {
                    padding: 25px 20px; /* Отступы для тела */
                }

                .finesse-form-group {
                    margin-bottom: 20px; /* Увеличенный отступ между группами */
                }

                .input-wrapper {
                    position: relative;
                }

                .finesse-form-group label {
                    display: block;
                    margin-bottom: 8px; /* Отступ после метки */
                    font-weight: 500; /* Средняя насыщенность */
                    color: #495057; /* Темно-серый цвет */
                }

                .finesse-input {
                    width: 100%;
                    padding: 10px 12px; /* Компактные отступы */
                    /* Уменьшаем padding для пароля, чтобы освободить место для иконки */
                    padding-right: 40px; /* Отступ справа для иконки глаза */
                    border: 1px solid #ced4da; /* Стандартная рамка Bootstrap */
                    border-radius: 4px; /* Небольшое скругление */
                    font-size: 1em; /* Стандартный размер шрифта */
                    box-sizing: border-box; /* Учитываем padding и border в ширине */
                    transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out; /* Плавные переходы */
                }
                /* Убираем правый padding для поля логина */
                #finesseUsername.finesse-input {
                     padding-right: 12px;
                }

                .finesse-input:focus {
                    border-color: #80bdff; /* Цвет рамки при фокусе */
                    outline: 0;
                    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25); /* Тень при фокусе */
                }

                #finesse-password-toggle {
                    position: absolute;
                    right: 12px;
                    /* Revert to 50% top and transform for centering within the new wrapper */
                    top: 50%;
                    transform: translateY(-50%);
                    cursor: pointer;
                    color: #6c757d; /* Серый цвет иконки */
                    font-size: 1.1em;
                    padding: 5px; /* Увеличим область клика */
                    line-height: 1; /* Исправляем возможное смещение иконки */
                }

                #finesse-password-toggle:hover {
                    color: #343a40; /* Темнее при наведении */
                }

                .finesse-form-actions {
                    display: flex;
                    justify-content: flex-end; /* Кнопки справа */
                    margin-top: 25px; /* Отступ сверху */
                }

                .finesse-cancel-btn,
                .finesse-login-btn {
                    padding: 10px 18px; /* Увеличенные отступы */
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1em;
                    font-weight: 500;
                    margin-left: 10px; /* Отступ между кнопками */
                    transition: background-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out; /* Плавные переходы */
                }

                .finesse-cancel-btn {
                    background-color: #6c757d; /* Серый цвет */
                    color: white;
                }

                .finesse-cancel-btn:hover {
                    background-color: #5a6268; /* Темнее при наведении */
                }

                .finesse-login-btn {
                    background-color: #007bff; /* Синий цвет */
                    color: white;
                }

                .finesse-login-btn:hover {
                    background-color: #0056b3; /* Темнее при наведении */
                }

                .finesse-login-btn:disabled {
                    background-color: #a0cfff; /* Светлее, когда неактивна */
                    cursor: not-allowed;
                }

                .finesse-login-btn .login-spinner {
                    margin-left: 5px;
                }

                #finesseLoginError {
                    color: #dc3545;
                    margin-bottom: 15px;
                    font-size: 0.9em;
                    text-align: center;
                }

                /* Анимации */
                @keyframes fadeInModal {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }

                @keyframes fadeOutModal {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }

                @keyframes slideInModal {
                    from { transform: translateY(-30px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }

                /* Адаптивность */
                @media (max-width: 768px) {
                    .finesse-modal-content {
                        margin: 15% auto;
                        width: 95%;
                    }
                }

                /* Стили для ссылки на Finesse и обновленного заголовка аккордеона */
                .accordion-header {
                    /* Используем flex для удобного расположения элементов */
                    display: flex;
                    justify-content: space-between; /* Иконка справа, остальное слева */
                    align-items: center;
                    cursor: pointer; /* Стандартный курсор для кликабельных элементов */
                    padding: 10px 15px; /* Примерные отступы, можно настроить */
                    /* ... другие стили для .accordion-header, если они есть или нужны ... */
                }

                .accordion-header > .header-title-content { /* Обертка для основного текста заголовка */
                    flex-grow: 1; /* Позволяет тексту занимать доступное пространство */
                    margin-right: 10px; /* Отступ от ссылки/иконки */
                }

                .finesse-direct-link {
                    margin-left: 10px; /* Отступ от заголовка */
                    margin-right: 10px; /* Отступ от иконки */
                    font-size: 0.85em;
                    color: #0056b3;
                    background-color: #e9ecef;
                    padding: 5px 10px;
                    border-radius: 4px;
                    text-decoration: none;
                    border: 1px solid #ced4da;
                    transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease;
                    display: inline-flex;
                    align-items: center;
                    white-space: nowrap; /* Предотвратить перенос текста ссылки */
                }

                .finesse-direct-link:hover {
                    background-color: #007bff;
                    color: white;
                    border-color: #0056b3;
                    text-decoration: none;
                }

                .accordion-icon {
                    margin-left: auto; /* Прижимает иконку вправо, если нет других элементов после нее */
                    transition: transform 0.3s ease;
                }

                .accordion-panel.active .accordion-icon {
                    transform: rotate(180deg);
                }
            `;
            document.head.appendChild(style);
        }


        const modalHtml = `
            <div id="finesseLoginModal" class="finesse-modal">
                <div class="finesse-modal-content">
                    <div class="finesse-modal-header">
                        <h2 class="finesse-modal-title">Вход в Cisco Finesse</h2>
                        <button class="finesse-close-btn" aria-label="Close">&times;</button>
                    </div>
                    <div class="finesse-modal-body">
                        <form id="finesseLoginForm" novalidate>
                            <div class="finesse-form-group">
                                <label for="finesseUsername">Имя пользователя</label>
                                <input type="text" id="finesseUsername" class="finesse-input" required autocomplete="username">
                            </div>
                            <div class="finesse-form-group">
                                <label for="finessePassword">Пароль</label>
                                <div class="input-wrapper">
                                    <input type="password" id="finessePassword" class="finesse-input" required autocomplete="current-password">
                                    <span id="finesse-password-toggle" class="fas fa-eye" title="Показать/скрыть пароль"></span>
                                </div>
                            </div>
                            <div id="finesseLoginError" style="color: #dc3545; margin-bottom: 15px; display: none;"></div>
                            <div class="finesse-form-actions">
                                <button type="button" class="finesse-cancel-btn">Отмена</button>
                                <button type="submit" class="finesse-login-btn">
                                    <span class="login-text">Войти</span>
                                    <span class="login-spinner" style="display: none;">
                                        <i class="fas fa-spinner fa-spin"></i>
                                    </span>
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Добавляем модальное окно в DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        const modalElement = modalContainer.firstElementChild;
        document.body.appendChild(modalElement);

        // Получаем элементы модального окна
        const modal = document.getElementById('finesseLoginModal');
        const closeBtn = modal.querySelector('.finesse-close-btn');
        const cancelBtn = modal.querySelector('.finesse-cancel-btn');
        const form = document.getElementById('finesseLoginForm');
        const errorElement = document.getElementById('finesseLoginError');
        const loginBtn = modal.querySelector('.finesse-login-btn');
        const loginText = loginBtn.querySelector('.login-text');
        const loginSpinner = loginBtn.querySelector('.login-spinner');
        const passwordInput = document.getElementById('finessePassword');
        const passwordToggle = document.getElementById('finesse-password-toggle');


        // Обработчик закрытия модального окна
        const closeModal = () => {
            modal.style.animation = 'fadeOutModal 0.3s forwards'; // Добавляем forwards
            setTimeout(() => {
                modal.style.display = 'none';
                modal.style.animation = ''; // Сбрасываем анимацию

                // Сбрасываем форму
                form.reset();
                passwordInput.type = 'password'; // Сбрасываем тип пароля
                passwordToggle.classList.remove('fa-eye-slash');
                passwordToggle.classList.add('fa-eye');
                errorElement.style.display = 'none';
                loginText.style.display = '';
                loginSpinner.style.display = 'none';
                loginBtn.disabled = false;
            }, 300);
        };

        // Навешиваем обработчики
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);

        // Обработчик переключения видимости пароля
        passwordToggle.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            // Переключаем иконку
            passwordToggle.classList.toggle('fa-eye-slash');
            passwordToggle.classList.toggle('fa-eye');
        });

        // Обработчик отправки формы
        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Получаем данные формы
            const username = document.getElementById('finesseUsername').value;
            const password = passwordInput.value; // Используем переменную

            // Показываем спиннер
            loginText.style.display = 'none';
            loginSpinner.style.display = 'inline-block';
            loginBtn.disabled = true;
            errorElement.style.display = 'none';

            try {
                // Вызываем метод входа
                const result = await window.finesseAuth.login(username, password);

                if (result.success) {
                    // Закрываем модальное окно
                    closeModal();

                    // Обновляем интерфейс
                    updateUI(true);
                } else {
                    // Показываем ошибку
                    errorElement.textContent = result.message;
                    errorElement.style.display = 'block';
                }
            } catch (error) {
                // Показываем ошибку
                errorElement.textContent = error.message || 'Произошла ошибка при авторизации';
                errorElement.style.display = 'block';
            } finally {
                // Скрываем спиннер
                loginText.style.display = '';
                loginSpinner.style.display = 'none';
                loginBtn.disabled = false;
            }
        });

        return {
            show: () => {
                modal.style.display = 'block';
                modal.style.animation = ''; // Сброс анимации перед показом
                requestAnimationFrame(() => { // Гарантируем применение display: block перед анимацией
                  modal.style.animation = 'fadeInModal 0.3s';
                });
                document.getElementById('finesseUsername').focus();
            },
            hide: closeModal
        };
    }

    // Функция для обновления интерфейса в зависимости от состояния авторизации
    function updateUI(isAuthenticated) {
        // Получаем панель операторов
        const agentsPanel = document.querySelector('.supervisor-panel');
        const newLoginButton = document.querySelector('header .header-actions .login-btn');
        const newLogoutButton = document.querySelector('header .header-actions .logout-btn');

        if (isAuthenticated) {
            // Если пользователь авторизован, показываем панель операторов
            if (agentsPanel) {
                agentsPanel.style.display = 'block';
            }

            // Обновляем информацию о пользователе
            const userData = window.finesseAuth.userData;
            if (userData) {
                // Обновляем информацию в хедере
                const agentUsername = document.getElementById('agent-username');
                const statusIndicator = document.querySelector('.status-indicator');
                const statusText = document.querySelector('.status-text');

                if (agentUsername) {
                    agentUsername.textContent = userData.firstName
                        ? `${userData.firstName} ${userData.lastName || ''}`
                        : userData.loginId || 'Оператор';
                }

                if (statusIndicator && statusText) {
                    const state = userData.state || 'LOGOUT';

                    // Определяем цвет индикатора и текст статуса
                    let color = '#6c757d'; // Серый по умолчанию
                    let text = 'Выход';

                    switch (state) {
                        case 'READY':
                            color = '#28a745'; // Зеленый
                            text = 'Готов';
                            break;
                        case 'NOT_READY':
                            color = '#dc3545'; // Красный
                            text = 'Не готов';
                            break;
                        case 'TALKING':
                            color = '#ffc107'; // Желтый
                            text = 'Разговор';
                            break;
                    }

                    statusIndicator.style.backgroundColor = color;
                    statusText.textContent = text;
                }
            }

            // Управляем новыми кнопками
            if (newLoginButton) newLoginButton.style.display = 'none';
            if (newLogoutButton) newLogoutButton.style.display = 'flex'; // или 'inline-flex'

            // Инициируем загрузку статусов операторов
            if (typeof window.fetchAgentStatuses === 'function') {
                window.fetchAgentStatuses();
            }
        } else {
            // Если пользователь не авторизован, скрываем панель операторов
            if (agentsPanel && !agentsPanel.getAttribute('data-no-auth')) {
                agentsPanel.style.display = 'none';
            }

            // Скрываем информацию о пользователе
            const agentUsername = document.getElementById('agent-username');
            const statusIndicator = document.querySelector('.status-indicator');
            const statusText = document.querySelector('.status-text');

            if (agentUsername) {
                agentUsername.textContent = '';
            }

            if (statusIndicator && statusText) {
                statusIndicator.style.backgroundColor = '#6c757d'; // Серый
                statusText.textContent = 'Не авторизован';
            }

            // Управляем новыми кнопками
            if (newLoginButton) newLoginButton.style.display = 'flex'; // или 'inline-flex'
            if (newLogoutButton) newLogoutButton.style.display = 'none';
        }
    }

    // Инициализация модуля
    function init() {
        // Пытаемся загрузить сохраненные данные авторизации
        const isAuthenticated = window.finesseAuth.loadAuth();

        // Обновляем интерфейс в зависимости от состояния авторизации
        updateUI(isAuthenticated);

        // Если пользователь авторизован, обновляем статус агента
        if (isAuthenticated) {
            window.finesseAuth.updateAgentState();
        }

        // Создаем модальное окно авторизации
        const loginModal = createLoginModal();

        // Назначаем обработчик для НОВОЙ кнопки "Войти" из header
        const newLoginButton = document.querySelector('header .header-actions .login-btn');
        if (newLoginButton) {
            newLoginButton.addEventListener('click', () => {
                if (loginModal && typeof loginModal.show === 'function') {
                    loginModal.show();
                } else {
                    console.error('Login modal is not available or not initialized.');
                }
            });
        }

        // Назначаем обработчик для НОВОЙ кнопки "Выйти" из header
        const newLogoutButton = document.querySelector('header .header-actions .logout-btn');
        if (newLogoutButton) {
            newLogoutButton.addEventListener('click', () => {
                if (window.finesseAuth && typeof window.finesseAuth.logout === 'function') {
                    window.finesseAuth.logout();
                } else {
                    console.error('finesseAuth.logout function is not available.');
                }
            });
        }

        // Обработчики событий авторизации
        document.addEventListener('finesseAuthSuccess', (e) => {
            updateUI(true);
        });

        document.addEventListener('finesseLogout', () => {
            updateUI(false);
        });

        document.addEventListener('finesseStateUpdate', (e) => {
            // Обновляем отображение статуса агента
            const statusIndicator = document.querySelector('.status-indicator');
            const statusText = document.querySelector('.status-text');

            if (statusIndicator && statusText) {
                const state = e.detail.state || 'LOGOUT';

                // Определяем цвет индикатора и текст статуса
                let color = '#6c757d'; // Серый по умолчанию
                let text = 'Выход';

                switch (state) {
                    case 'READY':
                        color = '#28a745'; // Зеленый
                        text = 'Готов';
                        break;
                    case 'NOT_READY':
                        color = '#dc3545'; // Красный
                        text = 'Не готов';
                        break;
                    case 'TALKING':
                        color = '#ffc107'; // Желтый
                        text = 'Разговор';
                        break;
                }

                statusIndicator.style.backgroundColor = color;
                statusText.textContent = text;
            }
        });

        // Инициализация аккордеона
        initAccordion();
    }

    // Инициализация аккордеона
    function initAccordion() {
        const panels = document.querySelectorAll('.supervisor-panel');

        panels.forEach(panel => {
            // Создаем структуру аккордеона, если она отсутствует
            if (!panel.classList.contains('accordion-panel')) {
                // Получаем заголовок и контент
                const header = panel.querySelector('.section-header');
                const content = panel.querySelector('.panel-content, .calls-list, div:not(.section-header)');

                if (header && content) {
                    // Оборачиваем контент в div с классом accordion-content
                    const accordionContent = document.createElement('div');
                    accordionContent.className = 'accordion-content';

                    // Перемещаем контент в новый контейнер
                    while (content.childNodes.length) {
                        accordionContent.appendChild(content.childNodes[0]);
                    }

                    // Заменяем исходный контент на новый
                    content.replaceWith(accordionContent);

                    // Преобразуем заголовок в кликабельный заголовок аккордеона
                    const accordionHeader = document.createElement('div');
                    accordionHeader.className = 'accordion-header';

                    // Обертка для оригинального содержимого заголовка
                    const headerTitleContent = document.createElement('span');
                    headerTitleContent.className = 'header-title-content';
                    headerTitleContent.innerHTML = header.innerHTML;
                    accordionHeader.appendChild(headerTitleContent);

                    const icon = document.createElement('i');
                    icon.className = 'fas fa-chevron-down accordion-icon';
                    accordionHeader.appendChild(icon);


                    // Заменяем исходный заголовок на новый
                    header.replaceWith(accordionHeader);

                    // Добавляем класс accordion-panel к панели
                    panel.classList.add('accordion-panel');

                    // Назначаем обработчик клика
                    accordionHeader.addEventListener('click', () => {
                        panel.classList.toggle('active');
                        // Обновляем состояние иконки, если необходимо (уже сделано через CSS .accordion-panel.active .accordion-icon)
                    });

                    // Раскрываем панель по умолчанию, если она не отмечена как закрытая
                    if (!panel.hasAttribute('data-collapsed')) {
                        panel.classList.add('active');
                    }
                }
            }
        });
    }

    // Запускаем инициализацию после загрузки DOM
    document.addEventListener('DOMContentLoaded', init);
})();
