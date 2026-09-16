# PET Quest V46.30 — Acceptance QA: usuario, login, audio y tablas

Fecha de auditoría: 2026-09-15

## Correcciones aplicadas

1. Se corrigió el flujo roto de `START_PET_QUEST_POSTGRES_WINDOWS.bat`.
2. `START_PET_QUEST_WINDOWS.bat` ahora delega al launcher PostgreSQL y conserva el código de salida.
3. `start_pet_quest.py` ya no fuerza cuentas demo; respeta `PETQUEST_SEED_DEMO_DATA=0` y espera `/api/ready`.
4. `/api/health` y `/api/ready` informan explícitamente el estado del almacén PostgreSQL de autenticación.
5. `postgres_check.py` ahora valida la arquitectura real V46.30: base `PET`, tabla `pet_users`, columnas e índices requeridos.
6. `postgres_schema.sql` habilita `citext` antes de usar `CITEXT`.
7. Se corrigió el QA de Audio Bank para el texto actual `REAL EXAM MODE`.
8. Se añadió `DATA_STORE_MAP_V46_30.md` con la trazabilidad de tablas.
9. Se normalizaron finales de línea CRLF de los launchers Windows.

## Prueba de usuario dinámica

Flujo probado mediante HTTP contra el servidor V46.30 con un adaptador PostgreSQL de prueba equivalente al contrato `pet_users`:

- Crear usuario: PASS.
- Sesión automática después de registro: PASS a nivel API.
- Login por username: PASS.
- Login por correo: PASS.
- Solicitud de recuperación: PASS.
- Crear nueva contraseña: PASS.
- Contraseña antigua rechazada: PASS.
- Contraseña nueva aceptada: PASS.
- Username duplicado bloqueado: PASS.
- Correo duplicado bloqueado: PASS.
- `/api/health` reporta almacén auth PostgreSQL: PASS.
- `/api/ready` exige SQLite + PostgreSQL auth disponibles: PASS.

Nota: el navegador Chromium del entorno de QA bloquea `localhost` por política administrativa, por lo que no se declara una automatización visual de navegador completa. La interfaz fue validada estáticamente y los endpoints fueron probados dinámicamente.

## Persistencia dinámica — 22/22 PASS

Se ejecutaron escrituras y lecturas reales y se verificaron las tablas:

- `snapshots`: progreso del estudiante.
- `learning_events`: respuestas/actividad.
- `academic_error_events`: Error DNA.
- `academic_remediation_attempts`: correcciones/reintentos.
- `mock_attempts`: cabecera del simulacro.
- `mock_item_responses`: respuestas por pregunta.
- `speaking_attempts`: evidencia de Speaking.
- PostgreSQL `pet_users`: identidad/autenticación.

Los endpoints `/snapshot`, `/my-preparation`, `/practice-diagnostic` y `/academic-remediation` recuperaron la información generada por esas tablas correctamente.

## QA de interfaz y recursos

- 59 scripts referenciados por `index.html`: todos presentes.
- 59 scripts: sintaxis JavaScript válida.
- `verify_windows_runtime.py`: 165/165 recursos runtime presentes.
- Windows Safe Login V46.30: 27/27 PASS.
- Registration/Recovery V46.30: PASS.
- PostgreSQL contract V46.30: 20/20 PASS.
- Practice Bank: 18/18 PASS; 5.000 ítems.
- Full Mock Bank: 272/272 PASS; 20 mocks, 1.140 ítems, 300 recording IDs.

## Audio

- Audio Bank For Schools: 500/500 archivos presentes.
- Decodificación completa de 500/500 MP3: PASS.
- Part 1: 180.
- Part 2: 160.
- Part 3: 80.
- Part 4: 80.
- Audio Bank QA: 28/28 PASS.

### Bloqueador para producción externa

Los 500 audios actuales siguen declarados correctamente como `synthetic_multivoice_reference` / simulados. `validate_studio_audio.py` continúa devolviendo `NOT READY` porque todavía faltan:

- `recording_type = human_studio`;
- `production_ready = true`;
- `rights_cleared = true`;
- `academic_qa_signed_off = true`.

Esto no debe cambiarse hasta incorporar y revisar las grabaciones humanas.

## Arquitectura de datos validada

### PostgreSQL `PET`

`pet_users` es autoritativa para username, email y hash de contraseña.

### SQLite local V46.30

Continúa siendo autoritativo para perfil/tenant, sesiones, tokens, progreso y evidencia educativa. Esta separación es deliberada en V46.30 y está documentada en `DATA_STORE_MAP_V46_30.md`.

## Resultado

La versión corregida pasa los contratos funcionales y de persistencia revisados. El único bloqueo declarado para una salida académica externa 100% es el reemplazo/QA de audio humano y las evidencias externas que ya estaban pendientes.
