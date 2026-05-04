// Service Worker registration and notification handling
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/js/sw.js')
        .then(registration => {
            console.log('[App] Service Worker registered successfully:', registration);
        })
        .catch(error => {
            console.log('[App] Service Worker registration failed:', error);
        });
}

// Listen for notifications from the server (via WebSocket or polling)
// This function is called when the app receives a notification
window.sendNotificationToUser = function(title, options = {}) {
    if ('Notification' in window && Notification.permission === 'granted') {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            navigator.serviceWorker.controller.postMessage({
                type: 'SHOW_NOTIFICATION',
                title: title,
                options: {
                    icon: options.icon || 'https://cdn-icons-png.flaticon.com/512/732/732200.png',
                    badge: options.badge || 'https://cdn-icons-png.flaticon.com/512/732/732200.png',
                    body: options.body || '',
                    tag: options.tag || 'gmail-earn-notification',
                    requireInteraction: options.requireInteraction || false,
                    ...options
                }
            });
        }
    }
};
