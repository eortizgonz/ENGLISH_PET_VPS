#!/bin/sh
set -eu

: "${PETQUEST_PG_HOST:=postgres}"
: "${PETQUEST_PG_PORT:=5432}"
: "${PETQUEST_PG_DB:=PET}"
: "${PETQUEST_PG_USER:=postgres}"
: "${PETQUEST_PG_PASSWORD:=12345}"

export PETQUEST_PG_HOST PETQUEST_PG_PORT PETQUEST_PG_DB PETQUEST_PG_USER PETQUEST_PG_PASSWORD

mkdir -p "${PETQUEST_BACKUP_DIR:-/data/backups}"

printf '%s\n' "[PET Quest] Esperando PostgreSQL en ${PETQUEST_PG_HOST}:${PETQUEST_PG_PORT}/${PETQUEST_PG_DB} ..."

attempt=0
until python - <<'PY'
import os
import psycopg
try:
    with psycopg.connect(
        host=os.environ['PETQUEST_PG_HOST'],
        port=int(os.environ['PETQUEST_PG_PORT']),
        dbname='postgres',
        user=os.environ['PETQUEST_PG_USER'],
        password=os.environ['PETQUEST_PG_PASSWORD'],
        connect_timeout=3,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
except Exception as exc:
    raise SystemExit(1)
PY
do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "[PET Quest] ERROR: PostgreSQL no estuvo disponible despues de 120 segundos."
    exit 1
  fi
  sleep 2
done

printf '%s\n' "[PET Quest] PostgreSQL disponible. Creando/verificando esquema y contenido maestro..."
python setup_postgres_pet.py

printf '%s\n' "[PET Quest] Inicio de la aplicacion en puerto ${PORT:-8080}."
exec "$@"
