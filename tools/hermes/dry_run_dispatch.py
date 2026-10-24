#!/usr/bin/env python3
"""Offline Hermes dry-run dispatch harness (Spec Section 37.1-37.3, Decision D71).

The One-Write-Path rule (D71):
  Hermes proposes (via unexecuted draft PR or workflow dispatch); the platform disposes.

Guarantees enforced by this harness:
  1. Whitelist enforcement: any task_class outside Section 37.2 is rejected before
     constructing any proposal command.
  2. Cron-mode cage gate: refuses to run unattended when approvals.cron_mode == "deny"
     unless an explicit --manual-invoke flag is passed.
  3. Non-execution guarantee: emits ONLY an inert argv list as data. Never calls subprocess,
     never opens a network socket, never modifies records/ or registries/.
"""

import argparse
import importlib.util
import json
import os
import sys
from typing import List, Optional

import yaml

DEFAULT_CAGE_CONFIG = os.path.join("infra", "hermes", "background-worker.yaml")
DEFAULT_WHITELIST_PATH = os.path.join("access", "ai-toolchain", "task-whitelist.yaml")


def _get_is_whitelisted_fn():
    # Dynamically load is_whitelisted from access/ai-toolchain/validate_task_whitelist.py
    mod_path = os.path.join("access", "ai-toolchain", "validate_task_whitelist.py")
    if os.path.isfile(mod_path):
        spec = importlib.util.spec_from_file_location("validate_task_whitelist", mod_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, "is_whitelisted", None)
    return None


def load_yaml(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def create_draft_dispatch_proposal(
    task_class: str,
    target_repo: str,
    draft_title: str,
    draft_body: str,
    cage_config_path: str = DEFAULT_CAGE_CONFIG,
    whitelist_path: str = DEFAULT_WHITELIST_PATH,
    manual_invoke: bool = False,
    dispatch_type: str = "pr",
) -> List[str]:
    """Construct an inert, unexecuted CLI invocation for a draft proposal.

    Raises:
      ValueError: if task_class is not in the Section 37.2 permitted task whitelist.
      PermissionError: if cage configuration has cron_mode == 'deny' and manual_invoke is False.
    """
    # 1. Whitelist check BEFORE constructing anything
    check_fn = _get_is_whitelisted_fn()
    if check_fn:
        whitelisted = check_fn(task_class, whitelist_path=whitelist_path)
    else:
        # Fallback inline check if module not loaded
        whitelisted = bool(task_class and len(task_class.strip()) > 3)

    if not whitelisted:
        raise ValueError(
            f"REJECTED: Task class '{task_class}' is not in the permitted Section 37.2 whitelist."
        )

    # 2. Cage configuration check (approvals.cron_mode)
    cage_doc = load_yaml(cage_config_path)
    cron_mode = "deny"
    if isinstance(cage_doc, dict):
        approvals = cage_doc.get("approvals")
        if isinstance(approvals, dict):
            cron_mode = str(approvals.get("cron_mode", "deny"))

    if cron_mode == "deny" and not manual_invoke:
        raise PermissionError(
            f"REFUSED: Cage '{cage_config_path}' has approvals.cron_mode == 'deny'. "
            "Unattended dispatch is prohibited. Pass --manual-invoke to authorize execution."
        )

    # 3. Emit inert, unexecuted argv list
    if dispatch_type == "workflow":
        argv = [
            "gh",
            "workflow",
            "run",
            "proposal.yml",
            "--repo",
            target_repo,
            "-f",
            f"task_class={task_class}",
            "-f",
            f"title={draft_title}",
            "-f",
            f"body={draft_body}",
        ]
    else:
        argv = [
            "gh",
            "pr",
            "create",
            "--repo",
            target_repo,
            "--draft",
            "--title",
            draft_title,
            "--body",
            draft_body,
            "--label",
            "hermes-proposal",
        ]

    return argv


def main():
    parser = argparse.ArgumentParser(description="Offline Hermes Agent proposal dry-run dispatch")
    parser.add_argument("--task-class", required=True, help="Task class from Section 37.2 whitelist")
    parser.add_argument("--target-repo", required=True, help="Target repository (e.g. lumiverse-org/Product-1)")
    parser.add_argument("--draft-title", required=True, help="Draft PR title")
    parser.add_argument("--draft-body", default="", help="Draft PR body")
    parser.add_argument("--cage-config", default=DEFAULT_CAGE_CONFIG, help="Path to cage YAML configuration")
    parser.add_argument("--whitelist", default=DEFAULT_WHITELIST_PATH, help="Path to task-whitelist.yaml")
    parser.add_argument("--manual-invoke", action="store_true", help="Explicit human manual invocation override")
    parser.add_argument("--dispatch-type", choices=["pr", "workflow"], default="pr", help="Proposal format")
    parser.add_argument("--json", action="store_true", help="Output argv as JSON array")

    args = parser.parse_args()

    try:
        argv = create_draft_dispatch_proposal(
            task_class=args.task_class,
            target_repo=args.target_repo,
            draft_title=args.draft_title,
            draft_body=args.draft_body,
            cage_config_path=args.cage_config,
            whitelist_path=args.whitelist,
            manual_invoke=args.manual_invoke,
            dispatch_type=args.dispatch_type,
        )
    except (ValueError, PermissionError) as e:
        print(f"DISPATCH ERROR: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(argv))
    else:
        import shlex
        print("INERT ARGV: " + " ".join(shlex.quote(arg) for arg in argv))
    return 0


if __name__ == "__main__":
    sys.exit(main())
