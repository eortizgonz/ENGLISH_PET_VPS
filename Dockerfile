FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PETQUEST_HOST=0.0.0.0 \
    PORT=8080 \
    PETQUEST_ENV=docker \
    PETQUEST_DEV_MODE=0 \
    PETQUEST_SEED_DEMO_DATA=0 \
    PETQUEST_REQUIRE_POSTGRES_AUTH=1 \
    PETQUEST_REQUIRE_POSTGRES_IN_PRODUCTION=0 \
    PETQUEST_REQUIRE_SMTP_IN_PRODUCTION=0 \
    PETQUEST_REQUIRE_HTTPS_IN_PRODUCTION=0 \
    PETQUEST_SQLITE_PATH=/data/petquest.db \
    PETQUEST_BACKUP_DIR=/data/backups

WORKDIR /app

COPY requirements-postgres.txt /app/requirements-postgres.txt
RUN pip install --no-cache-dir -r /app/requirements-postgres.txt

COPY . /app
COPY docker-entrypoint.sh /usr/local/bin/petquest-entrypoint
RUN chmod +x /usr/local/bin/petquest-entrypoint \
    && mkdir -p /data/backups \
    && useradd --system --uid 10001 --create-home petquest \
    && chown -R petquest:petquest /app /data

USER petquest

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/ready', timeout=4)" || exit 1

ENTRYPOINT ["petquest-entrypoint"]
CMD ["python", "api_server.py"]
