# PET Quest V46.30 — PostgreSQL PET

Configuración solicitada para Windows local:

- Base de datos: `PET`
- Host: `localhost`
- Puerto: `5432`
- Usuario: `postgres`
- Contraseña: `12345`

## Inicio recomendado

Ejecutar `START_PET_QUEST_POSTGRES_WINDOWS.bat`.

El launcher:
1. verifica Python;
2. instala `psycopg` si falta;
3. crea la base `PET` si no existe;
4. crea la tabla `pet_users` e índices únicos;
5. inicia PET Quest.

## Persistencia

La identidad de registro/login es autoritativa en PostgreSQL `PET` (`pet_users`).
Las contraseñas se almacenan como hash PBKDF2-SHA256, nunca en texto plano.
La recuperación y el cambio de contraseña sincronizan PostgreSQL y el almacén académico local.

> Nota de arquitectura V46.30: el resto del historial académico mantiene la persistencia SQLite heredada. PostgreSQL es autoritativo para identidad/autenticación en esta entrega.

## Verificación

Después de preparar PostgreSQL puedes ejecutar:

```bat
python postgres_check.py
```

Debe informar `ok: true`, base `PET`, usuario `postgres`, tabla `pet_users` y los tres índices requeridos.

## Mapa de almacenamiento V46.30

- PostgreSQL `PET.pet_users`: usuario, correo, hash de contraseña, rol de identidad, modo de perfil y último login.
- SQLite `users`: sombra local del perfil y vínculo con colegio/curso.
- SQLite `sessions`: sesiones activas.
- SQLite `account_tokens`: verificación y recuperación de contraseña.
- SQLite `snapshots`: progreso/estado serializado del estudiante.
- SQLite `learning_events`: respuestas y actividad real.
- SQLite `academic_error_events`: Error DNA / errores detectados.
- SQLite `academic_remediation_attempts`: correcciones y reintentos.
- SQLite `mock_attempts` + `mock_item_responses`: simulacros y respuestas.
- SQLite `speaking_attempts` / `speaking_interaction_*`: evidencia de Speaking.
