# ADR-001: One FastAPI service serving the API and the built frontend

Status: accepted · Date: 2026-10-28

## Context
The first design was a client-only app computing in the browser. The owner asked for a real backend and Render deployment. We need saved, shareable models and want the engine to use exact decimal arithmetic.

## Decision
A single Python/FastAPI service exposes the JSON API and serves the compiled React app, backed by one Postgres database. The calculation engine is a pure module with no web or database imports (enforced by a test). Rejected: a client-only app (no sharing, floats in the browser), and separate API and static-site services (extra deploy, CORS, second free-tier quota).

## Consequences
One deployable and no CORS. Two toolchains (Python and Node) in one image, handled by a multi-stage Dockerfile. The UI cannot work offline, and a free Render instance has a cold start of about a minute.
