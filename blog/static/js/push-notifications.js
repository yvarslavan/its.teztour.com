/**
 * Модуль для управления браузерными пуш-уведомлениями
 */

class PushNotificationManager {
    constructor() {
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
        this.registration = null;
        this.vapidPublicKey = null;
        this.isSubscribed = false;
        this.subscription = null;
        this.isInitialized = false;
        this.isInitializing = false;

        // Элементы интерфейса
        this.pushButton = null;
        this.statusIndicator = null;

        // Звуки уведомлений
        this.notificationSounds = {
            default: '/static/sounds/notification.mp3'
        };

        // Убираем автоинициализацию из конструктора
        // this.init();
    }

    async init() {
        // Предотвращаем множественную инициализацию
        if (this.isInitialized) {
            console.log('[PushManager] Уже инициализирован, пропускаем');
            return;
        }

        if (this.isInitializing) {
            console.log('[PushManager] Инициализация уже в процессе, ожидаем...');
            // Ждем завершения текущей инициализации
            while (this.isInitializing) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return;
        }

        this.isInitializing = true;
        console.log('[PushManager] Инициализация...');

        if (!this.isSupported) {
            console.warn('[PushManager] Браузер не поддерживает пуш-уведомления');
            this.showUnsupportedMessage();
            this.isInitializing = false;
            return;
        }

        try {
            // Регистрируем Service Worker
            console.log('[PushManager] Запуск регистрации Service Worker...');
            await this.registerServiceWorker();
            console.log('[PushManager] Service Worker зарегистрирован успешно');

            // Получаем VAPID ключ
            console.log('[PushManager] Получение VAPID ключа...');
            await this.getVapidPublicKey();
            console.log('[PushManager] VAPID ключ получен успешно');

            // Проверяем текущий статус подписки
            console.log('[PushManager] Проверка статуса подписки...');
            await this.checkSubscriptionStatus();
            console.log('[PushManager] Статус подписки проверен');

            // Инициализируем UI
            console.log('[PushManager] Инициализация UI...');
            this.initializeUI();

            this.isInitialized = true;
            console.log('[PushManager] Инициализация завершена успешно');

            // Добавляем обработчик сообщений от Service Worker
            this.setupServiceWorkerMessageHandler();

        } catch (error) {
            console.error('[PushManager] Ошибка инициализации:', error);
            this.showError('Ошибка инициализации пуш-уведомлений: ' + error.message);
        } finally {
            this.isInitializing = false;
        }
    }

    async registerServiceWorker() {
        try {
            console.log('[PushManager] Запуск регистрации Service Worker...');

            // Проверяем наличие существующей регистрации
            const existingRegistration = await navigator.serviceWorker.getRegistration();
            if (existingRegistration) {
                console.log('[PushManager] Найдена существующая регистрация, отменяем...');
                await existingRegistration.unregister();
            }

            // Регистрируем Service Worker с правильным путем
            const swPath = '/sw.js';
            console.log('[PushManager] Регистрация Service Worker по пути:', swPath);

            try {
                console.log(`[PushManager] Попытка регистрации Service Worker с путем: ${swPath} и scope: '/'`);
                this.registration = await navigator.serviceWorker.register(swPath, {
                    scope: '/'
                });
                console.log('[PushManager] Service Worker зарегистрирован успешно:', this.registration);

                // Проверяем состояние Service Worker
                if (this.registration.installing) {
                    console.log('[PushManager] Service Worker устанавливается...');
                    await this.waitForServiceWorker(this.registration.installing);
                } else if (this.registration.waiting) {
                    console.log('[PushManager] Service Worker в ожидании, активируем...');
                    this.registration.waiting.postMessage({type: 'SKIP_WAITING'});
                    await this.waitForServiceWorker(this.registration.waiting);
                } else if (this.registration.active) {
                    console.log('[PushManager] Service Worker уже активен');
                }

                // Обновляем Service Worker
                await this.registration.update();

            } catch (error) {
                console.error('[PushManager] Ошибка регистрации Service Worker:', error);
                throw error;
            }

        } catch (error) {
            console.error('[PushManager] Ошибка регистрации Service Worker:', error);
            throw error;
        }
    }

