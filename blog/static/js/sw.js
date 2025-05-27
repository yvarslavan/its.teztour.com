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
    console.log('[SW] Установка Service Worker начата');

    event.waitUntil(
        Promise.all([
            // Кешируем необходимые файлы
            caches.open(CACHE_NAME).then(function(cache) {
                console.log('[SW] Кеширование файлов...');
                return cache.addAll([
                    '/static/sounds/notification.mp3',
                    '/static/img/notification_icon.png',
                    '/static/img/notification_badge.png',
                    '/static/img/view_icon.png'
                ]).then(() => {
                    console.log('[SW] Файлы успешно кешированы');
                });
            }),

            // Принудительно активируем новый Service Worker
            self.skipWaiting().then(() => {
                console.log('[SW] skipWaiting выполнен успешно');
            })
        ]).then(() => {
            console.log('[SW] Установка Service Worker завершена успешно');
        })
    );
});

// Активация Service Worker
self.addEventListener('activate', function(event) {
    console.log('[SW] Активация Service Worker начата');

    event.waitUntil(
        Promise.all([
            // Очищаем старый кеш
            caches.keys().then(function(cacheNames) {
                return Promise.all(
                    cacheNames.map(function(cacheName) {
                        if (cacheName !== CACHE_NAME) {
                            console.log('[SW] Удаление старого кеша:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),

            // Берем контроль над всеми клиентами
            self.clients.claim().then(() => {
                console.log('[SW] Контроль над клиентами получен');
            })
        ]).then(() => {
            console.log('[SW] Активация Service Worker завершена успешно');
        })
    );
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
        requireInteraction: true,
        silent: false  // Всегда включаем звук по умолчанию
    };

    // Парсим данные если они есть
    if (event.data) {
        try {
            const pushData = event.data.json();
            console.log('[SW] Данные пуш-уведомления:', pushData);

            notificationData = {
                ...notificationData,  // Сохраняем значения по умолчанию
                title: pushData.title || notificationData.title,
                body: pushData.body || notificationData.body,
                icon: pushData.icon || notificationData.icon,
                badge: pushData.badge || notificationData.badge,
                tag: pushData.tag || `notification_${Date.now()}`,
                data: pushData.data || notificationData.data,
                actions: pushData.actions || notificationData.actions,
                requireInteraction: pushData.requireInteraction !== undefined ?
                    pushData.requireInteraction : notificationData.requireInteraction,
                vibrate: [200, 100, 200],  // Добавляем вибрацию
                silent: false  // Всегда включаем звук
            };

            // Для тестовых уведомлений добавляем специальные настройки
            if (pushData.data && pushData.data.type === 'test') {
                notificationData.actions = [
                    {
                        action: 'view',
                        title: 'Открыть',
                        icon: '/static/img/view_icon.png'
                    }
                ];
                notificationData.requireInteraction = false;
                notificationData.silent = false;  // Явно включаем звук для тестовых уведомлений
                notificationData.vibrate = [200, 100, 200, 100, 200];  // Усиленная вибрация для теста
            }
        } catch (error) {
            console.error('[SW] Ошибка парсинга данных пуш-уведомления:', error);
        }
    }

    console.log('[SW] Отображение уведомления:', notificationData);

    // Показываем уведомление и воспроизводим звук
    const showNotification = self.registration.showNotification(
        notificationData.title,
        notificationData
    );

    // Отправляем сообщение для воспроизведения звука
    const playSound = self.clients.matchAll().then(clients => {
        console.log('[SW] Найдено клиентов для отправки звука:', clients.length);
        const soundUrl = '/static/sounds/notification.mp3';
        clients.forEach(client => {
            console.log('[SW] Отправка сообщения клиенту для воспроизведения звука');
            client.postMessage({
                type: 'PLAY_SOUND',
                soundUrl: soundUrl
            });
        });
    });

    // Ждем выполнения обоих промисов
    event.waitUntil(Promise.all([showNotification, playSound]));
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
    // Проверяем, что запрос относится к нашему домену
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    // Кешируем только GET запросы для статических ресурсов уведомлений
    if (event.request.method !== 'GET' ||
        !(event.request.url.includes('/static/sounds/') ||
          event.request.url.includes('/static/img/notification') ||
          event.request.url.includes('/static/img/view_icon'))) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    console.log('[SW] Возвращаем ответ из кеша:', event.request.url);
                    return response;
                }

                console.log('[SW] Кеш не найден, загружаем из сети:', event.request.url);
                return fetch(event.request).then(function(networkResponse) {
                    if (!networkResponse || networkResponse.status !== 200) {
                        console.warn('[SW] Получен некорректный ответ от сети:', networkResponse?.status);
                        return networkResponse;
                    }

                    // Кешируем успешный ответ
                    return caches.open(CACHE_NAME).then(function(cache) {
                        console.log('[SW] Кеширование ответа для:', event.request.url);
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    }).catch(function(error) {
                        console.error('[SW] Ошибка кеширования:', error);
                        return networkResponse;
                    });
                }).catch(function(error) {
                    console.error('[SW] Ошибка загрузки из сети:', error);
                    throw error;
                });
            })
    );
});

// Обработка ошибок
self.addEventListener('error', function(event) {
    console.error('[SW] Ошибка Service Worker:', event.error);
});

self.addEventListener('unhandledrejection', function(event) {
    console.error('[SW] Необработанное отклонение промиса:', event.reason);
});

console.log('[SW] Service Worker загружен и готов к работе');
