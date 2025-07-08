/**
 * Отладочный модуль для диагностики пуш-уведомлений
 * Использование: PushDebug.runFullDiagnostic() в консоли браузера
 */

window.PushDebug = {

    async runFullDiagnostic() {
        console.log('🔍 Запуск полной диагностики пуш-уведомлений...');
        console.log('=' * 60);

        const results = {
            browserSupport: await this.checkBrowserSupport(),
            permissions: await this.checkPermissions(),
            serviceWorker: await this.checkServiceWorker(),
            vapidKey: await this.checkVapidKey(),
            subscription: await this.checkSubscription(),
            serverStatus: await this.checkServerStatus()
        };

        console.log('📊 Результаты диагностики:');
        console.table(results);

        this.generateRecommendations(results);

        return results;
    },

    async checkBrowserSupport() {
        console.log('1️⃣ Проверка поддержки браузера...');

        const support = {
            serviceWorker: 'serviceWorker' in navigator,
            pushManager: 'PushManager' in window,
            notifications: 'Notification' in window
        };

        const isSupported = support.serviceWorker && support.pushManager && support.notifications;

        console.log(`   Service Worker: ${support.serviceWorker ? '✅' : '❌'}`);
        console.log(`   Push Manager: ${support.pushManager ? '✅' : '❌'}`);
        console.log(`   Notifications: ${support.notifications ? '✅' : '❌'}`);
        console.log(`   Общая поддержка: ${isSupported ? '✅' : '❌'}`);

        return {
            supported: isSupported,
            details: support
        };
    },

    async checkPermissions() {
        console.log('2️⃣ Проверка разрешений...');

        if (!('Notification' in window)) {
            console.log('   ❌ Notifications API недоступен');
            return { permission: 'unavailable' };
        }

        const permission = Notification.permission;
        const icon = permission === 'granted' ? '✅' : permission === 'denied' ? '❌' : '⚠️';

        console.log(`   Статус разрешения: ${icon} ${permission}`);

        if (permission === 'denied') {
            console.log('   💡 Для сброса разрешений:');
            console.log('      - Edge: edge://settings/content/notifications');
            console.log('      - Chrome: chrome://settings/content/notifications');
            console.log('      - Firefox: about:preferences#privacy');
        }

        return { permission };
    },

    async checkServiceWorker() {
        console.log('3️⃣ Проверка Service Worker...');

        if (!('serviceWorker' in navigator)) {
            console.log('   ❌ Service Worker не поддерживается');
            return { supported: false };
        }

        try {
            const registrations = await navigator.serviceWorker.getRegistrations();
            const swRegistration = registrations.find(reg =>
                reg.scope.includes('/static/js/') || reg.scope.includes('sw.js')
            );

            if (!swRegistration) {
                console.log('   ❌ Service Worker не зарегистрирован');
                return { registered: false };
            }

            const state = swRegistration.active ? swRegistration.active.state : 'inactive';
            console.log(`   ✅ Service Worker зарегистрирован`);
            console.log(`   Состояние: ${state}`);
            console.log(`   Scope: ${swRegistration.scope}`);

            return {
                registered: true,
                state,
                scope: swRegistration.scope,
                registration: swRegistration
            };

        } catch (error) {
            console.log(`   ❌ Ошибка проверки Service Worker: ${error.message}`);
            return { error: error.message };
        }
    },

    async checkVapidKey() {
        console.log('4️⃣ Проверка VAPID ключа...');

        try {
            const response = await fetch('/api/vapid-public-key');

            if (!response.ok) {
                console.log(`   ❌ Ошибка HTTP: ${response.status}`);
                return { error: `HTTP ${response.status}` };
            }

            const data = await response.json();

            if (!data.publicKey) {
                console.log('   ❌ VAPID ключ отсутствует в ответе');
                return { error: 'Ключ отсутствует' };
            }

            console.log(`   ✅ VAPID ключ получен: ${data.publicKey.substring(0, 20)}...`);
            return {
                available: true,
                key: data.publicKey.substring(0, 20) + '...'
            };

        } catch (error) {
            console.log(`   ❌ Ошибка получения VAPID ключа: ${error.message}`);
            return { error: error.message };
        }
    },

    async checkSubscription() {
        console.log('5️⃣ Проверка подписки...');

        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();

            if (!subscription) {
                console.log('   ⚠️ Локальная подписка отсутствует');
                return { local: false };
            }

            console.log('   ✅ Локальная подписка найдена');
            console.log(`   Endpoint: ${subscription.endpoint.substring(0, 50)}...`);

            return {
                local: true,
                endpoint: subscription.endpoint.substring(0, 50) + '...',
                keys: Object.keys(subscription.toJSON().keys)
            };

        } catch (error) {
            console.log(`   ❌ Ошибка проверки подписки: ${error.message}`);
            return { error: error.message };
        }
    },

    async checkServerStatus() {
        console.log('6️⃣ Проверка статуса на сервере...');

        try {
            const response = await fetch('/api/push/status');

            if (response.status === 401) {
                console.log('   ⚠️ Требуется авторизация');
                return { error: 'Не авторизован' };
            }

            if (!response.ok) {
                console.log(`   ❌ Ошибка HTTP: ${response.status}`);
                return { error: `HTTP ${response.status}` };
            }

            const data = await response.json();

            console.log(`   Включены на сервере: ${data.enabled ? '✅' : '❌'}`);
            console.log(`   Количество подписок: ${data.subscriptions_count}`);

            return {
                enabled: data.enabled,
                subscriptions: data.subscriptions_count,
                hasSubscriptions: data.has_subscriptions
            };

        } catch (error) {
            console.log(`   ❌ Ошибка проверки статуса: ${error.message}`);
            return { error: error.message };
        }
    },

    generateRecommendations(results) {
        console.log('💡 Рекомендации:');

        if (!results.browserSupport.supported) {
            console.log('   🔄 Обновите браузер до последней версии');
            return;
        }

        if (results.permissions.permission === 'denied') {
            console.log('   🔓 Сбросьте разрешения на уведомления в настройках браузера');
            console.log('   📖 См. инструкции в PUSH_NOTIFICATIONS_TROUBLESHOOTING.md');
            return;
        }

        if (results.permissions.permission !== 'granted') {
            console.log('   ✋ Предоставьте разрешение на уведомления');
            return;
        }

        if (!results.serviceWorker.registered) {
            console.log('   🔄 Перезагрузите страницу для регистрации Service Worker');
            return;
        }

        if (!results.vapidKey.available) {
            console.log('   ⚙️ Проверьте конфигурацию VAPID ключей на сервере');
            return;
        }

        if (results.serverStatus.error === 'Не авторизован') {
            console.log('   🔑 Авторизуйтесь в системе');
            return;
        }

        if (!results.subscription.local && !results.serverStatus.enabled) {
            console.log('   ▶️ Нажмите кнопку "Включить уведомления"');
            return;
        }

        if (results.subscription.local && results.serverStatus.enabled) {
            console.log('   ✅ Все настроено корректно!');
            console.log('   🧪 Попробуйте отправить тестовое уведомление');
            return;
        }

        console.log('   🔍 Требуется дополнительная диагностика');
    },

    async testNotification() {
        console.log('🧪 Отправка тестового уведомления...');

        try {
            const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');

            if (!csrfToken) {
                console.log('   ❌ CSRF токен не найден');
                return { error: 'CSRF токен отсутствует' };
            }

            const response = await fetch('/api/push/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            });

            const data = await response.json();

            if (response.ok) {
                console.log('   ✅ Тестовое уведомление отправлено');
                console.log(`   Ответ: ${data.message}`);

                // Дополнительная проверка Service Worker
                await this.checkServiceWorkerMessages();

                return { success: true, message: data.message };
            } else {
                console.log(`   ❌ Ошибка: ${data.error}`);
                return { error: data.error };
            }

        } catch (error) {
            console.log(`   ❌ Ошибка отправки: ${error.message}`);
            return { error: error.message };
        }
    },

    async checkServiceWorkerMessages() {
        console.log('📡 Проверка сообщений Service Worker...');

        if (!('serviceWorker' in navigator)) {
            console.log('   ❌ Service Worker не поддерживается');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.ready;

            // Проверяем активный Service Worker
            if (registration.active) {
                console.log('   ✅ Service Worker активен');
                console.log(`   Состояние: ${registration.active.state}`);
                console.log(`   URL: ${registration.active.scriptURL}`);
            } else {
                console.log('   ❌ Service Worker не активен');
            }

            // Проверяем подписку
            const subscription = await registration.pushManager.getSubscription();
            if (subscription) {
                console.log('   ✅ Push подписка активна');
                console.log(`   Endpoint: ${subscription.endpoint.substring(0, 50)}...`);
            } else {
                console.log('   ❌ Push подписка отсутствует');
            }

        } catch (error) {
            console.log(`   ❌ Ошибка проверки SW: ${error.message}`);
        }
    },

    async testLocalNotification() {
        console.log('🔔 Тест локального уведомления...');

        if (!('Notification' in window)) {
            console.log('   ❌ Notifications API недоступен');
            return { error: 'API недоступен' };
        }

        if (Notification.permission !== 'granted') {
            console.log('   ❌ Разрешение не предоставлено');
            return { error: 'Нет разрешения' };
        }

        try {
            const notification = new Notification('Тест локального уведомления', {
                body: 'Это тестовое уведомление создано локально в браузере',
                icon: '/static/img/notification_icon.png',
                badge: '/static/img/notification_badge.png',
                tag: 'local-test',
                requireInteraction: false
            });

            console.log('   ✅ Локальное уведомление создано');

            notification.onclick = function() {
                console.log('   👆 Клик по локальному уведомлению');
                notification.close();
            };

            // Автоматически закрываем через 5 секунд
            setTimeout(() => {
                notification.close();
                console.log('   ⏰ Локальное уведомление закрыто автоматически');
            }, 5000);

            return { success: true };

        } catch (error) {
            console.log(`   ❌ Ошибка создания уведомления: ${error.message}`);
            return { error: error.message };
        }
    },

    async checkNotificationSettings() {
        console.log('⚙️ Проверка настроек уведомлений...');

        // Проверяем разрешения
        console.log(`   Разрешение: ${Notification.permission}`);

        // Проверяем максимальные действия
        if ('maxActions' in Notification.prototype) {
            console.log(`   Максимум действий: ${Notification.maxActions}`);
        }

        // Проверяем поддержку различных свойств
        const testNotification = {
            body: 'test',
            icon: 'test',
            badge: 'test',
            image: 'test',
            tag: 'test',
            data: {},
            requireInteraction: true,
            silent: false,
            vibrate: [200, 100, 200],
            actions: []
        };

        const supportedFeatures = {};

        for (const [key, value] of Object.entries(testNotification)) {
            try {
                const tempNotif = new Notification('Test', { [key]: value });
                supportedFeatures[key] = '✅';
                tempNotif.close();
            } catch (error) {
                supportedFeatures[key] = '❌';
            }
        }

        console.log('   Поддерживаемые функции:');
        console.table(supportedFeatures);

        return supportedFeatures;
    },

    async resetSubscription() {
        console.log('🔄 Сброс подписки...');

        try {
            // Отписываемся локально
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();

            if (subscription) {
                await subscription.unsubscribe();
                console.log('   ✅ Локальная подписка удалена');
            }

            // Отписываемся на сервере
            const csrfToken = document.querySelector('meta[name=csrf-token]')?.getAttribute('content');

            if (csrfToken) {
                const response = await fetch('/api/push/unsubscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    }
                });

                if (response.ok) {
                    console.log('   ✅ Подписка удалена с сервера');
                } else {
                    console.log('   ⚠️ Ошибка удаления с сервера');
                }
            }

            console.log('   💡 Теперь можно заново включить уведомления');
            return { success: true };

        } catch (error) {
            console.log(`   ❌ Ошибка сброса: ${error.message}`);
            return { error: error.message };
        }
    },

    showHelp() {
        console.log('📚 Доступные команды PushDebug:');
        console.log('');
        console.log('PushDebug.runFullDiagnostic()     - Полная диагностика системы');
        console.log('PushDebug.testNotification()      - Отправить тестовое уведомление');
        console.log('PushDebug.testLocalNotification() - Тест локального уведомления');
        console.log('PushDebug.checkNotificationSettings() - Проверить настройки уведомлений');
        console.log('PushDebug.resetSubscription()     - Сбросить подписку');
        console.log('PushDebug.checkPermissions()      - Проверить разрешения');
        console.log('PushDebug.checkServiceWorker()    - Проверить Service Worker');
        console.log('PushDebug.showHelp()              - Показать эту справку');
        console.log('');
        console.log('💡 Для диагностики проблем с отображением:');
        console.log('1. PushDebug.testLocalNotification() - проверить локальные уведомления');
        console.log('2. PushDebug.checkNotificationSettings() - проверить настройки браузера');
        console.log('3. PushDebug.runFullDiagnostic() - полная диагностика');
    }
};

// Автоматически показываем справку при загрузке
console.log('🔧 Модуль диагностики пуш-уведомлений загружен');
console.log('💡 Выполните PushDebug.showHelp() для просмотра команд');
console.log('🚀 Или сразу PushDebug.runFullDiagnostic() для диагностики');
