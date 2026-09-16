# PET Quest V46.30 - Windows Path Fix QA

## Incidente reproducido desde el log de Windows

La aplicación iniciaba correctamente en `http://127.0.0.1:8080`, pero múltiples recursos estáticos y audios devolvían 404/FileNotFoundError.

La ruta original de ejecución era demasiado profunda. Ejemplos calculados sobre la ruta reportada:

- `v46_30_windows_runtime_guard.js`: 264 caracteres.
- `v46_22_practice_diagnostic.js`: 262 caracteres.
- `PRACTICE_BANK_ADULT_V46_26.json`: 264 caracteres.
- `assets/audio/mock_bank/pq-mock-a/pq-mock-a-l1-1.mp3`: 284 caracteres.

Esto supera el límite clásico de rutas de Windows de 260 caracteres y explica que archivos incluidos en el ZIP no fueran accesibles tras la extracción/ejecución.

## Correcciones aplicadas

1. Carpeta raíz del paquete acortada a `PET`.
2. `verify_windows_runtime.py` valida longitud proyectada y existencia de assets antes de iniciar.
3. El launcher de Windows ejecuta la validación antes de PostgreSQL y del servidor.
4. Cache PWA incrementada a `petquest-v46-30-pathfix-1` para invalidar cache anterior.
5. Instalación del service worker endurecida para que un fallo opcional de cache no invalide toda la instalación.
6. `api_server.py` responde 204 a `/favicon.ico` y a la consulta de Chrome DevTools.
7. `api_server.py` absorbe `BrokenPipeError`, `ConnectionResetError` y `ConnectionAbortedError` producidos por cancelaciones normales del navegador al recargar/navegar.

## Validaciones ejecutadas

- Python compile: PASS.
- Runtime package integrity: PASS.
- Service worker runtime assets presentes: 165 rutas únicas.
- Requests de todos los assets listados en el service worker: 166/166 HTTP 200.
- Recursos que fallaban en el log: HTTP 200 tras el fix.
- Audio `pq-mock-a-l1-1.mp3`: HTTP 200 tras el fix.
- `/favicon.ico`: HTTP 204 sin error.
- `/.well-known/appspecific/com.chrome.devtools.json`: HTTP 204 sin error.

## Instalación recomendada

Extraer el ZIP manteniendo la carpeta interna `PET` y ejecutar:

`PET\START_PET_QUEST_POSTGRES_WINDOWS.bat`

Si se vuelve a ubicar la app en una ruta excesivamente profunda, el launcher se detendrá antes de iniciar y mostrará la recomendación de moverla a `C:\PET` o a una ruta corta del Escritorio.
