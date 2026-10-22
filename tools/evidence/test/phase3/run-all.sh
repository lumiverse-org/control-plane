#!/usr/bin/env bash
# Lane 2 Phase 3 negative-test suite.
# Every gate of this phase is proven to FAIL CLOSED on its named condition.
# Spec: Sections 27.2, 33.4, 37.3, 39.5; charter DoD-04 and DoD-05.
# Re-runnable, offline, no GitHub API. Prints SUITE_PASS or SUITE_FAIL.
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
PY="${PYTHON:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY="python"
fi
X="$PY tools/evidence/test/phase3/extract-step.py"
F="tools/evidence/test/phase3/fixtures"
W="$(mktemp -d)"
PASS=0; FAIL=0

D1=sha256:1111111111111111111111111111111111111111111111111111111111111111
D2=sha256:2222222222222222222222222222222222222222222222222222222222222222
D3=sha256:3333333333333333333333333333333333333333333333333333333333333333

expect() {  # expect <label> <expected-token> <expected-rc> -- <command...>
  local label="$1" token="$2" want_rc="$3"; shift 4
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" = "$want_rc" ] && printf '%s' "$out" | grep -q "$token"; then
    echo "PASS ${label}"; PASS=$((PASS+1))
  else
    echo "FAIL ${label} rc=${rc} want=${want_rc}"
    printf '%s\n' "$out" | tail -3
    FAIL=$((FAIL+1))
  fi
}

# ---------------------------------------------------------------- runner tier
RT="$W/runner-tier.sh"
"$PY" -c "import yaml,sys;print(yaml.safe_load(open('templates/workflows/runner-tier-assert.step.yml'))[0]['run'])" > "$RT"

expect "runner-tier/hosted-passes" "RUNNER_TIER_OK hosted" 0 -- \
  env RUNNER_ENVIRONMENT=github-hosted PRIVILEGED_SELF_HOSTED_DECLARED=false \
      PRIVILEGED_RUNNER_MARKER=/nonexistent EPHEMERAL_RUNNER_MARKER=/nonexistent \
      bash "$RT"
expect "runner-tier/undeclared-self-hosted-refused" "RUNNER_TIER_UNDECLARED_SELF_HOSTED" 1 -- \
  env RUNNER_ENVIRONMENT=self-hosted PRIVILEGED_SELF_HOSTED_DECLARED=false \
      PRIVILEGED_RUNNER_MARKER=/nonexistent EPHEMERAL_RUNNER_MARKER=/nonexistent \
      bash "$RT"
expect "runner-tier/shared-pool-refused" "RUNNER_TIER_SHARED_POOL" 1 -- \
  env RUNNER_ENVIRONMENT=self-hosted PRIVILEGED_SELF_HOSTED_DECLARED=true \
      PRIVILEGED_RUNNER_MARKER=/nonexistent EPHEMERAL_RUNNER_MARKER=/nonexistent \
      bash "$RT"
touch "$W/priv.marker"
expect "runner-tier/non-ephemeral-refused" "RUNNER_TIER_NOT_EPHEMERAL" 1 -- \
  env RUNNER_ENVIRONMENT=self-hosted PRIVILEGED_SELF_HOSTED_DECLARED=true \
      PRIVILEGED_RUNNER_MARKER="$W/priv.marker" EPHEMERAL_RUNNER_MARKER=/nonexistent \
      bash "$RT"
touch "$W/eph.marker"
expect "runner-tier/privileged-ephemeral-passes" "RUNNER_TIER_OK privileged-ephemeral" 0 -- \
  env RUNNER_ENVIRONMENT=self-hosted PRIVILEGED_SELF_HOSTED_DECLARED=true \
      PRIVILEGED_RUNNER_MARKER="$W/priv.marker" EPHEMERAL_RUNNER_MARKER="$W/eph.marker" \
      bash "$RT"
expect "runner-tier/unknown-environment-refused" "RUNNER_TIER_UNRESOLVED" 1 -- \
  env RUNNER_ENVIRONMENT= PRIVILEGED_SELF_HOSTED_DECLARED=true \
      PRIVILEGED_RUNNER_MARKER="$W/priv.marker" EPHEMERAL_RUNNER_MARKER="$W/eph.marker" \
      bash "$RT"

# ----------------------------------------------------------------- actor gate
AG="$W/actor-gate.py"
$X .github/workflows/actor-gate.yml actor-gate "Resolve the actor against people.yaml" --python > "$AG"
mkdir -p "$W/ag"; cp "$F/registry/people.yaml" "$W/ag/people.yaml"
: > "$W/ag/out.txt"

expect "actor-gate/capable-human-passes" "ACTOR_GATE_PASS person-approver" 0 -- \
  bash -c 'cd "$0" && env ACTOR=approver-login REQUIRED_CAPABILITIES=production-approval MACHINE_DISPATCH_CLASS=none GITHUB_OUTPUT=out.txt '"$PY"' "$1"' "$W/ag" "$AG"
expect "actor-gate/unknown-actor-refused" "ACTOR_NOT_HUMAN" 1 -- \
  bash -c 'cd "$0" && env ACTOR=nobody REQUIRED_CAPABILITIES=production-approval MACHINE_DISPATCH_CLASS=none GITHUB_OUTPUT=out.txt '"$PY"' "$1"' "$W/ag" "$AG"
