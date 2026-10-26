#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/01-create-product.sh
source e2e/lib/checkpoint.sh

# The scaffolding operation. One command, run by a devops-capability holder. Nothing hand-made.
cp_assert CP-0101 "create-product completes" \
  ./tools/provision/create-product \
    --id "${E2E_PRODUCT}" \
    --contract e2e/fixtures/pilot-one/product.yaml \
    --template product-template \
    --executor devops-1

# CP-0102 The eight local-environment commands exist (Section 33.1) — AT-009 conformance.
for target in setup dev test uat-local migrate reset health parity; do
  cp_assert "CP-0102-${target}" "Makefile exposes ${target}" \
    bash -c "gh api repos/${E2E_REPO}/contents/Makefile --jq .content | base64 -d | grep -qE '^${target}:'"
done

# CP-0103 Required files present — checked, not assumed (Section 33.1).
cp_assert CP-0103 "required repository files present" \
  ./tools/provision/check-required-files --repo "${E2E_REPO}"
#   .env.example · docker-compose.dev.yml · Makefile · seed data · migrations/ · verification/ · AGENTS.md · product.yaml

# CP-0104 Required workflows present, all seven, generated from templates and consuming reusable
#         workflows by PINNED TAG (Section 33.2). restore-production.yml is required because the pilot
#         declares a recovery: block — AT-103.
for wf in ci build deploy-staging deploy-production migrate restore-test restore-production; do
  cp_assert "CP-0104-${wf}" "${wf}.yml generated and tag-pinned" \
    bash -c "gh api repos/${E2E_REPO}/contents/.github/workflows/${wf}.yml --jq .content | base64 -d \
             | grep -qE 'uses: (lumiverse-org|org)/control-plane/.github/workflows/.*@workflows/v[0-9]+'"
done

# CP-0105 Third-party actions pinned to full commit SHA — no tags, no branches (invariant #85).
cp_assert CP-0105 "third-party actions pinned to 40-char SHA" \
  ./tools/verify-action-pins.sh --repo "${E2E_REPO}" --require-sha

# CP-0106 Environments exist WITH deployment branch and tag policies (Section 33.4). The environments
#         alone are not the control; the ref restriction is.
cp_assert CP-0106 "staging and production restricted to default branch and protected tags" \
  ./tools/provision/check-environment-policy --repo "${E2E_REPO}" \
    --env staging --env production --expect default-branch,protected-tags

# CP-0107 Branch protection matches the committed template (Section 53.1, blocking row).
cp_assert CP-0107 "branch protection matches template" \
  ./tools/provision/diff-branch-protection --repo "${E2E_REPO}" --template templates/protection/service.json --exit-nonzero-on-diff

# CP-0108 AUTOMATIC DISCOVERY — AT-001. The product appears on every surface with nobody editing a
#         dashboard. Each of these enumerates from the registry.
for surface in portfolio-board grafana scorecard devlake reviewer-matrix dependency-graph; do
  cp_assert "CP-0108-${surface}" "pilot-one discoverable on ${surface}" \
    ./tools/verify-surface-enumeration.sh --surface "${surface}" --product "${E2E_PRODUCT}"
done

# CP-0109 AT-001's hard clause: no dashboard, workflow or script contains a product list.
cp_assert CP-0109 "no hard-coded product list anywhere" \
  ./tools/verify-no-product-list.sh --scan dashboards/ .github/workflows/ tools/ templates/

# CP-0110 The CONFIGURE checklist issue and the alert-channel / support-intake steps exist as tracked
#         work, not as silent omissions (Section 19.1).
cp_assert CP-0110 "CONFIGURE checklist and channel/mailbox steps emitted" \
  ./tools/provision/check-scaffold-issues --product "${E2E_PRODUCT}" \
    --require configure-checklist,alert-channel,support-intake
