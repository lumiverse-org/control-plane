#!/usr/bin/env bash
# tools/verify-no-product-list.sh — AT-001 hard clause: no dashboard, workflow or script contains a product list
set -euo pipefail

SCAN_PATHS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --scan)
      shift
      while [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; do
        SCAN_PATHS+=("$1")
        shift
      done
      ;;
    *)
      SCAN_PATHS+=("$1")
      shift
      ;;
  esac
done

if [ ${#SCAN_PATHS[@]} -eq 0 ]; then
  SCAN_PATHS=(".github/workflows" "tools" "templates")
fi

python3 - "${SCAN_PATHS[@]}" <<'PYEOF'
import sys, os, re

scan_paths = sys.argv[1:]
violations = []

# Pattern 1: YAML array containing multiple products: [Product-01, Product-02, ...] or matrix: [Product-...]
# Pattern 2: Multi-line list items: - Product-01 \n - Product-02
# Exclude test files, fixtures, self script
EXCLUDE_DIRS = {".git", "__pycache__", "tests", "fixtures", "node_modules", "scratch"}

for base in scan_paths:
    if not os.path.exists(base):
        continue
    if os.path.isfile(base):
        files_to_check = [base]
    else:
        files_to_check = []
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith((".py", ".sh", ".yaml", ".yml", ".json", ".md")):
                    files_to_check.append(os.path.join(root, f))
    
    for fpath in files_to_check:
        if "verify-no-product-list" in fpath or "test_" in fpath:
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        # Look for hardcoded list/matrix of products: e.g. "products: [Product-1, Product-2]"
        inline_list = re.findall(r'(?:products|matrix|repos)\s*[:=]\s*\[[^\]]*Product-[0-9]+[^\]]*Product-[0-9]+[^\]]*\]', content, re.IGNORECASE)
        if inline_list:
            violations.append(f"{fpath}: hard-coded inline product list found: {inline_list[0][:80]}")

        # Look for consecutive product list items in yaml/markdown
        block_list = re.findall(r'(?:-\s*[\'"]?Product-[0-9]+[\'"]?\s*\n\s*-\s*[\'"]?Product-[0-9]+[\'"]?)', content)
        if block_list:
            violations.append(f"{fpath}: hard-coded product list block found")

if violations:
    print(f"VERIFY-NO-PRODUCT-LIST FAIL: {len(violations)} hardcoded product list violations found:")
    for v in violations:
        print(f"  {v}")
    sys.exit(1)

print("VERIFY-NO-PRODUCT-LIST PASS: No hard-coded product lists found in scanned paths.")
sys.exit(0)
PYEOF
