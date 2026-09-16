# QA Docker Deploy - PET Quest V46.33

## Resultado
PASS en validaciones disponibles en el entorno de construcción.

## Archivos
- Dockerfile
- docker-compose.yml
- docker-entrypoint.sh
- .dockerignore
- .env.docker.example
- DOCKER_DEPLOY.md

## Controles ejecutados
- Dockerfile contiene imagen Python 3.13 slim.
- psycopg[binary] se instala mediante requirements-postgres.txt.
- proceso corre como usuario no-root `petquest`.
- healthcheck HTTP apunta a `/api/ready`.
- docker-entrypoint.sh pasa `sh -n`.
- entrypoint espera PostgreSQL antes de continuar.
- entrypoint ejecuta `setup_postgres_pet.py` antes de `api_server.py`.
- docker-compose.yml parsea como YAML valido.
- docker-compose.yml contiene servicios `postgres` y `pet`.
- PostgreSQL usa volumen persistente `pet_postgres_data`.
- runtime SQLite/backups usa volumen persistente `pet_runtime_data`.
- app usa `PETQUEST_PG_HOST=postgres` dentro de la red Docker.
- base por defecto: PET.
- usuario por defecto: postgres.
- password por defecto: 12345 (debe cambiarse para despliegue publico).
- puertos configurables: 8080 app, 5432 PostgreSQL.

## Limitacion de validacion
El entorno de construcción actual no dispone del binario Docker/daemon, por lo que no se ejecutó `docker compose up`. Se validaron estructura YAML, shell, Python y contratos de variables/arranque.
