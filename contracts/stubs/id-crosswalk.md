# Master Identifier Crosswalk Fixture (FD-082, §97, §98, §100)

This crosswalk fixture provides canonical identifier normalization across all build lanes (L0, L1, L2, L3, L4, L5).

## 1. Lane Tasks Normalization (FD-082)
- Format: `L<Lane>-<Feature>-<Task>` (e.g. `L0-00-01`, `L1-05-01`, `L4-P1-01`).

## 2. Invariant Normalization
- All 111 Invariants indexed as `INV-001` .. `INV-111`.
- Categorized into `mechanical`, `policy`, and `review-held` per Invariant Classification Contract.

## 3. Acceptance Test Normalization
- All 110 Acceptance Tests indexed as `AT-001` .. `AT-110`.
- Negative Twins indexed as `NT-<ID>`.
- Entry Criteria indexed as `EC-001` .. `EC-112`.

## 4. Signal Normalization
- Signals indexed as `SIG-01` .. `SIG-52`.
