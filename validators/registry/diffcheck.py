"""Diff-aware comparison helpers for the Section 26.4 authority-delta rules
(R-CHG-01/02/03, task L1-504).

Standalone, directly-tested helper module -- not wired into the frozen Option B
(FD-094) dispatch engine. Follows the same adaptation as r_svc_01.py,
r_exc_01.py and r_inv_01.py.

Four pure functions (no git calls, take already-parsed dicts/strings -- these
are what r_chg_01/02/03's check_document() call and what their tests exercise
directly), plus impure git-shelling helpers used only by the Option-B-shaped
check() wrappers.
"""
from __future__ import annotations

import os
import re
import subprocess
from collections import namedtuple
from pathlib import Path

# Section 11.2, Developer row: "Write on Repositories of products where they
# hold primary_owner, cross_reviewer, backup_owner or temporary_contributor."
WRITE_CONFERRING_TYPES = frozenset(
    {"primary_owner", "cross_reviewer", "backup_owner", "temporary_contributor"}
)

# Matches schemas/registry/common/defs.v1.schema.json $defs.decisionRecordId
# pattern (^DEC-\d{4}-\d{3,}$) exactly -- do not diverge from it.
_TRAILER_RE = re.compile(r"^Decision-Record:\s*(DEC-\d{4}-\d{3,})\s*$", re.MULTILINE)

GitBase = namedtuple("GitBase", "docs commit_message")


def linked_decision_records(commit_message: str) -> list[str]:
    """Every Decision-Record: DEC-... trailer in commit_message, in order."""
    return _TRAILER_RE.findall(commit_message or "")


def _entities_and_field(doc: dict | None) -> tuple[list[dict], str] | None:
    """Auto-detect whether doc is roles.yaml- or people.yaml-shaped and return
    (entity list, capability-field name). None if doc is absent/unrecognised."""
    if not isinstance(doc, dict):
        return None
    if "roles" in doc:
        return (doc.get("roles") or []), "default_capabilities"
    if "people" in doc:
        return (doc.get("people") or []), "capabilities"
    return None


def added_capabilities(base: dict, head: dict) -> list[tuple[str, str]]:
    """(entity_id, capability) for every capability present on an entity in
    head that the same entity id did not carry in base. Works for either a
    roles.yaml-shaped or a people.yaml-shaped pair (auto-detected from head;
    a brand-new entity id absent from base entirely counts all of its head
    capabilities as added, since base 'did not carry' any of them -- this is
    the literal reading of Section 26.4 and is intentional, not a bug).
    Entities removed between base and head are ignored (not an addition).
    Capabilities *removed* from an entity are never reported (Section 26.4:
    only *adds*; see fixtures/chg01/valid/capability_removed_no_trailer/)."""
    head_info = _entities_and_field(head)
    if head_info is None:
        return []
    head_entities, field = head_info
    base_info = _entities_and_field(base)
    base_entities = base_info[0] if base_info else []
    base_by_id = {
        e.get("id"): set(e.get(field) or [])
        for e in base_entities
        if isinstance(e, dict)
    }
    results: list[tuple[str, str]] = []
    for entity in head_entities:
        if not isinstance(entity, dict):
            continue
        entity_id = entity.get("id")
        added = set(entity.get(field) or []) - base_by_id.get(entity_id, set())
        for cap in sorted(added):
            results.append((entity_id, cap))
    return results


def added_write_assignments(base: dict, head: dict) -> list[tuple[str, str]]:
    """(assignment_type, person_id) for every (person, type) pair present in
    head['assignments'] but not in base['assignments'], restricted to types
    in WRITE_CONFERRING_TYPES. base/head are product.yaml- or
    service.yaml-shaped documents (schemas/registry/common/assignments.v1.schema.json
    $ref's this array from both)."""

    def _keys(doc):
        if not isinstance(doc, dict):
            return set()
        return {
            (a.get("person"), a.get("type"))
            for a in (doc.get("assignments") or [])
            if isinstance(a, dict)
        }

    added = _keys(head) - _keys(base)
    return sorted(
        (atype, person)
        for person, atype in added
        if atype in WRITE_CONFERRING_TYPES
    )


def changed_access_status(base: dict, head: dict) -> list[tuple[str, str, str]]:
    """(person_id, old_status, new_status) for every person whose
    access_status differs between base and head. A person absent from base
    entirely is not a 'change' (there is nothing to compare against)."""

    def _statuses(doc):
        if not isinstance(doc, dict):
            return {}
        return {
            p.get("id"): p.get("access_status")
            for p in (doc.get("people") or [])
            if isinstance(p, dict)
        }

    base_s, head_s = _statuses(base), _statuses(head)
    results = []
    for person_id, new in head_s.items():
        old = base_s.get(person_id)
        if old is not None and new is not None and old != new:
            results.append((person_id, old, new))
    return results


# ---- impure helpers: only used by the Option-B check() wrappers below ----


def _git_show(path: str, base_ref: str, cwd: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "show", f"{base_ref}:{path}"],
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return out.stdout
    except (subprocess.CalledProcessError, OSError):
        return None


def load_git_base(repo_root: str, doc_paths: dict[str, str]) -> "GitBase | None":
    """doc_paths maps a doc kind ('people', 'roles', ...) to its path relative
    to repo_root (e.g. {'people': 'registries/people.yaml'}). Reads each at
    REGISTRY_DIFF_BASE (env var, default 'origin/integration') via `git show`,
    and the current commit's message via `git log -1 --format=%B`. Returns
    None when not one single doc could be read at the base revision (e.g. a
    shallow clone with no reachable base) -- callers must then skip the rule
    entirely and report zero findings, mirroring ctx.git_base is None in the
    task's original (superseded) design."""
    import yaml

    base_ref = os.environ.get("REGISTRY_DIFF_BASE", "origin/integration")
    docs: dict[str, dict] = {}
    for kind, rel_path in doc_paths.items():
        raw = _git_show(rel_path, base_ref, repo_root)
        if raw is None:
            continue
        try:
            docs[kind] = yaml.safe_load(raw) or {}
        except yaml.YAMLError:
            docs[kind] = {}
    if not docs:
        return None
    try:
        msg = subprocess.run(
            ["git", "log", "-1", "--format=%B"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, OSError):
        msg = ""
    return GitBase(docs=docs, commit_message=msg)
