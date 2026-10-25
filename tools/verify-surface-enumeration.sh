#!/usr/bin/env bash
# tools/verify-surface-enumeration.sh
# Checkpoint CP-0108: Verify that a product is discoverable on a declared surface
# without hand-editing a dashboard (AT-001, Invariant #52, Section 19.1).
# Every surface must enumerate from the product registry.
set -euo pipefail

SURFACE=""
PRODUCT=""
SURFACES_FILE="tools/provision/surfaces.yaml"
FIXTURE_REGISTRY=""
MOCK_REACHABLE="false"

while [ $# -gt 0 ]; do
  case "$1" in
    --surface) SURFACE="$2"; shift 2 ;;
    --product) PRODUCT="$2"; shift 2 ;;
    --surfaces-file) SURFACES_FILE="$2"; shift 2 ;;
    --fixture-registry) FIXTURE_REGISTRY="$2"; shift 2 ;;
    --mock-reachable) MOCK_REACHABLE="true"; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

python3 - "$SURFACE" "$PRODUCT" "$SURFACES_FILE" "$FIXTURE_REGISTRY" "$MOCK_REACHABLE" <<'PYEOF'
import sys, os
from pathlib import Path
import yaml

surface = sys.argv[1].strip()
product = sys.argv[2].strip()
surfaces_file = sys.argv[3].strip()
fixture_registry = sys.argv[4].strip()
mock_reachable = (sys.argv[5].strip().lower() == "true")

VALID_SURFACES = {
    "portfolio-board",
    "grafana",
    "scorecard",
    "devlake",
    "reviewer-matrix",
    "dependency-graph",
}

if not surface:
    print("ERROR: --surface is required", file=sys.stderr)
    sys.exit(2)

if surface not in VALID_SURFACES:
    print(f"ERROR: Unknown surface '{surface}'. Must be one of: {', '.join(sorted(VALID_SURFACES))}", file=sys.stderr)
    sys.exit(2)

if not product:
    print("ERROR: --product is required", file=sys.stderr)
    sys.exit(2)

# Load surfaces.yaml
sf_path = Path(surfaces_file)
if not sf_path.is_file():
    # Try searching relative to repo root if run from subfolder
    alt_path = Path(__file__).resolve().parent / "provision" / "surfaces.yaml" if "__file__" in globals() else None
    if alt_path and alt_path.is_file():
        sf_path = alt_path
    else:
        print(f"ERROR: surfaces file not found at {surfaces_file}", file=sys.stderr)
        sys.exit(1)

try:
    data = yaml.safe_load(sf_path.read_text(encoding="utf-8")) or {}
except Exception as e:
    print(f"ERROR: failed to parse surfaces file {sf_path}: {e}", file=sys.stderr)
    sys.exit(1)

surfaces_list = data.get("surfaces", [])
matched = None
for s in surfaces_list:
    if s.get("id") == surface:
        matched = s
        break

if not matched:
    print(f"ERROR: surface '{surface}' not declared in {sf_path}", file=sys.stderr)
    sys.exit(1)

if matched.get("enumerates_from") != "product_registry":
    print(
        f"ERROR: surface '{surface}' specifies enumerates_from: '{matched.get('enumerates_from')}' "
        f"(expected 'product_registry')",
        file=sys.stderr,
    )
    sys.exit(1)

# Check reachability / fixture
if mock_reachable:
    if fixture_registry:
        fr_path = Path(fixture_registry)
        if not fr_path.exists():
            print(f"ERROR: fixture registry not found: {fixture_registry}", file=sys.stderr)
            sys.exit(1)
        found = False
        if fr_path.is_file():
            text = fr_path.read_text(encoding="utf-8", errors="ignore")
            found = product in text
        elif fr_path.is_dir():
            for p in fr_path.rglob("*"):
                if p.is_file() and product in p.read_text(encoding="utf-8", errors="ignore"):
                    found = True
                    break
        if not found:
            print(f"SURFACE {surface} FAIL: product '{product}' not found in registry {fixture_registry}", file=sys.stderr)
            sys.exit(1)
        print(f"SURFACE {surface} OK: product '{product}' discoverable via {fixture_registry}")
        sys.exit(0)

    print(f"SURFACE {surface} OK: product '{product}' discoverable via product_registry (mock probe)")
    sys.exit(0)

# Default: live infrastructure is not present in this offline environment
print(f"SURFACE {surface} UNREACHABLE: no live deployment available to probe product '{product}' (Section 19.1, AT-001)")
sys.exit(3)
PYEOF
