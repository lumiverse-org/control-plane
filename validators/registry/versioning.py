"""Multi-version contract dispatch: v1 and v2 validated side by side.

Spec anchor: Section 60.2; Section 60.3; AT-025; Invariant 73.
Task: lanes/L1-05-tasks.md, L1-701.

This module provides multi-version schema dispatch for contract and registry
documents. In accordance with FD-094 and r_prd_11.py, this module is not wired
into cli.py, which uses the flat R01-R18 rules dispatch. Instead, callers import
and use document_version, select_schema, and supported_versions directly.
"""
from __future__ import annotations

import re
from pathlib import Path

# --- kind -> version field -------------------------------------------------
# Transcribed from Section 60.2's table (lanes/L1-05-tasks.md, L1-701).
# The two rows Lane 1 does not own -- Operational record envelope
# (records/**, record_schema_version) and Event envelope (events/**,
# event_schema_version) -- belong to Lane 4 (PARTITION.md) and are
# deliberately absent. Do not add them.
VERSION_FIELD: dict[str, str] = {
    "product": "contract_version",
    "verification-contract": "contract_version",
    "people": "registry_version",
    "roles": "registry_version",
    "service": "service_version",
    "platform": "platform_version",
    "topology": "registry_version",
    "exceptions": "registry_version",
    "policies": "registry_version",
    "os-health": "registry_version",
    "patterns": "registry_version",
    "economics": "registry_version",
    "platform-roadmap": "registry_version",
    "owners": "registry_version",
    "tools": "registry_version",
}

# Every distinct version-field name used anywhere in VERSION_FIELD. A
# document carrying zero, or more than one, of these is malformed
# regardless of kind (Section 60.2: "Every contract schema carries a
# version").
_ALL_VERSION_FIELDS = sorted(set(VERSION_FIELD.values()))

# kind -> schema path template (schemas/**), one '{v}' placeholder for the
# version. Verified against the schema files actually present in this tree:
_SCHEMA_PATH_TEMPLATE: dict[str, str] = {
    "product": "schemas/product/product.contract.v{v}.schema.json",
    "verification-contract": "schemas/product/verification.contract.v{v}.schema.json",
    "people": "schemas/registry/people.registry.v{v}.schema.json",
    "roles": "schemas/registry/roles.registry.v{v}.schema.json",
    "service": "schemas/registry/service.v{v}.schema.json",
    "platform": "schemas/registry/platform.registry.v{v}.schema.json",
    "topology": "schemas/registry/topology.v{v}.schema.json",
    "exceptions": "schemas/registry/exceptions.registry.v{v}.schema.json",
    "policies": "schemas/registry/policies.registry.v{v}.schema.json",
    "os-health": "schemas/registry/os-health.v{v}.schema.json",
    "patterns": "schemas/registry/patterns.v{v}.schema.json",
    "economics": "schemas/registry/economics.v{v}.schema.json",
    "platform-roadmap": "schemas/registry/platform-roadmap.v{v}.schema.json",
    "owners": "schemas/registry/owners.v{v}.schema.json",
    "tools": "schemas/registry/tools.v{v}.schema.json",
}

# platform_version is the one non-integer version field (Section 60.2,
# "Event-type enum" row). registries/platform.yaml carries
# `platform_version: "4.0"` today -- a dotted numeric string, not
# single-integer and not full three-part semver -- so the validator
# accepts one-or-more dot-separated integer segments and nothing else.
_PLATFORM_VERSION_RE = re.compile(r"^[0-9]+(\.[0-9]+)+$")


class UnknownKind(ValueError):
    """`kind` is not one of VERSION_FIELD's 15 Lane-1 versioned kinds.

    Raised for the two kinds Lane 1 deliberately does not own (`records`,
    `events` -- Lane 4, schemas/records/**) and for any other kind string
    the caller passes that is not in VERSION_FIELD. Never add `records` or
    `events` to VERSION_FIELD to make this stop firing -- see the module
    docstring and PARTITION rule 4.
    """


