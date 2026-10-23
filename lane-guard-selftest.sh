#!/usr/bin/env sh
# lane-guard-selftest.sh — L0-owned root file.
# Adversarial proof that the guard FAILS what it must fail. Builds throwaway
# repositories under a temp dir; touches nothing real. Exits non-zero on any
# case that does not behave exactly as specified.
set -eu
SELF_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WORK=$(mktemp -d 2>/dev/null || mktemp -d -t lgst)
trap 'rm -rf "$WORK"' EXIT
PASS=0; TOTAL=0

setup() {
  R="$WORK/$1"; mkdir -p "$R"; cd "$R"
  git init -q .
  git config user.email lane-guard@example.invalid
  git config user.name  lane-guard-selftest
  cp "$SELF_DIR/lane-paths.tsv" "$SELF_DIR/lane-owners.tsv" \
     "$SELF_DIR/lane-guard.sh"  "$SELF_DIR/lane-guard-exceptions.tsv" .
  chmod +x lane-guard.sh
  mkdir -p registries reconciler contracts contracts/ci .github/workflows
  echo base > registries/base.yaml
  echo base > reconciler/base.py
  echo base > contracts/base.md
  echo base > contracts/ci/lane-guard.yml.frozen
  echo base > .github/workflows/lane-guard.yml
  echo base > CODEOWNERS
  git add -A >/dev/null; git commit -q -m base
  git branch -f base HEAD
}

expect() {  # expect <num> <label> <lane> <want-rc> <want-grep> [pr]
  TOTAL=$((TOTAL + 1))
  _pr="${6:-none}"
  out=$(LG_PR="$_pr" sh ./lane-guard.sh "$3" base HEAD 2>&1) && rc=0 || rc=$?
  if [ "$rc" = "$4" ] && printf '%s' "$out" | grep -q "$5"; then
    printf 'CASE %s %-32s PASS\n' "$1" "$2"; PASS=$((PASS + 1))
  else
    printf 'CASE %s %-32s FAIL (rc=%s, wanted %s + /%s/)\n' "$1" "$2" "$rc" "$4" "$5"
    printf '%s\n' "$out" | sed 's/^/      /'
  fi
}

setup c01; echo more >> registries/base.yaml; git add -A >/dev/null; git commit -q -m c01
expect 01 same-lane-edit 1 0 'LANE-GUARD OK'

setup c02; echo more >> reconciler/base.py; git add -A >/dev/null; git commit -q -m c02
expect 02 foreign-path-named-owner 1 1 'owner lane   : 3'

setup c03; mkdir -p telemetry/agents; echo x > telemetry/agents/a.yaml
git add -A >/dev/null; git commit -q -m c03
expect 03 unassigned-tree 1 1 'UNASSIGNED-PATH'

setup c04; echo tampered > .github/workflows/lane-guard.yml
git add -A >/dev/null; git commit -q -m c04
expect 04 l2-edits-the-guard 2 1 'GUARD-CRITICAL'

setup c05; echo tampered > CODEOWNERS; git add -A >/dev/null; git commit -q -m c05
expect 05 lane-edits-codeowners 1 1 'GUARD-CRITICAL'

setup c06; echo more >> contracts/base.md; git add -A >/dev/null; git commit -q -m c06
expect 06 contracts-are-l0 1 1 'owner lane   : 0'

setup c07; git mv reconciler/base.py registries/moved.py; git commit -q -m c07
expect 07 rename-out-of-foreign-tree 1 1 'reconciler/base.py'

setup c08; echo x > "registries/a b.yaml"; git add -A >/dev/null; git commit -q -m c08
expect 08 illegal-path-with-space 1 1 'PATH-ILLEGAL'

setup c09
sha=$(printf 'reconciler/base.py' | git hash-object -w --stdin)
git update-index --add --cacheinfo 120000,"$sha",registries/link >/dev/null
git commit -q -m c09
expect 09 symlink-into-foreign-tree 1 1 'SYMLINK-ADDED'

setup c10; git rm -q reconciler/base.py; git commit -q -m c10
expect 10 delete-foreign-file 1 1 'owner lane   : 3'

setup c11; echo more >> reconciler/base.py; git add -A >/dev/null; git commit -q -m c11
printf 'EXC-LG-001\t1\treconciler/base.py\t42\t2099-12-31\t@lead\tlane 3 ships the real file\tselftest\n' \
  >> lane-guard-exceptions.tsv
expect 11 valid-override-honoured 1 0 'LANE-GUARD OVERRIDE' 42

setup c12; echo more >> reconciler/base.py; git add -A >/dev/null; git commit -q -m c12
printf 'EXC-LG-001\t1\treconciler/base.py\t42\t2000-01-01\t@lead\tlane 3 ships the real file\tselftest\n' \
  >> lane-guard-exceptions.tsv
expect 12 expired-override-refused 1 1 'FOREIGN-PATH' 42

setup c13; echo more >> reconciler/base.py; git add -A >/dev/null; git commit -q -m c13
printf 'EXC-LG-001\t1\treconciler/base.py\t42\t2099-12-31\t@lead\tlane 3 ships the real file\tselftest\n' \
  >> lane-guard-exceptions.tsv
expect 13 override-wrong-pr-refused 1 1 'FOREIGN-PATH' 43

setup c14; echo more >> registries/base.yaml; git add -A >/dev/null; git commit -q -m c14
printf 'EXC-LG-002\t1\tCODEOWNERS\t42\t2099-12-31\t@lead\tnever\tselftest\n' \
  >> lane-guard-exceptions.tsv
expect 14 override-refused-on-critical 1 2 'can never be excepted' 42

printf '\n %s/%s ' "$PASS" "$TOTAL"
if [ "$PASS" -eq "$TOTAL" ]; then printf 'PASS\n'; exit 0; fi
printf 'FAIL\n'; exit 1
