# PET Quest V46.30 — Login / Identity Sync Fix

Correcciones aplicadas:

- PostgreSQL `pet_users` puede reconstruir el usuario académico local si `petquest.db` pertenece a una instalación nueva.
- Se conserva/reutiliza `local_user_id` cuando no existe colisión.
- Si el mismo correo/usuario ya existe localmente con otro id, PostgreSQL se religa al id local existente.
- Se aceptan hashes actuales PBKDF2-SHA256 y hashes legacy SHA-256 de 64 hex únicamente para migración.
- Un login exitoso con hash legacy o credenciales desincronizadas genera un hash PBKDF2 nuevo y lo escribe en PostgreSQL y SQLite.
- Restablecer contraseña elimina bloqueos de login previos.
- `forgot-password` busca primero la identidad PostgreSQL y reconstruye el usuario local si falta.
- El panel de Demo local solo se muestra cuando las cuentas demo realmente existen y el seed demo está habilitado.
- Se incluye `REPAIR_USER_PASSWORD_WINDOWS.bat` como herramienta manual de emergencia; solicita la nueva contraseña de forma interactiva y nunca la imprime.

QA ejecutado:

- Identity restore: 6/6 PASS
- Login hash migration: 13/13 PASS
- Registration/recovery static QA: PASS
- Acceptance static: 47/47 PASS
- JavaScript syntax: PASS
- Audio bank presence: 500/500
- SQLite release DB: integrity OK, 0 demo/test users

Nota: no se almacena ninguna contraseña en texto plano dentro del paquete.
