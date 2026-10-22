"""R-CHG-03 -- an authority delta: access_status for a person changed with
no linked decision record (Section 26.4).

Standalone, directly-tested rule module -- not wired into the frozen Option B
R01-R18 dispatch table (validators/registry/rules/registry.py; FD-094,
contracts/validator-contract.md: "Any change to this interface requires a new
FD entry"). Follows the same adaptation as r_svc_01.py, r_exc_01.py and
r_inv_01.py: a check_document() entry point the tests call directly, plus an
Option-B-shaped check() wrapper kept for parity, not exercised by this task's
own ACCEPTANCE commands.
"""
from __future__ import annotations

from validators.registry import diffcheck

RULE_ID = "R-CHG-03"
SPEC = "Section 26.4"
APPLIES_TO = ["people"]


def check_document(
    base: dict | None,
    head: dict,
    commit_message: str,
    source: str = "<document>",
) -> tuple[bool, list[str]]:
    """base is None when no base revision is available at all (mirrors
    ctx.git_base is None in the superseded design) -- returns (True, [])
    immediately in that case, no matter what head contains."""
    if base is None:
        return True, []
    if diffcheck.linked_decision_records(commit_message):
        return True, []
    findings = [
        f"{RULE_ID} {source}: authority delta: access_status for '{person_id}' changed from "
        f"'{old}' to '{new}' with no linked decision record; {SPEC}"
        for person_id, old, new in diffcheck.changed_access_status(base, head)
    ]
    return len(findings) == 0, findings


def check(registry_root, as_of, records_root=None):
    """Option-B-shaped wrapper. Diffs registries/people.yaml under registry_root
    against REGISTRY_DIFF_BASE."""
    base_info = diffcheck.load_git_base(
        registry_root,
        {"people": "registries/people.yaml"},
    )
    if base_info is None:
        return True, []
    import yaml
    from pathlib import Path

    head_path = Path(registry_root) / "registries" / "people.yaml"
    if not head_path.exists():
        return True, []
    head_doc = yaml.safe_load(head_path.read_text(encoding="utf-8")) or {}
    base_doc = base_info.docs.get("people")
    if base_doc is None:
        return True, []
    return check_document(base_doc, head_doc, base_info.commit_message, source="registries/people.yaml")
