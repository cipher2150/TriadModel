# Testing

## Layers

| Layer | Location | Tool | What it proves |
|---|---|---|---|
| Engine unit | `backend/tests/unit/` | pytest | Forecast formulas against hand-computed values; graph ordering, cycle/undefined/duplicate detection; each integrity flag fires when its relationship is broken, and at the tolerance boundary; scenarios; the engine imports only the standard library |
| Property | `backend/tests/property/` | Hypothesis | For hundreds of random *valid* assumption sets: integrity flags never fire, results are deterministic, the revolver stays within its limit, cash misses the minimum only by the reported shortfall |
| API / contract | `backend/tests/api/` | pytest + TestClient | Status codes, schemas, error envelope, token auth, version conflicts, size limit, security headers, rate limiting, CSV injection, static serving and path traversal |
| Integration | `backend/tests/integration/` | pytest + real Postgres | Alembic up/down on SQLite and Postgres, migrated schema equals the models, JSONB storage, an 8-thread race where exactly one writer wins, the API on Postgres |
| Frontend unit/component | `frontend/src/**/*.test.*` | Vitest + Testing Library | Number handling, editing and recalculation, invalid input, flags as text, trace panel, save/conflict/view-only flows. Fixtures are generated from the real backend (`scripts/export_frontend_fixtures.py`) so UI tests use true API shapes |
| End-to-end | `frontend/e2e/` | Playwright (Chromium) | Real browser, real server, fresh migrated database: propagation across all three statements, shortfall flag, tracing, save/reload/view-only, invalid and unbalanced imports, an axe accessibility scan (serious/critical), security headers |
| Smoke | `scripts/smoke_test.py` | stdlib | Run against any deployed URL: health, UI served, demo, calculate, create/read/update/conflict/forbidden/delete |

## Commands

```bash
# Backend (from repo root, venv active)
ruff format --check backend scripts
ruff check backend scripts
mypy
pytest --cov                                  # Postgres tests skip unless TEST_DATABASE_URL is set

# Backend with Postgres (all tests; REQUIRE_POSTGRES turns skips into failures)
export TEST_DATABASE_URL=postgresql+psycopg://triad:triad@127.0.0.1:5432/triad_test
REQUIRE_POSTGRES=1 pytest --cov

# Frontend
cd frontend
npm run format:check && npm run lint && npm run build
npm test                                      # or: npm run test:coverage

# End-to-end (needs a frontend build and the venv's Python)
npm run build && PYTHON=$PWD/../.venv/bin/python npm run test:e2e

# Smoke test of a running deployment
python scripts/smoke_test.py https://<your-service>.onrender.com
```

Regenerate frontend fixtures after changing API response shapes: `python scripts/export_frontend_fixtures.py`.

## Coverage

Backend: `pytest --cov` (branch coverage) with a CI gate of 90%. Frontend: `npm run test:coverage`; no hard gate, target ≥ 70%. Coverage shows which code ran, not whether the behaviour is right; the property tests and hand-computed values carry the correctness argument.

## Limitations

- The 7 Postgres tests are skipped locally without `TEST_DATABASE_URL`; CI sets `REQUIRE_POSTGRES=1` so they must run there.
- E2E covers Chromium only and checks accessibility with automated rules, which find only part of real accessibility problems. No manual screen-reader pass has been done.
- No load or performance test suite. The only measurement: `calculate` for a 5-year scenario took a median 0.43 ms over 200 runs on a developer laptop (engine only, excluding HTTP).
- The Render deployment itself is verified only by running `scripts/smoke_test.py` against the live URL.
