"""R-EXC-00 -- week-one minimal exceptions.yaml validator (L1-108).

Section 54.5 Phase-1 completion check: "expiry, owner, deactivation trigger
present" and the validator must "reject a deliberately malformed
exception". Invariant 77: an exception with no expiry is a hard error.

Standalone, directly-tested rule function -- not wired into the frozen
Option B (FD-094) R01..R18 dispatch table in
validators/registry/rules/registry.py. contracts/validator-contract.md
freezes that catalogue ("R01 through R18... Any change to this interface
requires a new FD entry"); extending it for R-EXC-00 is not this task's
call to make, exactly as r_tol_01.py, r_svc_01.py and r_prd_11.py already
reason for their own rule ids. validators/registry/tests/test_exceptions_
minimal.py exercises this module directly against the fixtures named in
the task (validators/registry/fixtures/exceptions/<case>/exceptions.yaml),
not through validators/registry/cli.py.

The message format below -- "ERROR R-EXC-00 <path>:<json-pointer>
exception <id> has no expiry; invariant 77" -- reproduces verbatim the
line lanes/L1-05-tasks.md's SELF-VERIFY names for the pre-FD-094 CLI
grammar ("ERROR <RULE-ID> <path>:<pointer> <message>", contracts/
validator-contract.md's predecessor), so the substance of that expected
line is genuinely produced and tested here even though it is not
reachable by invoking the frozen cli.py end-to-end.
"""
from __future__ import annotations

from pathlib import Path

RULE_ID = "R-EXC-00"
SPEC = "Section 54.2 / invariant 77"
APPLIES_TO = ["exceptions"]


def check_document(doc: dict, source: str = "exceptions.yaml") -> "tuple[bool, list[str]]":
    """Check one already-parsed exceptions.yaml-shaped document.

    An exception whose `expiry` key is absent, or present but null, is a
    finding: "exception <id> has no expiry; invariant 77". Returns
    (passed, findings) where findings are full CLI-grammar-style lines,
    one per offending exception, in document order.
    """
    findings = []
    if not isinstance(doc, dict):
        return True, []
    exceptions = doc.get("exceptions") or []
    for idx, exc in enumerate(exceptions):
        if not isinstance(exc, dict):
            continue
        if exc.get("expiry") is None:
            exc_id = exc.get("id", "<unknown>")
            findings.append(
                f"ERROR R-EXC-00 {source}:/exceptions/{idx} exception {exc_id} "
                f"has no expiry; invariant 77"
            )
    return len(findings) == 0, findings


def check(registry_root, as_of, records_root=None) -> "tuple[bool, list[str]]":
    """Option B call-signature entry point: check registries/exceptions.yaml
    under registry_root, when it exists. Silent (passes) when the file is
    absent -- the week-one registry is optional until Section 54.5's first
    bootstrap entry lands."""
    root = Path(registry_root)
    path = root / "registries" / "exceptions.yaml"
    if not path.exists():
        return True, []

    import yaml

    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return False, [f"R-EXC-00 {path}: could not parse YAML: {e}"]

    return check_document(doc, source=str(path))
