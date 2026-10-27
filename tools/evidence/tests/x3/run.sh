#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "$0")/../../../.." || exit 1
. tools/evidence/tests/lib/dispatch.sh
d_preflight >/dev/null || { echo "X3 UNARMED (D-L2-11) - gate is RED, not skipped" >&2; exit 1; }
echo "X3 armed for $*"
