#!/usr/bin/env python3
"""verify_contracts.py — run all contract self-checks; prints CONTRACTS-VERIFY OK N/N on success."""
import os
import pathlib
import re
import sys
import yaml

ROOT = pathlib.Path(__file__).parent.parent
REG_PATH = ROOT / "register.yaml"
data = yaml.safe_load(REG_PATH.read_text(encoding="utf-8"))
contracts = data.get("contracts", [])
total = len(contracts)
passed = 0

for c in contracts:
    cid = c.get("id", "UNKNOWN")
    stub_rel = c.get("stub", "")
    stub_path = ROOT / stub_rel
    if not stub_path.exists():
        print(f"MISSING stub: {cid} -> {stub_rel}", file=sys.stderr)
        continue

    content = stub_path.read_text(encoding="utf-8")
    lines = content.strip().splitlines()
    if len(lines) < 3 or len(content.encode("utf-8")) < 40:
        print(f"EMPTY/TRIVIAL stub: {cid} -> {stub_rel} ({len(lines)} lines, {len(content)} bytes)", file=sys.stderr)
        continue

    if re.search(r'stub:\s*true', content, re.IGNORECASE):
        print(f"PLACEHOLDER stub flag: {cid} -> {stub_rel} contains stub: true", file=sys.stderr)
        continue

    if "STUB — placeholder" in content:
        print(f"PLACEHOLDER comment: {cid} -> {stub_rel} contains placeholder header", file=sys.stderr)
        continue

    passed += 1

print(f"CONTRACTS-VERIFY OK {passed}/{total}" if passed == total else f"CONTRACTS-VERIFY FAIL {passed}/{total}")
sys.exit(0 if passed == total else 1)
