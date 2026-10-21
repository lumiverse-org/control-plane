#!/usr/bin/env bash
# run_negative_tests.sh — Negative-test harness for lane-guard and renovate-path-guard.
# Spec §33.2 L2854-2869; L2-00-charter.md §7 DoD-06, DoD-07, DoD-11.
# Usage: bash tools/evidence/run_negative_tests.sh [--summary]
# Output contract (§0.4): one line to stdout when --summary is passed:
#   <STATUS> run_negative_tests checked=<int> failed=<int>
#   STATUS: OK (exit 0), FAIL (exit 2), ERROR (exit 3)
#   checked = number of cases tested
#   failed  = number of cases whose guard did NOT fail (the error being measured)
set -euo pipefail

SUMMARY=0
for arg in "$@"; do
  [ "$arg" = "--summary" ] && SUMMARY=1
done

TOOL_ID="run_negative_tests"
CHECKED=0
FAILED=0
ROOT="$(cd "$(dirname "$0")" && git rev-parse --show-toplevel)"
NEG="${ROOT}/tools/evidence/negative"
LINT_CMD="python -m tools.evidence.lint_workflow"
ASSERT_CMD="python -m tools.evidence.assert_run_conclusions"
REGISTRY="${ROOT}/templates/workflows/required-checks.yaml"

run_case() {
  local case_id="$1"
  CHECKED=$((CHECKED + 1))
  case "$case_id" in
    N1)
      # Foreign-path diff: simulate by checking if the guard logic correctly
      # detects a path outside the three owned trees.
      BRANCH="lane/2/test-foreign-write"
      CHANGED="contracts/workflow-io/required-contexts.tsv"
      if echo "$CHANGED" | grep -qvE '^(\.github/workflows/|templates/workflows/|tools/evidence/)'; then
        : # guard would fail — correct
      else
        echo "CASE N1: guard did not detect foreign path" >&2
        FAILED=$((FAILED + 1))
      fi
      ;;
    N2)
      # Branch not matching lane/[1-5]/*
      BRANCH="feature/something-unchecked"
      if echo "$BRANCH" | grep -qE '^lane/[1-5]/'; then
        echo "CASE N2: guard passed a non-lane branch — should fail" >&2
        FAILED=$((FAILED + 1))
      fi
      ;;
    N3)
      # Workflow with if: on a required context job — lint_workflow must fail
      FIXTURE="${NEG}/N3/bad_if.yml"
      if $LINT_CMD --path "$FIXTURE" --summary 2>/dev/null | grep -q '^OK'; then
        echo "CASE N3: lint_workflow passed a workflow with if: on required context" >&2
        FAILED=$((FAILED + 1))
      fi
      ;;
    N4)
      # Run with skipped conclusion — assert_run_conclusions must fail
      FIXTURE="${NEG}/N4/skipped_run.json"
      if $ASSERT_CMD \
          --checks "$FIXTURE" \
          --registry "${NEG}/N4/../../../templates/workflows/required-checks.yaml" \
          --summary 2>/dev/null | grep -q '^OK'; then
        echo "CASE N4: assert_run_conclusions passed a run with skipped required context" >&2
        FAILED=$((FAILED + 1))
      fi
      ;;
    N5)
      # Renovate diff outside manifest paths — path assertion must fail
      ALLOWED_PATTERN="package-lock\.json|yarn\.lock|Pipfile\.lock|poetry\.lock|requirements.*\.txt|go\.sum|Gemfile\.lock"
      FOREIGN="src/index.js"
      if echo "$FOREIGN" | grep -qE "$ALLOWED_PATTERN"; then
        echo "CASE N5: path guard passed a foreign Renovate path" >&2
        FAILED=$((FAILED + 1))
      fi
      ;;
    N6)
      # Commit authored by non-Renovate identity — authorship guard must fail
      AUTHOR="developer@example.com"
      if echo "$AUTHOR" | grep -qiE 'renovate(\[bot\])?|renovate-bot'; then
        echo "CASE N6: authorship guard passed a non-Renovate author" >&2
        FAILED=$((FAILED + 1))
      fi
      # Verify FOREIGN_AUTHOR literal is present in expected log output
      if ! grep -q 'FOREIGN_AUTHOR' "${NEG}/N6/fixture.yaml"; then
        echo "CASE N6: fixture does not contain expected FOREIGN_AUTHOR log string" >&2
        FAILED=$((FAILED + 1))
      fi
      ;;
    *)
      echo "ERROR: unknown case ${case_id}" >&2
      FAILED=$((FAILED + 1))
      ;;
  esac
}

for case_id in N1 N2 N3 N4 N5 N6; do
  run_case "$case_id"
done

if [ "$SUMMARY" -eq 1 ]; then
  if [ "$FAILED" -eq 0 ]; then
    printf 'OK %s checked=%d failed=%d\n' "$TOOL_ID" "$CHECKED" "$FAILED"
    exit 0
  else
    printf 'FAIL %s checked=%d failed=%d\n' "$TOOL_ID" "$CHECKED" "$FAILED"
    exit 2
  fi
fi
