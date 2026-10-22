"""R-INV-02 -- Invariant classification register and its CI rule (L1-902).

Spec anchor: Section 101 preamble; Section 55; Section 52.6; Section 0.7.
Task: lanes/L1-05-tasks.md, L1-902.

Section 101 preamble:
"Each of the 111 is exactly one of: mechanical, naming the CI check,
branch-protection rule, reconciliation row or AT- identifier that enforces it;
policy, naming the policies.yaml entry that carries its owner, review date and
enforcement mechanism (Section 55); or review-held, naming the standing review
that reads it and the role that chairs that review. ... Control-plane CI fails
when an invariant classified mechanical names no live check or AT- identifier,
when one classified policy names no live policies.yaml entry, or when any
invariant carries no classification at all."

Five limbs:
(a) classification absent or null -> error
(b) classification == mechanical: enforced_by must not be null, must be a
    RULE_ID in RULES.md / known rule catalogue or match ^AT-\\d{3}$
(c) classification == policy: policy_id must match a policy in policies.yaml
    (returns zero errors when policies.yaml is absent from ctx.docs, per R-PPL-04)
(d) classification == review-held: review and chair must both be non-null
(e) invariants non-empty and len(invariants) != declared_count -> count mismatch
    (Limb e applies ONLY to a non-empty register; a file shipping invariants: []
    is an unpopulated register, not a miscounted one, and firing on it every run
    would make the rule noise from day one).

Standalone, directly-tested rule function -- see r_inv_01.py's docstring for
why this is not wired into the frozen Option B (FD-094) R01-R18 dispatch table.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

RULE_ID = "R-INV-02"
SPEC = "Section 101 preamble"
APPLIES_TO = ["invariants", "policies"]

_AT_IDENTIFIER_PATTERN = re.compile(r"^AT-\d{3}$")
_RULE_ID_PATTERN = re.compile(r"^R[0-9]{2}$|^R-[A-Z0-9]+-[0-9]{2}$")


def get_known_rule_ids(rules_dir: Path | None = None, rules_md_path: Path | None = None) -> set[str]:
    """Discover known rule IDs from Python rule files and RULES.md if present."""
    known: set[str] = {
        # Standard frozen Option B rules
        f"R{i:02d}" for i in range(1, 19)
    }
    # Also add hyphenated variants R-01..R-18
    known.update(f"R-{i:02d}" for i in range(1, 19))

    # Scan rules directory
    if rules_dir is None:
        rules_dir = Path(__file__).parent

    if rules_dir.is_dir():
        for py_file in rules_dir.glob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                matches = re.findall(r'RULE_ID\s*=\s*["\']([^"\']+)["\']', content)
                known.update(matches)
            except Exception:
                pass

    # Scan RULES.md if it exists
    if rules_md_path and Path(rules_md_path).is_file():
        try:
            content = Path(rules_md_path).read_text(encoding="utf-8")
            for token in re.findall(r"\b(R-[A-Z0-9]+-[0-9]{2}|R[0-9]{2})\b", content):
                known.add(token)
        except Exception:
            pass

    return known


def check_document(
    doc: dict[str, Any] | None,
    policies_doc: dict[str, Any] | None = None,
    known_rules: set[str] | None = None,
    source: str = "registries/invariants.yaml",
) -> tuple[bool, list[str]]:
    """Check one parsed invariants.yaml document against R-INV-02.

    Returns (passed: bool, findings: list[str]).
    """
    if not isinstance(doc, dict):
        return True, []

    if known_rules is None:
        known_rules = get_known_rule_ids()

    findings: list[str] = []

    declared_count = doc.get("declared_count")
    invariants = doc.get("invariants") or []

    # Limb (e): invariants non-empty and len(invariants) != declared_count
    # Note: limb e applies only to a non-empty register.
    if len(invariants) > 0 and declared_count is not None and len(invariants) != declared_count:
        findings.append(
            f"R-INV-02 {source}:/invariants the invariant register holds {len(invariants)} "
            f"entries; declared_count is {declared_count}; Section 101 states 111"
        )

    # Collect live policy ids if policies_doc is provided
    # If policies_doc is None (absent from ctx.docs), limb c returns zero errors.
    known_policy_ids: set[str] | None = None
    if policies_doc is not None and isinstance(policies_doc, dict):
        known_policy_ids = {
            p.get("id")
            for p in policies_doc.get("policies", [])
            if isinstance(p, dict) and p.get("id")
        }

    for idx, inv in enumerate(invariants):
        if not isinstance(inv, dict):
            continue

        num = inv.get("number", idx + 1)
        classification = inv.get("classification")

        # Limb (a): classification absent or null
        if classification is None:
            findings.append(
                f"R-INV-02 {source}:/invariants/{idx}/classification invariant {num} "
                f"carries no enforcement classification; Section 101"
            )
            continue

        # Limb (b): classification == mechanical
        if classification == "mechanical":
            enforced_by = inv.get("enforced_by")
            is_valid_enforcement = False
            if enforced_by is not None and isinstance(enforced_by, str):
                if _AT_IDENTIFIER_PATTERN.match(enforced_by):
                    is_valid_enforcement = True
                elif enforced_by in known_rules:
                    is_valid_enforcement = True

            if not is_valid_enforcement:
                findings.append(
                    f"R-INV-02 {source}:/invariants/{idx}/enforced_by invariant {num} "
                    f"is classified mechanical and names no live check or AT- identifier; Section 101"
                )

        # Limb (c): classification == policy
        elif classification == "policy":
            if known_policy_ids is not None:
                policy_id = inv.get("policy_id")
                if not policy_id or policy_id not in known_policy_ids:
                    findings.append(
                        f"R-INV-02 {source}:/invariants/{idx}/policy_id invariant {num} "
                        f"is classified policy and names no live policies.yaml entry; Section 101"
                    )

        # Limb (d): classification == review-held
        elif classification == "review-held":
            review = inv.get("review")
            chair = inv.get("chair")
            if not review or not chair:
                ptr = "review" if not review else "chair"
                findings.append(
                    f"R-INV-02 {source}:/invariants/{idx}/{ptr} invariant {num} "
                    f"is classified review-held and names no standing review or chairing role; Section 101"
                )

    return len(findings) == 0, findings


def check(registry_root: str | Path, as_of: Any = None, records_root: str | Path | None = None) -> tuple[bool, list[str]]:
    """Option B-compatible entry point (FD-094)."""
    root = Path(registry_root)
    inv_path: Path | None = None
    for cand in (root / "registries" / "invariants.yaml", root / "invariants.yaml"):
        if cand.is_file():
            inv_path = cand
            break

    if not inv_path:
        return True, []

    try:
        inv_doc = yaml.safe_load(inv_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, [f"R-INV-02 {inv_path.as_posix()} failed to load: {exc}"]

    pol_doc: dict[str, Any] | None = None
    roots = [root]
    if records_root:
        roots.append(Path(records_root))

    for r in roots:
        for cand in (r / "registries" / "policies.yaml", r / "policies.yaml"):
            if cand.is_file():
                try:
                    pol_doc = yaml.safe_load(cand.read_text(encoding="utf-8"))
                    break
                except Exception:
                    pass
        if pol_doc is not None:
            break

    rules_md_path = root / "RULES.md"
    if not rules_md_path.is_file():
        rules_md_path = root / "validators" / "registry" / "RULES.md"

    known_rules = get_known_rule_ids(
        rules_dir=root / "validators" / "registry" / "rules",
        rules_md_path=rules_md_path if rules_md_path.is_file() else None,
    )

    return check_document(
        inv_doc,
        policies_doc=pol_doc,
        known_rules=known_rules,
        source=inv_path.as_posix(),
    )
