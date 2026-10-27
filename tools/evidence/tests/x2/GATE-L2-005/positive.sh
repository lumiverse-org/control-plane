#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../../../../.." || exit 1
T="$(mktemp)"
printf '%s\n' '{"ref":"refs/heads/main","environment":"production","policy":{"default_branch":true,"protected_tags":true,"custom":[]}}' > "$T"
python3 -m tools.evidence.env_policy_assert --case "$T" --summary >/dev/null 2>&1
rc=$?; rm -f "$T"; exit $rc
