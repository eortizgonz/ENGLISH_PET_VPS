# Seguridad — PET Quest V9

## Antes de producción

- Cambiar/eliminar todas las cuentas demo y contraseñas incluidas.
- `PETQUEST_ENV=production` y `PETQUEST_DEV_MODE=0`.
- HTTPS obligatorio en proxy/plataforma y `PETQUEST_PUBLIC_BASE_URL=https://...`.
- Secretos únicamente mediante secret manager/variables seguras; nunca dentro del ZIP o repositorio.
- Configurar SMTP real y validar SPF/DKIM/DMARC del dominio de envío.
- Mantener consentimiento de tutor habilitado para cuentas infantiles cuando corresponda.
- Ejecutar pentest y revisión legal/privacidad del país donde opere el colegio.
- Mantener backups cifrados/off-site y verificar periódicamente su integridad y restauración.
- Para escala horizontal, sustituir SQLite por un datastore compartido validado y mover rate limiting/sesiones a infraestructura distribuida.

## Controles V9

- Hash PBKDF2 heredado de V6+.
- Expiración y revocación de sesiones.
- Rate limiting de autenticación/recuperación.
- CSP, HSTS en producción HTTPS, X-Frame-Options y Permissions-Policy.
- Consentimiento de tutor y revocación.
- Exportación y solicitud/resolución de eliminación de datos.
- Auditoría y request IDs.
- Verificación de integridad de recovery points.
- Observabilidad y learning analytics.


## V25
La personalización se basa en rendimiento, evidencia y preferencias flexibles. No infiere diagnósticos psicológicos ni perfiles sensibles, y la preferencia elegida se guarda localmente.


## V27
Los grupos de refuerzo respetan el ámbito del colegio y solo permiten miembros matriculados en la clase seleccionada. La creación queda auditada y no modifica la matrícula base del alumno.

## V30 — Intervention outcomes
- Las evaluaciones de intervención quedan limitadas al `school_id` autenticado.
- Los miembros pertenecen al grupo/curso y sus resultados se obtienen desde snapshots autorizados.
- La línea base queda persistida para evitar reescritura retrospectiva del resultado inicial.
- Las reevaluaciones generan eventos de auditoría.
- Los outcomes son indicadores pedagógicos internos; no deben tratarse como diagnósticos del alumno.

## V31 Executive analytics
Executive review endpoints require teacher, school, or admin authorization. Public student rankings are intentionally excluded. Period snapshots remain school-scoped and auditable. Printing/PDF generation occurs client-side through the browser print flow and does not upload the report to a third party.


## V32 Governance
School Governance & Quality Assurance: objetivos academicos, responsables, acciones, alertas de desviacion y revisiones de impacto. Version 32.0.


## V33 Forecasting guardrails
Las proyecciones son orientativas, no decisiones automatizadas de alto impacto. El panel muestra confianza y metodologia; los escenarios no deben usarse para evaluar o sancionar individualmente a estudiantes o profesores.


## V35 simulation safety
Los escenarios de decision son orientativos y muestran supuestos, confianza y rangos. No deben usarse como garantia de resultados ni para decisiones individuales automatizadas sobre menores.


## V36 portfolio optimization guardrails
El optimizador de portafolio es una herramienta de planificación institucional. No debe usarse para decisiones automatizadas de alto impacto sobre menores. Los límites de solapamiento evitan sobreasignación innecesaria, pero la selección final debe ser revisada por personal académico autorizado.
