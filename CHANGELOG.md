# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/). Versions are not yet tagged.

## [Unreleased]

### Changed
- Vitest and `@vitest/coverage-v8` upgraded to 5.0.5 together; Dependabot now groups them because they declare peer dependencies on each other.

### Added
- Calculation engine: `Decimal`-based, dependency graph with cycle detection, forecast modules (revenue, costs, PP&E, working capital, tax, term loan, revolver, dividends, equity), statements assembled without plugs, integrity and liquidity checks.
- Base / Upside / Downside scenarios derived from documented deltas.
- REST API: stateless `/api/calculate`, `/api/demo`, saved-model CRUD with write tokens, optimistic locking, JSON/CSV export, error envelope, body-size limit, security headers, rate limiting.
- PostgreSQL/SQLite persistence with Alembic migration.
- React frontend: assumption editing, statements with click-to-trace, flags, scenario comparison, save/share, JSON import/export.
- Dockerfile, Render Blueprint, GitHub Actions CI, Dependabot, smoke-test script.
- Test suites: unit, property, API, integration (Postgres), frontend component, Playwright E2E with accessibility scan.
