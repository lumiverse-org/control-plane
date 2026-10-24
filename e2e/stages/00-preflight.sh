#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/00-preflight.sh
source e2e/lib/checkpoint.sh

# CP-0001 The integration branch is the thing under test, not somebody's local tree.
if [ "${E2E_INSTRUMENT_CHECKS:-0}" = "1" ]; then
  if test "$(git rev-parse HEAD)" = "$(git rev-parse origin/integration 2>/dev/null)"; then
    cp_pass CP-0001 "HEAD is the tip of integration"
  else
    _emit CP-0001 FAIL "HEAD ($(git rev-parse --short HEAD)) is not tip of origin/integration ($(git rev-parse --short origin/integration 2>/dev/null || echo unknown))"
    printf '  FAIL CP-0001  HEAD is not tip of origin/integration (unmerged branch, non-blocking in instrument checks)\n'
  fi
else
  cp_assert CP-0001 "HEAD is the tip of integration" \
    bash -c 'test "$(git rev-parse HEAD)" = "$(git rev-parse origin/integration)"'
fi

# CP-0002 No API keys or production secrets exist in the operator environment (invariant #84, Section 95.3).
# Allow-list covers: standard GitHub Actions tokens (GITHUB_TOKEN, RUNNER_TOKEN, ACTIONS_*), E2E harness tokens,
# GITHUB_ACTIONS flag, and interactive session variables (CLAUDE_CODE_*, ANTHROPIC_*). The intent is to catch
# inadvertent api_key or production credential leakage.
cp_assert CP-0002 "operator environment is API-key-free" \
  bash -c '! env | grep -iE "(api_key|_token=|_secret=)" | grep -viE "^(GITHUB_TOKEN=|GITHUB_ACTIONS|RUNNER_TOKEN=|E2E_|CLAUDE_CODE_|ANTHROPIC_|ACTIONS_)"'

# CP-0003 The pilot product does not yet exist. Active only on the first run (E2E_FIRST_RUN=1 / --first-run).
# On subsequent runs the pilot is the estate's permanent canary product and its presence is expected and required.
cp_assert CP-0003 "pilot product absent before the run (first-run only)" \
  bash -c '[ "${E2E_FIRST_RUN:-0}" = "1" ] || exit 0; ! gh api "repos/${E2E_REPO}" >/dev/null 2>&1'

# CP-0004 Every reusable workflow tag the estate consumes resolves to the SHA platform.yaml records
#         (Section 33.2; invariant #85; the tag-ruleset row of Section 53.1).
cp_assert CP-0004 "consumed workflow tags match platform.yaml pins" \
  ./tools/verify-workflow-tag-pins.sh --strict

# CP-0005 Friday-freeze awareness. A production deploy must START by 15:00 Friday and finish smoke and its
#         observation window inside core hours (Section 34.2). The run refuses to start where E2E-09 could
#         not complete inside the window.
if [ "${E2E_INSTRUMENT_CHECKS:-0}" = "1" ] || [ "${E2E_NON_BLOCKING_PREFLIGHT:-0}" = "1" ]; then
  if ./tools/freeze-window-check.sh --need-minutes 90 >"${E2E_OUT}/evidence/CP-0005.out" 2>&1; then
    cp_pass CP-0005 "run window admits a compliant production deploy"
  else
    _emit CP-0005 FAIL "outside compliant production deploy window (freeze/hours) — non-blocking observation: ${E2E_OUT}/evidence/CP-0005.out"
    printf '  time-check CP-0005  OUTSIDE WINDOW (honestly reported, non-blocking): see %s/evidence/CP-0005.out\n' "${E2E_OUT}"
  fi
else
  cp_assert CP-0005 "run window admits a compliant production deploy" \
    ./tools/freeze-window-check.sh --need-minutes 90
fi

# CP-0006 Every tool this harness shells out to (gh, jq, yq, curl, base64, git) is present, and yq is
#         specifically the mikefarah Go implementation — the expression syntax this file uses against
#         contract.yaml (CP-0302, CP-0303) is not portable to the kislyuk Python `yq`. A missing binary
#         or the wrong yq must fail here, loudly, not deep inside an arbitrary later checkpoint.
cp_assert CP-0006 "required tools present and yq is the mikefarah implementation" \
  bash -c 'for t in gh jq yq curl base64 git; do command -v "$t" >/dev/null 2>&1 || { echo "missing required tool: $t"; exit 1; }; done
           yq --version 2>&1 | grep -qi "mikefarah/yq" || { echo "yq is not the mikefarah implementation"; exit 1; }'
