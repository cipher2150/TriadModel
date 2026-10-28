# Security

## Reporting a vulnerability

Please do **not** open a public issue. Use GitHub's private vulnerability reporting on this repository (Security → Report a vulnerability), or contact the maintainer through the email on their GitHub profile. Include steps to reproduce and the affected version. You should get an acknowledgement within a few days; this is a small project without a formal SLA.

## Security model

- **No accounts.** Access to a saved model uses capability tokens: the model's random UUID grants **read** access (it is the share link: anyone with it can view the model); the **write token**, shown once at creation, grants update and delete. Only the token's SHA-256 hash is stored and it is compared in constant time. There is no endpoint that lists models.
- **Data stays low-sensitivity by design:** do not upload real confidential financial data to a public deployment; saved models are readable by anyone who has the link, and the database is not encrypted beyond the hosting provider's defaults.
- **The write token is kept in the browser's `localStorage`.** Anyone with access to that browser profile can edit the model. Clear site data on shared machines.
- **Input handling:** all request bodies are validated by Pydantic schemas (types, ranges, unknown fields rejected, array lengths bounded); body size is capped; SQL goes through SQLAlchemy parameters; validation errors never echo submitted values; unexpected errors return a generic message and are logged server-side.
- **Output handling:** React escapes by default and no raw HTML is rendered; CSV exports neutralise text cells that begin with `= + - @`.
- **HTTP hardening:** `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, HSTS in production, no CORS by default, API docs disabled in production, per-client rate limiting on state-changing requests (per instance, in memory).
- **Container:** runs as a non-root user.
- **Dependencies:** `pip-audit` and `npm audit` run in CI; Dependabot proposes updates weekly.

## Known gaps

- No secret-scanning step in CI. Enable GitHub's secret scanning and push protection in the repository settings.
- Rate limiting is per instance and resets on restart; it is not a defence against distributed abuse.
- Automated checks passing does not mean the system is secure; no external penetration test has been done.
