# PET Quest V46.6 - Screen Integrity Fix

## Defecto reproducido desde evidencia del usuario
El modo Nino mostraba la barra superior pero el area principal quedaba visualmente en blanco, mientras el modo Adulto cargaba contenido.

## Causa raiz
En `v11_ux.js`, `v11Home()` buscaba el titulo `Elige una aventura` y ejecutaba:

`firstTitle.parentElement.style.display='none'`

Ese `parentElement` era `main.container`, por lo que se ocultaba toda la pantalla Nino. La rama Adulto no ejecutaba esa instruccion.

## Correccion
- Se cambia a `firstTitle.style.display='none'` para ocultar solo el encabezado sustituido por el mapa infantil.
- Se agrega un failsafe en `enhanceV11()` que mantiene `main.container` visible en modo Nino.
- Se eleva cache PWA a `petquest-v46-6` y todas las referencias activas a `v=46.6`.
- El service worker elimina caches anteriores durante `activate`.
- Se incorpora `qa_all_screens_v46_6.py` para validar rutas, acciones, scripts, assets y la regresion de la pantalla Nino.
- Se incorpora `qa_runtime_http_v46_6.py` para validar recursos HTTP, audios, login por rol y endpoints de pantallas operacionales.

## Validacion
- Screen Integrity QA: 172/172 PASS.
- Runtime HTTP QA: PASS.
- Student E2E: PASS (incluido dentro del gate de Screen Integrity).
- Security regression: PASS.
- Academic regression: PASS.
- Mock Bank regression: PASS.
- Psychometrics regression: PASS.
- Backup/restore regression: PASS.
- Load smoke: 500/500 HTTP health requests successful, 50 workers.

## Nota sobre QA historicos
Algunos QA V12-V35 conservan asserts de caches/versiones historicas y pueden marcar FAIL al ejecutarse aislados contra V46.6. Esos asserts estan superseded por `qa_all_screens_v46_6.py` y `qa_runtime_http_v46_6.py`; los fallos observados eran exclusivamente expectativas de version/cache anterior, no defectos funcionales de las pantallas actuales.
