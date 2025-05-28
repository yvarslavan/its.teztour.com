console.log('[SW] Minimal sw.js STARTED');

self.addEventListener('install', (event) => {
  console.log('[SW] Event: install');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Event: activate');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // console.log('[SW] Event: fetch', event.request.url);
  // Не обрабатываем fetch для простоты
});

self.addEventListener('push', function(event) {
  console.log('[SW] Minimal: Push event received. Event object:', event);

  let pushDataText = null;
  let parsedData = {};

  if (event.data) {
    try {
      pushDataText = event.data.text();
      console.log('[SW] Raw push data text:', pushDataText);
    } catch (e) {
      console.error('[SW] Error reading push data as text:', e);
    }

    try {
      // Попытка распарсить JSON, даже если pushDataText пуст (json() может обработать "")
      parsedData = event.data.json();
      console.log('[SW] Parsed push data (JSON):', parsedData);
    } catch (e) {
      console.error('[SW] Error parsing push data as JSON:', e);
      // Если JSON.parse падает, parsedData останется {}, как и инициализировано
      // В этом случае, используем pushDataText в теле уведомления, если он не пуст
    }
  } else {
    console.log('[SW] Push event.data is null or undefined.');
  }

  const title = parsedData.title || 'Push-уведомление';
  const options = {
    body: parsedData.message || 'Нет содержимого.',
    icon: parsedData.data?.icon || parsedData.icon || '/static/img/push-icon.png', // Use icon from payload.data, then payload.icon, or default
    data: parsedData.data || {} // Pass along any additional data
  };

  console.log(`[SW] Showing notification with title: "${title}", body: "${options.body}", icon: "${options.icon}", data:`, options.data);

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

console.log('[SW] Minimal sw.js LOADED');
