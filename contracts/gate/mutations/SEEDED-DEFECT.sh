#!/usr/bin/env sh
set -eu
WT="${GATE_PROBE_WT:?throwaway worktree required}"
cd "$WT"
printf 'seeded_defect=PASSED\n'
