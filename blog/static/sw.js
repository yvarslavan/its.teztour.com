/**
 * Service Worker for my-issues page optimization
 * Implements caching strategies for improved performance
 */

const CACHE_NAME = 'my-issues-v1.0.0';
const STATIC_CACHE = 'static-v1.0.0';
const DYNAMIC_CACHE = 'dynamic-v1.0.0';

// Files to cache immediately
const STATIC_FILES = [
  '/static/css/my_issues_optimized.css',
  '/static/js/my_issues_optimized.js',
  '/static/css/layout.css',
  '/static/js/layout.js'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  '/api/my-issues/optimized',
  '/api/my-issues/statistics'
];

// Cache strategies
const CACHE_STRATEGIES = {
  // Static assets - Cache First
  static: {
    pattern: /\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/,
    strategy: 'cacheFirst',
    ttl: 86400 * 30 // 30 days
  },

  // API responses - Network First with fallback
  api: {
    pattern: /\/api\//,
    strategy: 'networkFirst',
    ttl: 300 // 5 minutes
  },

  // HTML pages - Network First
  html: {
    pattern: /\.html$/,
    strategy: 'networkFirst',
    ttl: 3600 // 1 hour
  }
};

// Install event - cache static files
self.addEventListener('install', event => {
  console.log('🔧 Service Worker installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('📦 Caching static files...');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('✅ Static files cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('❌ Failed to cache static files:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker activating...');

  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('🗑️ Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('✅ Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Determine cache strategy
  const strategy = getCacheStrategy(request.url);

  if (strategy) {
    event.respondWith(handleRequest(request, strategy));
  }
});

// Get cache strategy for URL
function getCacheStrategy(url) {
  for (const [name, config] of Object.entries(CACHE_STRATEGIES)) {
    if (config.pattern.test(url)) {
      return { ...config, name };
    }
  }
  return null;
}

// Handle request based on strategy
async function handleRequest(request, strategy) {
  const cacheName = strategy.name === 'static' ? STATIC_CACHE : DYNAMIC_CACHE;

  try {
    switch (strategy.strategy) {
      case 'cacheFirst':
        return await cacheFirst(request, cacheName);

      case 'networkFirst':
        return await networkFirst(request, cacheName, strategy.ttl);

      case 'staleWhileRevalidate':
        return await staleWhileRevalidate(request, cacheName);

      default:
        return await fetch(request);
    }
  } catch (error) {
    console.error('❌ Cache strategy failed:', error);
    return await fetch(request);
  }
}

// Cache First strategy
async function cacheFirst(request, cacheName) {
  const cachedResponse = await caches.match(request);

  if (cachedResponse) {
    console.log('📦 Serving from cache:', request.url);
    return cachedResponse;
  }

  const networkResponse = await fetch(request);

  if (networkResponse.ok) {
    const cache = await caches.open(cacheName);
    cache.put(request, networkResponse.clone());
    console.log('💾 Cached response:', request.url);
  }

  return networkResponse;
}

// Network First strategy
async function networkFirst(request, cacheName, ttl = 300) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      const responseWithTimestamp = addTimestamp(networkResponse.clone(), ttl);
      cache.put(request, responseWithTimestamp);
      console.log('🌐 Network response cached:', request.url);
    }

    return networkResponse;
  } catch (error) {
    console.log('🔄 Network failed, trying cache:', request.url);

    const cachedResponse = await caches.match(request);

    if (cachedResponse) {
      const timestamp = cachedResponse.headers.get('sw-cache-timestamp');
      const isExpired = timestamp && (Date.now() - parseInt(timestamp)) > (ttl * 1000);

      if (!isExpired) {
        console.log('📦 Serving stale cache:', request.url);
        return cachedResponse;
      } else {
        console.log('⏰ Cache expired, removing:', request.url);
        const cache = await caches.open(cacheName);
        cache.delete(request);
      }
    }

    throw error;
  }
}

