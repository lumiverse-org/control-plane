#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/13-access.sh
source e2e/lib/checkpoint.sh

# CP-1310 AT-108 — the founder ops console is provably read-only: four attempts fail, then a read query
#         over Layer A still answers correctly.
cp_assert CP-1310 "ops console read-only on all four attempts, read still works" \
  ./tools/e2e-drive/at-108-ops-console.sh

# CP-1311 AT-109 — the background cage egress wall holds at the HOST layer, not by harness configuration,
#         and the systemd wall-clock stop terminates the worker at the window boundary.
cp_assert CP-1311 "cage egress wall and wall-clock stop hold" \
  ./tools/e2e-drive/at-109-cage.sh

# CP-1312 Invariant #18 / Section 37.3 actor gate: the background machine account cannot merge, approve or
#         deploy — verified GitHub-side, outside the harness.
cp_assert CP-1312 "machine account restricted to draft PRs, GitHub-side" \
  ./tools/e2e-drive/draft-pr-only-verification.sh --account machine-bg

# CP-1313 Invariant #111 — no customer data in repositories. Fixture provenance and record construction
#         are both checked on the pilot's tree and records.
cp_assert CP-1313 "no customer data in repositories" \
  ./tools/evidence/check-no-customer-data --repo "${E2E_REPO}" --records "${E2E_RECORDS_REPO}"
