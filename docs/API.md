# API

JSON over HTTP, same origin as the UI. In development, interactive docs are at `/docs`. All amounts are decimal **strings** (responses rounded to 4 decimal places); rates are fractions (`0.08` = 8%); working-capital days are plain numbers.

There is no user authentication. Access to a saved model uses capability tokens:

- The model **id** (a random UUID) grants read access: it is the share link.
- The **write token**, returned once at creation, grants update and delete via the `X-Write-Token` header. Only its SHA-256 hash is stored.
- There is deliberately **no list endpoint**; models cannot be enumerated.

## Endpoints

| Method and path | Auth | Description |
|---|---|---|
| `GET /health/live` | none | Liveness: `{"status":"ok"}` |
| `GET /health/ready` | none | Readiness: 200 if the database answers, else 503 |
| `GET /api/demo` | none | Demo `ModelPayload`, `is_demo: true` |
| `POST /api/calculate?include_trace=false` | none | Calculate all three scenarios without saving |
| `POST /api/models` | none | Save a model. 201 with `write_token` |
| `GET /api/models/{id}` | id | Model plus calculated result |
| `PUT /api/models/{id}` | write token | Body `{"version": n, "model": ModelPayload}`. 409 if `version` is stale |
| `DELETE /api/models/{id}` | write token | 204 |
| `GET /api/models/{id}/export?format=json\|csv&scenario=base` | id | JSON payload, or CSV of the chosen scenario's statements (history + forecast) |

Unmatched `/api/*` and `/health/*` paths return a JSON 404; any other unmatched GET returns the single-page app so client-side links work.

## ModelPayload

```jsonc
{
  "company_name": "Demo Co (illustrative data)",
  "is_demo": true,
  "tolerance": "0.01",                 // allowed difference in accounting identities
  "historicals": [                      // 1-5 contiguous ascending years
    { "year": 2024,
      "income_statement": { "revenue": "2825", "cogs": "...", "sga": "...", "depreciation": "...", "interest_expense": "...", "tax_expense": "..." },
      "balance_sheet":    { "cash": "...", "accounts_receivable": "...", "inventory": "...", "other_current_assets": "...", "ppe_net": "...",
                            "accounts_payable": "...", "other_current_liabilities": "...", "revolver": "...", "term_loan": "...",
                            "common_stock": "...", "retained_earnings": "..." },
      "cash_flow":        { "beginning_cash": "...", "net_income": "...", "depreciation": "...", "change_in_receivables": "...", "...": "..." } }
  ],
  "scenarios": {                        // exactly base, upside, downside; same length (1-10 years)
    "base": [ { "revenue_growth": "0.08", "cogs_pct": "0.60", "sga_pct": "0.21", "depreciation_rate": "0.10",
                "capex_pct": "0.08", "dso": "36.5", "dio": "55", "dpo": "38", "tax_rate": "0.25",
                "term_loan_rate": "0.05", "revolver_rate": "0.07", "cash_yield": "0.02",
                "term_loan_repayment": "40", "min_cash": "150", "revolver_limit": "300", "dividend_payout": "0.30" } ],
    "upside": [ "..." ], "downside": [ "..." ]
  }
}
```

Cash-flow items are signed: positive = inflow. Every historical balance sheet must balance within `tolerance`; unknown fields are rejected. Field bounds are enforced by the schemas in `backend/app/schemas/model.py`.

## Result

`CalculationOut`: `company_name`, `is_demo`, `historicals[]`, and `scenarios.{base,upside,downside}` each with `years[]` (income statement, balance sheet, cash flow with derived totals), `flags[]` and, only with `include_trace=true`, `trace` (calculation-node key → `{formula, inputs, value}`).

A flag is `{code, severity: "error"|"warning", year, message, amount}`. Financial problems are always flags in a 200 response, never HTTP errors. Codes: `BS_IMBALANCE`, `CASH_TIE_OUT`, `NI_TIE_OUT`, `RE_ROLLFORWARD`, `PPE_ROLLFORWARD`, `DEBT_ROLLFORWARD`, `REVOLVER_LIMIT_EXCEEDED`, `NEGATIVE_CASH`, `CASH_BELOW_MINIMUM`, `NEGATIVE_EQUITY`.

## Errors

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Request validation failed",
             "details": [ { "location": "body.scenarios.base.2.tax_rate", "message": "Input should be less than or equal to 1" } ] } }
```

| Status | `code` | When |
|---|---|---|
| 403 | `FORBIDDEN` | Missing or wrong write token |
| 404 | `NOT_FOUND` | Unknown model or route |
| 405 | `METHOD_NOT_ALLOWED` | Wrong method on a known route |
| 409 | `VERSION_CONFLICT` | `PUT` based on a stale `version` |
| 413 | `PAYLOAD_TOO_LARGE` | Body above `MAX_REQUEST_BYTES` |
| 422 | `VALIDATION_ERROR` / `INVALID_MODEL` | Invalid input (details name the field, never echo the value) |
| 429 | `RATE_LIMITED` | Over the per-minute limit; `Retry-After` header set |
| 500 | `INTERNAL_ERROR` | Unexpected; generic message, details only in server logs |

## Examples

```bash
curl -s localhost:8000/api/demo > demo.json
curl -s -X POST localhost:8000/api/calculate -H 'content-type: application/json' -d @demo.json
curl -s -X POST localhost:8000/api/models    -H 'content-type: application/json' -d @demo.json   # note write_token
curl -s -X PUT  localhost:8000/api/models/$ID -H "X-Write-Token: $TOKEN" -H 'content-type: application/json' \
     -d "{\"version\": 1, \"model\": $(cat demo.json)}"
```
