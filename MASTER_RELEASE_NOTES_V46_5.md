# PET Quest B1 for Schools V46.5 MASTER

Base: V46.4 Clean PWA Startup + hardening de runtime derivado de V42.2.

## Correcciones aplicadas
- Eliminado el conflicto JavaScript con `window.top`: `top()` pasó a `topBar()` en la cadena de dependencias.
- Reparado el wrapper V6 para usar `topBar` sin generar una segunda falla de runtime.
- Reparados los Full Mocks V43 para usar `topBar`.
- Cache PWA actualizado a `petquest-v46-5` y query strings a `v=46.5`.
- Dockerfile corregido: ahora arranca `api_server.py` y no un servidor histórico.
- Metadata/backend actualizados a V46.5.
- Frontend captura el entorno del endpoint `/api/health`.
- Credenciales demo visibles/prellenadas únicamente en development/test.
- `.env.example` actualizado y normalizado a `DATABASE_URL`.
- Agregados iniciadores Windows/macOS/Linux y `docker-compose.local.yml`.
- Agregado gate unificado `qa_master_v46_5.py`.

## Evidencia interna reproducida
- Startup V46.5: PASS.
- Security V46: 8/8 PASS.
- Student E2E: 72/72 PASS.
- V43 Mock Bank: PASS.
- V41 Academic Fidelity: 20/20 PASS.
- V44 Psychometrics code/UI: PASS.
- V46 Unified Release Gate code: PASS.
- Exam pack validators: PASS.
- Chromium headless: 0 JavaScript runtime exceptions durante carga completa.

## Estado
**LOCAL / QA / STAGING: OPERATIVO.**

**COMMERCIAL PRODUCTION: aún requiere infraestructura/evidencia externa.** El paquete no falsifica estos gates.

Bloqueadores externos o de despliegue final:
1. PostgreSQL runtime real en producción (el runtime actual sigue siendo SQLite para local/piloto).
2. SMTP transaccional real.
3. Dominio y TLS/HTTPS reales.
4. Audios humanos de estudio con derechos liberados y firma académica; los MP3 incluidos son de referencia QA.
5. Backup off-host + restore drill en infraestructura real.
6. Pentest independiente.
7. Revisión legal/privacidad infantil y tratamiento de voz.
8. Matriz física de dispositivos/navegadores.
9. Piloto con niños/padres/profesores y calibración externa.

No publicar “100% Cambridge equivalent” ni probabilidad de aprobación hasta cerrar la calibración externa.
