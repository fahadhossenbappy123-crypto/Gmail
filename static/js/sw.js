// Service Worker for Gmail Earn - Handles background notifications

const CACHE_NAME = 'gmail-earn-v1';
const URLS_TO_CACHE = [
    '/',
    '/static/js/sw.js'
];

// Install event - cache files
self.addEventListener('install', event => {
    console.log('[Service Worker] Installing...');
    self.skipWaiting(); // Activate immediately
});

// Activate event
self.addEventListener('activate', event => {
    console.log('[Service Worker] Activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Clearing old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Handle notification click
self.addEventListener('notificationclick', event => {
    console.log('[Service Worker] Notification clicked:', event.notification.tag);
    event.notification.close();
    
    const urlToOpen = '/dashboard';
    
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        })
        .then(clientList => {
            // Check if there's already a window with the target URL open
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            // If not, open a new window
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Handle notification close
self.addEventListener('notificationclose', event => {
    console.log('[Service Worker] Notification closed:', event.notification.tag);
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
            .catch(() => {
                return caches.match('/');
            })
    );
});

// Listen for messages from the main thread
self.addEventListener('message', event => {
    console.log('[Service Worker] Message received:', event.data);
    
    if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
        const { title, options } = event.data;
        self.registration.showNotification(title, options);
    }
});