expect "actor-gate/machine-refused" "ACTOR_NOT_HUMAN" 1 -- \
  bash -c 'cd "$0" && env ACTOR=hermes-bot REQUIRED_CAPABILITIES=devops MACHINE_DISPATCH_CLASS=none GITHUB_OUTPUT=out.txt '"$PY"' "$1"' "$W/ag" "$AG"
expect "actor-gate/departed-refused" "ACTOR_NOT_ACTIVE" 1 -- \
  bash -c 'cd "$0" && env ACTOR=lapsed-login REQUIRED_CAPABILITIES=production-approval MACHINE_DISPATCH_CLASS=none GITHUB_OUTPUT=out.txt '"$PY"' "$1"' "$W/ag" "$AG"
expect "actor-gate/capability-missing-refused" "ACTOR_CAPABILITY_MISSING" 1 -- \
  bash -c 'cd "$0" && env ACTOR=deployer-login REQUIRED_CAPABILITIES=production-approval MACHINE_DISPATCH_CLASS=none GITHUB_OUTPUT=out.txt '"$PY"' "$1"' "$W/ag" "$AG"

# ------------------------------------------------------------- identity gate
IG="$W/identity.py"
$X .github/workflows/workflow-identity-gate.yml workflow-identity-gate \
   "Compare the approving identity with the deploying identity" --python > "$IG"

for d in approvals-clean approvals-self approvals-wrongdigest approvals-empty; do
  cp -r "$F/$d" "$W/$d"; : > "$W/$d/out.txt"
done

expect "identity/clean-passes" "IDENTITY_GATE_PASS" 0 -- \
  bash -c 'cd "$0" && env PRODUCT=demo DIGEST="$1" DEPLOYING_ACTOR=deployer-login GITHUB_OUTPUT=out.txt '"$PY"' "$2"' "$W/approvals-clean" "$D1" "$IG"
# charter DoD-04 — the exact string, no substitute accepted.
expect "identity/self-approval-refused" "APPROVER_EQUALS_DEPLOYER" 1 -- \
  bash -c 'cd "$0" && env PRODUCT=demo DIGEST="$1" DEPLOYING_ACTOR=deployer-login GITHUB_OUTPUT=out.txt '"$PY"' "$2"' "$W/approvals-self" "$D1" "$IG"
expect "identity/substituted-digest-refused" "APPROVAL_DIGEST_MISMATCH" 1 -- \
  bash -c 'cd "$0" && env PRODUCT=demo DIGEST="$1" DEPLOYING_ACTOR=deployer-login GITHUB_OUTPUT=out.txt '"$PY"' "$2"' "$W/approvals-wrongdigest" "$D1" "$IG"
expect "identity/no-approval-refused" "NO_APPROVAL_RECORD" 1 -- \
  bash -c 'cd "$0" && env PRODUCT=demo DIGEST="$1" DEPLOYING_ACTOR=deployer-login GITHUB_OUTPUT=out.txt '"$PY"' "$2"' "$W/approvals-empty" "$D1" "$IG"
expect "identity/unresolvable-deployer-refused" "DEPLOYER_UNRESOLVED" 1 -- \
  bash -c 'cd "$0" && env PRODUCT=demo DIGEST="$1" DEPLOYING_ACTOR=ghost GITHUB_OUTPUT=out.txt '"$PY"' "$2"' "$W/approvals-clean" "$D1" "$IG"

# --------------------------------------------------------------- rollback leg
RB="$W/rollback.py"
$X .github/workflows/rollback.yml rollback-target \
   "Resolve the rollback target and the migration boundary" --python > "$RB"
for d in rollback-clean rollback-nomigfield; do cp -r "$F/$d" "$W/$d"; : > "$W/$d/out.txt"; done

expect "rollback/target-resolves-and-flags-migration" "ROLLBACK_TARGET_OK" 0 -- \
  bash -c 'cd "$0" && env PRODUCT=demo CURRENT_DIGEST="$1" CONFIRM_DIGEST="$2" GITHUB_OUTPUT=out.txt '"$PY"' "$3"' "$W/rollback-clean" "$D2" "$D1" "$RB"
expect "rollback/confirmation-mismatch-refused" "ROLLBACK_CONFIRMATION_MISMATCH" 1 -- \
  bash -c 'cd "$0" && env PRODUCT=demo CURRENT_DIGEST="$1" CONFIRM_DIGEST="$2" GITHUB_OUTPUT=out.txt '"$PY"' "$3"' "$W/rollback-clean" "$D2" "$D3" "$RB"
expect "rollback/missing-migration-field-refused" "MIGRATION_BOUNDARY_UNRESOLVED" 1 -- \
  bash -c 'cd "$0" && env PRODUCT=demo CURRENT_DIGEST="$1" CONFIRM_DIGEST="$2" GITHUB_OUTPUT=out.txt '"$PY"' "$3"' "$W/rollback-nomigfield" "$D2" "$D1" "$RB"

# -------------------------------------------------------------- posture check
expect "posture/estate-passes" "PRIVILEGED_POSTURE_OK" 0 -- \
  "$PY" tools/evidence/assert-privileged-workflows.py --require rollback.template.yml
expect "posture/zero-templates-is-not-a-pass" "PRIVILEGED_NO_TEMPLATES_CHECKED" 2 -- \
  "$PY" tools/evidence/assert-privileged-workflows.py --templates-dir "$W/empty-dir-does-not-exist"

rm -rf "$W"
echo "PASS=${PASS} FAIL=${FAIL}"
if [ "$FAIL" = "0" ] && [ "$PASS" -ge 20 ]; then echo "SUITE_PASS"; else echo "SUITE_FAIL"; fi
