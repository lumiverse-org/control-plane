#!/usr/bin/env sh
set -eu
WT="${GATE_PROBE_WT:?throwaway worktree required}"
cd "$WT"
printf '%s\n' "self_signoff=1"
