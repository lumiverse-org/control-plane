#!/usr/bin/env sh
set -eu
WT="${GATE_PROBE_WT:?throwaway worktree required}"
cd "$WT"
SB="$(mktemp -d)"
mkdir -p "$SB/set"
cp -r validators/drift/comparison-set/* "$SB/set/" 2>/dev/null || true
rm -f "$SB/set"/canary-*.yaml
if [ -x reconciler/lane-verify.sh ]; then
  reconciler/lane-verify.sh --comparison-set "$SB/set" --summary 2>&1 | tail -1
else
  printf 'canary=MISSING\n'
fi
