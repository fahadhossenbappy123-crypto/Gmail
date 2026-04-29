# 🔔 Notification System Documentation

## Overview
The Gmail Earn application now includes a comprehensive real-time notification system that notifies users when their Gmail accounts or withdrawal requests are approved/rejected by admins.

## Features Implemented

### 1. **Responsive Mobile Top Navigation Bar**
- ✅ Hamburger menu for mobile devices (appears on screens < 768px)
- ✅ Smooth animations and transitions
- ✅ Sticky navigation bar that stays at the top while scrolling
- ✅ Mobile-optimized layout with proper spacing and touch targets
- ✅ Desktop navigation hidden on mobile, replaced with hamburger menu
- ✅ Compact balance display on mobile

### 2. **Notification Icon with Badge**
- ✅ Bell icon in the top navigation bar
- ✅ Red badge showing count of unread notifications
- ✅ Badge automatically updates when new notifications arrive
- ✅ Badge hides when all notifications are read

### 3. **Notification Dropdown Panel**
- ✅ Click notification bell to see recent notifications (last 5)
- ✅ Shows notification title, message, and time received
- ✅ Visual distinction for unread vs. read notifications
- ✅ Click any notification to mark it as read
- ✅ "Mark all as read" button to dismiss all at once
- ✅ Smooth animations and professional styling

### 4. **Auto-Update Notifications**
- ✅ Notifications load automatically when the page loads
- ✅ Notifications refresh every 10 seconds automatically
- ✅ No page reload needed to see new notifications

### 5. **Browser Notifications (Push Notifications)**
- ✅ Request notification permission banner on first visit
- ✅ Permission can be granted or dismissed
- ✅ Browser notifications show even when app is minimized/closed
- ✅ Click on browser notification to open dashboard

### 6. **Notification Triggers**
When an admin approves or rejects accounts/withdrawals, users receive notifications:

#### Account Approval:
- **Title**: ✅ Gmail Account Approved!
- **Message**: Your Gmail account [email] has been approved. You earned ৳[amount]
- **Type**: `account_approved`

#### Account Rejection:
- **Title**: ❌ Gmail Account Rejected
- **Message**: Your Gmail account [email] was rejected. Please review and try again.
- **Type**: `account_rejected`

#### Withdrawal Approval:
- **Title**: ✅ Withdrawal Approved!
- **Message**: Your withdrawal of ৳[amount] to [bkash_number] has been approved and is being processed.
- **Type**: `withdrawal_approved`

#### Withdrawal Rejection:
- **Title**: ❌ Withdrawal Rejected
- **Message**: Your withdrawal of ৳[amount] was rejected. The amount has been refunded to your account.
- **Type**: `withdrawal_rejected`

## Database Schema

### New Notification Table
```sql
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL FOREIGN KEY REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,  -- 'account_approved', 'withdrawal_approved', etc.
    related_id VARCHAR(36),     -- References the account_id or withdrawal_id
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
)
```

## API Endpoints

### Get Notifications
```
GET /api/notifications?limit=20
Response: {
    "success": true,
    "notifications": [
        {
            "id": "notification_id",
            "title": "✅ Gmail Account Approved!",
            "message": "Your Gmail account...",
            "type": "account_approved",
            "is_read": false,
            "created_at": "2026-04-29T10:30:00",
            "related_id": "account_id"
        }
    ]
}
```

### Get Unread Count
```
GET /api/notifications/unread-count
Response: {
    "success": true,
    "unread_count": 3
}
```

### Mark Single Notification as Read
```
POST /api/notifications/{notification_id}/read
Response: {
    "success": true,
    "unread_count": 2
}
```

### Mark All as Read
```
POST /api/notifications/mark-all-read
Response: {
    "success": true,
    "unread_count": 0
}
```

## How to Test the Notification System

### Test In-App Notifications:
1. Log in to the user account
2. In another tab, open admin panel
3. Go to Admin → Accounts (or Admin → Withdrawals)
4. Approve a pending account or withdrawal
5. Switch back to the user tab
6. The notification should appear in the dropdown immediately (within 10 seconds)
7. The badge count will update

### Test Browser Notifications:
1. Log in to user account
2. Click "Allow Notifications" button in the banner (or in notification dropdown)
3. Approve an account/withdrawal as admin
4. A browser notification will pop up in the user's system (even if browser is minimized)
5. Click the notification to return to the dashboard

