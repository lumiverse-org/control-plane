#!/usr/bin/env bash
# tools/records/rw-token.sh — Mints a short-lived records-writer installation token.
# MasterSpec Section 40.1 fifth secrets tier; D89; FD-136; L4-P1-T12.
# Requires: APP_ID, INSTALLATION_ID, RW_PEM (path to the private key).
# Prints the token on stdout and nothing else. Never log the output.
set -euo pipefail

: "${APP_ID:=5422825}"
: "${INSTALLATION_ID:=174038206}"
: "${RW_PEM:=${SECRETS_DIR:-C:/secrets}/records-writer.pem}"

if command -v wslpath >/dev/null 2>&1 && [[ "$RW_PEM" =~ ^[A-Za-z]: ]]; then
  RW_PEM="$(wslpath "$RW_PEM")"
fi

[ -r "${RW_PEM}" ] || { echo "rw-token.sh: cannot read ${RW_PEM}" >&2; exit 2; }

HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${L4_PY:-python3}"
if ! command -v "$PY" >/dev/null 2>&1; then
  PY="python"
fi

exec "$PY" "$HERE/lib/mint_token.py" --pem "$RW_PEM" --app-id "$APP_ID" --installation-id "$INSTALLATION_ID"
