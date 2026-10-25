#!/usr/bin/env bash
# tests/test_provision_sh_safety.sh — safety regression test suite for scripts/provision/provision.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROVISION_SH="$REPO_ROOT/scripts/provision/provision.sh"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Mock gh CLI that logs arguments to a file
cat > "$TMPDIR/gh" << 'EOF'
#!/usr/bin/env bash
echo "$@" >> "$MOCK_GH_LOG"
exit 0
EOF
chmod +x "$TMPDIR/gh"

export PATH="$TMPDIR:$PATH"
export GITHUB_TOKEN="mock-token-for-test"
export MOCK_GH_LOG="$TMPDIR/gh_invocations.txt"

# Sanity check: verify mock gh CLI interception works before trusting any test results
rm -f "$MOCK_GH_LOG"
gh sanity-check-interception
if ! grep -q "sanity-check-interception" "$MOCK_GH_LOG"; then
  echo "FAIL: Mock gh CLI interception failed sanity check!" >&2
  exit 1
fi
rm -f "$MOCK_GH_LOG"

run_test_1() {
  echo "=== TEST 1: Command injection via eval is completely neutralized ==="
  PROOF_FILE="$TMPDIR/INJECTED_PROOF"
  INJECTION_PAYLOAD="Evil'; touch $PROOF_FILE; echo 'done"

  (
    cd "$TMPDIR"
    bash "$PROVISION_SH" create-product \
      --product-id "safe-prod" \
      --product-name "$INJECTION_PAYLOAD" \
      --org "test-org" \
      --mode apply
  )

  if [[ -f "$PROOF_FILE" ]]; then
    echo "FAIL: INJECTED_PROOF was created via command injection!" >&2
    exit 1
  fi
  echo "PASS: Command injection blocked; INJECTED_PROOF was not created."

  # Verify gh received description literally
  if ! grep -q "Evil'; touch" "$MOCK_GH_LOG"; then
    echo "FAIL: Expected literal payload in gh invocation log" >&2
    cat "$MOCK_GH_LOG" >&2
    exit 1
  fi
  echo "PASS: Injection payload passed as literal description argument to gh."
}

run_test_2() {
  echo "=== TEST 2: Problem 2 - Invalid product IDs are rejected (exit 2) ==="
  BAD_PRODUCT_IDS=(
    "../../etc/cronjob"
    "../traversal"
    "/absolute/path"
    "has space"
    "has;semicolon"
    'has`backtick`'
    'has$(subshell)'
    "has'quote"
    'has"doublequote'
  )

  for bad_id in "${BAD_PRODUCT_IDS[@]}"; do
    set +e
    ERR_OUT=$(bash "$PROVISION_SH" create-product --product-id "$bad_id" --product-name "Valid" --org "test-org" --mode dry 2>&1)
    RC=$?
    set -e
    if [[ $RC -ne 2 ]] || ! echo "$ERR_OUT" | grep -q "ERROR: Invalid --product-id"; then
      echo "FAIL: bad product-id '$bad_id' was not rejected with exit code 2. Got rc=$RC, out=$ERR_OUT" >&2
      exit 1
    fi
  done
  echo "PASS: All ${#BAD_PRODUCT_IDS[@]} invalid product-id variants rejected with exit code 2."
}

run_test_3() {
  echo "=== TEST 3: Problem 2 - Invalid repo names are rejected (exit 2) ==="
  BAD_REPOS=(
    "../../etc/cronjob"
    "../traversal"
    "has space"
    "has;semicolon"
    'has`backtick`'
    'has$(subshell)'
  )

  for bad_repo in "${BAD_REPOS[@]}"; do
    set +e
    ERR_OUT=$(bash "$PROVISION_SH" create-product --product-id "valid-prod" --product-name "Valid" --repo "$bad_repo" --org "test-org" --mode dry 2>&1)
    RC=$?
    set -e
    if [[ $RC -ne 2 ]] || ! echo "$ERR_OUT" | grep -q "ERROR: Invalid --repo"; then
      echo "FAIL: bad repo '$bad_repo' was not rejected with exit code 2. Got rc=$RC, out=$ERR_OUT" >&2
      exit 1
    fi
  done
  echo "PASS: All ${#BAD_REPOS[@]} invalid repo variants rejected with exit code 2."
}

