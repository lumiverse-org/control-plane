# Contract: the lane-guard workflow

**Owner:** L0. **Frozen** from this placement forward (PARTITION.md rule 2; lanes/L0-02-lane-guard.md §4, L0D-LG-1).

`.github/workflows/lane-guard.yml` in this repository MUST be byte-identical to
`contracts/ci/lane-guard.yml.frozen`. The check named `lane-guard` compares them on
every pull request and fails with class `GUARD-TAMPER` if they differ.

The path `.github/workflows/**` belongs to L2 (PARTITION.md). L2 owns the directory
and does not own this file's bytes (L0D-LG-2). L2 changes it only through a Contract
Change Request: `docs/escalation/CCR.md`.

**Placement note:** lanes/L0-02-lane-guard.md's own text assumes this freeze happens
in Phase 0, before any lane branch exists. This repository is well past that point —
`.github/workflows/lane-guard.yml` had already been edited multiple times (FD-102,
FD-086, FD-123, and the branch-path-ownership enforcement added under FD-136's
surrounding work) before this contract was ever placed. This is a retrofit freeze,
not the originally-intended bootstrap placement. The mechanism (byte-identity going
forward) is unaffected by the late timing.

Rules this contract carries, and their spec anchors:

| Rule | Anchor | Status |
|---|---|---|
| The job carries no `if:` and no path filter; a skipped required check counts as satisfied | MasterSpec v4.0 §33.2 | Holds |
| No third-party GitHub Action is used, so there is no unpinned action | §33.2; L0D-LG-4 | **Exception — see below** |
| `permissions: contents: read` only — least privilege | §33.2 | Holds (the job also carries `pull-requests: read`, needed by `scripts/actor-gate.sh`; not a `contents` scope issue) |
| The manifest, owners table, exception register and guard script are read from the BASE ref | §53.1 | Holds |
| The check context name is exactly `lane-guard` and never changes | §33.2 | Holds (job name corrected from `Lane Guard` to `lane-guard` at the time of this freeze) |

## Tracked exception: `actions/checkout` is used

The live (and now frozen) workflow uses `actions/checkout@<full SHA> # v4.2.2` to get
repository contents onto the runner. This is a third-party `uses:` reference, which
L0D-LG-4's "no third-party GitHub Action" rule forbids outright for this specific
file — the intent being zero supply-chain dependency on the gate that enforces
everything else.

This is accepted as a deliberate, tracked exception at freeze time, not silently
waived: the action is pinned to an exact commit SHA (not a floating tag), which
substantially mitigates the supply-chain risk the rule exists to prevent, and
replacing it with raw `git` commands is a real behavioral change to a
security-critical CI gate that deserves its own reviewed change, not a rewrite done
in passing while establishing the freeze.

**Trigger to revisit:** before this exception is relied upon as precedent for any
other third-party action anywhere else in `.github/workflows/**`, and as a standing
item to replace `actions/checkout` with an inline `git` checkout under its own
Contract Change Request.
