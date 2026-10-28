# TriadModel

An integrated three-statement forecasting engine. Load historical income statement, balance sheet and cash flow data, change the assumptions, and watch the consequences propagate through all three statements. The app flags broken accounting relationships and cash shortfalls.

> **Demo data.** The bundled company ("Demo Co") is illustrative, generated so the history balances. It is not real financial data and is labelled as such everywhere it appears.

## What it does

- Forecasts revenue, operating costs, working capital (DSO/DIO/DPO), PP&E, a term loan, a revolver, tax, dividends and cash for 1–10 years.
- Links the three statements: the cash flow statement is built from balance-sheet movements and balance-sheet cash *is* the cash flow statement's ending cash. Nothing is plugged, so the balance sheet either balances or the app says why it doesn't.
- Runs **Base, Upside and Downside** scenarios side by side. Each scenario is a complete, independently editable assumption set; Upside and Downside start from documented deltas on Base.
- Flags: balance sheet imbalance, cash-flow/cash tie-out, net income tie-out, retained earnings / PP&E / debt roll-forwards, negative cash, cash below minimum, revolver limit exceeded (unfunded cash shortfall), negative equity.
- Click any forecast figure to see its formula and the exact inputs it used.
- Save a model, share it by link, export JSON or CSV, import JSON.

## How it works, briefly

A pure-Python `Decimal` calculation engine builds a small dependency graph (each line declares its inputs), evaluates it in topological order and assembles the statements. FastAPI exposes it as a JSON API and also serves the compiled React app. Saved models live in Postgres. See [architecture.md](architecture.md).

## Technology

Python 3.12+ (FastAPI, Pydantic v2, SQLAlchemy 2, Alembic) · Postgres (SQLite for local use) · React 19 + TypeScript + Vite · pytest + Hypothesis · Vitest + Playwright · Docker · GitHub Actions · Render.

## Quick start

Prerequisites: Python ≥ 3.12, Node ≥ 22, npm. Docker is optional. Full instructions and troubleshooting: [docs/SETUP.md](docs/SETUP.md).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
(cd frontend && npm ci && npm run build)
alembic upgrade head
uvicorn app.main:app --app-dir backend --port 8000
```

Open http://127.0.0.1:8000.

## Tests and checks

```bash
ruff format --check backend scripts && ruff check backend scripts && mypy   # backend static checks
pytest --cov                                                                # backend tests
cd frontend && npm run format:check && npm run lint && npm run build && npm test   # frontend
cd frontend && npm run test:e2e                                             # browser tests
```

Details, Postgres test setup and coverage targets: [docs/TESTING.md](docs/TESTING.md).

## Documentation

| Document | Contents |
|---|---|
| [architecture.md](architecture.md) | Design, data flow, calculation model, trade-offs |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Requirements checklist with verification status |
| [docs/API.md](docs/API.md) | Endpoints, schemas, errors |
| [docs/SETUP.md](docs/SETUP.md) | Local setup and troubleshooting |
| [docs/TESTING.md](docs/TESTING.md) | Test layers and commands |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Render deployment, limits, rollback |
| [docs/DECISIONS/](docs/DECISIONS/) | Architecture decision records |
| [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) · [CHANGELOG.md](CHANGELOG.md) | Project process |

## Known limitations

Annual periods only; no tax-loss carry-forward, deferred tax, leases or equity issuance; interest on opening balances (no circularity); anyone holding a model's link can read it (no accounts); CSV import is not implemented (JSON import is). See [architecture.md](architecture.md#18-known-limitations-and-future-work).

## License

Apache License 2.0, see [LICENSE](LICENSE).