    // Вспомогательный метод для ожидания готовности Service Worker
    async waitForServiceWorker(serviceWorker) {
        return new Promise((resolve, reject) => {
            const stateChange = () => {
                console.log('[PushManager] Service Worker state changed to:', serviceWorker.state);

                if (serviceWorker.state === 'activated') {
                    serviceWorker.removeEventListener('statechange', stateChange);
                    resolve();
                } else if (serviceWorker.state === 'redundant') {
                    serviceWorker.removeEventListener('statechange', stateChange);
                    reject(new Error('Service Worker стал избыточным'));
                }
            };

            serviceWorker.addEventListener('statechange', stateChange);

            // Timeout для предотвращения бесконечного ожидания
            setTimeout(() => {
                serviceWorker.removeEventListener('statechange', stateChange);
                reject(new Error('Timeout ожидания активации Service Worker'));
            }, 30000); // 30 секунд
        });
    }

    async getVapidPublicKey() {
        try {
            console.log('[PushManager] Выполняю запрос к /api/vapid-public-key...');
            const response = await fetch('/api/vapid-public-key');

            console.log('[PushManager] Ответ сервера получен, статус:', response.status);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('[PushManager] Данные получены:', data);

            if (data.publicKey && data.publicKey.trim()) {
                this.vapidPublicKey = data.publicKey.trim();
                console.log('[PushManager] VAPID ключ сохранен:', this.vapidPublicKey.substring(0, 20) + '...');
            } else {
                console.error('[PushManager] VAPID ключ пустой или отсутствует в ответе:', data);
                throw new Error('VAPID ключ пустой или не получен');
            }

        } catch (error) {
            console.error('[PushManager] Ошибка получения VAPID ключа:', error);
            throw error;
        }
    }

    async checkSubscriptionStatus() {
        try {
            if (!this.registration) {
                throw new Error('Service Worker не зарегистрирован');
            }

            this.subscription = await this.registration.pushManager.getSubscription();
            this.isSubscribed = this.subscription !== null;

            // Проверяем статус на сервере
            const response = await fetch('/api/push/status');
            const serverStatus = await response.json();

            console.log('[PushManager] Статус подписки:', {
                localSubscription: this.isSubscribed,
                serverEnabled: serverStatus.enabled,
                serverSubscriptions: serverStatus.subscriptions_count
            });

            // Синхронизируем состояние
            if (this.isSubscribed && !serverStatus.enabled) {
                // Локально подписаны, но сервер не знает - отправляем подписку
                await this.sendSubscriptionToServer();
            } else if (!this.isSubscribed && serverStatus.enabled) {
                // Сервер думает, что подписаны, но локально нет - очищаем сервер
                await this.unsubscribeFromServer();
            }

        } catch (error) {
            console.error('[PushManager] Ошибка проверки статуса:', error);
            this.isSubscribed = false;
        }
    }

    initializeUI() {
        // Создаем кнопку управления уведомлениями
        this.createPushButton();

        // Создаем индикатор статуса
        this.createStatusIndicator();

        // Обновляем UI
        this.updateUI();
    }

    createPushButton() {
        // Ищем существующую кнопку или создаем новую
        this.pushButton = document.getElementById('push-notification-btn');

        if (!this.pushButton) {
            this.pushButton = document.createElement('button');
            this.pushButton.id = 'push-notification-btn';
            this.pushButton.className = 'btn btn-outline-primary push-notification-btn';

            // Добавляем кнопку в навигацию
            const navbar = document.querySelector('.navbar-nav');
            if (navbar) {
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.appendChild(this.pushButton);
                navbar.appendChild(li);
            }
        }

        // Добавляем обработчик клика
        this.pushButton.addEventListener('click', () => this.toggleSubscription());
    }

    createStatusIndicator() {
        this.statusIndicator = document.getElementById('push-status-indicator');

        if (!this.statusIndicator) {
            this.statusIndicator = document.createElement('span');
            this.statusIndicator.id = 'push-status-indicator';
            this.statusIndicator.className = 'push-status-indicator';

            // Добавляем рядом с кнопкой
            if (this.pushButton && this.pushButton.parentNode) {
                this.pushButton.parentNode.appendChild(this.statusIndicator);
            }
        }
    }

    updateUI() {
        if (!this.pushButton) return;

        if (!this.isSupported) {
            this.pushButton.textContent = 'Уведомления не поддерживаются';
            this.pushButton.disabled = true;
            this.pushButton.className = 'btn btn-secondary push-notification-btn';
            return;
        }

        if (this.isSubscribed) {
            this.pushButton.innerHTML = '<i class="fas fa-bell-slash"></i> Отключить уведомления';
            this.pushButton.className = 'btn btn-outline-danger push-notification-btn';
            this.pushButton.title = 'Отключить браузерные уведомления';

            if (this.statusIndicator) {
                this.statusIndicator.innerHTML = '<i class="fas fa-bell text-success"></i>';
                this.statusIndicator.title = 'Уведомления включены';
            }
        } else {
            this.pushButton.innerHTML = '<i class="fas fa-bell"></i> Включить уведомления';
            this.pushButton.className = 'btn btn-outline-primary push-notification-btn';
            this.pushButton.title = 'Включить браузерные уведомления';

            if (this.statusIndicator) {
                this.statusIndicator.innerHTML = '<i class="fas fa-bell-slash text-muted"></i>';
                this.statusIndicator.title = 'Уведомления отключены';
            }
        }

        this.pushButton.disabled = false;
    }