// Stale While Revalidate strategy
async function staleWhileRevalidate(request, cacheName) {
  const cachedResponse = await caches.match(request);

  // Fetch in background to update cache
  const fetchPromise = fetch(request).then(networkResponse => {
    if (networkResponse.ok) {
      const cache = caches.open(cacheName);
      cache.then(c => c.put(request, networkResponse.clone()));
      console.log('🔄 Background cache update:', request.url);
    }
    return networkResponse;
  });

  // Return cached response immediately if available
  if (cachedResponse) {
    console.log('📦 Serving stale while revalidating:', request.url);
    return cachedResponse;
  }

  // Otherwise wait for network
  return await fetchPromise;
}

// Add timestamp to response for TTL management
function addTimestamp(response, ttl) {
  const headers = new Headers(response.headers);
  headers.set('sw-cache-timestamp', Date.now().toString());
  headers.set('sw-cache-ttl', ttl.toString());

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers
  });
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    console.log('🔄 Background sync triggered');
    event.waitUntil(doBackgroundSync());
  }
});

// Background sync implementation
async function doBackgroundSync() {
  try {
    // Sync any pending offline actions
    const pendingActions = await getPendingActions();

    for (const action of pendingActions) {
      try {
        await syncAction(action);
        await removePendingAction(action.id);
        console.log('✅ Synced action:', action.id);
      } catch (error) {
        console.error('❌ Failed to sync action:', action.id, error);
      }
    }
  } catch (error) {
    console.error('❌ Background sync failed:', error);
  }
}

// Get pending actions from IndexedDB
async function getPendingActions() {
  // Implementation would depend on your IndexedDB setup
  return [];
}

// Sync individual action
async function syncAction(action) {
  const response = await fetch(action.url, {
    method: action.method,
    headers: action.headers,
    body: action.body
  });

  if (!response.ok) {
    throw new Error(`Sync failed: ${response.status}`);
  }

  return response;
}

// Remove pending action after successful sync
async function removePendingAction(actionId) {
  // Implementation would depend on your IndexedDB setup
}

// Push notifications
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    console.log('📱 Push notification received:', data);

    const options = {
      body: data.body,
      icon: '/static/images/icon-192x192.png',
      badge: '/static/images/badge-72x72.png',
      tag: data.tag || 'my-issues-notification',
      data: data.data,
      actions: [
        {
          action: 'view',
          title: 'Просмотреть',
          icon: '/static/images/view-icon.png'
        },
        {
          action: 'dismiss',
          title: 'Закрыть',
          icon: '/static/images/dismiss-icon.png'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'view') {
    event.waitUntil(
      clients.openWindow('/my-issues-optimized')
    );
  }
});

// Message handling for cache management
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(clearAllCaches());
  }

  if (event.data && event.data.type === 'GET_CACHE_SIZE') {
    event.waitUntil(getCacheSize().then(size => {
      event.ports[0].postMessage({ cacheSize: size });
    }));
  }
});

// Clear all caches
async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames.map(cacheName => caches.delete(cacheName))
  );
  console.log('🗑️ All caches cleared');
}

// Get total cache size
async function getCacheSize() {
  const cacheNames = await caches.keys();
  let totalSize = 0;

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();

    for (const request of keys) {
      const response = await cache.match(request);
      if (response) {
        const blob = await response.blob();
        totalSize += blob.size;
      }
    }
  }

  return totalSize;
}

// Performance monitoring
self.addEventListener('fetch', event => {
  const startTime = performance.now();

  event.respondWith(
    handleRequest(event.request, getCacheStrategy(event.request.url))
      .then(response => {
        const endTime = performance.now();
        const duration = endTime - startTime;

        if (duration > 1000) {
          console.warn('⚠️ Slow request detected:', event.request.url, `${duration.toFixed(2)}ms`);
        }

        return response;
      })
  );
});

console.log('✅ Service Worker loaded successfully');