### Manual Testing Commands (Python):
```python
# In Flask shell
from database import db, User, Notification
from datetime import datetime

user = User.query.first()
notif = Notification(
    user_id=user.id,
    title="Test Notification",
    message="This is a test notification",
    type="account_approved",
    related_id="test_id"
)
db.session.add(notif)
db.session.commit()
```

## Mobile Responsiveness

### Mobile-Specific Features:
- **Hamburger Menu**: Replaces desktop navigation on screens < 768px
- **Touch-Friendly**: Larger touch targets (44x44px minimum)
- **Bottom Navigation Bar**: Quick access to main features
- **Notification Bell**: Full-screen dropdown on mobile
- **Balance Display**: Compact version on small screens
- **Hidden on Mobile**: Some desktop elements (balance, withdraw button)

### Breakpoints:
- **Small Mobile**: < 640px (hide non-essential elements)
- **Mobile**: < 768px (show hamburger menu, bottom nav)
- **Tablet/Desktop**: ≥ 768px (show full desktop layout)

## Service Worker

The application includes a service worker (`static/js/sw.js`) that:
- ✅ Caches files for offline support
- ✅ Handles notification clicks (opens dashboard)
- ✅ Enables background notifications even when app is closed
- ✅ Intercepts fetch requests for better performance

## Browser Compatibility

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Notifications API | ✅ | ✅ | ❌* | ✅ |
| Service Worker | ✅ | ✅ | ✅ | ✅ |
| Hamburger Menu | ✅ | ✅ | ✅ | ✅ |
| Dropdown Panel | ✅ | ✅ | ✅ | ✅ |

*Safari has limited notification support; web push works on Mac notifications but not mobile

## File Structure

```
gmail-earn/
├── app.py (updated with notification endpoints)
├── database.py (updated with Notification model)
├── templates/
│   └── base.html (updated with responsive nav & notification UI)
├── static/
│   └── js/
│       ├── sw.js (service worker for background notifications)
│       └── notifications.js (service worker registration)
└── README.md (this file)
```

## JavaScript Functions in base.html

### Core Functions:
- `loadNotifications()` - Fetches notifications from API
- `updateNotificationBadge()` - Updates badge count
- `markAsRead(notificationId)` - Mark single notification as read
- `markAllAsRead()` - Mark all notifications as read
- `requestNotificationPermission()` - Request browser notification permission
- `showBrowserNotification(title, message)` - Show browser notification
- `dismissNotificationBanner()` - Hide permission request banner

### Helper Functions:
- `getTimeAgo(date)` - Format notification timestamp (e.g., "2 hours ago")

## Security Considerations

✅ **User Authorization**: Users can only see their own notifications
✅ **CSRF Protection**: All POST requests use Flask's CSRF protection
✅ **Input Validation**: All inputs are validated before processing
✅ **XSS Prevention**: All user data is escaped in templates
✅ **Authentication Required**: Notification endpoints require login

## Future Enhancements

- [ ] Email notifications (send email when important events occur)
- [ ] SMS notifications (send SMS for critical updates)
- [ ] Notification preferences (allow users to customize notification types)
- [ ] Notification history page (view all past notifications)
- [ ] Notification sounds (play sound when notification arrives)
- [ ] Web push notifications (keep-alive server connection)
- [ ] Notification grouping (group similar notifications together)
- [ ] Action buttons in notifications (approve/reject from notification)

## Troubleshooting

### Notifications Not Showing:
1. Check browser console for errors (F12 → Console)
2. Verify notification permission is granted
3. Check if user_id is properly set in session
4. Verify database migration ran successfully (check notifications table exists)

### Service Worker Not Registering:
1. Check that static files are being served correctly
2. Verify app is running on HTTPS (or localhost for testing)
3. Clear browser cache and service worker: Settings → Privacy → Clear browsing data

### Badge Not Updating:
1. Check network tab to see if `/api/notifications/unread-count` is being called
2. Verify response is valid JSON
3. Check browser console for JavaScript errors

## Deployment Notes

1. **Database Migration**: Ensure `Notification` table is created
   - Run: `python run.py` to auto-create tables

2. **Static Files**: Ensure Flask serves static folder
   - Check: `static/js/sw.js` and `static/js/notifications.js` are accessible

3. **HTTPS**: Browser notifications require HTTPS (except for localhost)
   - Configure SSL certificate in production

4. **Service Worker Cache**: May need to clear cache in production
   - Update CACHE_NAME in `static/js/sw.js` to bust cache

## Support

For issues or feature requests, please create an issue in the project repository.
