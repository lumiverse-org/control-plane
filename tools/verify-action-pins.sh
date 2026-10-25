#!/usr/bin/env bash
# tools/verify-action-pins.sh — Invariant #85: third-party actions pinned to 40-char commit SHA (CP-0105)
set -euo pipefail

REPO=""
REQUIRE_SHA=0
REF="HEAD"
LOCAL_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --require-sha) REQUIRE_SHA=1; shift ;;
    --ref) REF="$2"; shift 2 ;;
    --local-dir) LOCAL_DIR="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$REPO" ] && [ -z "$LOCAL_DIR" ]; then
  echo "VERIFY-ACTION-PINS FAIL: --repo OWNER/NAME or --local-dir DIR required" >&2
  exit 2
fi

python3 - "$REPO" "$REQUIRE_SHA" "$REF" "$LOCAL_DIR" <<'PYEOF'
import sys, os, re, json, base64, subprocess
from pathlib import Path

repo = sys.argv[1]
require_sha = (sys.argv[2] == "1")
ref = sys.argv[3] or "HEAD"
local_dir = sys.argv[4]

SHA_REGEX = re.compile(r'^[0-9a-f]{40}$')
USES_REGEX = re.compile(r'(?:^|\s+)uses:\s*([^\s#]+)')

workflow_files = [] # list of (display_path, content_text)

if local_dir:
    ld = Path(local_dir)
    if not ld.is_dir():
        print(f"VERIFY-ACTION-PINS FAIL: local dir not found: {local_dir}", file=sys.stderr)
        sys.exit(2)
    # Search for all workflow files under .github/workflows or direct directory
    wf_dir = ld / ".github" / "workflows" if (ld / ".github" / "workflows").is_dir() else ld
    for p in wf_dir.rglob("*"):
        if p.is_file() and p.suffix in (".yml", ".yaml"):
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                workflow_files.append((p.as_posix(), content))
            except Exception as e:
                print(f"WARN: could not read {p}: {e}", file=sys.stderr)
else:
    # Fetch from GitHub via gh api
    # First get recursive tree
    endpoint = f"repos/{repo}/git/trees/{ref}?recursive=1"
    res = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"VERIFY-ACTION-PINS FAIL: error fetching repo {repo}: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    try:
        tree_data = json.loads(res.stdout)
    except Exception as e:
        print(f"VERIFY-ACTION-PINS FAIL: failed to parse tree JSON: {e}", file=sys.stderr)
        sys.exit(1)

    wf_paths = [
        item["path"]
        for item in tree_data.get("tree", [])
        if item.get("path", "").startswith(".github/workflows/")
        and (item.get("path", "").endswith(".yml") or item.get("path", "").endswith(".yaml"))
        and item.get("type") == "blob"
    ]

    for path in wf_paths:
        content_res = subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}"],
            capture_output=True,
            text=True,
        )
        if content_res.returncode == 0:
            try:
                c_json = json.loads(content_res.stdout)
                raw_b64 = c_json.get("content", "")
                decoded = base64.b64decode(raw_b64).decode("utf-8", errors="ignore")
                workflow_files.append((path, decoded))
            except Exception:
                pass

if not workflow_files:
    target_desc = local_dir if local_dir else f"{repo} ({ref})"
    print(f"VERIFY-ACTION-PINS FAIL: no workflow files found in {target_desc}", file=sys.stderr)
    sys.exit(1)

violations = []
total_actions = 0

for file_path, content in workflow_files:
    for line_no, line in enumerate(content.splitlines(), start=1):
        m = USES_REGEX.search(line)
        if not m:
            continue
        uses_target = m.group(1).strip()
        if "@" not in uses_target:
            continue
        action, _, action_ref = uses_target.partition("@")
        action = action.strip()
        action_ref = action_ref.strip()

        # Filter out internal reusable workflows and local actions
        if action.startswith(".") or action.startswith("/") or "/.github/workflows/" in action:
            continue

        total_actions += 1
        if require_sha:
            if not SHA_REGEX.match(action_ref):
                violations.append((file_path, line_no, action, action_ref))

target_name = local_dir if local_dir else repo
if violations:
    print(f"VERIFY-ACTION-PINS FAIL: {len(violations)} unpinned action(s) in {target_name}:", file=sys.stderr)
    for vf, vl, vact, vref in violations:
        print(f"  {vf}:{vl}: {vact}@{vref} (must be 40-character commit SHA, invariant #85)", file=sys.stderr)
    sys.exit(1)

print(f"VERIFY-ACTION-PINS OK: all {total_actions} third-party action(s) in {target_name} are pinned to 40-char SHA")
sys.exit(0)
PYEOF
