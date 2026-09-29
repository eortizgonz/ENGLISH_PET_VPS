# ENGLISH_PET_VPS_20260928_V3

## Cambios
- Mensaje animado de éxito al responder correctamente antes de avanzar.
- Mantiene el flujo sin botón `Comprobar`: `Siguiente` valida la respuesta.
- Una respuesta incorrecta no avanza y solo marca en rojo la opción seleccionada.
- La respuesta correcta no se revela cuando el intento es incorrecto.
- Se corrigió la persistencia de progreso en `public.snapshots` para usuarios autenticados.
- `POST /api/snapshot` ya no queda bloqueado por consentimiento de tutor; el consentimiento continúa aplicando a funciones sensibles como captura de audio/speaking.
- El indicador superior distingue `Conectado`, `Guardando…`, `Sincronizado` y `Sin sincronizar` según el resultado real de la sincronización.
- Versión interna backend: `46.32-pg`.
- Entrega LIGHT: no incluye `assets/audio`.
