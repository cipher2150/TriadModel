# Deployment (Render)

TriadModel deploys as **one Docker web service plus one Postgres database**, described by [render.yaml](../render.yaml). The image is built from the [Dockerfile](../Dockerfile): stage 1 builds the frontend, stage 2 runs the API and serves those static files as a non-root user.

## Read this first: free-tier limits

Checked against Render's documentation (render.com/docs/free) on 2026-10-28; verify again before relying on them.

| Free web service | Free Postgres |
|---|---|
| Spins down after 15 minutes without traffic; waking takes about a minute (the UI shows a "waking the server" message) | **Expires 30 days after creation**; 14-day grace period, then the database and its data are deleted |
| 750 free instance hours per month per workspace | 1 GB storage |
| Local files do not persist | **No backups** |
| One instance only (no horizontal scaling) | Only one free database per workspace |

**Consequence: with a free database, saved models are lost after about 30 days (or 44 with the grace period unless upgraded).** `render.yaml` ships with `plan: free` for the database so the project deploys at zero cost, but anything you want to keep needs a paid database plan: change `plan: free` to e.g. `0.1c-256mb` in `render.yaml` before the first deploy (or upgrade later in the Render dashboard). The demo and the stateless `/api/calculate` flow do not depend on the database.

## Prerequisites

- The repository on GitHub with CI green.
- A Render account connected to GitHub. (Manual step; cannot be automated from this repository.)

## Steps

1. Merge to `main`. 
2. In Render: **New → Blueprint**, select the repository, confirm the `triadmodel` web service and `triadmodel-db` database. Review the database plan (see above).
3. Render builds the Docker image and starts it. On start the container runs `alembic upgrade head`, then Uvicorn on `$PORT`. Render health-checks `/health/ready`, which fails with 503 if the database is unreachable.
4. Set no secrets: the only environment values are `DATABASE_URL` (injected from the database), `APP_ENV=production` and `LOG_LEVEL`.
5. Verify: `python scripts/smoke_test.py https://<service>.onrender.com`. Allow up to a minute for the first response from a cold service. The deployment counts as successful only when this prints `Smoke test passed.`

Check in the Render dashboard that auto-deploy is enabled for the service if you want deploys on every push to `main`.

## Configuration

All settings are environment variables; see [SETUP.md](SETUP.md#configuration). Production specifics: `APP_ENV=production` enables HSTS and removes the interactive API docs; the container sets `STATIC_DIR=/app/static`.

`--proxy-headers --forwarded-allow-ips='*'` is passed to Uvicorn so the rate limiter sees real client addresses. This trusts `X-Forwarded-For` from any peer, which is only safe because the container is reachable solely through Render's proxy. Do not reuse that command on a directly exposed host.

## Operations

- **Logs:** stdout, available in the Render dashboard.
- **Rate limiting** is per instance and in memory; it resets on restart.
- **Migrations** run on every start. Write migrations to be backward-compatible with the previous release so a code rollback does not need a database rollback.
- **Rollback:** in Render, redeploy a previous successful deploy. The service is stateless apart from the database.
- **Backups:** Render free databases have none; for paid plans, check the plan's backup features. You can always export a model to JSON from its page (`Export JSON`) or via `GET /api/models/{id}/export`.
- **Capacity:** a single instance; suitable for demos and light use, not for sustained traffic.

## Local production-like run

```bash
docker build -t triadmodel .
docker run --rm -p 10000:10000 -e DATABASE_URL=sqlite:////tmp/triad.db triadmodel   # or a postgres:// URL
python scripts/smoke_test.py http://127.0.0.1:10000
```

## Status

Verified locally: the image builds, runs as uid 10001, reports healthy, and passes the smoke test against Postgres 16. **Not yet deployed to Render**; that needs the manual steps above.
