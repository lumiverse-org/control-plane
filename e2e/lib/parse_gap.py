#!/usr/bin/env python3
"""Parse protocol/08-E2E-READINESS-GAP.md and output TSV of checkpoint classifications."""

import sys, os, re

def parse_gap(gap_file):
    if not os.path.exists(gap_file):
        print(f"ERROR: {gap_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(gap_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    entries = {}
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 5:
            cid = parts[0].strip("` *")
            if re.match(r"^(CP-\d+|NEG-\d+)", cid):
                desc = parts[1].strip("` *")
                tool = parts[2].strip("` *")
                tool_exists = parts[3].strip("` *")
                readiness = parts[4].strip("` *")
                lane = parts[5].strip("` *") if len(parts) > 5 else ""
                blocker = parts[6].strip("` *") if len(parts) > 6 else ""

                kind = "BLOCKED" if "GENUINELY BLOCKED" in readiness else "OFFLINE"
                entries[cid] = (kind, blocker, desc, tool)

    return entries

if __name__ == "__main__":
    gap_file = sys.argv[1] if len(sys.argv) > 1 else "protocol/08-E2E-READINESS-GAP.md"
    entries = parse_gap(gap_file)
    for cid, (kind, blocker, desc, tool) in sorted(entries.items()):
        # Escape any tabs or newlines
        blocker_clean = blocker.replace("\t", " ").replace("\n", " ")
        desc_clean = desc.replace("\t", " ").replace("\n", " ")
        print(f"{cid}\t{kind}\t{blocker_clean}\t{desc_clean}")
