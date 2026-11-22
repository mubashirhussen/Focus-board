# FocusBoard — PWA, Offline Task Storage & Mobile Optimization

## 1. Progressive Web App (PWA)
- **Manifest (`manifest.webmanifest`)**:
  - Configured with `display: standalone`, `#4F46E5` theme color, portrait primary orientation, and maskable icons.
- **Service Worker (`public/sw.js`)**:
  - **Static Assets**: Cache-first strategy for instant subsequent reloads.
  - **App Shell**: Stale-while-revalidate for seamless zero-downtime background updates.
  - **API & WebSockets**: Network-first with IndexedDB sync queue fallback.

---

## 2. Offline Task Management & Reconciliation Engine
- **IndexedDB (`focusboard_offline_db`)**:
  - Stores local tasks and the mutation queue (`sync_queue`) when disconnected.
- **Offline Sync Engine (`src/services/offlineSyncEngine.js`)**:
  - Queues mutations (`CREATE_TASK`, `UPDATE_TASK`, `DELETE_TASK`).
  - Automatically detects network restoration (`navigator.onLine`) and replays queued operations in FIFO order with duplicate mitigation.
  - Shows an offline notification banner with real-time pending mutation counts.

---

## 3. Web Push Notifications
- Backend VAPID key support via `PushNotificationService`.
- Subscribes browser push tokens via standard `PushManager` API.
- Delivers background notifications for task deadlines, assignments, and daily plan reminders.

---

## 4. Mobile Ergonomics
- Responsive bottom navigation bar (`MobileBottomNav.jsx`) on screens $\le 768px$.
- Accessible touch targets $\ge 44px \times 44px$.
- Verified across 320px, 375px, 390px, 414px, 768px, 1024px, and 1440px viewports.