class UnknownVersion(ValueError):
    """The document's version field is missing, duplicated, malformed, or
    names a version with no schema file on disk.

    Covers every case Section 60.2's dispatch rules name as a usage error:
    no version field present, two or more version fields present, the
    present field is not the one this kind expects, the value is the
    wrong type (e.g. a string where an int is required), the value is out
    of range (e.g. 0), or the value is well-formed but no schema file
    exists for it. `select_schema` never falls back to the newest schema
    when this fires -- Section 60.2: "Write the v2 schema alongside v1 --
    do not replace."
    """


def _expected_field(kind: str) -> str:
    try:
        return VERSION_FIELD[kind]
    except KeyError:
        raise UnknownKind(
            f"kind '{kind}' is not a Lane 1 versioned contract kind "
            f"(not in validators.registry.versioning.VERSION_FIELD)"
        ) from None


def document_version(kind: str, doc: dict) -> int | str:
    """Read and validate `doc`'s version field for `kind`.

    Returns an int for every kind except "platform", which returns the
    raw dotted-numeric version string (e.g. "4.0"). Raises `UnknownKind`
    if `kind` is not in VERSION_FIELD, and `UnknownVersion` for every
    malformed-document case described in the module docstring. Never
    raises any other exception type and never returns a value that was
    not read verbatim from `doc`.
    """
    expected_field = _expected_field(kind)

    present = [f for f in _ALL_VERSION_FIELDS if f in doc]
    if len(present) == 0:
        raise UnknownVersion(
            f"document declares no version field; kind '{kind}' requires "
            f"'{expected_field}'"
        )
    if len(present) > 1:
        raise UnknownVersion(
            f"document declares {len(present)} version fields {sorted(present)}; "
            f"exactly one is required"
        )
    if present[0] != expected_field:
        raise UnknownVersion(
            f"kind '{kind}' requires version field '{expected_field}', "
            f"found '{present[0]}'"
        )

    value = doc[expected_field]

    if expected_field == "platform_version":
        if not isinstance(value, str) or not _PLATFORM_VERSION_RE.match(value):
            raise UnknownVersion(
                f"platform_version must be a dotted numeric version string "
                f"(e.g. '4.0'), got {value!r}"
            )
        return value

    # bool is a subclass of int in Python -- reject it explicitly so
    # `contract_version: true` does not silently become version 1.
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise UnknownVersion(
            f"{expected_field} must be a positive integer, got {value!r}"
        )
    return value


def select_schema(kind: str, doc: dict) -> str:
    """Return the schema path (relative to the repo root) that validates
    `doc` under `kind`'s declared version.

    Raises `UnknownKind` (via `document_version`) for an unowned kind, and
    `UnknownVersion` for every malformed-version case `document_version`
    raises, plus the one case `document_version` cannot see: a
    well-formed version with no schema file on disk, raised here as
    `UnknownVersion(f"no schema for kind '{kind}' version {version}")` --
    this exact message/format is pinned by L1-701's ACCEPTANCE item 1.
    Never falls back to the newest schema file for the kind.
    """
    version = document_version(kind, doc)
    template = _SCHEMA_PATH_TEMPLATE[kind]
    path = template.format(v=version)
    if not Path(path).is_file():
        raise UnknownVersion(f"no schema for kind '{kind}' version {version}")
    return path


def supported_versions(platform_doc: dict | None, kind: str) -> list[int]:
    """Return the list of contract versions `platform.yaml` declares
    supported for `kind`, or `[]` if `platform_doc` is `None`, the
    `supported_contract_versions` key is absent, or `kind` has no entry
    under it.

    Reads `platform_doc["supported_contract_versions"][kind]` verbatim --
    see `registries/platform.yaml`'s `supported_contract_versions.product:
    [1, 2]`. This is consumed by R-VER-01 (L1-702, a separate task
    depending on this one); the only kind R-VER-01 actually calls this
    with today is "product".
    """
    if not platform_doc:
        return []
    return list(platform_doc.get("supported_contract_versions", {}).get(kind, []))
