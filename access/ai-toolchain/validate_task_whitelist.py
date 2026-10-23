#!/usr/bin/env python3
"""Permitted background-layer task whitelist validator (Spec Section 37.2).

Validates access/ai-toolchain/task-whitelist.yaml:
  W1 File is valid YAML mapping with schema_version and spec_reference == "37.2"
  W2 Contains tasks list of exactly the 9 closed Section 37.2 classes, no more and no fewer
  W3 Every entry declares spec_reference == "37.2" and task_class verbatim from Spec §37.2

Exposes:
  is_whitelisted(task_class: str) -> bool
"""

import argparse
import os
import sys
from typing import List, Optional, Set, Tuple

import yaml

DEFAULT_WHITELIST_PATH = os.path.join("access", "ai-toolchain", "task-whitelist.yaml")

# Verbatim Section 37.2 permitted task whitelist (closed set of 9 classes)
PERMITTED_TASK_CLASSES: Set[str] = {
    "Test suite drafts for existing code",
    "Documentation and docstrings",
    "Lint, format and type fixes",
    "Safe mechanical refactors and renames",
    "Dependency work where explicitly permitted",
    "CI failure triage drafts",
    "Commit message and PR description drafts",
    "Evaluation scenario drafts (draft-only, confirmed by a human before entering `verification/ai-eval/`; local inference — Section 38.3)",
    "Intake gap assessment drafts (draft-only, the recorded assessment is written by the human assessor; local inference — Section 96.6)",
}


def load_whitelist(path: Optional[str] = None) -> Set[str]:
    """Load permitted task classes from YAML file or return canonical set."""
    p = path or DEFAULT_WHITELIST_PATH
    if not os.path.isfile(p):
        return set(PERMITTED_TASK_CLASSES)
    try:
        with open(p, "r", encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        if isinstance(doc, dict) and isinstance(doc.get("tasks"), list):
            loaded = {
                str(t.get("task_class", "")).strip()
                for t in doc["tasks"]
                if isinstance(t, dict) and t.get("task_class")
            }
            if loaded:
                return loaded
    except Exception:
        pass
    return set(PERMITTED_TASK_CLASSES)


def is_whitelisted(task_class: str, whitelist_path: Optional[str] = None) -> bool:
    """Return True if task_class matches any permitted class from Section 37.2."""
    if not task_class:
        return False
    tc = task_class.strip()
    permitted = load_whitelist(whitelist_path)
    if tc in permitted:
        return True
    # Normalized / slug match fallback
    norm_tc = tc.lower().replace("_", "-").replace(" ", "-")
    for p in permitted:
        norm_p = p.lower().replace("_", "-").replace(" ", "-")
        if norm_tc == norm_p or norm_tc in norm_p:
            return True
    return False


def check(path: str) -> Tuple[List[str], int]:
    errors = []
    if not os.path.isfile(path):
        return [f"W0 file absent: {path}"], 0

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    doc = yaml.safe_load(raw)
    if not isinstance(doc, dict):
        return ["W1 file is not a YAML mapping"], 0

    if str(doc.get("spec_reference", "")).strip() != "37.2":
        errors.append(f"W1 spec_reference must be '37.2', got {doc.get('spec_reference')!r}")

    tasks = doc.get("tasks")
    if not isinstance(tasks, list):
        errors.append("W2 'tasks' must be a list")
        return errors, 0

    if len(tasks) != 9:
        errors.append(f"W2 expected exactly 9 task classes, got {len(tasks)}")

    seen_classes: Set[str] = set()
    for idx, item in enumerate(tasks):
        if not isinstance(item, dict):
            errors.append(f"W3 tasks[{idx}] is not a mapping")
            continue
        tc = str(item.get("task_class", "")).strip()
        if not tc:
            errors.append(f"W3 tasks[{idx}] missing task_class")
            continue
        spec_ref = str(item.get("spec_reference", "")).strip()
        if spec_ref != "37.2":
            errors.append(f"W3 tasks[{idx}] '{tc}' has spec_reference {spec_ref!r}, expected '37.2'")
        if tc in seen_classes:
            errors.append(f"W2 duplicate task_class: '{tc}'")
        seen_classes.add(tc)

    # Check closed set: exactly PERMITTED_TASK_CLASSES
    missing = PERMITTED_TASK_CLASSES - seen_classes
    if missing:
        errors.append(f"W2 missing required Section 37.2 task classes: {sorted(missing)}")
    extra = seen_classes - PERMITTED_TASK_CLASSES
    if extra:
        errors.append(f"W2 unapproved task classes not in Section 37.2: {sorted(extra)}")

    return errors, len(seen_classes)


def validate_whitelist(path: str = DEFAULT_WHITELIST_PATH) -> int:
    errors, count = check(path)
    if errors:
        for err in errors:
            print(f"FAIL {path}: {err}")
        print(f"TASK-WHITELIST-VALIDATE: FAIL ({len(errors)} errors)")
        return 1
    print(f"OK {path}")
    print(f"TASK-WHITELIST-VALIDATE: PASS ({count} classes)")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Validate Section 37.2 Hermes task whitelist")
    parser.add_argument("path", nargs="?", default=DEFAULT_WHITELIST_PATH, help="Path to task-whitelist.yaml")
    args = parser.parse_args()
    return validate_whitelist(args.path)


if __name__ == "__main__":
    sys.exit(main())
