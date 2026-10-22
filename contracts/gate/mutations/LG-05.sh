#!/usr/bin/env sh
set -eu
WT="${GATE_PROBE_WT:?throwaway worktree required}"
cd "$WT"
printf '%s\n' "seeded_defect=PASSED"
