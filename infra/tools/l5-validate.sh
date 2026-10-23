#!/usr/bin/env bash
# L5 lane validation entrypoint. Owned by lane L5 (PARTITION.md line 21).
# Modes are added by later L5 tasks. --layout is implemented here.
set -u
MODE="${1:---layout}"

l5_dirs() {
  cat <<'DIRS'
access/model
access/branch-protection
access/secrets
access/layer-b
access/fail-closed
access/published
access/ai-runtime/runtimes
access/ai-runtime/extensions
access/ai-runtime/mcp-servers
access/ai-runtime/checks
access/ai-runtime/constitution
access/ai-runtime/benchmark
infra/github-org
infra/runners
infra/network
infra/tools
infra/published
ops-vm/compose
ops-vm/jobs
ops-vm/rebuild
ops-vm/smoke
ops-vm/offvm
ops-vm/published
notify/routing
notify/channels
notify/escalation
notify/published
assets/inventory
assets/deadlines
assets/watch
assets/published
DIRS
}

case "$MODE" in
  --layout)
    missing=0
    while IFS= read -r d; do
      [ -d "$d" ] || { echo "MISSING $d"; missing=1; }
    done < <(l5_dirs)
    if [ "$missing" -eq 0 ]; then echo "L5 LAYOUT PASS"; else echo "L5 LAYOUT FAIL"; fi
    ;;
  *)
    echo "L5 VALIDATE UNIMPLEMENTED-MODE $MODE"
    exit 2
    ;;
esac
