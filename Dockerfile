# Stage 1: build the React frontend.
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime serving the API and the built frontend.
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY alembic.ini ./
COPY backend ./backend
COPY --from=frontend /build/dist ./static

RUN useradd --system --uid 10001 --no-create-home app && chown -R app /app
USER app

ENV APP_ENV=production \
    STATIC_DIR=/app/static \
    PORT=10000
EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request as u; u.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health/live', timeout=3)"

# Migrations run before the server starts. --proxy-headers lets the rate limiter see real client
# addresses behind Render's proxy; trusting forwarded headers from any source is acceptable only
# because the container is reachable solely through that proxy.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
