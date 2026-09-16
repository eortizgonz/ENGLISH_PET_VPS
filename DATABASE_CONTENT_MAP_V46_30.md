# PET Quest V46.30 — Mapa de datos PostgreSQL

## Tablas maestras: deben contener datos inmediatamente después de instalar
- `content_packages`: inventario y versión de cada banco cargado.
- `practice_bank_items`: 5.000 actividades For Schools + 3.000 Adult.
- `curriculum_lessons`: 100 lecciones PET Learn A2→B1+.
- `audio_assets`: todos los archivos de audio incluidos en `assets/audio`, con transcript/metadata cuando existe en los manifiestos.
- `exam_packs`: 20 mocks For Schools + 20 mocks Adult.
- `exam_items`: Reading, Listening, Writing y Speaking de los 40 mocks.
- `content_seed_runs`: historial de cargas del material maestro.
- `pet_users`: identidades registradas; puede estar vacía antes del primer registro.

## Tablas transaccionales: empiezan vacías y se llenan cuando el alumno usa la app
`learning_events`, `academic_error_events`, `academic_remediation_attempts`, `mock_attempts`, `mock_item_responses`, `speaking_attempts`, `speaking_interaction_sessions`, `speaking_interaction_turns`, `snapshots`, `sessions`, `login_attempts`, `account_tokens`, `audit_log`.

## Tablas escolares/administrativas: pueden iniciar vacías hasta configurar un colegio
`schools`, `users`, `courses`, `enrollments`, `assignments`, `support_groups`, `intervention_runs`, `school_licenses`, `guardian_consents`, `teacher_availability`, `schedule_sessions`, `governance_*`, `planning_scenarios`, etc.

## Runtime
Practice Bank, PET Learn, Audio Bank y Full Mocks consultan primero PostgreSQL mediante `/api/content/*`.
Los JSON incluidos en el ZIP se mantienen como respaldo offline y evidencia reproducible del contenido original.

## Audio
Los MP3/WAV no se guardan como BLOB dentro de PostgreSQL. PostgreSQL guarda su ruta, hash, transcript, pregunta, respuesta, voces y metadata técnica. Los archivos binarios permanecen en `assets/audio` para servirlos eficientemente desde la aplicación.
