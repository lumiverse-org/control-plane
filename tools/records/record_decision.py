#!/usr/bin/env python3
"""tools/records/record_decision.py
record-decision CLI — pending, then decided (spec §97.2 lines 8865–8866; §99.2 line 9230; L4-06-tasks.md row L4-P4-07; FD-131).
Usage:
    record-decision pending --product <prod> --decider <id> --subject <text> [options]
    record-decision decide --id <DEC-ID> --options <opt1> <opt2> --evidence <ev1> [options]
    record-decision --from-file <file> [--decide]
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import yaml

from tools.records.lib.decision import (
    create_pending_decision,
    decide_pending_decision,
    mint_decision_id,
    validate_decider,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="record-decision CLI: pending and decided records.")
    parser.add_argument("--records-root", default=".", help="Root of records directory structure")
    subparsers = parser.add_subparsers(dest="subcommand", help="Operation mode")

    # Pending subcommand
    p_parser = subparsers.add_parser("pending", help="Open a pending decision record")
    p_parser.add_argument("--product", required=True, help="Product identifier (e.g. product-1 or shared-infrastructure)")
    p_parser.add_argument("--decider", required=True, help="Decider role or person id (D88 compliant)")
    p_parser.add_argument("--subject", required=True, help="Subject/prompt of the decision")
    p_parser.add_argument("--prompt-received", help="Date prompt received (YYYY-MM-DD)")
    p_parser.add_argument("--id", help="Explicit decision ID (DEC-YYYY-MM-DD-NNN)")
    p_parser.add_argument("--options", nargs="*", default=None, help="Options considered")
    p_parser.add_argument("--evidence", nargs="*", default=None, help="Evidence links")

    # Decide subcommand
    d_parser = subparsers.add_parser("decide", help="Record final decision for a pending prompt")
    d_parser.add_argument("--id", required=True, help="Decision ID (DEC-YYYY-MM-DD-NNN)")
    d_parser.add_argument("--options", nargs="+", required=True, help="Options considered (at least one required)")
    d_parser.add_argument("--evidence", nargs="+", required=True, help="Evidence links (at least one required)")
    d_parser.add_argument("--decided", help="Date decided (YYYY-MM-DD)")
    d_parser.add_argument("--review-date", help="Scheduled review date (YYYY-MM-DD)")

    # Legacy/single-file mode
    parser.add_argument("--from-file", help="YAML file describing pending or decided record")
    parser.add_argument("--decide-mode", action="store_true", help="When using --from-file, treat as decide operation")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.from_file:
            path = Path(args.from_file)
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError("input file must contain a YAML mapping")

            if args.decide_mode or "decided" in data:
                res = decide_pending_decision(
                    records_root=args.records_root,
                    decision_id=data["id"],
                    options_considered=data.get("options_considered", []),
                    evidence=data.get("evidence", []),
                    decided=data.get("decided"),
                    review_date=data.get("review_date"),
                )
                print(f"DECISION-DECIDED: {res['id']}")
            else:
                res = create_pending_decision(
                    records_root=args.records_root,
                    product=data["product"],
                    decider=data["decider"],
                    subject=data["subject"],
                    prompt_received=data.get("prompt_received"),
                    decision_id=data.get("id"),
                    options_considered=data.get("options_considered"),
                    evidence=data.get("evidence"),
                )
                print(f"DECISION-PENDING: {res['id']}")
            return 0

        if args.subcommand == "pending":
            res = create_pending_decision(
                records_root=args.records_root,
                product=args.product,
                decider=args.decider,
                subject=args.subject,
                prompt_received=args.prompt_received,
                decision_id=args.id,
                options_considered=args.options,
                evidence=args.evidence,
            )
            print(f"DECISION-PENDING: {res['id']}")
            return 0

        elif args.subcommand == "decide":
            res = decide_pending_decision(
                records_root=args.records_root,
                decision_id=args.id,
                options_considered=args.options,
                evidence=args.evidence,
                decided=args.decided,
                review_date=args.review_date,
            )
            print(f"DECISION-DECIDED: {res['id']}")
            return 0

        else:
            parser.print_help(sys.stderr)
            return 2

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
