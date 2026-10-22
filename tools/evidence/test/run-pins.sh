#!/usr/bin/env bash
# Lane 2 - action-pin resolver and applier test harness (L2-T531).
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
EV="$(cd "$HERE/.." && pwd)"
PASS=0
FAIL=0

check() { # label expected_exit expected_first_token -- command...
  local label="$1" xc="$2" tok="$3"; shift 4
  local out rc first
  out="$("$@" 2>&1)"; rc=$?
  first="$(printf '%s' "$out" | head -1 | cut -d' ' -f1)"
  if [ "$rc" = "$xc" ] && [ "$first" = "$tok" ]; then
    printf 'PASS %s\n' "$label"; PASS=$((PASS+1))
  else
    printf 'FAIL %s expected_exit=%s got_exit=%s expected_token=%s got_token=%s output=%s\n' \
      "$label" "$xc" "$rc" "$tok" "$first" "$out"; FAIL=$((FAIL+1))
  fi
}

export PATH="$HERE/stub:$PATH"
R="$EV/resolve_action_pin.sh"

# Test 1: STUB_GH_MODE=ok resolve_action_pin.sh -> exit 0, stdout exactly "actions/checkout v7.0.1 <40 e's>"
EXPECTED_SHA="$(printf 'e%.0s' $(seq 1 40))"
EXPECTED_LINE="actions/checkout v7.0.1 ${EXPECTED_SHA}"
OUT="$(STUB_GH_MODE=ok bash "$R" actions/checkout v7.0.1 2>&1)"
RC=$?
if [ "$RC" -eq 0 ] && [ "$OUT" = "$EXPECTED_LINE" ]; then
  printf 'PASS resolve-ok\n'; PASS=$((PASS+1))
else
  printf 'FAIL resolve-ok expected_exit=0 got_exit=%s expected_out="%s" got_out="%s"\n' "$RC" "$EXPECTED_LINE" "$OUT"
  FAIL=$((FAIL+1))
fi

# Test 2: STUB_GH_MODE=not-found -> exit 3, token EVIDENCE-FAIL
check resolve-not-found 3 EVIDENCE-FAIL -- env STUB_GH_MODE=not-found bash "$R" actions/checkout v0.0.0-nope

# Test 3: STUB_GH_MODE=bad-sha -> exit 3, token EVIDENCE-FAIL
check resolve-bad-sha 3 EVIDENCE-FAIL -- env STUB_GH_MODE=bad-sha bash "$R" actions/checkout v7.0.1

# Test 4: tag omitted -> exit 3, token EVIDENCE-FAIL
check resolve-missing-tag 3 EVIDENCE-FAIL -- bash "$R" actions/checkout

# Test 5 & 6: apply_pins in scratch tree
SCRATCH1="$(mktemp -d)"
mkdir -p "$SCRATCH1/.github/workflows" "$SCRATCH1/templates/workflows" "$SCRATCH1/tools/evidence/lib"
cp "$EV/apply_pins.sh" "$SCRATCH1/tools/evidence/"
cp -r "$EV/lib/"* "$SCRATCH1/tools/evidence/lib/"
cat <<EOF > "$SCRATCH1/tools/evidence/action-pins.txt"
# Pinned actions
actions/checkout v7.0.1 ${EXPECTED_SHA}
EOF

printf 'uses: PIN:actions/checkout\n' > "$SCRATCH1/.github/workflows/wf.yml"
printf 'uses: PIN:actions/checkout\n' > "$SCRATCH1/templates/workflows/tmpl.yml"

(cd "$SCRATCH1" && bash tools/evidence/apply_pins.sh >/dev/null 2>&1)
RC5=$?
EXPECTED_CONTENT="uses: actions/checkout@${EXPECTED_SHA} # v7.0.1"
CONTENT1="$(cat "$SCRATCH1/.github/workflows/wf.yml")"
CONTENT2="$(cat "$SCRATCH1/templates/workflows/tmpl.yml")"

if [ "$RC5" -eq 0 ] && [ "$CONTENT1" = "$EXPECTED_CONTENT" ] && [ "$CONTENT2" = "$EXPECTED_CONTENT" ]; then
  printf 'PASS apply-pins-substitution\n'; PASS=$((PASS+1))
else
  printf 'FAIL apply-pins-substitution rc=%s c1="%s" c2="%s"\n' "$RC5" "$CONTENT1" "$CONTENT2"
  FAIL=$((FAIL+1))
fi

# Test 6: idempotent run 2
HASH1_PRE="$(sha256sum "$SCRATCH1/.github/workflows/wf.yml" | cut -d' ' -f1)"
HASH2_PRE="$(sha256sum "$SCRATCH1/templates/workflows/tmpl.yml" | cut -d' ' -f1)"
(cd "$SCRATCH1" && bash tools/evidence/apply_pins.sh >/dev/null 2>&1)
RC6=$?
HASH1_POST="$(sha256sum "$SCRATCH1/.github/workflows/wf.yml" | cut -d' ' -f1)"
HASH2_POST="$(sha256sum "$SCRATCH1/templates/workflows/tmpl.yml" | cut -d' ' -f1)"

if [ "$RC6" -eq 0 ] && [ "$HASH1_PRE" = "$HASH1_POST" ] && [ "$HASH2_PRE" = "$HASH2_POST" ]; then
  printf 'PASS apply-pins-idempotent\n'; PASS=$((PASS+1))
else
  printf 'FAIL apply-pins-idempotent rc=%s\n' "$RC6"
  FAIL=$((FAIL+1))
fi

# Test 7: unresolvable placeholder with empty/missing ledger row -> exit 3, files unchanged
SCRATCH2="$(mktemp -d)"
mkdir -p "$SCRATCH2/.github/workflows" "$SCRATCH2/templates/workflows" "$SCRATCH2/tools/evidence/lib"
cp "$EV/apply_pins.sh" "$SCRATCH2/tools/evidence/"
cp -r "$EV/lib/"* "$SCRATCH2/tools/evidence/lib/"
touch "$SCRATCH2/tools/evidence/action-pins.txt"
printf 'uses: PIN:actions/unknown\n' > "$SCRATCH2/.github/workflows/wf.yml"
HASH7_PRE="$(sha256sum "$SCRATCH2/.github/workflows/wf.yml" | cut -d' ' -f1)"
(cd "$SCRATCH2" && bash tools/evidence/apply_pins.sh >/dev/null 2>&1)
RC7=$?
HASH7_POST="$(sha256sum "$SCRATCH2/.github/workflows/wf.yml" | cut -d' ' -f1)"

if [ "$RC7" -eq 3 ] && [ "$HASH7_PRE" = "$HASH7_POST" ]; then
  printf 'PASS apply-pins-missing-ledger-exits-3-unchanged\n'; PASS=$((PASS+1))
else
  printf 'FAIL apply-pins-missing-ledger-exits-3-unchanged rc=%s pre=%s post=%s\n' "$RC7" "$HASH7_PRE" "$HASH7_POST"
  FAIL=$((FAIL+1))
fi

printf '\nL2 ACTION-PINS SUITE: pass=%s fail=%s\n' "$PASS" "$FAIL"
if [ "$FAIL" -ne 0 ]; then echo "SUITE_FAIL"; exit 1; fi
echo "SUITE_PASS"
exit 0
