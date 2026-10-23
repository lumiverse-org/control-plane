# Record and Event Schema Versioning Policy

Master Spec v4.0 Section 60.2 and Section 97.2 line 8888.

## Principles

1. **Versioned Contracts**: Record and event schemas are immutable contracts.
2. **Never Replace**: Per §60.2, write v2 alongside v1 — do not replace or edit an existing schema version in place.
3. **Retire, Never Remove**: When a schema version is superseded, it is marked `retired: true` in `versions.yaml`. It is never deleted from the repository so that historical records and events remain verifiable for their full retention lifespan.
4. **Register**: All active and retired schemas are cataloged in `schemas/records/versions.yaml`.
