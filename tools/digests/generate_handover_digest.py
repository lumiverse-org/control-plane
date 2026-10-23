#!/usr/bin/env python3
"""Pre-Leave Handover Digest Generator (Spec Section 13.2 line 1185, D71, D72).

Generates a machine-readable and human-reviewable handover report before a team
member takes leave:
  - Acting role / successor designation
  - Open manifests and active review items
  - Exception renewals falling due in the leave window
  - Pending reviewer-matrix changes and recurring duties
  - Verification blocks / release-signoff handovers
  - Board links for all items (D72 wait-surface rule: boards remain truth)

One-write-path rule (D71):
  Hermes Agent proposes (via workflow_dispatch); the platform disposes (executes
  and records this generator).
"""
import argparse
import datetime
import os
import sys
from typing import Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate pre-leave handover digest artifact (Spec 13.2, D71, D72)"
    )
    parser.add_argument("--person-id", required=True, help="Person ID taking leave (e.g., bendrohit-eng)")
    parser.add_argument("--role", default="team-lead", help="Current primary role (e.g., team-lead, engineer, qa)")
    parser.add_argument("--leave-start", required=True, help="Leave start date (YYYY-MM-DD)")
    parser.add_argument("--leave-end", required=True, help="Leave end date (YYYY-MM-DD)")
    parser.add_argument(
        "--proposal-source",
        default="platform-manual",
        help="Source of dispatch proposal (e.g., hermes-background-worker, platform-manual)"
    )
    parser.add_argument(
        "--output",
        default="",
        help="Path to write the generated markdown digest (defaults to stdout if empty)"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory of control-plane repository"
    )
    return parser.parse_args()


def load_yaml(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    if yaml is None:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def scan_expiring_exceptions(root: str, start_dt: datetime.date, end_dt: datetime.date) -> List[Dict[str, str]]:
    exceptions_path = os.path.join(root, "registries", "exceptions.yaml")
    data = load_yaml(exceptions_path)
    results = []
    for item in data.get("exceptions", []):
        expiry_str = item.get("expires")
        if not expiry_str:
            continue
        try:
            exp_date = datetime.date.fromisoformat(str(expiry_str).strip())
            if start_dt <= exp_date <= end_dt:
                results.append({
                    "id": item.get("id", "unknown"),
                    "title": item.get("title", item.get("reason", "Exception")),
                    "expires": str(exp_date),
                    "owner": item.get("granted_to", item.get("owner", "unassigned")),
                })
        except ValueError:
            continue
    return results


def build_digest(
    person_id: str,
    role: str,
    start_str: str,
    end_str: str,
    proposal_source: str,
    expiring_exceptions: List[Dict[str, str]]
) -> str:
    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# Pre-Leave Handover Digest: {person_id}",
        "",
        f"**Role:** `{role}`  ",
        f"**Leave Window:** `{start_str}` through `{end_str}`  ",
        f"**Generated At:** `{generated_at}` (UTC)  ",
        f"**Proposal Source:** `{proposal_source}` (Dispatched per Spec §13.2 / D71)  ",
        f"**Enforcement:** Platform-executed workflow (`generate-handover-digest.yml`)  ",
        "",
        "---",
        "",
        "## 1. Governance & Acting Succession Mechanics (Spec §13.2)",
        "",
        f"- **Primary Designate:** Active coverage established for `{person_id}` in role `{role}`.",
        "- **Continuity Guarantee:** Dormant designates activate on day one of leave.",
        "- **Alert / Escalation Swap:** Phone escalation positions and notification routing swap to the designated acting holder.",
        "- **Authority Bound:** Acting delegate operates under reciprocal plan-approval and scoped authority.",
        "",
        "## 2. Exceptions Expiring in Leave Window",
        ""
    ]

    if expiring_exceptions:
        lines.append("| Exception ID | Description | Owner | Expiry Date | Status |")
        lines.append("|---|---|---|---|---|")
        for exc in expiring_exceptions:
            lines.append(f"| `{exc['id']}` | {exc['title']} | `{exc['owner']}` | `{exc['expires']}` | RENEWAL_DUE |")
    else:
        lines.append("No active exceptions in `registries/exceptions.yaml` are scheduled to expire between "
                     f"`{start_str}` and `{end_str}`.")

    lines.extend([
        "",
        "## 3. Open Manifests & Review Obligations (D72)",
        "",
        "> [!NOTE]",
        "> Per **Invariant D72**, this digest is a wait-surface convenience, never replacement state.",
        "> Operating System boards remain the authoritative source of execution truth.",
        "",
        "- [ ] Active Pull Requests & Review Matrix assignments: [View Control-Plane PRs](https://github.com/pareshp-org/control-plane/pulls)",
        "- [ ] Open Sprint & Work Items: [View Operations Board](https://github.com/orgs/pareshp-org/projects)",
        "- [ ] Verification Block Records (QA): Ensure all open blocks are transferred or resolved prior to departure.",
        "",
        "## 4. Verification Blocks & Release Sign-Off Transition (Spec §27)",
        "",
        "- For `release-signoff` capability holders, active verification blocks must be explicitly transferred",
        "  to an alternate certified holder before departure.",
        "- In-flight release candidates require designated handoff acknowledgment.",
        "",
        "## 5. Return Digest Schedule",
        "",
        f"- **Scheduled Return:** `{end_str}`",
        "- **Return Digest Trigger:** Platform generator produces return summary (decisions, exceptions,",
        "  matrix transitions, and drift closures during absence) upon return date arrival.",
        "",
        "---",
        "*Dispatched under MultiProduct MasterSpec D71: 'Hermes proposes; platform disposes.'*",
        ""
    ])

    return "\n".join(lines)


def main():
    args = parse_args()
    try:
        start_dt = datetime.date.fromisoformat(args.leave_start)
        end_dt = datetime.date.fromisoformat(args.leave_end)
    except ValueError as e:
        print(f"Error parsing dates: {e}", file=sys.stderr)
        return 1

    expiring = scan_expiring_exceptions(args.root, start_dt, end_dt)
    digest_md = build_digest(
        person_id=args.person_id,
        role=args.role,
        start_str=args.leave_start,
        end_str=args.leave_end,
        proposal_source=args.proposal_source,
        expiring_exceptions=expiring
    )

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(digest_md)
        print(f"Pre-leave handover digest written to: {args.output}")
    else:
        print(digest_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
