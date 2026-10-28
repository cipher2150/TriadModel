# Contributing

## Workflow

1. Branch from `main`: `feat/<topic>`, `fix/<topic>`, or `docs/<topic>`.
2. Make small, focused commits. Imperative subject line; explain *why* in the body.
3. Open a pull request. CI must be green: backend (lint, types, tests with Postgres, audit), frontend, E2E and Docker smoke test.
4. Update documentation and `CHANGELOG.md` in the same PR when behaviour, commands or configuration change.

## Before you push

```bash
source .venv/bin/activate
ruff format backend scripts && ruff check backend scripts && mypy && pytest --cov
cd frontend && npm run format && npm run lint && npm run build && npm test
```

Run `npm run test:e2e` when you change UI behaviour or the API contract.

## Rules of the codebase

- **The engine stays pure.** `backend/app/engine` imports only the standard library and itself; a test enforces this. No HTTP, database or Pydantic there.
- **Accounting logic lives only in the engine.** The UI and API format and transport numbers; they never compute financial results.
- **Never plug.** Do not force the balance sheet to balance. If an identity fails, a check must say so.
- **Money is `Decimal`** in the engine and a decimal string over the wire; never a float in storage. Display-only arithmetic in the UI is acceptable.
- **Validate at the boundary** (Pydantic schemas). Financial problems become `flags`, not exceptions or HTTP errors.
- **Schema changes need an Alembic migration** and a test; keep migrations backward-compatible for one release.
- **A new check or forecast rule needs** a hand-computed unit test, a fault-injection test for any new integrity flag, and continued passing of the property tests.
- Changing API response shapes: regenerate frontend fixtures (`python scripts/export_frontend_fixtures.py`) and update `docs/API.md`.
- No secrets in the repository; configuration comes from environment variables (`.env.example` documents them).
- Do not disable a failing test to get green; fix the cause or discuss it in the PR.

## Architecture decisions

Significant decisions are recorded in `docs/DECISIONS/` as `ADR-NNN-title.md` (context, decision, consequences). Add one when you change something an ADR describes.
