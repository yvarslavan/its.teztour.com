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

        // Элементы интерфейса - БОЛЬШЕ НЕ ИСПОЛЬЗУЮТСЯ ЗДЕСЬ
        // this.pushButton = null;
        // this.statusIndicator = null;

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

            // Инициализируем UI - БОЛЬШЕ НЕ ВЫЗЫВАЕТСЯ ОТСЮДА
            // console.log('[PushManager] Инициализация UI...');
            // this.initializeUI();

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
            console.log('[PushManager] Начало registerServiceWorker()');
            const swScope = '/';

            // Проверяем наличие существующей регистрации
            console.log(`[PushManager] Попытка получить существующую регистрацию SW для scope: ${swScope}`);
            const existingRegistration = await navigator.serviceWorker.getRegistration(swScope);
            if (existingRegistration) {
                console.log('[PushManager] Найдена существующая регистрация SW, scope:', existingRegistration.scope, 'Попытка отмены регистрации...');
                const unregisterResult = await existingRegistration.unregister();
                console.log('[PushManager] Результат отмены регистрации:', unregisterResult ? 'Успешно' : 'Неуспешно или нет активного SW для отмены');
                if (!unregisterResult) {
                    console.warn('[PushManager] Не удалось отменить регистрацию существующего Service Worker. Это может помешать регистрации нового.');
                }
            } else {
                console.log('[PushManager] Существующая регистрация SW не найдена для scope:', swScope);
            }

            const swPath = '/sw.js';
            console.log(`[PushManager] Попытка регистрации НОВОГО Service Worker. Путь: ${swPath}, Scope: ${swScope}`);

            try {
                // Прямой try...catch вокруг register
                console.log('[PushManager] Перед вызовом navigator.serviceWorker.register...');
                this.registration = await navigator.serviceWorker.register(swPath, {
                    scope: swScope
                });
                console.log('[PushManager] navigator.serviceWorker.register ВЫПОЛНЕН. Регистрация:', this.registration);
            } catch (registerError) {
                console.error('[PushManager] КРИТИЧЕСКАЯ ОШИБКА непосредственно при вызове navigator.serviceWorker.register:', registerError);
                this.registration = null; // Убедимся, что registration сброшен
                throw registerError; // Перебрасываем ошибку, чтобы ее было видно выше
            }

            if (!this.registration) {
                console.error('[PushManager] Регистрация Service Worker не удалась, this.registration остался null ПОСЛЕ вызова register.');
                throw new Error('Service Worker registration failed, this.registration is null');
            }

            console.log('[PushManager] Проверка состояния Service Worker (this.registration):', this.registration);
            if (this.registration.installing) {
                console.log('[PushManager] Service Worker в состоянии installing. Ожидание активации...');
                await this.waitForServiceWorker(this.registration.installing);
            } else if (this.registration.waiting) {
                console.log('[PushManager] Service Worker в состоянии waiting. Попытка активации через postMessage SKIP_WAITING...');
                this.registration.waiting.postMessage({type: 'SKIP_WAITING'});
                await this.waitForServiceWorker(this.registration.waiting);
            } else if (this.registration.active) {
                console.log('[PushManager] Service Worker уже в состоянии active.');
            }

            console.log('[PushManager] Попытка выполнить registration.update()...');
            await this.registration.update();
            console.log('[PushManager] registration.update() выполнен.');
            console.log('[PushManager] Service Worker успешно зарегистрирован и обновлен.');

        } catch (error) {
            console.error('[PushManager] ОБЩАЯ ОШИБКА в registerServiceWorker (возможно, после успешной регистрации, но до ее полной активации):', error);
            this.registration = null; // Важно сбросить, если что-то пошло не так
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

    async toggleSubscription() { // ЭТОТ МЕТОД БОЛЬШЕ НЕ ИСПОЛЬЗУЕТСЯ И МОЖЕТ БЫТЬ УДАЛЕН,
                               // НО ДЛЯ БЕЗОПАСНОСТИ ОСТАВИМ ПОКА ЗАКОММЕНТИРОВАННЫМ ИЛИ УДАЛИМ ПОЗЖЕ
        /*
        try {
            // this.pushButton.disabled = true; // this.pushButton здесь больше нет

            if (this.isSubscribed) {
                await this.unsubscribe();
            } else {
                await this.subscribe();
            }

        } catch (error) {
            console.error('[PushManager] Ошибка переключения подписки:', error);
            this.showError('Ошибка при изменении настроек уведомлений');
        } finally {
            // this.pushButton.disabled = false; // this.pushButton здесь больше нет
        }
        */
        console.warn("[PushManager] toggleSubscription больше не должен вызываться напрямую из этого класса.");
    }

    async subscribe() {
        try {
            console.log('[PushManager] Запрос разрешения на уведомления...');

            // Проверяем, что VAPID ключ получен
            if (!this.vapidPublicKey) {
                throw new Error('VAPID ключ не получен. Попробуйте обновить страницу.');
            }

            // УПРОЩЕННЫЙ ЗАПРОС РАЗРЕШЕНИЯ (без кастомного таймаута)
            console.log('[PushManager] Вызов Notification.requestPermission(). Ожидание ответа от пользователя...');
            let permission;
            try {
                permission = await Notification.requestPermission();
                console.log('[PushManager] Notification.requestPermission() завершен. Результат:', permission);
            } catch (rpError) {
                console.error('[PushManager] Ошибка при вызове Notification.requestPermission():', rpError);
                throw new Error('Ошибка при запросе разрешения на уведомления: ' + rpError.message);
            }
            // КОНЕЦ УПРОЩЕННОГО ЗАПРОСА

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
            // this.updateUI(); // УДАЛЕНО - account.html обновит UI

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
            // this.updateUI(); // УДАЛЕНО - account.html обновит UI

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
            audio.volume = 0.5; // Можно поставить 1.0 для теста
            console.log('[PushManager] Audio объект создан:', audio);
            const playPromise = audio.play();

            if (playPromise !== undefined) {
                playPromise.then(_ => {
                    console.log(`[PushManager] Воспроизведение звука ${finalSoundUrl} началось.`);
                }).catch(error => {
                    console.warn(`[PushManager] Не удалось воспроизвести звук ${finalSoundUrl}:`, error);
                    // Здесь можно добавить более явное уведомление пользователю или UI фидбек
                    // Например, если это из-за отсутствия взаимодействия пользователя:
                    if (error.name === 'NotAllowedError') {
                        console.warn('[PushManager] Воспроизведение звука заблокировано браузером. Требуется взаимодействие пользователя со страницей.');
                        // Можно показать маленький UI элемент, предлагающий кликнуть для включения звука
                    }
                });
            }
        } catch (error) {
            console.warn('[PushManager] Ошибка при попытке воспроизведения звука:', error);
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
                    console.log('[PushManager] Сообщение PLAY_SOUND получено. URL:', event.data.soundUrl);
                    if (event.data.soundUrl) {
                        this.playNotificationSound(event.data.soundUrl);
                    } else {
                        console.log('[PushManager] URL звука не указан, используем звук по умолчанию.');
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
