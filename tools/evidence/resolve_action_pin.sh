#!/usr/bin/env bash
# Authority: L2-05-tasks.md L2-T531; spec §48.1 L4300-4308; §101 invariant 85 L9565
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib/common.sh"

# This script's own runtime contract fixes every refusal at exit 3 (its own
# "nothing resolved / nothing applied" code, L2-05-tasks.md L2-T531),
# distinct from common.sh's generic exit 1 default. Redefined locally after
# sourcing, same pattern as deploy-gate.sh and escalate-digest-mismatch.sh.
ev_die() { printf '%s %s: %s\n' "$EV_FAIL_PREFIX" "$1" "$2" >&2; exit 3; }

REPO="${1:-}"
TAG="${2:-}"
[ -n "$REPO" ] || ev_die "BAD_ARG" "usage: resolve_action_pin.sh <owner/repo> <tag>"
[ -n "$TAG" ]  || ev_die "BAD_ARG" "usage: resolve_action_pin.sh <owner/repo> <tag>"
ev_require_cmd gh

SHA="$(gh api "repos/${REPO}/commits/${TAG}" --jq '.sha' 2>/dev/null)" \
  || ev_die "RESOLVE_FAILED" "cannot resolve ${REPO}@${TAG} via gh api"

case "$SHA" in
  [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) : ;;
  *) ev_die "SHA_FORMAT_INVALID" "resolved value for ${REPO}@${TAG} is not a 40-hex SHA: ${SHA}" ;;
esac

printf '%s %s %s\n' "$REPO" "$TAG" "$SHA"
