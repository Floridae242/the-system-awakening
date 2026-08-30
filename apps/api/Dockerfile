FROM python:3.14.0-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 10001 awakening \
    && useradd --uid 10001 --gid awakening --no-create-home --shell /usr/sbin/nologin awakening

WORKDIR /app
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --requirement /tmp/requirements.txt

COPY --chown=awakening:awakening alembic.ini ./alembic.ini
COPY --chown=awakening:awakening 09_CONTENT_SEED.json ./09_CONTENT_SEED.json
COPY --chown=awakening:awakening apps/api ./apps/api

USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "apps/api", "--host", "0.0.0.0", "--port", "8000"]
