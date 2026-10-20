#!/usr/bin/env bash
# Lane 1 pinned-toolchain preflight (spec Section 99.2, subsystem B; invariant 85).
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
cd "$REPO_ROOT"

fail() {
  echo "PREFLIGHT FAIL: $1"
  exit 1
}

PY_VERSION="$(python3 --version 2>&1)" || fail "python3 not found"
echo "$PY_VERSION" | grep -qE '^Python 3\.12\.' || fail "python3 is not 3.12 (found: ${PY_VERSION})"

python3 -c "import jsonschema, yaml, pytest" 2>/dev/null || fail "jsonschema, yaml or pytest is not importable"

for d in rules tests fixtures; do
  test -d "validators/registry/${d}" || fail "validators/registry/${d} does not exist"
done

echo "PREFLIGHT OK"
