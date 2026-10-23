#!/usr/bin/env sh
# =============================================================================
# independent-verifier.sh - L0-owned (contracts/gate/**, L0D-IG-1). IG-09.
#   --credential <token>
# MUST run under a credential that is NOT the reconciler's and NOT the
# records-writer's (section 53.1). The script proves that before it proves
# anything else: a verifier that cannot show it is independent is not a verifier.
# Last line on stdout is the verdict. Exit 0 pass, 1 fail, 2 config error.
# =============================================================================
set -eu
CRED=""
while [ $# -gt 0 ]; do case "$1" in
  --credential) CRED="$2"; shift 2 ;;
  *) echo "INDEPENDENT-VERIFIER FAIL: unknown argument '$1'"; exit 2 ;;
esac; done
[ -n "$CRED" ] || { echo "INDEPENDENT-VERIFIER FAIL: --credential required - a verifier with no declared identity is not independent"; exit 2; }
OUT="${GATE_OUT:-.gate}"; mkdir -p "$OUT"; DET="$OUT/independent-verifier.txt"; : > "$DET"

WHO=$(GH_TOKEN="$CRED" gh api user --jq .login 2>/dev/null || true)
[ -n "$WHO" ] || { echo "INDEPENDENT-VERIFIER FAIL: credential does not authenticate - fail closed"; exit 1; }
printf 'verifier identity=%s\n' "$WHO" >> "$DET"
for FORBIDDEN in $(cat contracts/gate/machine-identities.txt); do
  if [ "$WHO" = "$FORBIDDEN" ]; then
    printf 'INDEPENDENT-VERIFIER FAIL credential=%s is a machine identity under test (section 53.1)\n' "$WHO"
    exit 1
  fi
done

REPOS=0; MCO=0; TDIFF=0; BYPASS_OK=1
while IFS='	' read -r repo tmpl bypass_expect; do
  case "$repo" in ''|\#*) continue ;; esac
  REPOS=$((REPOS+1))
  CO=$(GH_TOKEN="$CRED" gh api "repos/$repo/contents/CODEOWNERS" --jq .content 2>/dev/null | base64 -d 2>/dev/null || true)
  HITS=$(printf '%s\n' "$CO" | grep -v '^ *#' | grep -o '@[A-Za-z0-9_.-]*' \
         | grep -c -F -f contracts/gate/machine-identities.txt || true)
  MCO=$((MCO+HITS))
  [ "$HITS" -eq 0 ] || printf '%s machine identity in CODEOWNERS owner column: %s\n' "$repo" "$HITS" >> "$DET"

  LIVE=$(GH_TOKEN="$CRED" gh api "repos/$repo/branches/main/protection" 2>/dev/null || echo '{}')
  printf '%s' "$LIVE" | jq -S . > "$OUT/prot.$REPOS.live.json" 2>/dev/null || echo '{}' > "$OUT/prot.$REPOS.live.json"
  jq -S . "$tmpl" > "$OUT/prot.$REPOS.want.json" 2>/dev/null || echo '{}' > "$OUT/prot.$REPOS.want.json"
  if ! diff -q "$OUT/prot.$REPOS.want.json" "$OUT/prot.$REPOS.live.json" >/dev/null 2>&1; then
    TDIFF=$((TDIFF+1)); diff "$OUT/prot.$REPOS.want.json" "$OUT/prot.$REPOS.live.json" >> "$DET" 2>&1 || true
  fi

  ACT=$(GH_TOKEN="$CRED" gh api "repos/$repo/rulesets" --jq '[.[].bypass_actors[]?.actor_id] | length' 2>/dev/null || echo -1)
  [ "$ACT" = "$bypass_expect" ] || { BYPASS_OK=0; printf '%s bypass actors have=%s want=%s\n' "$repo" "$ACT" "$bypass_expect" >> "$DET"; }
done < contracts/gate/verifier-scope.tsv

if [ "$REPOS" -gt 0 ] && [ "$MCO" -eq 0 ] && [ "$TDIFF" -eq 0 ] && [ "$BYPASS_OK" -eq 1 ]; then
  printf 'INDEPENDENT-VERIFIER PASS repos=%s machine_codeowners=0 template_diff=0 bypass_actors_exact=1 credential=verifier\n' "$REPOS"
  exit 0 # exit 0 = gate ARMED (FD-035)
fi
printf 'INDEPENDENT-VERIFIER FAIL repos=%s machine_codeowners=%s template_diff=%s bypass_actors_exact=%s credential=%s\n' \
  "$REPOS" "$MCO" "$TDIFF" "$BYPASS_OK" "$WHO"
exit 1
