console.log('[SW] Файл sw.js НАЧАЛ выполнение');

/**
 * Service Worker для обработки пуш-уведомлений
 */

const CACHE_NAME = 'helpdesk-notifications-v1';
const NOTIFICATION_SOUNDS = {
    default: '/static/sounds/notification.mp3'
};

// Установка Service Worker
self.addEventListener('install', function(event) {
    console.log('[SW] Установка Service Worker');

    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            console.log('[SW] Кеш открыт');
            return cache.addAll([
                '/static/sounds/notification.mp3',
                '/static/img/notification_icon.png',
                '/static/img/notification_badge.png',
                '/static/img/view_icon.png'
            ]);
        })
    );

    // Принудительно активируем новый Service Worker
    self.skipWaiting();
});

// Активация Service Worker
self.addEventListener('activate', function(event) {
    console.log('[SW] Активация Service Worker');

    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Удаление старого кеша:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );

    // Берем контроль над всеми клиентами
    return self.clients.claim();
});

// Обработка пуш-уведомлений
self.addEventListener('push', function(event) {
    console.log('[SW] Получено пуш-событие:', event);

    let notificationData = {
        title: 'Новое уведомление',
        body: 'У вас есть новое уведомление',
        icon: '/static/img/notification_icon.png',
        badge: '/static/img/notification_badge.png',
        tag: 'default',
        data: {},
        actions: [],
        requireInteraction: true
    };

    // Парсим данные если они есть
    if (event.data) {
        try {
            const pushData = event.data.json();
            console.log('[SW] Данные пуш-уведомления:', pushData);

            notificationData = {
                title: pushData.title || notificationData.title,
                body: pushData.body || notificationData.body,
                icon: pushData.icon || notificationData.icon,
                badge: pushData.badge || notificationData.badge,
                tag: pushData.tag || notificationData.tag,
                data: pushData.data || notificationData.data,
                actions: pushData.actions || notificationData.actions,
                requireInteraction: pushData.requireInteraction !== undefined ? pushData.requireInteraction : notificationData.requireInteraction,
                vibrate: pushData.vibrate || [200, 100, 200]
            };
        } catch (error) {
            console.error('[SW] Ошибка парсинга данных пуш-уведомления:', error);
        }
    }

    console.log('[SW] Отображение уведомления:', notificationData);

    // Показываем уведомление
    const notificationPromise = self.registration.showNotification(notificationData.title, {
        body: notificationData.body,
        icon: notificationData.icon,
        badge: notificationData.badge,
        tag: notificationData.tag,
        data: notificationData.data,
        actions: notificationData.actions,
        requireInteraction: notificationData.requireInteraction,
        vibrate: notificationData.vibrate
    });

    // Отправляем сообщение клиенту для воспроизведения звука
    const soundPromise = self.clients.matchAll().then(clients => {
        console.log('[SW] Найдено клиентов для отправки звука:', clients.length);

        const soundUrl = notificationData.data.type === 'comment_added'
            ? '/static/sounds/comment_added.mp3'
            : notificationData.data.type === 'status_change'
            ? '/static/sounds/status_change.mp3'
            : '/static/sounds/default.mp3';

        clients.forEach(client => {
            console.log('[SW] Отправка сообщения клиенту для воспроизведения звука:', soundUrl);
            client.postMessage({
                type: 'PLAY_SOUND',
                soundUrl: soundUrl
            });
        });
    });

    event.waitUntil(Promise.all([notificationPromise, soundPromise]));
});

// Обработка кликов по уведомлениям
self.addEventListener('notificationclick', function(event) {
    console.log('[SW] Клик по уведомлению:', event);

    const notification = event.notification;
    const action = event.action;
    const data = notification.data || {};

    // Закрываем уведомление
    notification.close();

    if (action === 'close') {
        console.log('[SW] Уведомление закрыто пользователем');
        return;
    }

    // Определяем URL для перехода
    let targetUrl = '/';

    if (action === 'view' || !action) {
        if (data.url) {
            targetUrl = data.url;
        } else if (data.issue_id) {
            targetUrl = `/my-issues/${data.issue_id}`;
        } else {
            targetUrl = '/notifications';
        }
    }

    console.log('[SW] Переход по URL:', targetUrl);

    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(function(clientList) {
            // Ищем открытое окно с нашим сайтом
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                const clientUrl = new URL(client.url);
                const targetUrlObj = new URL(targetUrl, self.location.origin);

                if (clientUrl.origin === targetUrlObj.origin) {
                    // Фокусируемся на существующем окне и переходим на нужную страницу
                    return client.focus().then(function() {
                        return client.navigate(targetUrl);
                    });
                }
            }

            // Если подходящего окна нет, открываем новое
            return clients.openWindow(targetUrl);
        })
    );
});

// Обработка закрытия уведомлений
self.addEventListener('notificationclose', function(event) {
    console.log('[SW] Уведомление закрыто:', event.notification.tag);

    // Можно отправить аналитику о закрытии уведомления
    const data = event.notification.data || {};

    if (data.issue_id) {
        console.log('[SW] Закрыто уведомление для заявки:', data.issue_id);
    }
});

// Функция воспроизведения звука
async function playNotificationSound(type = 'default') {
    try {
        console.log('[SW] Попытка воспроизведения звука');

        // Используем единственный звук для всех типов уведомлений
        const soundUrl = NOTIFICATION_SOUNDS.default;

        // Проверяем, есть ли звук в кеше
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(soundUrl);

        if (cachedResponse) {
            console.log('[SW] Звук найден в кеше');

            // Отправляем сообщение всем клиентам для воспроизведения звука
            const clients = await self.clients.matchAll();
            clients.forEach(client => {
                client.postMessage({
                    type: 'PLAY_SOUND',
                    soundUrl: soundUrl,
                    soundType: 'default'
                });
            });
        } else {
            console.log('[SW] Звук не найден в кеше, пропускаем воспроизведение');
        }

    } catch (error) {
        console.error('[SW] Ошибка воспроизведения звука:', error);
    }
}

// Обработка сообщений от клиентов
self.addEventListener('message', function(event) {
    console.log('[SW] Получено сообщение:', event.data);

    const data = event.data;

    switch (data.type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;

        case 'GET_VERSION':
            event.ports[0].postMessage({
                version: CACHE_NAME
            });
            break;

        case 'CLEAR_CACHE':
            event.waitUntil(
                caches.delete(CACHE_NAME).then(() => {
                    event.ports[0].postMessage({
                        success: true
                    });
                })
            );
            break;

        default:
            console.log('[SW] Неизвестный тип сообщения:', data.type);
    }
});

// Обработка fetch запросов (для кеширования)
self.addEventListener('fetch', function(event) {
    // Кешируем только статические ресурсы уведомлений
    if (event.request.url.includes('/static/sounds/') ||
        event.request.url.includes('/static/img/notification') ||
        event.request.url.includes('/static/img/view_icon')) {

        event.respondWith(
            caches.match(event.request).then(function(response) {
                // Возвращаем из кеша или загружаем из сети
                return response || fetch(event.request).then(function(response) {
                    // Кешируем ответ для будущих запросов
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(function(cache) {
                        cache.put(event.request, responseClone);
                    });
                    return response;
                });
            })
        );
    }
});

// Обработка ошибок
self.addEventListener('error', function(event) {
    console.error('[SW] Ошибка Service Worker:', event.error);
});

self.addEventListener('unhandledrejection', function(event) {
    console.error('[SW] Необработанное отклонение промиса:', event.reason);
});

console.log('[SW] Service Worker загружен и готов к работе');