run_test_4() {
  echo "=== TEST 4: GAP A - Strict --org validation and whitespace rejection under --mode apply ==="
  
  # 1. Test omission of --org flag
  rm -f "$MOCK_GH_LOG"
  SANDBOX="$TMPDIR/sb_org_omit"
  mkdir -p "$SANDBOX"
  set +e
  ERR_OUT=$(cd "$SANDBOX" && ORG="lumiverse-org" bash "$PROVISION_SH" create-product --product-id "alpha-prod" --product-name "Alpha" --mode apply 2>&1)
  RC=$?
  set -e
  if [[ $RC -ne 2 ]] || ! echo "$ERR_OUT" | grep -q "ERROR: --org must be passed explicitly"; then
    echo "FAIL: missing literal --org was not rejected with exit code 2. Got rc=$RC, out=$ERR_OUT" >&2
    exit 1
  fi
  if [[ -d "$SANDBOX/records" || -d "$SANDBOX/registries" || -f "$MOCK_GH_LOG" ]]; then
    echo "FAIL: side effects produced when --org was omitted!" >&2
    exit 1
  fi

  # 2. Test all whitespace variants
  declare -A WS_VARIANTS=(
    ["space"]="   "
    ["tab"]=$'\t'
    ["newline"]=$'\n'
    ["cr"]=$'\r'
    ["vt"]=$'\v'
    ["ff"]=$'\f'
    ["nbsp"]=$'\xC2\xA0'
    ["mixed"]=$' \t \r\n '
    ["empty"]=""
  )

  for ws_name in "${!WS_VARIANTS[@]}"; do
    ws_val="${WS_VARIANTS[$ws_name]}"
    rm -f "$MOCK_GH_LOG"
    WS_BOX="$TMPDIR/sb_ws_${ws_name}"
    mkdir -p "$WS_BOX"
    set +e
    ERR_OUT=$(cd "$WS_BOX" && ORG="lumiverse-org" bash "$PROVISION_SH" create-product --product-id "ws-prod" --product-name "WS Prod" --org "$ws_val" --mode apply 2>&1)
    RC=$?
    set -e
    if [[ $RC -ne 2 ]] || ! echo "$ERR_OUT" | grep -q "ERROR: --org must be passed explicitly"; then
      echo "FAIL: whitespace --org variant '$ws_name' was not rejected with exit code 2. Got rc=$RC, out=$ERR_OUT" >&2
      exit 1
    fi
    if [[ -d "$WS_BOX/records" || -d "$WS_BOX/registries" || -f "$MOCK_GH_LOG" ]]; then
      echo "FAIL: side effects produced for whitespace --org variant '$ws_name'!" >&2
      exit 1
    fi
  done
  echo "PASS: All 9 whitespace/empty --org variants rejected with exit 2 and zero side-effects."

  # 3. Test invalid org regex variants
  BAD_ORGS=(
    "../../evil"
    "bad/org"
    "org;evil"
    'org`backtick`'
    'org$(subshell)'
    "org with space"
  )
  for bad_org in "${BAD_ORGS[@]}"; do
    rm -f "$MOCK_GH_LOG"
    BAD_BOX="$TMPDIR/sb_badorg"
    rm -rf "$BAD_BOX" && mkdir -p "$BAD_BOX"
    set +e
    ERR_OUT=$(cd "$BAD_BOX" && bash "$PROVISION_SH" create-product --product-id "bad-prod" --product-name "Bad" --org "$bad_org" --mode apply 2>&1)
    RC=$?
    set -e
    if [[ $RC -ne 2 ]] || ! echo "$ERR_OUT" | grep -q "ERROR: Invalid --org"; then
      echo "FAIL: bad org '$bad_org' was not rejected with exit code 2. Got rc=$RC, out=$ERR_OUT" >&2
      exit 1
    fi
    if [[ -d "$BAD_BOX/records" || -d "$BAD_BOX/registries" || -f "$MOCK_GH_LOG" ]]; then
      echo "FAIL: side effects produced for bad org '$bad_org'!" >&2
      exit 1
    fi
  done
  echo "PASS: All ${#BAD_ORGS[@]} invalid --org regex variants rejected with exit 2 and zero side-effects."
}

