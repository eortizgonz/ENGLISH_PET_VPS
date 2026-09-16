# PET Quest V40 — Commercial Release Candidate

## Estado
V40 alcanza **100/100 en el gate interno automatizado** cuando están presentes licencia, roles, curso piloto, consentimiento, evidencia académica, backup y controles del entorno aplicables.

Esto no equivale a afirmar 100/100 de mercado sin validación externa. Para declarar producción comercial plena deben completarse los puntos de PILOT_PROTOCOL.md y los bloqueadores de `/api/release-readiness` en el entorno real.

## Capacidades comerciales cerradas
- Experiencia infantil guiada, adaptativa y visual.
- Reading 32 preguntas / Listening 25 preguntas / Writing / Speaking.
- Tutor Milo, ruta diaria, progreso semanal, portafolio y retención saludable.
- Padre/profesor/colegio, clases, intervenciones, outcomes, impacto, gobierno y forecast.
- Presupuesto, portafolio de intervenciones y horario/capacidad docente.
- Licenciamiento por cupos y onboarding institucional.
- Release Readiness con bloqueadores y advertencias explícitas.
- Recuperación de cuenta, auditoría, consentimiento de tutor, backups y PWA/offline.

## Gate comercial
El endpoint `/api/release-readiness` calcula una puntuación objetiva y separa:
- bloqueadores internos;
- advertencias operativas;
- validaciones externas necesarias.

La prueba `qa_v40_commercial.py` demuestra un flujo interno completo con resultado 100/100.


## V41 academic correction
- Reading Part 6 is open cloze (one produced word per gap).
- Listening Part 3 is a six-gap monologue task.
- Exact mock uses packaged audio files; bundled files are reference QA audio and do **not** satisfy the studio-human production gate.
- Writing includes a rule-based Error Intelligence layer with category, severity, recurrence, mini-lesson and corrective practice; it is formative, not an official Cambridge mark.
- Speaking automatic feedback no longer scores pronunciation/true interaction from text; human review uses Cambridge-aligned criteria and Part 3 has an interactive partner simulator.
- Current server includes privacy export, rectification, deletion request/resolution and consent revocation.
- Commercial QA waits on `/api/ready` instead of fixed startup sleep.
- Production readiness refuses SQLite when PostgreSQL is required.
