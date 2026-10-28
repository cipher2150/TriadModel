# TriadModel — Requirements Checklist

Status legend: `[ ]` not started · `[~]` implemented, not verified · `[x]` implemented and verified (evidence noted) · `[!]` blocked.

## Users and primary workflows

Users: finance students, analysts and small-business owners who have 2–5 years of historical statements and want a projected three-statement model without maintaining a spreadsheet.

1. Load historical statements (JSON/CSV upload, or built-in demo company clearly labelled as demo data).
2. Review the derived historical ratios that seed the assumptions.
3. Edit assumptions for Base / Upside / Downside and see all three statements update immediately.
4. Read the integrity and liquidity flags; trace a flagged number to its inputs.
5. Compare scenarios side by side; export results and assumptions.

## Functional requirements (MVP)

| ID | Requirement | Status |
|----|-------------|--------|
| F1 | Canonical historical schema for IS, BS, CF with import validation (reject unbalanced BS, missing lines, non-finite numbers, with line-specific errors) | [~] JSON import validation via API schemas verified; CSV import not implemented |
| F2 | Revenue forecast (growth rate per year) | [x] engine only — engine tests: hand-calculated year 1 |
| F3 | Operating expense forecast (COGS % revenue, SG&A % revenue, D&A from PP&E) | [x] engine only — same |
| F4 | Working capital forecast (DSO, DIO, DPO → AR, inventory, AP; other items held or % revenue) | [x] engine only — same |
| F5 | PP&E roll-forward (capex % revenue, depreciation) | [x] engine only — same |
| F6 | Debt schedule: term loan with scheduled amortization, revolver that draws to hold minimum cash and repays from surplus up to a limit, interest on opening balances | [x] engine only — unit: draw/repay/cap/term-loan cap |
| F7 | Tax expense (rate on positive pre-tax income; losses are not carried forward in MVP — documented limitation) | [x] engine only — unit: loss year pays no tax |
| F8 | Equity roll-forward (retained earnings, dividends as payout ratio) | [x] engine only — unit: RE roll-forward |
| F9 | Cash flow statement derived from IS and BS movements (indirect method) and tied to BS cash | [x] engine only — unit + property: CF ties to ledger cash |
| F10 | Three scenarios (Base, Upside, Downside), each a complete assumption set; switching or editing recalculates all statements | [~] backend only — scenarios calculate together via API; UI pending |
| F11 | Integrity checks: balance sheet balances; CF ending cash = BS cash; NI IS = NI CF; RE, PP&E and debt roll-forwards tie out; each reported per period with tolerance | [x] engine only — fault-injection tests per flag + property tests |
| F12 | Liquidity flags: cash below minimum, revolver limit exceeded (unfunded shortfall), negative equity | [x] engine only — unit: shortfall/negative cash/negative equity |
| F13 | Dependency graph: each forecast line declares its inputs; calculation order is derived, cycles are detected and reported | [x] engine only — graph tests: order, cycle, undefined/duplicate |
| F14 | Trace view: for any forecast cell, show the formula and the inputs it used | [x] engine only — trace unit test (API/UI view pending) |
| F15 | Scenario comparison view (key outputs across scenarios) | [ ] |
| F16 | Export/import model as JSON; export statements as CSV | [~] JSON/CSV export and JSON re-import verified via API; no UI yet |
| B1 | REST API: stateless `/api/calculate`; create/read/update/delete saved models; health endpoints; consistent error envelope | [x] API tests (calculate, demo, models CRUD, export, error envelope) |
| B2 | Saved models persisted in Postgres with migrations; optimistic concurrency (409 on stale version) | [x] Alembic migration tested up/down on SQLite and Postgres; 8-thread race test on Postgres 14 |
| B3 | Capability-token access: model UUID = read, write token = write/delete; no list endpoint | [x] token/403/404/no-list tests |

## Non-functional requirements

| ID | Requirement | Status |
|----|-------------|--------|
| N1 | `calculate` for a 5-year scenario completes in < 50 ms server-side (**measured**, not assumed); UI debounces edits | [~] engine measured: median 0.43 ms for 5 years (dev laptop); API latency not yet measured |
| N2 | Engine is pure Python (stdlib only), `Decimal`-based, deterministic; import-boundary test enforces it | [x] test_architecture.py |
| N3 | All imported/edited input validated at the boundary; clear messages | [ ] |
| N4 | Accessible UI (labelled inputs, keyboard operable, flags not colour-only); axe checks in E2E | [ ] |
| N5 | No secrets in repo; config via validated env vars; security headers, request-size cap, rate limiting; tokens never logged | [~] headers, size cap, rate limit, no token in logs/responses verified; secret scan not yet configured |
| N6 | Reproducible setup from a clean checkout; CI runs format, lint, typecheck, tests, build | [ ] |
| N7 | Dockerised app deployed on Render (service + Postgres) and smoke-tested | [ ] |

## Assumptions (nonessential ambiguities, resolved conservatively)

- A1. Annual periods. Historical: 1–5 years. Forecast horizon: 5 years (configurable 1–10).
- A2. Single currency, reported in units chosen by the user (e.g. thousands); no FX.
- A3. Interest is computed on **opening** balances. This avoids a circular reference (interest → net income → cash → revolver → interest). Average-balance interest with iteration is a documented future option.
- A4. No tax-loss carry-forward, no deferred taxes, no leases, no stock issuance/buybacks, no minority interest in MVP.
- A5. Amounts are `Decimal`; integrity checks still use a small absolute tolerance (default 0.01 currency units, configurable) because divisions (e.g. DSO/365) are non-terminating.
- A6. No user accounts. Access is via capability tokens (see architecture §9). Anyone with a model link can read it.
- A8. Hosting is Render via Docker; free-tier limits (cold starts, Postgres retention) are unverified and must be checked before deploy.
- A7. The app ships with one demo company; every screen that shows it carries a "Demo data" label.

## Out of scope for MVP

Quarterly/monthly periods, multi-entity consolidation, Monte-Carlo simulation, covenant modelling, user accounts and cloud sync, PDF reports.

## Acceptance criteria (high level)

- AC1. Changing any assumption alters every downstream statement line it should, and no others (verified by dependency tests).
- AC2. For every scenario and every forecast year on the demo data, BS balances within tolerance with zero hand-set plugs.
- AC3. A deliberately broken model (e.g. a forced CF/BS mismatch in a test harness, an unbalanced import) produces a specific, named flag — not a generic error.
- AC4. A downside scenario that exhausts the revolver produces a cash-shortfall flag in the correct year.
- AC5. Round-trip: export model JSON → import → identical outputs.
