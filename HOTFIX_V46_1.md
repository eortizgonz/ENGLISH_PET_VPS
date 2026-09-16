# PET Quest V46.1 Hotfix

Resolved `401 Unauthorized (from service worker)` on `/api/production-gate`.

Changes:
- canonical auth token key `petQuestToken` is now read by V45/V46 panels;
- `/api/*` bypasses Service Worker cache;
- only successful static GET responses are cached;
- Service Worker cache bumped to `petquest-v46-1`;
- `skipWaiting()` and `clients.claim()` force activation;
- Release Gate shows explicit session/role messages;
- backend version aligned to 46.1.
