console.log('[SW] Service Worker v1.1 STARTED');

self.addEventListener('install', (event) => {
  console.log('[SW] Event: install');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Event: activate');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Не обрабатываем fetch для простоты
});

self.addEventListener('push', function(event) {
  try {
    console.log('[SW] Push event received:', new Date().toISOString());

    // Базовые значения для уведомления по умолчанию
    let notificationTitle = 'Push-уведомление';
    let notificationOptions = {
      body: 'Получено новое уведомление',
      icon: '/static/img/push-icon.png',
      data: {
        url: '/',
        timestamp: Date.now()
      },
      tag: 'helpdesk-notification-' + Date.now(),
      timestamp: Date.now()
    };

    // Проверяем наличие данных
    if (event.data) {
      try {
        const pushDataText = event.data.text();
        console.log('[SW] Raw push data length:', pushDataText ? pushDataText.length : 0);
        console.log('[SW] Raw push data preview:', pushDataText ? pushDataText.substring(0, 100) + '...' : 'empty');

        if (pushDataText && pushDataText.trim() !== '') {
          try {
            const parsedData = JSON.parse(pushDataText);
            console.log('[SW] JSON parsed successfully');

            // Обновляем заголовок и текст
            if (parsedData.title) {
              notificationTitle = parsedData.title;
              console.log('[SW] Using title:', notificationTitle);
            }

            if (parsedData.message) {
              notificationOptions.body = parsedData.message;
              console.log('[SW] Using message:', notificationOptions.body.substring(0, 50) + '...');
            }

            // Обрабатываем данные
            if (parsedData.data) {
              notificationOptions.data = parsedData.data;
              console.log('[SW] Using data object:', JSON.stringify(notificationOptions.data).substring(0, 100) + '...');

              // Приоритет иконки: data.icon -> icon -> default
              if (parsedData.data.icon) {
                notificationOptions.icon = parsedData.data.icon;
                console.log('[SW] Using icon from data:', notificationOptions.icon);
              }
            }

            // Запасной вариант для иконки
            if (parsedData.icon) {
              notificationOptions.icon = parsedData.icon;
              console.log('[SW] Using icon from root:', notificationOptions.icon);
            }

          } catch (jsonError) {
            console.error('[SW] JSON parse error:', jsonError);
            console.error('[SW] Problem with data:', pushDataText.substring(0, 200));
          }
        } else {
          console.log('[SW] Empty push data, using defaults');
        }
      } catch (dataError) {
        console.error('[SW] Error reading push data:', dataError);
      }
    } else {
      console.log('[SW] No data in push event, using defaults');
    }

    // Отображаем уведомление
    return event.waitUntil(
      self.registration.showNotification(notificationTitle, notificationOptions)
        .then(() => {
          console.log('[SW] Notification shown successfully');
          // Отправляем сообщение клиенту для воспроизведения звука
          return self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true
          });
        })
        .then((clients) => {
          if (clients && clients.length) {
            console.log('[SW] Found', clients.length, 'clients to notify');
            clients.forEach(client => {
              client.postMessage({
                type: 'PUSH_RECEIVED',
                title: notificationTitle,
                options: notificationOptions,
                body: notificationOptions.body,
                icon: notificationOptions.icon,
                url: notificationOptions.data.url,
                issue_id: notificationOptions.data.issue_id,
                notification_type: notificationOptions.data.notification_type,
                raw_data: notificationOptions.data
              });
            });
          } else {
            console.log('[SW] No clients found to notify');
          }
        })
        .catch(error => {
          console.error('[SW] Error showing notification:', error);
        })
    );
  } catch (globalError) {
    console.error('[SW] Global error in push handler:', globalError);
    // Пытаемся показать хотя бы простое уведомление при любой ошибке
    return event.waitUntil(
      self.registration.showNotification('Системное уведомление', {
        body: 'Получено новое уведомление (с ошибкой обработки)',
        icon: '/static/img/push-icon.png'
      })
    );
  }
});

// Обработчик клика по уведомлению
self.addEventListener('notificationclick', function(event) {
  console.log('[SW] Notification click received');

  // Закрываем уведомление
  event.notification.close();

  // Извлекаем URL для перехода
  let targetUrl = '/';

  try {
    if (event.notification.data && event.notification.data.url) {
      targetUrl = event.notification.data.url;
      console.log('[SW] Target URL from notification data:', targetUrl);
    }
  } catch (error) {
    console.error('[SW] Error extracting URL from notification data:', error);
  }

  // Открываем URL при клике
  event.waitUntil(
    clients.matchAll({ type: 'window' })
      .then(windowClients => {
        // Проверяем, есть ли уже открытое окно
        for (const client of windowClients) {
          if (client.url === targetUrl && 'focus' in client) {
            console.log('[SW] Focusing existing window');
            return client.focus();
          }
        }

        // Открываем новое окно
        console.log('[SW] Opening new window with URL:', targetUrl);
        if (clients.openWindow) {
          return clients.openWindow(targetUrl);
        }
      })
      .catch(error => {
        console.error('[SW] Error handling notification click:', error);
      })
  );
});

console.log('[SW] Service Worker v1.1 LOADED SUCCESSFULLY');
