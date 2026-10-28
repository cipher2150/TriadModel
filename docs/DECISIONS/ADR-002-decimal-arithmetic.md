# ADR-002: Decimal arithmetic with an explicit tolerance

Status: accepted · Date: 2026-10-28

## Context
Financial statements must reconcile. IEEE-754 floats accumulate error and make 'does the balance sheet balance' ambiguous. Some formulas (days / 365) divide into non-terminating decimals even with Decimal.

## Decision
The engine uses Python `Decimal` at 28 digits of precision, set in one place. Accounting-identity checks compare within an absolute tolerance (default 0.01, configurable per model). Amounts cross the API as strings and are rounded to 4 places only on output. Rejected: floats, and integer cents (awkward for ratios and days).

## Consequences
Exact addition and subtraction; residual error is about 1e-25, far below the tolerance. Slower than floats, which is irrelevant here (0.43 ms median for a 5-year scenario). The UI converts to floating point for display only.
