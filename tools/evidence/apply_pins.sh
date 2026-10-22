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

LEDGER="tools/evidence/action-pins.txt"
WORKFLOW_DIRS=(".github/workflows" "templates/workflows")

ev_require_file "$LEDGER" "LEDGER_ABSENT"

# lookup_pin <repo> -> prints "<tag> <sha>" to stdout, returns 1 if no row
lookup_pin() {
  local want="$1" repo tag sha
  while IFS=' ' read -r repo tag sha; do
    [ -z "${repo:-}" ] && continue
    case "$repo" in '#'*) continue ;; esac
    if [ "$repo" = "$want" ]; then printf '%s %s\n' "$tag" "$sha"; return 0; fi
  done < "$LEDGER"
  return 1
}

# Pass 1 — scan every placeholder, fail before touching anything if any is unresolvable.
MISSING=0
for DIR in "${WORKFLOW_DIRS[@]}"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r -d '' WFILE; do
    while IFS= read -r LINE; do
      if [[ "$LINE" =~ PIN:([A-Za-z0-9._/-]+) ]]; then
        REPO="${BASH_REMATCH[1]}"
        if ! lookup_pin "$REPO" >/dev/null; then
          printf '%s NO_LEDGER_ROW: no ledger row for placeholder PIN:%s in %s\n' \
            "$EV_FAIL_PREFIX" "$REPO" "$WFILE" >&2
          MISSING=$((MISSING+1))
        fi
      fi
    done < "$WFILE"
  done < <(find "$DIR" -maxdepth 1 -name '*.yml' -print0)
done
[ "$MISSING" -eq 0 ] || exit 3

# Pass 2 — apply.
for DIR in "${WORKFLOW_DIRS[@]}"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r -d '' WFILE; do
    while IFS= read -r LINE; do
      [[ "$LINE" =~ PIN:([A-Za-z0-9._/-]+) ]] || continue
      REPO="${BASH_REMATCH[1]}"
      TAGSHA="$(lookup_pin "$REPO")"
      TAG="${TAGSHA%% *}"; SHA="${TAGSHA##* }"
      sed -i "s|PIN:${REPO}|${REPO}@${SHA} # ${TAG}|g" "$WFILE"
    done < "$WFILE"
  done < <(find "$DIR" -maxdepth 1 -name '*.yml' -print0)
done
echo "apply_pins: substitution complete"
