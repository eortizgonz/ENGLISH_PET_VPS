# PET Quest V46.30 — Windows Safe Login

Root cause fixed:
- V34–V40 could auto-call privileged endpoints before authentication / in the wrong role.
- Anonymous 401 responses could trigger render again, allowing a request/render loop.
- Login could render twice after bootstrap.
- A global `top` helper could collide with the browser `window.top` binding.
- Persistent 20-second progress polling was unnecessary.
- Old localhost service workers/caches could mix JS from different builds.

Corrections:
- Role/view/token guards on all V34–V40 automatic loads.
- Anonymous 401 never forces render.
- GET request dedupe and 12s request timeout.
- Single-flight bootstrap.
- API circuit breaker (>24 requests/second).
- Event-driven progress refresh; no perpetual polling.
- `top()` renamed to `mockTopBar4620()`.
- Localhost PWA cache/service-worker hygiene and network-first JS/JSON/CSS.
