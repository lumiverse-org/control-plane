#!/usr/bin/env bash
set -euo pipefail
VENV="$HOME/.venv-l5"
python -m venv "$VENV" 2>/dev/null || python3 -m venv "$VENV"
if [ -x "$VENV/bin/python" ]; then PY="$VENV/bin/python"; else PY="$VENV/Scripts/python.exe"; fi
"$PY" -m pip install --disable-pip-version-check -q -r infra/requirements.txt
echo "L5PY=$PY"
