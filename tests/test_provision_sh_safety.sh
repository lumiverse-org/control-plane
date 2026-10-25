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
  echo "=== TEST 4: Problem 3 - Literal --org is required under --mode apply (exit 2) ==="
  set +e
  ERR_OUT=$(ORG="lumiverse-org" bash "$PROVISION_SH" create-product --product-id "alpha-prod" --product-name "Alpha" --mode apply 2>&1)
  RC=$?
  set -e
  if [[ $RC -ne 2 ]] || ! echo "$ERR_OUT" | grep -q "ERROR: --org must be passed explicitly"; then
    echo "FAIL: missing literal --org was not rejected with exit code 2. Got rc=$RC, out=$ERR_OUT" >&2
    exit 1
  fi
  echo "PASS: Omission of literal --org under apply rejected with exit code 2."
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
  4|problem3_org)
    run_test_4
    ;;
  5|problem4_private)
    run_test_5
    ;;
  6|dry_run)
    run_test_6
    ;;
  all)
    run_test_1
    run_test_2
    run_test_3
    run_test_4
    run_test_5
    run_test_6
    echo "ALL TESTS PASSED (6/6)."
    ;;
  *)
    echo "Unknown test target: $TARGET" >&2
    exit 1
    ;;
esac