run_test_5() {
  echo "=== TEST 5: Problem 4 - Repositories created --private (not --public) ==="
  rm -f "$MOCK_GH_LOG"
  (
    cd "$TMPDIR"
    bash "$PROVISION_SH" create-product \
      --product-id "beta-prod" \
      --product-name "Beta Product" \
      --org "test-org" \
      --mode apply
  )

  if ! grep -q -- "--private" "$MOCK_GH_LOG"; then
    echo "FAIL: Expected --private in gh repo create invocation" >&2
    cat "$MOCK_GH_LOG" >&2
    exit 1
  fi

  if grep -q -- "--public" "$MOCK_GH_LOG"; then
    echo "FAIL: Found unexpected --public in gh repo create invocation" >&2
    cat "$MOCK_GH_LOG" >&2
    exit 1
  fi
  echo "PASS: Repository created with --private by default."
}

run_test_6() {
  echo "=== TEST 6: Dry-run mode functions cleanly without --org or writes ==="
  DRY_OUT=$(bash "$PROVISION_SH" create-product --product-id "gamma-prod" --product-name "Gamma" --mode dry)
  if ! echo "$DRY_OUT" | grep -q "\[DRY-RUN\] Would create GitHub repo: lumiverse-org/gamma-prod"; then
    echo "FAIL: Unexpected dry-run output: $DRY_OUT" >&2
    exit 1
  fi
  if ! echo "$DRY_OUT" | grep -q "\[DRY-RUN\] Would create: records/products/gamma-prod.yaml"; then
    echo "FAIL: Unexpected dry-run record line: $DRY_OUT" >&2
    exit 1
  fi
  echo "PASS: Dry-run planning mode completely functional and unregressed."
}

run_test_7() {
  echo "=== TEST 7: GAP B - --product-name YAML escaping and integrity ==="
  NAME_VARIANTS=(
    'Evil", injected_field: "pwned'
    'Has "double quotes" inside'
    $'Multi\nLine\nName'
    'Back\Slash\Name'
    $'Complex "Name" \\ with \n newlines and \t tabs'
  )

  local idx=0
  for test_name in "${NAME_VARIANTS[@]}"; do
    idx=$((idx + 1))
    PID="esc-prod-${idx}"
    TEST_DIR="$TMPDIR/sb_esc_${idx}"
    mkdir -p "$TEST_DIR"
    rm -f "$MOCK_GH_LOG"

    (
      cd "$TEST_DIR"
      bash "$PROVISION_SH" create-product \
        --product-id "$PID" \
        --product-name "$test_name" \
        --org "test-org" \
        --mode apply
    )

    PROD_RECORD="$TEST_DIR/records/products/${PID}.yaml"
    CAP_RECORD="$TEST_DIR/registries/capabilities/${PID}.yaml"

    if [[ ! -f "$PROD_RECORD" || ! -f "$CAP_RECORD" ]]; then
      echo "FAIL: Record or capability file missing for test variant $idx" >&2
      exit 1
    fi

    # Verify records parse cleanly with Python's yaml parser and data matches exactly
    python3 -c "
import yaml, sys
path_p = sys.argv[1]
path_c = sys.argv[2]
expected = sys.argv[3]

with open(path_p, 'r', encoding='utf-8') as f:
    data_p = yaml.safe_load(f)
assert data_p['name'] == expected, f'Product record mismatch: {data_p[\"name\"]} != {expected}'

with open(path_c, 'r', encoding='utf-8') as f:
    data_c = yaml.safe_load(f)
assert data_c['name'] == expected, f'Capability record mismatch: {data_c[\"name\"]} != {expected}'
" "$PROD_RECORD" "$CAP_RECORD" "$test_name"

    echo "PASS: Variant $idx record parses cleanly and preserves exact input string."
  done
  echo "PASS: All ${#NAME_VARIANTS[@]} --product-name escaping variants verified with real YAML parser."
}

TARGET="${1:-all}"
case "$TARGET" in
  1|problem1)
    run_test_1
    ;;
  2|problem2_product_id)
    run_test_2
    ;;
  3|problem2_repo)
    run_test_3
    ;;
  4|gap_a_org)
    run_test_4
    ;;
  5|problem4_private)
    run_test_5
    ;;
  6|dry_run)
    run_test_6
    ;;
  7|gap_b_yaml)
    run_test_7
    ;;
  all)
    run_test_1
    run_test_2
    run_test_3
    run_test_4
    run_test_5
    run_test_6
    run_test_7
    echo "ALL TESTS PASSED (7/7)."
    ;;
  *)
    echo "Unknown test target: $TARGET" >&2
    exit 1
    ;;
esac
