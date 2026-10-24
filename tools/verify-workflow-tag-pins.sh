#!/usr/bin/env bash
# tools/verify-workflow-tag-pins.sh — Verify reusable workflow tag pins against platform.yaml (§33.2, invariant #85, CP-0004)
set -euo pipefail

STRICT=0
PLATFORM_YAML="registries/platform.yaml"

while [ $# -gt 0 ]; do
  case "$1" in
    --strict) STRICT=1; shift ;;
    --platform) PLATFORM_YAML="$2"; shift 2 ;;
    *) shift ;;
  esac
done

python3 - <<PYEOF
import sys, os, re, yaml, subprocess

strict = ($STRICT == 1)
platform_path = "${PLATFORM_YAML}"

# 1. Load registries/platform.yaml
if not os.path.isfile(platform_path):
    print(f"ERROR: platform registry not found at {platform_path}")
    sys.exit(1)

with open(platform_path, "r", encoding="utf-8") as f:
    try:
        data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"ERROR: failed to parse {platform_path}: {e}")
        sys.exit(1)

rwv = data.get("reusable_workflow_versions", {})
# Known formats: tag_pins dict, current/supported lists, etc.
current_tag = rwv.get("current")
supported_tags = set(rwv.get("supported") or [])
if current_tag:
    supported_tags.add(current_tag)

tag_pins = rwv.get("tag_shas") or rwv.get("pins") or {}

# 2. Find all uses: .../workflows/*@TAG references
scan_dirs = [".github/workflows", "templates/workflows"]
consumed_tags = {} # tag -> list of files

pattern = re.compile(r'^\s*-\s*uses:\s*([^\s#]+@([^\s#]+))|^\s*uses:\s*([^\s#]+@([^\s#]+))')

for sdir in scan_dirs:
    if not os.path.isdir(sdir):
        continue
    for root, _, files in os.walk(sdir):
        for file in files:
            if not (file.endswith(".yml") or file.endswith(".yaml")):
                continue
            fpath = os.path.join(root, file)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    m = pattern.search(line)
                    if m:
                        full_ref = m.group(1) or m.group(3)
                        tag = m.group(2) or m.group(4)
                        # Check if it's a reusable workflow call (contains workflows/)
                        if "workflows" in full_ref and not tag.startswith("{{"):
                            # Strip any comments or trailing quotes
                            tag = tag.strip("\"' ")
                            consumed_tags.setdefault(tag, []).append(fpath)

if not consumed_tags:
    print("PASS: zero workflow tags consumed in scanned directories")
    sys.exit(0)

errors = []
for tag, files in sorted(consumed_tags.items()):
    # Check if tag exists in git
    res = subprocess.run(["git", "rev-parse", f"refs/tags/{tag}^{{commit}}"], capture_output=True, text=True)
    git_sha = res.stdout.strip() if res.returncode == 0 else None
    
    # Check if tag is recorded in platform.yaml
    expected_sha = tag_pins.get(tag)
    
    if strict:
        if tag not in supported_tags and tag not in tag_pins:
            errors.append(f"Tag '{tag}' is consumed in {len(files)} file(s) ({files[0]}) but is NOT recorded in {platform_path} reusable_workflow_versions")
        elif expected_sha and git_sha and expected_sha != git_sha:
            errors.append(f"Tag '{tag}' git SHA ({git_sha[:8]}) does not match {platform_path} recorded SHA ({expected_sha[:8]})")
        elif not git_sha:
            errors.append(f"Tag '{tag}' consumed in {files[0]} does not resolve to a git commit SHA")
    else:
        if expected_sha and git_sha and expected_sha != git_sha:
            errors.append(f"Tag '{tag}' git SHA mismatch: git={git_sha[:8]} vs recorded={expected_sha[:8]}")

if errors:
    print("FAIL: consumed workflow tags do not match platform.yaml pins:")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)

print(f"PASS: all {len(consumed_tags)} consumed workflow tag(s) match platform.yaml pins")
sys.exit(0)
PYEOF