    async toggleSubscription() {
        try {
            this.pushButton.disabled = true;

            if (this.isSubscribed) {
                await this.unsubscribe();
            } else {
                await this.subscribe();
            }

        } catch (error) {
            console.error('[PushManager] Ошибка переключения подписки:', error);
            this.showError('Ошибка при изменении настроек уведомлений');
        } finally {
            this.pushButton.disabled = false;
        }
    }

    async subscribe() {
        try {
            console.log('[PushManager] Запрос разрешения на уведомления...');

            // Проверяем, что VAPID ключ получен
            if (!this.vapidPublicKey) {
                throw new Error('VAPID ключ не получен. Попробуйте обновить страницу.');
            }

            // Запрашиваем разрешение с таймаутом
            console.log('[PushManager] Запрос разрешения с таймаутом...');

            let permission;
            try {
                // Создаем промис с таймаутом для requestPermission
                const permissionPromise = new Promise((resolve, reject) => {
                    // Таймаут 10 секунд
                    const timeout = setTimeout(() => {
                        reject(new Error('Таймаут запроса разрешения на уведомления'));
                    }, 10000);

                    // Запрашиваем разрешение
                    const result = Notification.requestPermission();

                    // Обрабатываем как промис (современные браузеры) или callback (старые)
                    if (result && typeof result.then === 'function') {
                        result.then(perm => {
                            clearTimeout(timeout);
                            resolve(perm);
                        }).catch(err => {
                            clearTimeout(timeout);
                            reject(err);
                        });
                    } else {
                        // Для старых браузеров, где requestPermission возвращает значение сразу
                        clearTimeout(timeout);
                        resolve(result || Notification.permission);
                    }
                });

                permission = await permissionPromise;
            } catch (permError) {
                console.error('[PushManager] Ошибка запроса разрешения:', permError);
                throw new Error('Не удалось получить разрешение на уведомления: ' + permError.message);
            }

            console.log('[PushManager] Получено разрешение:', permission);

            if (permission !== 'granted') {
                throw new Error('Разрешение на уведомления не предоставлено');
            }

            console.log('[PushManager] Разрешение получено, создаем подписку...');
            console.log('[PushManager] Используем VAPID ключ:', this.vapidPublicKey.substring(0, 20) + '...');

            // Создаем подписку
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
            });

            console.log('[PushManager] Подписка создана:', subscription);

            // Отправляем подписку на сервер
            await this.sendSubscriptionToServer(subscription);

            this.subscription = subscription;
            this.isSubscribed = true;
            this.updateUI();

            this.showSuccess('Браузерные уведомления включены!');

