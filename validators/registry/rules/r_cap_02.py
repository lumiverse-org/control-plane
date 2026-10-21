"""R-CAP-02, R-CAP-03, R-CAP-04 -- role/people capability integrity
(L1-202, Section 8 (D106) / invariant 79; Section 8; Section 7.1).

Standalone, directly-tested rule functions -- see the module docstring of
``r_svc_01.py`` and ``r_inv_01.py`` for why these are not wired into the
frozen Option B (FD-094, ``contracts/validator-contract.md``) ``R01``..``R18``
dispatch table in ``validators/registry/rules/registry.py``. The CLI grammar
and ``discover()``/``RULE_ID``/``expect.yaml`` harness this task's own text
in ``lanes/L1-05-tasks.md`` describes predates FD-094 and is superseded by
it, exactly as already documented for R-SVC-01..03, R-INV-01/03 and
R-PPL-05/09/10/11/12. ``discover()`` was never added to
``validators/registry/rules/__init__.py`` (it ships empty); this task does
not add it either. All three rule ids below are bundled into this one file
-- matching the single artifact path this task tracks -- the same
consolidation ``r_ppl_05.py`` already makes for its own five rule ids.

Rules covered:

* R-CAP-02 -- a ``roles[].default_capabilities`` entry naming one of the
  eight ``dangerousCapability`` tokens (Section 8 / D106: these may only be
  granted to a specific person via an explicit ``people.yaml`` entry, never
  handed to everyone who holds a role by default).
* R-CAP-03 -- a duplicate ``roles[].id``. JSON Schema
  (``schemas/registry/roles.registry.v1.schema.json``) has no cross-item
  uniqueness constraint on an array of objects, so this is a genuine
  semantic-only check, not schema-redundant (contrast R-CAP-04 below).
* R-CAP-04 -- a ``people[].capabilities`` entry duplicated within one
  person's own list. ``schemas/registry/people.registry.v1.schema.json``
  already declares ``capabilities`` ``uniqueItems: true``, so on a
  schema-valid document this never fires -- exactly the same "the schema
  already denies; the rule exists so the invariant register can name a live
  check id" rationale L1-201's own task text gives for R-CAP-01. This
  module's tests call ``check_r_cap_04`` directly against a hand-built dict
  that was never run through jsonschema, so the duplicate is still
  observable here.

KNOWN RED, expected: Section 8's own ``founder`` role default (transcribed
verbatim into ``registries/roles.yaml`` by task L1-103) contains three
dangerous tokens (``lifecycle-decision``, ``exceptional-approval``,
``people-intelligence``) -- a contradiction the spec itself creates. L1-103's
own task text: "That contradiction is in the spec and resolving it is not
yours." This module reports it; it does not silence it, and the
``spec_founder_row`` fixture below is marked ``xfail`` for exactly this
reason, pending the ``BLOCKER L1 L1-103`` L0 decision.
"""
from __future__ import annotations

from pathlib import Path

import yaml

RULE_ID_DANGEROUS_DEFAULT = "R-CAP-02"
RULE_ID_DUPLICATE_ROLE_ID = "R-CAP-03"
RULE_ID_DUPLICATE_PERSON_CAPABILITY = "R-CAP-04"
SPEC = "Section 8 (D106); Section 7.1"
APPLIES_TO = ["roles", "people"]

# schemas/registry/common/defs.v1.schema.json $defs.dangerousCapability enum,
# transcribed verbatim -- update this tuple by hand if that enum ever changes.
DANGEROUS_CAPABILITIES = (
    "production-approval",
    "platform-change-approval",
    "platform-admin",
    "security-review",
    "migration-review",
    "exceptional-approval",
    "lifecycle-decision",
    "people-intelligence",
)


def check_r_cap_02(roles_doc: dict, source: str = "registries/roles.yaml") -> list[str]:
    """R-CAP-02 -- one finding per dangerous-capability token found in any
    role's ``default_capabilities``. Never inspects ``people.yaml`` -- an
    explicit per-person grant of the same token is exactly what D106 allows
    instead."""
    findings = []
    for role_idx, role in enumerate((roles_doc or {}).get("roles") or []):
        if not isinstance(role, dict):
            continue
        role_id = role.get("id", "<unknown-role>")
        defaults = role.get("default_capabilities") or []
        for cap_idx, token in enumerate(defaults):
            if token in DANGEROUS_CAPABILITIES:
                findings.append(
                    f"R-CAP-02 {source}:/roles/{role_idx}/default_capabilities/{cap_idx} "
                    f"dangerous capability '{token}' in role default '{role_id}'; "
                    f"D106 grants these only by explicit people.yaml entry"
                )
    return findings


