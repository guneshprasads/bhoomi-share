# Bhoomi Share: one image that runs anywhere a container runs (Render, Koyeb,
# Fly.io, Hugging Face Spaces, a VPS). The app listens on $PORT, default 8000.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# dependencies first, so code changes do not reinstall them
COPY backend/requirements.txt backend/requirements.txt
RUN pip install -r backend/requirements.txt

COPY backend backend

# run as an ordinary user; give it the two places the app writes
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /srv/backend/uploads /srv/backend/backups \
    && chown -R app:app /srv/backend/uploads /srv/backend/backups
USER app

WORKDIR /srv/backend

# production defaults; every one can be overridden by the host's environment
ENV BHOOMI_SEED_DEMO=0 \
    BHOOMI_COOKIE_SECURE=1 \
    WEB_CONCURRENCY=1 \
    PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT','8000'), timeout=4)"

# --proxy-headers so the app sees https and the visitor's IP behind the host's proxy
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers ${WEB_CONCURRENCY} --proxy-headers --forwarded-allow-ips='*'"]
