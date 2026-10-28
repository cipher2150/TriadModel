# ADR-005: Docker runtime on Render with a Blueprint

Status: accepted · Date: 2026-10-28

## Context
The build needs both Node (frontend) and Python (backend). Render's native Python runtime is not guaranteed to provide the Node toolchain, and we want the same artefact locally, in CI and in production.

## Decision
A multi-stage Dockerfile (Node builds the UI, a slim Python image runs the app as a non-root user) deployed through a `render.yaml` Blueprint. Migrations run at container start. CI builds the image and smoke-tests it against Postgres.

## Consequences
Parity between environments and a verifiable artefact. Builds are slower than native. Migrations at start assume a single instance (free tier) and need backward-compatible migrations. Free Postgres on Render expires after 30 days with no backups, so persistence needs a paid plan (see docs/DEPLOYMENT.md).