def check_r_cap_03(roles_doc: dict, source: str = "registries/roles.yaml") -> list[str]:
    """R-CAP-03 -- one finding per role whose ``id`` repeats an id already
    seen earlier in the array (the first occurrence of an id is never
    itself a finding)."""
    findings = []
    seen = {}
    for role_idx, role in enumerate((roles_doc or {}).get("roles") or []):
        if not isinstance(role, dict):
            continue
        role_id = role.get("id")
        if role_id is None:
            continue
        if role_id in seen:
            findings.append(
                f"R-CAP-03 {source}:/roles/{role_idx} duplicate role id '{role_id}'"
            )
        else:
            seen[role_id] = role_idx
    return findings


def check_r_cap_04(people_doc: dict, source: str = "registries/people.yaml") -> list[str]:
    """R-CAP-04 -- one finding per capability token that repeats within one
    person's own ``capabilities`` list (one finding per distinct repeated
    token per person, not one per extra repeat)."""
    findings = []
    if not isinstance(people_doc, dict):
        return []

    if "people" in people_doc and isinstance(people_doc["people"], list):
        for person_idx, person in enumerate(people_doc.get("people") or []):
            if not isinstance(person, dict):
                continue
            person_id = person.get("id", "<unknown-person>")
            seen = set()
            reported = set()
            for token in person.get("capabilities") or []:
                if token in seen and token not in reported:
                    findings.append(
                        f"R-CAP-04 {source}:/people/{person_idx}/capabilities "
                        f"duplicate capability '{token}' on person '{person_id}'"
                    )
                    reported.add(token)
                seen.add(token)
    elif "capabilities" in people_doc and isinstance(people_doc["capabilities"], list):
        person_id = people_doc.get("id", "<unknown-person>")
        seen = set()
        reported = set()
        for token in people_doc.get("capabilities") or []:
            if token in seen and token not in reported:
                findings.append(
                    f"R-CAP-04 {source}:/capabilities "
                    f"duplicate capability '{token}' on person '{person_id}'"
                )
                reported.add(token)
            seen.add(token)

    return findings


def check_roles_document(roles_doc, source: str = "registries/roles.yaml"):
    """Run R-CAP-02 + R-CAP-03 against one already-parsed roles.yaml-shaped
    document. Returns ``(passed, findings)``. Silent when ``roles_doc`` is
    not a dict -- mirrors r_inv_01.check_document's "nothing to compare
    against" convention."""
    if not isinstance(roles_doc, dict):
        return True, []
    findings = check_r_cap_02(roles_doc, source=source) + check_r_cap_03(roles_doc, source=source)
    return len(findings) == 0, findings


def check_people_document(people_doc, source: str = "registries/people.yaml"):
    """Run R-CAP-04 against one already-parsed people.yaml-shaped document.
    Returns ``(passed, findings)``. Silent when ``people_doc`` is not a
    dict."""
    if not isinstance(people_doc, dict):
        return True, []
    findings = check_r_cap_04(people_doc, source=source)
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
                roles_doc = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                findings.append(f"R-CAP-02 {candidate}: could not parse YAML: {e}")
                continue
            _, roles_findings = check_roles_document(roles_doc, source=str(candidate))
            findings.extend(roles_findings)

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
                        pdoc = yaml.safe_load(person_file.read_text(encoding="utf-8"))
                    except yaml.YAMLError as e:
                        findings.append(f"R-CAP-04 {person_file}: could not parse YAML: {e}")
                        continue
                    _, pfindings = check_people_document(pdoc, source=str(person_file))
                    findings.extend(pfindings)
                break

        # Check flat people document (legacy / fixture fallback)
        for candidate in (
            root / "registries" / "people.yaml",
            root / "people.yaml",
        ):
            if not candidate.exists() or not candidate.is_file():
                continue
            try:
                people_doc = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            except yaml.YAMLError as e:
                findings.append(f"R-CAP-04 {candidate}: could not parse YAML: {e}")
                continue
            _, people_findings = check_people_document(people_doc, source=str(candidate))
            findings.extend(people_findings)

    return len(findings) == 0, findings
