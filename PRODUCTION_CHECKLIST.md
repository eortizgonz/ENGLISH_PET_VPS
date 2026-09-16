# V30 Quality/Impact additions
- [ ] Define snapshot cadence (weekly/monthly).
- [ ] Validate executive thresholds with school leadership.
- [ ] Confirm risk rules with educators before production use.
- [ ] Review cohort comparisons for minimum sample sizes.

# PET Quest V30 — Production Checklist

- [x] Línea base automática de intervención.
- [x] Seguimiento antes vs. después.
- [x] Delta por alumno y grupo.
- [x] Recomendación cerrar/extender/cambiar estrategia/reunir evidencia.
- [x] Cierre del grupo al cumplir criterio.
- [x] Efectividad agregada por habilidad y curso.
- [x] Panel profesor/colegio V30.
- [x] PostgreSQL schema actualizado para V27-V30.
- [x] PWA V30 incluye nueva capa offline.
- [x] QA V30 outcome end-to-end.
- [x] Regresión V26-V30 backend.
- [x] Regresión UX V10-V30 compatible hacia adelante.

## Pendientes de producción comercial
- [ ] Calibrar umbrales con resultados de pilotos reales.
- [ ] PostgreSQL administrado como runtime real.
- [ ] Métricas longitudinales por varias intervenciones y cohortes.
- [ ] Pruebas de carga cloud y pentest.
- [ ] Validación pedagógica con profesores B1/PET.

## V31 Executive review
- [x] Monthly and quarterly review windows
- [x] Persistent academic review snapshots
- [x] Institutional trend chart
- [x] Course/teacher comparison
- [x] Course improvement comparison without public student ranking
- [x] Intervention effectiveness summary
- [x] Executive priorities
- [x] CSV export
- [x] Print/PDF-friendly report layout
- [ ] Validate monthly/quarterly governance cadence with pilot schools


## V32 Governance
School Governance & Quality Assurance: objetivos academicos, responsables, acciones, alertas de desviacion y revisiones de impacto. Version 32.0.


## V33 Academic Strategy & Forecasting
- [x] Escenarios 30/60/90 dias.
- [x] Confianza de proyeccion basada en cantidad de cortes historicos.
- [x] Escenario sin accion separado de escenario con accion.
- [x] No atribuir uplift si no existe evidencia historica de intervenciones.
- [x] Metas anuales persistentes.
- [x] Capacidad docente orientativa por alumnos en riesgo.
- [x] PostgreSQL schema preparado para strategic_targets.
- [x] PWA V33 incluye nueva capa offline.
- [ ] Calibrar supuestos de forecasting con pilotos longitudinales reales.
- [ ] Validar capacidad docente con horarios y tamanos de grupo reales.

- [ ] Validar supuestos V35 con datos historicos reales antes de usar escenarios para presupuesto.
- [ ] Revisar rangos de impacto y capacidad docente con direccion academica.

## V35 budget optimizer
- [x] Budget cap is enforced server-side.
- [x] Cost/hour and maximum weekly teacher hours are validated server-side.
- [x] Infeasible scenarios are excluded.
- [x] Zero eligible learners returns zero/no plan rather than fabricated impact.
- [x] Impact ranges and confidence remain visible.
- [ ] Calibrate cost/hour and scheduling assumptions with each school before operational use.


## V36 portfolio optimizer
- [x] Optimiza varias intervenciones simultáneas.
- [x] Respeta presupuesto total y horas máximas por semana.
- [x] Limita número de intervenciones simultáneas.
- [x] Limita solapamiento de un mismo alumno entre intervenciones.
- [x] Reporta cobertura única y alumnos en riesgo cubiertos.
- [x] No genera portafolio si las restricciones son inviables.
- [x] PWA incluye V36 offline.
- [ ] Calibrar función objetivo, penalización de solapamiento y supuestos con pilotos reales.


## V41 academic correction
- Reading Part 6 is open cloze (one produced word per gap).
- Listening Part 3 is a six-gap monologue task.
- Exact mock uses packaged audio files; bundled files are reference QA audio and do **not** satisfy the studio-human production gate.
- Writing includes a rule-based Error Intelligence layer with category, severity, recurrence, mini-lesson and corrective practice; it is formative, not an official Cambridge mark.
- Speaking automatic feedback no longer scores pronunciation/true interaction from text; human review uses Cambridge-aligned criteria and Part 3 has an interactive partner simulator.
- Current server includes privacy export, rectification, deletion request/resolution and consent revocation.
- Commercial QA waits on `/api/ready` instead of fixed startup sleep.
- Production readiness refuses SQLite when PostgreSQL is required.
