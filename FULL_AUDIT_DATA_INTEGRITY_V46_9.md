# PET Quest V46.9 — Auditoría total de formularios, controles y persistencia

Fecha: 2026-09-02

## Resultado
V46.9 consolida la auditoría formulario → acción → API → tabla → lectura de vuelta. Se corrigieron brechas de persistencia y consistencia encontradas en V46.8.

## Correcciones realizadas
1. Se implementaron las APIs que el frontend V8/V9 llamaba pero el backend consolidado no exponía: `/events`, `/analytics`, `/mastery/me`, `/mastery/school`, `/recovery/checks`, `/recovery/verify` y `/profile`.
2. Se creó `learning_events` para persistir eventos educativos/analíticos por usuario.
3. Se creó `recovery_checks` para guardar cada verificación real de backup.
4. Se creó `planning_scenarios` para que Decision Simulator, Budget Optimizer y Portfolio Optimizer no queden solo en pantalla: ahora guardan inputs y resultados completos.
5. El formulario Cuenta sincroniza el nombre con `users.name`; el rol real es de solo lectura y ya no puede divergir del rol de autorización.
6. La preparación Writing/Speaking ignora grabaciones/evidencias todavía no evaluadas; solo scores numéricos participan en la calificación.
7. La resolución de borrado de privacidad elimina también errores académicos, remediaciones, mocks, respuestas de mocks, calibración, learning events y escenarios del usuario antes de anonimizarlo.
8. PostgreSQL schema fue ampliado con las nuevas tablas para mantener equivalencia de diseño.

## Mapa de datos principal
| Pantalla / formulario / acción | API o mecanismo | Persistencia |
|---|---|---|
| Login | POST `/api/login` | `sessions`, `users.last_login_at`, `login_attempts` |
| Logout | POST `/api/logout` | elimina `sessions` |
| Recuperar contraseña | `/api/forgot-password`, `/api/reset-password` | `account_tokens`, `users.password_hash` |
| Cambiar contraseña | `/api/change-password` | `users.password_hash`, invalida sesiones según flujo |
| Cuenta / nombre | POST `/api/profile` | `users.name` |
| Fecha objetivo / preferencias / XP / historial / Word Book | POST `/api/snapshot` | `snapshots.payload` por `user_id` |
| Respuesta de práctica | snapshot + eventos | `snapshots.history`, `learning_events` |
| Writing | snapshot + Error Intelligence | `snapshots.writing`, `academic_error_events`, `academic_remediation_attempts` |
| Speaking | snapshot | `snapshots.speaking`; grabaciones sin score no reducen la nota |
| Mock exacto | POST `/api/mock-attempts` | `mock_attempts`, `mock_item_responses` |
| Progreso por usuario | GET `/api/my-preparation` | calcula desde snapshot + tablas académicas/mocks |
| Cursos | POST `/api/courses` | `courses` |
| Matrícula | POST `/api/enrollments` | `enrollments` |
| Tareas | POST `/api/assignments` | `assignments`; avance alumno en `snapshots.assignmentProgress` |
| CMS de preguntas | POST `/api/questions` | `questions` |
| Usuarios | POST `/api/users`, PATCH `/api/users/:id` | `users`, `account_tokens` |
| Colegio | POST `/api/schools` | `schools` |
| Consentimiento tutor | POST `/api/consents`, revoke | `guardian_consents` |
| Solicitudes privacidad | delete/rectify/resolve | `privacy_requests` + tablas afectadas |
| Grupos de apoyo | POST `/api/support-groups` | `support_groups`, `support_group_members`, `intervention_runs`, `intervention_run_members` |
| Evaluación intervención | POST `/api/interventions/evaluate` | actualiza `intervention_runs` y miembros |
| School Impact snapshot | POST `/api/school-impact/snapshot` | `school_quality_snapshots` |
| Executive Review snapshot | POST `/api/executive-review/snapshot` | `academic_review_snapshots` |
| Governance goal/action/review | endpoints governance | `governance_goals`, `governance_actions`, `governance_reviews` |
| Strategic target | POST `/api/strategy-targets` | `strategic_targets` |
| Disponibilidad profesor | POST `/api/teacher-availability` | `teacher_availability` |
| Planificación automática | POST `/api/schedule-planner/auto` | `schedule_sessions` |
| Licencia | POST `/api/commercial/license` | `school_licenses` |
| Onboarding | POST `/api/onboarding` | `onboarding_items` |
| Release readiness snapshot | POST endpoint | `release_acceptance_runs` |
| Calibration outcome | POST `/api/calibration/outcomes` | `calibration_outcomes` |
| Eventos educativos V8 | POST `/api/events` | `learning_events` |
| Learning analytics | GET `/api/analytics` | readback agregado de `learning_events` |
| Mastery alumno/colegio | GET mastery | snapshot + preparación individual |
| Backup | POST `/api/backup` | archivo `.db` fuera de la DB |
| Verify backup | POST `/api/recovery/verify` | `recovery_checks` + `PRAGMA integrity_check` |
| Decision Simulator | POST `/api/decision-simulator/run` | `planning_scenarios` (`decision_simulator`) |
| Budget Optimizer | POST `/api/budget-optimizer/run` | `planning_scenarios` (`budget_optimizer`) |
| Portfolio Optimizer | POST `/api/portfolio-optimizer/run` | `planning_scenarios` (`portfolio_optimizer`) |
| Auditoría de operaciones | múltiples writes | `audit_log` |

