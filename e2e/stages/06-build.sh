#!/usr/bin/env bash
set -euo pipefail
# e2e/stages/06-build.sh
source e2e/lib/checkpoint.sh

cp_assert CP-0601 "build workflow produced an artifact" \
  ./tools/e2e-drive/wait-workflow --repo "${E2E_REPO}" --workflow build.yml \
    --sha "$(cat "${E2E_OUT}/merge-sha")" --expect success

# The digest. Everything downstream is this string.
[ ! -x ./tools/evidence/read-digest ] || ./tools/evidence/read-digest --repo "${E2E_REPO}" --sha "$(cat "${E2E_OUT}/merge-sha" 2>/dev/null || true)" > "${E2E_OUT}/digest" 2>/dev/null || true
cp_assert CP-0602 "digest recorded and well-formed" \
  bash -c 'grep -Eq "^sha256:[0-9a-f]{64}$" "${E2E_OUT}/digest"'

# CP-0603 SBOM emitted beside the digest (Section 33.2, Section 48.3).
cp_assert CP-0603 "SBOM recorded beside the digest" \
  ./tools/evidence/check-sbom --digest "$(cat "${E2E_OUT}/digest")" --require-format spdx-json

# CP-0604 artifact_built event with the digest in the payload (Section 97.3).
cp_assert CP-0604 "artifact_built event carries the digest" \
  ./tools/records/find-event --type artifact_built --product "${E2E_PRODUCT}" \
    --require "payload.digest=$(cat "${E2E_OUT}/digest")"

# CP-0605 The artifact is IMMUTABLE in the registry — the tag cannot be moved onto another digest.
cp_refute CP-0605 "registry refuses to overwrite the pushed digest tag" \
  'immutable|denied|409|cannot be overwritten' \
  ./tools/e2e-drive/attempt-tag-overwrite --registry ghcr.io/org/pilot-one --digest "$(cat "${E2E_OUT}/digest")"
