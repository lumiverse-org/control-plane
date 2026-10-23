#!/usr/bin/env sh
set -eu
WT="${GATE_PROBE_WT:?throwaway worktree required}"
cd "$WT"
sed -i '$d' contracts/gate/at-index.tsv
GATE_OUT="${GATE_OUT:-.gate}" sh contracts/gate/count-integrity.sh --scope integration 2>&1 | tail -1