## Integridad de controles
- Botones encontrados en HTML/JS: 319.
- Campos input/select/textarea: 101.
- Atributos de control data-* únicos: 218.
- Rutas API literales llamadas por frontend: 52.
- Rutas API literales sin backend después de V46.9: 0.
- Screen Integrity: 174/174 PASS.
- Student End-to-End: 73/73 PASS.

## Integridad de persistencia
`qa_full_persistence_v46_9.py`: 45/45 PASS.
Verifica valor enviado, fila en SQLite y readback en los flujos críticos. Incluye snapshot exacto, curso, matrícula, tarea, CMS, grupo/intervención, errores/remediación, mocks, consentimientos, disponibilidad, estrategia, governance, onboarding, licencia, creación de usuario, privacidad, perfil, eventos, analytics, mastery, tres simuladores, recovery check, preparación, reportes, audit log, foreign keys y logout.

`qa_privacy_purge_v46_9.py`: PASS. No quedan filas educativas del usuario en snapshots, academic errors, remediation, mock attempts/responses, calibration ni learning events tras aprobación de borrado; la cuenta queda anonimizada y deshabilitada.

## Regresiones ejecutadas
- Startup: 9/9 PASS.
- Auth Session: 15/15 PASS.
- Security: 8/8 PASS.
- Screen Integrity: 174/174 PASS.
- Student E2E: 73/73 PASS.
- Academic Fidelity: 20/20 PASS.
- Privacy lifecycle: PASS.
- Calibration: PASS.
- Mock Bank V43: PASS.
- Psychometrics V44: 14/14 PASS.
- Backup/restore: PASS incluyendo nuevas tablas.
- Tenant isolation: PASS.
- Runtime HTTP: PASS.
- Exam packs A/B/C: PASS estructural (mantienen advertencias externas de sign-off académico/audio humano).
- Python compile: 91 archivos PASS.
- JavaScript syntax: 46 archivos PASS.
- Load smoke: 500/500 HTTP 200; 50 workers; p50 32.52 ms; p95 1226.26 ms; max 4354.60 ms, entorno local.

## Nota de alcance
Los controles de navegación, ayuda, cambio de pestaña, selección de respuestas y visualización no crean una fila propia porque no son formularios de negocio. Donde representan progreso o evidencia educativa, el estado se persiste en snapshot/eventos/mocks según el mapa anterior. Los simuladores, que antes eran cálculo temporal, sí se persisten desde V46.9.

La validación interna no sustituye pentest externo, audio humano/licenciado, despliegue PostgreSQL real, legal de menores ni piloto real.