            // Отправляем тестовое уведомление
            setTimeout(() => this.sendTestNotification(), 1000);

        } catch (error) {
            console.error('[PushManager] Ошибка подписки:', error);
            this.showError('Не удалось включить уведомления: ' + error.message);
        }
    }

    async unsubscribe() {
        try {
            console.log('[PushManager] Отписка от уведомлений...');

            if (this.subscription) {
                await this.subscription.unsubscribe();
            }

            // Уведомляем сервер
            await this.unsubscribeFromServer();

            this.subscription = null;
            this.isSubscribed = false;
            this.updateUI();

            this.showSuccess('Браузерные уведомления отключены');

        } catch (error) {
            console.error('[PushManager] Ошибка отписки:', error);
            this.showError('Не удалось отключить уведомления: ' + error.message);
        }
    }

    async sendSubscriptionToServer(subscription = null) {
        try {
            const sub = subscription || this.subscription;
            if (!sub) {
                throw new Error('Нет активной подписки');
            }

            // Получаем CSRF токен
            const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';

            const response = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    subscription: sub.toJSON()
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка сервера');
            }

            console.log('[PushManager] Подписка отправлена на сервер:', data.message);

        } catch (error) {
            console.error('[PushManager] Ошибка отправки подписки:', error);
            throw error;
        }
    }

    async unsubscribeFromServer() {
        try {
            // Получаем CSRF токен
            const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';

            const response = await fetch('/api/push/unsubscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    endpoint: this.subscription ? this.subscription.endpoint : null
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Ошибка сервера');
            }

            console.log('[PushManager] Отписка отправлена на сервер:', data.message);

        } catch (error) {
            console.error('[PushManager] Ошибка отправки отписки:', error);
            throw error;
        }
    }

    async sendTestNotification() {
        try {
            // Получаем CSRF токен
            const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';

            const response = await fetch('/api/push/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            const data = await response.json();

            if (response.ok) {
                console.log('[PushManager] Тестовое уведомление отправлено');
            } else {
                console.warn('[PushManager] Ошибка отправки тестового уведомления:', data.error);
            }

        } catch (error) {
            console.error('[PushManager] Ошибка отправки тестового уведомления:', error);
        }
    }

    // Утилиты
    urlBase64ToUint8Array(base64String) {
        if (!base64String || typeof base64String !== 'string') {
            throw new Error('VAPID ключ не определен или имеет неверный формат');
        }

        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }

        return outputArray;
    }

    playNotificationSound(soundUrlToPlay = null) {
        try {
            const finalSoundUrl = soundUrlToPlay || this.notificationSounds.default;
            console.log(`[PushManager] Попытка воспроизведения звука: ${finalSoundUrl}`);
            const audio = new Audio(finalSoundUrl);
            audio.volume = 0.5;
            audio.play().catch(error => {
                console.warn(`[PushManager] Не удалось воспроизвести звук: ${finalSoundUrl}`, error);
            });
        } catch (error) {
            console.warn('[PushManager] Ошибка воспроизведения звука:', error);
        }
    }

    // UI уведомления
    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showUnsupportedMessage() {
        this.showToast('Ваш браузер не поддерживает пуш-уведомления', 'warning');
    }

    showToast(message, type = 'info') {
        // Создаем toast уведомление
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        // Добавляем стили
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${this.getToastColor(type)};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            animation: slideInRight 0.3s ease-out;
        `;

        document.body.appendChild(toast);

        // Удаляем через 5 секунд
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 5000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }

    getToastColor(type) {
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        return colors[type] || colors.info;
    }

    // Обработчик сообщений от Service Worker
    setupServiceWorkerMessageHandler() {
        if (navigator.serviceWorker) {
            navigator.serviceWorker.onmessage = (event) => {
                console.log('[PushManager] Получено сообщение от SW:', event.data);
                if (event.data && event.data.type === 'PLAY_SOUND') {
                    if (event.data.soundUrl) {
                        this.playNotificationSound(event.data.soundUrl);
                    } else {
                        // Если URL не указан, используем звук по умолчанию
                        this.playNotificationSound();
                    }
                }
            };
            console.log('[PushManager] Обработчик сообщений от Service Worker настроен.');
        }
    }
}

// CSS анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .push-notification-btn {
        margin: 0 5px;
        font-size: 14px;
        padding: 8px 12px;
        border-radius: 6px;
        transition: all 0.3s ease;
    }

    .push-notification-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .push-status-indicator {
        margin-left: 5px;
        font-size: 16px;
    }

    .toast-content {
        display: flex;
        align-items: center;
        gap: 8px;
    }
`;
document.head.appendChild(style);

// Создаем глобальный объект с методами для внешнего использования
window.PushNotificationManager = {
    // Ссылка на класс для создания новых экземпляров
    Manager: PushNotificationManager,

    // Глобальный экземпляр
    instance: null,

    // Метод инициализации
    async init() {
        if (!this.instance) {
            console.log('[PushManager Global] Создание нового экземпляра...');
            this.instance = new this.Manager();
        }

        await this.instance.init();
        return this.instance;
    },

    // Проксирующие методы для удобства
    async getStatus() {
        if (!this.instance || !this.instance.isInitialized) {
            await this.init();
        }
        return {
            enabled: this.instance.isSubscribed,
            supported: this.instance.isSupported
        };
    },

    async subscribe() {
        if (!this.instance || !this.instance.isInitialized) {
            await this.init();
        }
        try {
            await this.instance.subscribe();
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    },

    async unsubscribe() {
        if (!this.instance || !this.instance.isInitialized) {
            await this.init();
        }
        try {
            await this.instance.unsubscribe();
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
};

// Инициализация только по запросу, без автоматической инициализации
// Это позволяет избежать конфликтов при множественных вызовах
console.log('[PushManager] Модуль загружен, инициализация по требованию');
