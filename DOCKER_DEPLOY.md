# PET Quest - despliegue Docker

## Requisitos
- Docker Desktop (Windows/Mac) o Docker Engine + Docker Compose Plugin (Linux)
- Puertos libres: 8080 para PET Quest y 5432 para PostgreSQL, salvo que se cambien en `.env`

## Arranque rapido

1. Opcional: copia `.env.docker.example` como `.env` y cambia las credenciales.
2. Desde esta carpeta ejecuta:

   docker compose up -d --build

3. Espera a que ambos servicios esten saludables:

   docker compose ps

4. Abre:

   http://localhost:8080

## Ver logs

   docker compose logs -f pet

## Detener

   docker compose down

## Detener y borrar tambien los datos

   docker compose down -v

ADVERTENCIA: `down -v` elimina PostgreSQL y la base SQLite persistente del contenedor.

## Arquitectura de datos de esta release

- PostgreSQL `PET`: autenticacion, `pet_users`, esquema PostgreSQL y contenido maestro.
- Volumen `pet_postgres_data`: persiste PostgreSQL.
- SQLite `/data/petquest.db`: runtime academico heredado que aun usa la release V46.33.
- Volumen `pet_runtime_data`: persiste SQLite y backups.

El entrypoint del contenedor espera PostgreSQL, ejecuta `setup_postgres_pet.py`, crea/verifica tablas y carga el contenido maestro antes de iniciar `api_server.py`.

## Credenciales por defecto solicitadas

- Base: PET
- Usuario: postgres
- Password: 12345

Para un servidor publico cambia la password mediante `.env` antes del primer arranque.
