# V46.3 PWA Startup Routing Hotfix

## Problema reproducido
Al instalar/abrir la PWA, `v46_operational_release_gate.js` buscaba vistas estáticas (`#view-reports`, `#view-school`, `#view-admin`) que no existen en el SPA dinámico. Al no encontrarlas, usaba `document.body` como fallback y mostraba Production Release Gate para cualquier usuario, incluso sin sesión.

## Correcciones
- Eliminado fallback a `document.body`.
- Gate solo se monta si `state.view === 'reports'`.
- Gate solo se monta si el usuario autenticado tiene rol `school` o `admin`.
- Sin token al arrancar: Login.
- Token inválido/expirado: se limpia y vuelve a Login.
- PWA `start_url` versionada con `?source=pwa`.
- Service Worker cache `petquest-v46-3`; `/api/*` sigue network-only/no-cache.
- Backend/version headers actualizados a 46.3.

## Resultado esperado
1. Nueva instalación sin sesión -> Login.
2. Login Student -> Home; nunca Production Gate.
3. Login Teacher -> Home/Reportes; no Production Gate.
4. Login School/Admin -> Home; Production Gate únicamente al entrar a Reportes.
