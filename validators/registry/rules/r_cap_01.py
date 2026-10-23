"""R-CAP-01 — undefined capability rejected.

Section 9.1 defines a closed vocabulary of capabilities (Invariant 11).
The schema's own enum in schemas/registry/common/defs.v1.schema.json already
denies an out-of-scope value structurally; this rule is the live check that
names the failure for CI/report purposes, so the invariant register (L1-902)
has a concrete check ID to reference.

See the module docstring of r_svc_01.py for why this is not wired into the
frozen Option B (FD-094) dispatch engine (validators/registry/rules/registry.py).

Call signature matches Option B: `check(registry_root, as_of, records_root=None) -> (passed, findings)`.
"""
from __future__ import annotations

from pathlib import Path
import yaml

RULE_ID = "R-CAP-01"
SPEC = "Section 9.1"
APPLIES_TO = ["roles", "people"]

# Verbatim copy of schemas/registry/common/defs.v1.schema.json $defs.capability.enum.
# Section 9 is the complete vocabulary (§9.1) -- do not add to this set here;
# a token missing from both this set AND the schema enum is a schema-authoring
# concern (L1-101/L1-102), never something this rule silently accepts.
_CAPABILITY_ENUM = frozenset({
    "backend", "frontend", "mobile", "data",
    "code-review", "architecture", "security-review", "migration-review",
    "verification", "uat", "release-signoff", "production-approval",
    "incident-response", "plan-approval", "reviewer-matrix-change", "platform-change-approval",
    "platform-admin", "devops", "lifecycle-decision", "escalation",
    "mobile-release", "exceptional-approval", "people-intelligence", "strategy",
    "budget", "hiring", "customer-commitment",
})


def check_roles_document(doc, source="roles.yaml"):
    """Check one already-parsed roles.yaml-shaped document (registry_version +
    roles[] per schemas/registry/roles.registry.v1.schema.json) for a
    default_capabilities[] token outside the Section 9 vocabulary.

    Returns (passed, findings) -- same (bool, list[str]) convention as
    r_tol_01.check_document / r_pat_01.check_document / r_pol_01.check_document.
    """
    findings = []
    if not isinstance(doc, dict):
        return True, []
    for idx, role in enumerate(doc.get("roles") or []):
        if not isinstance(role, dict):
            continue
        for tok_idx, token in enumerate(role.get("default_capabilities") or []):
            if token not in _CAPABILITY_ENUM:
                findings.append(
                    f"R-CAP-01 {source}:/roles/{idx}/default_capabilities/{tok_idx} "
                    f"undefined capability '{token}'; Section 9 is the complete vocabulary"
                )
    return len(findings) == 0, findings


def check_people_document(doc, source="people.yaml"):
    """Check one already-parsed people document for capabilities outside Section 9 vocabulary.
    Supports either:
    - Multi-person document: doc has `people: [...]`
    - Single-person document: doc has top-level `capabilities: [...]`

    Returns (passed, findings).
    """
    findings = []
    if not isinstance(doc, dict):
        return True, []
    if "people" in doc and isinstance(doc["people"], list):
        for idx, person in enumerate(doc.get("people") or []):
            if not isinstance(person, dict):
                continue
            for tok_idx, token in enumerate(person.get("capabilities") or []):
                if token not in _CAPABILITY_ENUM:
                    findings.append(
                        f"R-CAP-01 {source}:/people/{idx}/capabilities/{tok_idx} "
                        f"undefined capability '{token}'; Section 9 is the complete vocabulary"
                    )
    elif "capabilities" in doc and isinstance(doc["capabilities"], list):
        for tok_idx, token in enumerate(doc.get("capabilities") or []):
            if token not in _CAPABILITY_ENUM:
                findings.append(
                    f"R-CAP-01 {source}:/capabilities/{tok_idx} "
                    f"undefined capability '{token}'; Section 9 is the complete vocabulary"
                )
    return len(findings) == 0, findings


def check(registry_root, as_of, records_root=None):
    """Option B entry point (FD-094 call signature): check(registry_root, as_of,
    records_root=None) -> (passed, findings). Scans registries/roles.yaml,
    registries/people/*.yaml (and flat people.yaml fallback) under registry_root
    and, if given, records_root.
    """
    roots = [Path(registry_root)]
    if records_root:
        roots.append(Path(records_root))
    findings = []

    for root in roots:
        # Check roles document
        for candidate in (
            root / "registries" / "roles.yaml",
            root / "roles.yaml",
        ):
            if not candidate.exists() or not candidate.is_file():
                continue
            try:
                doc = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                findings.append(f"R-CAP-01 {candidate}: could not parse YAML: {e}")
                continue
            _, doc_findings = check_roles_document(doc, source=str(candidate))
            findings.extend(doc_findings)

        # Check directory-based people registry (FD-119)
        for people_dir in (
            root / "registries" / "people",
            root / "people",
        ):
            if people_dir.exists() and people_dir.is_dir():
                for person_file in sorted(people_dir.glob("*.yaml")):
                    if person_file.name.startswith("_"):
                        continue
                    try:
                        doc = yaml.safe_load(person_file.read_text(encoding="utf-8"))
                    except yaml.YAMLError as e:
                        findings.append(f"R-CAP-01 {person_file}: could not parse YAML: {e}")
                        continue
                    _, doc_findings = check_people_document(doc, source=str(person_file))
                    findings.extend(doc_findings)
                break

        # Check flat people document (legacy / fixture fallback)
        for candidate in (
            root / "registries" / "people.yaml",
            root / "people.yaml",
        ):
            if not candidate.exists() or not candidate.is_file():
                continue
            try:
                doc = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                findings.append(f"R-CAP-01 {candidate}: could not parse YAML: {e}")
                continue
            _, doc_findings = check_people_document(doc, source=str(candidate))
            findings.extend(doc_findings)

    return len(findings) == 0, findings
