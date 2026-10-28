# Local setup

All commands run from the repository root.

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | ≥ 3.12 (developed on 3.13) | `python3 --version` |
| Node.js | ≥ 22 (developed on 25) | `node --version` |
| npm | bundled with Node | `npm --version` |
| Docker | optional: image build, Postgres tests | `docker info` |

## First-time setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # optional; defaults work for local use
(cd frontend && npm ci && npm run build)
alembic upgrade head            # creates ./triadmodel.db (SQLite)
```

## Run

**Single process (production-like).** Serves the API and the built UI:

```bash
uvicorn app.main:app --app-dir backend --port 8000
```

Open http://127.0.0.1:8000. Interactive API docs are at `/docs` in development (disabled when `APP_ENV=production`).

**Frontend development with hot reload.** Run the API as above, then in another terminal:

```bash
cd frontend && npm run dev      # http://localhost:5173, proxies /api and /health to port 8000
```

The server serves the UI only if `frontend/dist` exists (`STATIC_DIR`); without a build it runs API-only.

## Configuration

See `.env.example`. Variables are validated at startup; an invalid value stops the app with a message naming the field.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | `production` enables HSTS and disables API docs |
| `DATABASE_URL` | `sqlite:///./triadmodel.db` | `postgres://` / `postgresql://` URLs are rewritten to the psycopg driver |
| `LOG_LEVEL` | `INFO` | Python log level |
| `MAX_REQUEST_BYTES` | `1048576` | Request body cap (413 above it) |
| `CORS_ALLOWED_ORIGINS` | empty | Comma list; empty means same-origin only |
| `RATE_LIMIT_PER_MINUTE` | `60` | Per-client limit on POST/PUT/DELETE under `/api/` |
| `STATIC_DIR` | `frontend/dist` | Compiled frontend location |

## Running against Postgres locally

```bash
docker run -d --name triad-pg -p 5432:5432 -e POSTGRES_USER=triad -e POSTGRES_PASSWORD=triad -e POSTGRES_DB=triad postgres:16-alpine
export DATABASE_URL=postgresql+psycopg://triad:triad@127.0.0.1:5432/triad
alembic upgrade head
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `sqlalchemy.exc.OperationalError: no such table: models` | Migrations not applied: run `alembic upgrade head` |
| Page shows JSON 404 at `/` | No frontend build: run `(cd frontend && npm run build)` |
| `ValidationError` at startup | A setting is invalid, e.g. `APP_ENV=staging`; the message names the field |
| 429 responses while testing | Rate limit; raise `RATE_LIMIT_PER_MINUTE` locally |
| `localStorage.clear is not a function` in frontend tests | Node ≥ 25 global `localStorage`; handled in `frontend/src/test/setup.ts` |
| Playwright cannot find a browser | `cd frontend && npx playwright install chromium` |
| `docker: Cannot connect to the Docker daemon` | Start Docker Desktop |
| `CERTIFICATE_VERIFY_FAILED` from `scripts/smoke_test.py` against an `https://` URL | The python.org macOS installer ships no CA certificates. Run `/Applications/Python 3.*/Install Certificates.command`, or run the script with a Python that has system certificates (e.g. Homebrew) |
