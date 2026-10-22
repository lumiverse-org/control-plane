# MERGE TRAIN RUNBOOK

## 9. The merge train

Fixed order, once per cycle: **L1 → L4 → L2 → L3 → L5.** The order is dependency order (PARTITION.md §"Dependency order"): L1 schemas and L4 record schemas produce what everything validates against; L2 workflows consume L1 schemas; L3 consumes L1 plus the L5 access model; L5 integrates last.

Per lane, in order:

1. Confirm the lane branch is rebased on `integration` and is less than one day old.
2. Run `make lane-guard LANE=<n> BASE=integration HEAD=<branch>` — must print `LANE-GUARD OK`.
3. Run the lane's own SELF-VERIFY block from its plan file — must produce its stated expected output.
4. Merge to `integration` with `--no-ff`.
5. Re-run steps 2–3 for the merged result before starting the next lane.

If any step fails, that lane is **skipped for the cycle** — the train does not stop for it, and the remaining lanes merge in order behind it. Skipping is L0's call and is recorded; a lane never negotiates its own skip. Revert versus roll-forward on a broken `integration` is L0D-08.

Promotion `integration → main` (L0D-09) happens only when `make promote-check` passes, and never after Friday 15:00.

---

## Cycle Log

<!-- CYCLE-LOG:BEGIN -->
| cycle | date | L1 | L4 | L2 | L3 | L5 | promoted | notes |
|---|---|---|---|---|---|---|---|---|
<!-- CYCLE-LOG:END -->
