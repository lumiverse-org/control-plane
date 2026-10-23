# Lane 3 — Reconciler & Provisioning — Handoff Manifest

**Lane:** L3 (Reconciler, Provisioning & Repository Automation)
**Charter / Spec:** MultiProduct MasterSpec Section 53, Section 12, Section 19, Section 100
**Authoritative task plan:** `L3-06-tasks.md`

---

## Handoff to Consumers

| Consumer | Lane 3 hands over | Lane 3 does not build |
| --- | --- | --- |
| **L5** (`ops-vm/**`) | `python -m reconciler.cli run --live` as the scheduled entry point, its exit-code contract (§0.5), its expected source host and run-count ceiling (L3-P5-07) | the systemd timer or any ops-VM configuration |
| **L2** (`.github/workflows/**`) | `python -m validators.drift.verifier --live` as the scheduled entry point, and the requirement that it run under `DRIFT_VERIFIER_TOKEN`, a credential distinct from the reconciler's (§53.1) | the workflow YAML, or the surface it writes its result to |
| **L4** (`records/**`, `schemas/records/**`) | run records, drift findings and repair records as contract-shaped objects, handed over for writing | any write to `records/**` or `events/**` — AT-110 attempt 5 forbids it |

---

## Boundaries and Prohibitions

1. **No foreign path writes:** Lane 3 code never writes to `records/`, `events/`, `.github/workflows/`, or `ops-vm/`.
2. **Read-only state port:** GitHub state is read through `reconciler.state.port.GitHubState`; the detect path physically cannot write.
3. **No direct credentials in developer environment:** Reconciler operates under bounded service identity.
4. **Stricter-only repair:** Auto-repair moves only toward declared stricter state; never loosens any control.

---

## Acceptance Matrix Status

All eleven Section 100 acceptance tests pass against `fixture-a`:
```
python -m reconciler.acceptance.run_matrix --summary
```
Expected output: `MATRIX passed=11 total=11`.
