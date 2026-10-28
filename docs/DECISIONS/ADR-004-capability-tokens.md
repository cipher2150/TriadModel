# ADR-004: Capability tokens instead of user accounts

Status: accepted · Date: 2026-10-28

## Context
Users want to save and share models. Building accounts, passwords or OAuth would dominate the project and add a large attack surface, while the data is illustrative.

## Decision
No accounts. A model's UUID grants read access; a random write token (returned once, stored hashed, compared in constant time) grants update and delete. No list endpoint, so models cannot be enumerated. Updates use optimistic locking: an atomic `UPDATE ... WHERE version = n`, returning 409 on a stale version.

## Consequences
Simple and testable. Anyone with the link can read a model, and a lost write token cannot be recovered (a copy can be made via export/import). Not suitable for confidential data; documented in SECURITY.md. Private multi-user workspaces would need real authentication.
