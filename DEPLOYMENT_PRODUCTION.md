# Despliegue de producción PET Quest V40

## Requisitos obligatorios
- `PETQUEST_ENV=production`
- `PETQUEST_DEV_MODE=0`
- `PETQUEST_PUBLIC_BASE_URL=https://...`
- SMTP real configurado.
- Secretos fuera del repositorio.
- Backup externo programado y restauración probada.
- Base PostgreSQL gestionada recomendada para despliegues de escala; SQLite queda apta para demo/piloto pequeño.
- Proxy HTTPS / WAF / logs centralizados según infraestructura elegida.

## Gate
Después del despliegue iniciar sesión como school/admin y revisar:
- `/api/ops/status`
- `/api/release-readiness`

No liberar si hay bloqueadores.
