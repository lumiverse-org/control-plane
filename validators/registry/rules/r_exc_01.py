"""R-EXC-01 -- an expired exception still open (Section 54.2, AT-037, SIG-19).

Section 54.2: an exception whose `expiry` has passed and which carries no
`closure` is still open past its own deadline. The boundary is strict `<` --
an exception expiring **today** is not yet expired (`valid/expires_today/`
proves it). This is the only date-sensitive rule among R-EXC-01..05; every
fixture pins `today` in its own `expect.yaml` so results are deterministic
regardless of wall-clock date.

This is a standalone, directly-tested rule module, not a module wired into
the FD-094 "Option B" dispatch engine (`validators/registry/cli.py` +
`validators/registry/rules/registry.py`, RULES = R01..R18). That interface
is frozen (`contracts/validator-contract.md`: "Rule identifiers: R01
through R18 with sub-codes... Any change to this interface requires a new
FD entry") and its rule-id space does not admit an `R-EXC-0n` token. Nor is
this module discovered via `validators.registry.rules.discover()` --
`validators/registry/README.md`'s ARCHITECTURE NOTE is explicit: "Do not
resurrect the module-discovery/RULE_ID/APPLIES_TO harness described in
lanes/L1-05-tasks.md task L1-005 ('Option D') -- FD-094 explicitly
supersedes it." `validators/registry/rules/__init__.py` is intentionally
empty for exactly this reason.

Follows the same standalone convention L1-201/L1-404/L1-501 already use
here (`r_svc_01.py`, `r_pat_01.py`, `r_tol_01.py`): module-level `RULE_ID`,
`SPEC`, `APPLIES_TO`, a `check_document(doc, today, source)` function for
direct testing, and a `check(registry_root, as_of, records_root=None)`
Option-B-shaped wrapper -- not registered in `registry.py`'s `RULES` list,
but callable the same way for later CLI wiring if an FD ever opens that
door. Unlike `r_pat_01`/`r_tol_01`, this wrapper honours `records_root`
(scanning `<records_root>/exceptions.yaml` when given) because L1-602's
own SELF-VERIFY commands need to point the checker at an isolated fixture
directory rather than the live `registries/exceptions.yaml` -- doing
otherwise would make the wrapper unable to ever observe a fixture.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

RULE_ID = "R-EXC-01"
SPEC = "Section 54.2"
APPLIES_TO = ["exceptions"]


def check_document(doc, today, source="exceptions.yaml"):
    """Check one already-parsed exceptions.yaml-shaped document.

    ``today`` is an ISO date string (or ``datetime.date``) standing in for
    ``ctx.today`` -- the CLI's ``--as-of``/``--today`` value. Returns
    (passed, findings) where findings are ``R-EXC-01`` message strings.
    """
    if not isinstance(doc, dict):
        return True, []

    if isinstance(today, date):
        today_date = today
    else:
        try:
            today_date = date.fromisoformat(str(today))
        except ValueError:
            return False, [f"{RULE_ID} {source}: invalid --today/--as-of date: {today!r}"]

    findings = []
    for idx, exc in enumerate(doc.get("exceptions", []) or []):
        if not isinstance(exc, dict):
            continue
        closure = exc.get("closure")
        if closure is not None:
            continue  # closed exceptions are never "still open"
        expiry = exc.get("expiry")
        if expiry is None:
            continue  # absence/shape is the schema's and R-EXC-00's job
        try:
            expiry_date = date.fromisoformat(str(expiry))
        except ValueError:
            continue  # malformed date shape is the schema's job, not this rule's
        if expiry_date < today_date:
            exc_id = exc.get("id", "<unknown>")
            findings.append(
                f"{RULE_ID} {source}:/exceptions/{idx}/expiry "
                f"exception '{exc_id}' expired on {expiry} and is still open; "
                f"Section 54.2, AT-037, SIG-19"
            )
    return len(findings) == 0, findings


def check(registry_root, as_of, records_root=None):
    """Option-B-shaped entry point: scan the exceptions.yaml under records_root
    (falling back to registry_root when records_root is not given)."""
    findings = []
    candidates = []
    if records_root:
        candidates.append(Path(records_root) / "exceptions.yaml")
    else:
        candidates.append(Path(registry_root) / "registries" / "exceptions.yaml")
        candidates.append(Path(registry_root) / "exceptions.yaml")

    for path in candidates:
        if not path.exists():
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            findings.append(f"{RULE_ID} {path}: could not parse YAML: {e}")
            continue
        _, doc_findings = check_document(doc, as_of, source=str(path))
        findings.extend(doc_findings)
    return len(findings) == 0, findings
