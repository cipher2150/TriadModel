# ADR-003: A minimal explicit dependency graph for forecast lines

Status: accepted · Date: 2026-10-28

## Context
The product's point is that changing an assumption propagates correctly. We also need the calculation to be explainable (formula and inputs per number) and need to detect circular references.

## Decision
Each forecast line is a node declaring its dependencies and a formula; the graph is topologically sorted, evaluated with each node seeing only its declared inputs, and cycles raise a `CycleError` naming the loop. Interest is computed on opening balances so the model has no intentional circularity. Rejected: hard-coded sequential calculation (no trace, no cycle detection, no change-impact tests) and a general spreadsheet engine (overkill).

## Consequences
About 100 lines of graph code buys the trace view, cycle detection and change-impact tests. Opening-balance interest is slightly less precise than average-balance interest, which would need bounded iteration (listed as future work).
