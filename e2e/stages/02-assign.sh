#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/02-assign.sh
source e2e/lib/checkpoint.sh

# Declared state only. Nobody touches GitHub Teams or CODEOWNERS by hand (invariant #55).
cp_assert CP-0201 "assignments merged to the registry" \
  ./tools/provision/apply-assignments --product "${E2E_PRODUCT}" \
    --set primary_owner=dev-a --set cross_reviewer=dev-b --set backup_owner=dev-b \
    --set primary_responder=dev-a --set backup_responder=dev-b --set verification=qa-1

cp_assert CP-0202 "reconciliation run applies declared state" \
  gh workflow run reconcile.yml -R "${E2E_CP_REPO}" -f mode=apply -f wait=true

# CP-0203 CODEOWNERS is GENERATED, and carries no machine identity (Section 53.1 independent verifier).
cp_assert CP-0203 "CODEOWNERS generated from assignments, no machine identity" \
  ./tools/provision/verify-codeowners --repo "${E2E_REPO}" --derived-from registry --forbid-machine-identities

# CP-0204 Team membership matches the contract (invariant #7; Section 53.1 fails CI on mismatch).
cp_assert CP-0204 "GitHub Team membership matches product.yaml assignments" \
  ./tools/provision/diff-team-membership --product "${E2E_PRODUCT}" --exit-nonzero-on-diff

# CP-0205 Zero blocking orphans for the new product (invariant #57).
cp_assert CP-0205 "no blocking orphans on pilot-one" \
  ./reconciler/orphan-report --product "${E2E_PRODUCT}" --fail-on blocking

# CP-0206 The cross-reviewer holds WRITE, not Read. A Read-only cross-reviewer fails silently
#         (Section 99.6, secondary risks) — so it is checked, loudly.
cp_assert CP-0206 "cross_reviewer holds Write" \
  ./tools/provision/check-permission --repo "${E2E_REPO}" --login dev-b --expect write
