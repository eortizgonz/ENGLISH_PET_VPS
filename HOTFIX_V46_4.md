# PET Quest V46.4 — Clean PWA Startup Fix

- Production Release Gate no longer auto-mounts.
- Gate is mounted explicitly only from Reports for authenticated School/Admin users.
- Manifest identity and start URL moved to V46.4.
- Critical scripts are query-versioned to break stale PWA cache.
- Service Worker uses network-first for navigation and never caches API responses.
- Server sends no-store headers for HTML/JS/CSS/manifest/service worker.
- Added `reset_pwa.html` to unregister stale workers/caches without deleting local progress.
