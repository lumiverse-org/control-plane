#!/usr/bin/env bash
# e2e/lib/checkpoint.sh
set -euo pipefail

: "${E2E_RUN_ID:?run ./e2e/run.sh — never a stage script directly}"
export E2E_OUT="e2e/out/${E2E_RUN_ID}"
mkdir -p "${E2E_OUT}/evidence" "${E2E_OUT}/checkpoints"
E2E_LOG="${E2E_OUT}/checkpoints/log.tsv"

_emit() { printf '%s\t%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "$3" >>"${E2E_LOG}"; }

cp_pass() { _emit "$1" PASS "$2"; printf '  ok   %s  %s\n' "$1" "$2"; }
cp_fail() { _emit "$1" FAIL "$2"; printf '  FAIL %s  %s\n' "$1" "$2"; exit 1; }

# POSITIVE checkpoint: the command must succeed.
cp_assert() {
  local id="$1" what="$2"; shift 2
  if "$@" >"${E2E_OUT}/evidence/${id}.out" 2>&1; then
    cp_pass "$id" "$what"
  else
    cp_fail "$id" "$what — evidence: ${E2E_OUT}/evidence/${id}.out"
  fi
}

# EQUALITY checkpoint: two values must be byte-identical. Used for the digest chain.
cp_equal() {
  local id="$1" what="$2" a="$3" b="$4"
  printf 'expected=%s\nactual=%s\n' "$a" "$b" >"${E2E_OUT}/evidence/${id}.out"
  [ "$a" = "$b" ] && cp_pass "$id" "$what" || cp_fail "$id" "$what — '$a' != '$b'"
}

# NEGATIVE checkpoint: the command MUST fail, AND must fail for the stated reason.
# A negative test that fails for the wrong reason is not a negative test.
cp_refute() {
  local id="$1" what="$2" reason_re="$3"; shift 3
  if "$@" >"${E2E_OUT}/evidence/${id}.out" 2>&1; then
    cp_fail "$id" "GATE DID NOT FIRE — '$what' succeeded and must not have"
  elif grep -Eq "$reason_re" "${E2E_OUT}/evidence/${id}.out"; then
    cp_pass "$id" "gate fired: $what refused, reason matched /$reason_re/"
  else
    cp_fail "$id" "WRONG REASON — '$what' failed, but not on /$reason_re/; the gate may be broken rather than working"
  fi
}
