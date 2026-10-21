#!/usr/bin/env bash
set -euo pipefail
missing=0
for d in access infra ops-vm notify assets; do
  [ -d "$d" ] || { echo "MISSING DIR: $d"; missing=1; }
done
[ -f infra/OWNERSHIP.md ] || { echo "MISSING FILE: infra/OWNERSHIP.md"; missing=1; }
[ "$missing" -eq 0 ] && echo "L5-T01 SELF-VERIFY PASS" || exit 1
