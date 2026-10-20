"""Contract map — the five frozen ``contracts/**`` paths Lane 3 reads.

L3-D2 (``lanes/L3-06-tasks.md`` §1) asked L0 to name, verbatim, the five
``contracts/**`` paths Lane 3 consumes: the drift finding, the reconciliation
run record, the repair record, the branch-protection template and the
environment template. This module copies those five paths verbatim and
nothing else. Per ``PARTITION.md`` rule 2 and L3-06-tasks.md §0.1, Lane 3
never creates or edits anything under ``contracts/**`` — this module only
reads it.

Paths recorded here are copied verbatim from the answer L0 authored directly
into the contract files themselves (each file's own ``_description``/
``description`` field states its L3-D2 role and its ``contracts_map.py``
``CONTRACTS`` key by name, and is dated "Founder confirmed, 2026-09-16"):

  - contracts/reconciler/drift-finding.v1.schema.json
  - contracts/reconciler/run-record.v1.schema.json
  - contracts/reconciler/repair-record.v1.schema.json
  - contracts/reconciler/branch-protection-template.v1.json
  - contracts/reconciler/environment-template.v1.json

KNOWN GAP (see notes returned alongside this task): as of this writing these
five files exist only on the yet-unmerged branch that authored them
(``chore/port-governance-decisions``, pushed to
``origin/chore/port-governance-decisions``); none of the five is present on
``origin/integration`` yet. ``load()`` below therefore raises
``FileNotFoundError`` for every key until that branch lands on
``integration``. This is a landing-order gap upstream of Lane 3, not an
invented value — no path below has been substituted or guessed.
"""

import json
from pathlib import Path

CONTRACTS = {
    "drift_finding": "contracts/reconciler/drift-finding.v1.schema.json",
    "run_record": "contracts/reconciler/run-record.v1.schema.json",
    "repair_record": "contracts/reconciler/repair-record.v1.schema.json",
    "branch_protection_template": "contracts/reconciler/branch-protection-template.v1.json",
    "environment_template": "contracts/reconciler/environment-template.v1.json",
}


def load(key):
    """Read and parse the JSON contract at ``CONTRACTS[key]``.

    Raises ``FileNotFoundError`` naming the key (and the path it maps to)
    when the contract is absent.
    """
    path = CONTRACTS[key]
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"contracts_map: {key!r} -> {path!r} does not exist")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)
