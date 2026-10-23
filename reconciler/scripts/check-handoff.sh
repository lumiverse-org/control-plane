#!/usr/bin/env bash
# L3-P8-06: check-handoff.sh — verifies handoff manifest and boundaries.
set -euo pipefail

HANDOFF="reconciler/HANDOFF.md"

if [ ! -f "$HANDOFF" ]; then
    echo "FAIL: $HANDOFF does not exist"
    exit 1
fi

# Assert all three consumers are named
for consumer in "L5" "L2" "L4"; do
    if ! grep -q "$consumer" "$HANDOFF"; then
        echo "FAIL: consumer $consumer is not named in $HANDOFF"
        exit 1
    fi
done

# Assert no Lane 3 module contains code writing to foreign paths
# Forbidden write patterns to records/, events/, .github/workflows/, ops-vm/
VIOLATIONS=$(grep -rnE '(open\(["\x27](records/|events/|\.github/workflows/|ops-vm/)[^"\x27]*["\x27],[ ]*["\x27][wa][+]?["\x27]\))' --exclude-dir=__pycache__ --include="*.py" reconciler/ tools/provision/ validators/drift/ 2>/dev/null || true)

if [ -n "$VIOLATIONS" ]; then
    echo "FAIL: Found foreign path write in Lane 3 code:"
    echo "$VIOLATIONS"
    exit 1
fi

echo "HANDOFF OK"
exit 0
