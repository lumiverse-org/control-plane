# Lane 2 — Pipeline & Evidence — Handoff Document

**Lane:** L2 (Pipeline & Evidence — Subsystems E and F)
**Branch prefix:** `lane/2/*`
**Merge-train position:** 3rd of 5 — L1 → L4 → L2 → L3 → L5
**Authoritative task plan:** `L2-05-tasks.md` (76 tasks)

---

## What Lane 2 published and where — by consumer

| Consumer | Published artifact | Where |
| --- | --- | --- |
| Lane 5 (branch protection) | the required-status-check context names (15 contexts in 3 groups) | `templates/workflows/required-checks.yaml` |
| Lane 3 (`create-product`) | the workflow templates, their placeholders and their rendering conditions | `templates/workflows/MANIFEST.yaml`, `templates/workflows/PLACEHOLDERS.yaml` |
| Lane 3 (reconciler, §53.1) | the consumed reusable-workflow tag and its resolved commit SHA | the `publish-workflow-tag.yml` run output |
| Lane 4 (records) | the record and event kinds Lane 2 writes (deployment, uat, restore-test, eval, events/) | `tools/evidence/HANDOFF.md` (this file) |
| L0 | the eight open decisions and their current state | `L2-05-tasks.md` §1 |

---

## Record and event kinds written by Lane 2

| Kind | Writer | Schema owner |
| --- | --- | --- |
| `deployment` | `tools/evidence/records_client.py` | Lane 4 (`schemas/records/**`) |
| `uat` | `tools/evidence/records_client.py` | Lane 4 |
| `restore-test` | `tools/evidence/records_client.py` | Lane 4 |
| `eval` | `tools/evidence/records_client.py` | Lane 4 |
| production_deployed event | `tools/evidence/event_writer.py` | Lane 4 |
| staging_deployed event | `tools/evidence/event_writer.py` | Lane 4 |

---

## Open decisions at handoff

See `L2-05-tasks.md` §1 for the full list. All eight are still open at the time this file is written. No decision in §1 was resolved by Lane 2; each is L0's to answer.

---

## DoD status

`acceptance_matrix.py` is the machine-readable gate. `checked=20 failed=0` is the only closing state.

```
python -m tools.evidence.acceptance_matrix --summary
```

Expected: `OK acceptance_matrix checked=20 failed=0`

---

## Owned paths (exclusive)

- `.github/workflows/**`
- `templates/workflows/**`
- `tools/evidence/**`

Lane 2 wrote no file outside these three trees. DoD-20 and the §0.3 close block on every task enforce this claim across the full cycle history.
