#!/usr/bin/env python3
"""
tools.evidence.render_template
L2-T539: Template renderer and placeholder lint (§19.1 L1826-1882)

Three modes, one tool-id ("render_template"):
  --lint <dir>                      Every {{TOKEN}} used in a *.yml template directly under
                                     <dir> is declared in <dir>/PLACEHOLDERS.yaml; every
                                     declared token is used by at least one template; no
                                     token sits inside a GitHub Actions ${{ }} expression.
  --render <file> [--values <yaml>] Substitutes {{TOKEN}} and prints to stdout only. NEVER
                                     writes into a product repository -- that is
                                     create-product, Lane 3's tree (PARTITION.md rule 4).
  --manifest <file>                 Validates that every templates/workflows/MANIFEST.yaml
                                     entry's "file" exists relative to the manifest (L2-T311).

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required", file=sys.stderr)
    print("ERROR render_template checked=0 failed=0")
    sys.exit(3)

import tools.evidence as e

TOOL_ID = "render_template"
PLACEHOLDER_FILE = "PLACEHOLDERS.yaml"
TOKEN_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
GHA_EXPR_RE = re.compile(r"\$\{\{[^}]*\{\{[A-Z_]+\}\}")


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load_placeholders(directory: Path) -> set[str] | None:
    """Load declared {{TOKEN}} strings from <directory>/PLACEHOLDERS.yaml.
    Returns None (after printing an ERROR to stderr) on any failure."""
    pf = directory / PLACEHOLDER_FILE
    if not pf.exists():
        print(f"ERROR: {PLACEHOLDER_FILE} not found in {directory}", file=sys.stderr)
        return None
    try:
        data = yaml.safe_load(pf.read_text())
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: cannot parse {pf}: {ex}", file=sys.stderr)
        return None
    if data is None:
        data = {}
    if not isinstance(data, dict):
        print(f"ERROR: {pf} is not a YAML mapping", file=sys.stderr)
        return None
    return set(data.get("tokens", []))


def cmd_lint(directory: Path, summary: bool) -> int:
    """--lint mode: validate every *.yml template file directly inside <directory>."""
    if not directory.is_dir():
        print(f"ERROR: {directory} is not a directory", file=sys.stderr)
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    declared = _load_placeholders(directory)
    if declared is None:
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    templates = sorted(directory.glob("*.yml"))
    checked = 0
    failed = 0
    used_tokens: set[str] = set()

    for tpl in templates:
        checked += 1
        try:
            content = tpl.read_text()
        except Exception as ex:  # noqa: BLE001
            print(f"ERROR: cannot read {tpl}: {ex}", file=sys.stderr)
            failed += 1
            continue

        found = set(TOKEN_RE.findall(content))
        full_found = {f"{{{{{t}}}}}" for t in found}
        used_tokens |= full_found

        # Rule 1: every token used in this template must be declared.
        for tok in sorted(full_found - declared):
            print(f"FAIL {tpl.name}: token {tok} is not declared in {PLACEHOLDER_FILE}", file=sys.stderr)
            failed += 1

        # Rule 3: no token may sit inside a GitHub Actions ${{ }} expression.
        for line_no, line in enumerate(content.splitlines(), 1):
            if GHA_EXPR_RE.search(line):
                print(
                    f"FAIL {tpl.name}:{line_no}: token inside GHA ${{{{ }}}} expression: {line.strip()}",
                    file=sys.stderr,
                )
                failed += 1

    # Rule 2: every declared token must be used by at least one template -- except when the
    # directory holds no templates at all (checked == 0). The sibling task's own README text
    # (quoted in L2-T300's body, lanes/L2-05-tasks.md ~line 4399) states this case explicitly:
    # "A run over an empty directory is OK render_template checked=0 failed=0 ... not an error."
    # Flagging every declared token as "unused" in that case would contradict that documented
    # contract, so Rule 2 is scoped to directories that actually hold at least one template.
    if checked > 0:
        for tok in sorted(declared - used_tokens):
            print(f"FAIL {PLACEHOLDER_FILE}: declared token {tok} is unused across all templates", file=sys.stderr)
            failed += 1

    if summary:
        if failed == 0:
            _summary(e.STATUS_OK, checked, 0)
        else:
            _summary(e.STATUS_FAIL, checked, failed)
    return e.EXIT_OK if failed == 0 else e.EXIT_FAIL


def cmd_render(template_file: Path, values_file: Path | None, summary: bool) -> int:
    """--render mode: substitute {{TOKEN}} and print to stdout ONLY.
    NEVER writes into a product repository -- that is create-product (Lane 3)."""
    if not template_file.exists():
        print(f"ERROR: template {template_file} not found", file=sys.stderr)
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    try:
        content = template_file.read_text()
        if values_file is not None:
            values = yaml.safe_load(values_file.read_text()) or {}
        else:
            values = {}
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: {ex}", file=sys.stderr)
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    def replace(m: re.Match[str]) -> str:
        key = f"{{{{{m.group(1)}}}}}"
        return str(values.get(key, key))

    rendered = TOKEN_RE.sub(replace, content)
    print(rendered, end="")  # stdout only -- never write a file
    if summary:
        _summary(e.STATUS_OK, 1, 0)
    return e.EXIT_OK


def cmd_manifest(manifest_file: Path, summary: bool) -> int:
    """--manifest mode: every entry's "file" must exist relative to the manifest (L2-T311)."""
    if not manifest_file.exists():
        print(f"ERROR: {manifest_file} not found", file=sys.stderr)
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    try:
        data = yaml.safe_load(manifest_file.read_text())
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: cannot parse {manifest_file}: {ex}", file=sys.stderr)
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    if not isinstance(data, dict):
        print(f"ERROR: {manifest_file} is not a YAML mapping", file=sys.stderr)
        if summary:
            _summary(e.STATUS_ERROR, 0, 0)
        return e.EXIT_ERROR

    templates = data.get("templates", [])
    checked = len(templates)
    failed = 0
    manifest_dir = manifest_file.parent

    for entry in templates:
        name = entry.get("file") or entry.get("template", "")
        if not (manifest_dir / name).exists():
            print(f"FAIL: manifest entry {name} does not exist at {manifest_dir / name}", file=sys.stderr)
            failed += 1

    if summary:
        if failed == 0:
            _summary(e.STATUS_OK, checked, 0)
        else:
            _summary(e.STATUS_FAIL, checked, failed)
    return e.EXIT_OK if failed == 0 else e.EXIT_FAIL


def main() -> None:
    parser = argparse.ArgumentParser(description="Template renderer and placeholder lint")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--lint", metavar="DIR", help="Lint all *.yml templates in DIR")
    group.add_argument("--render", metavar="FILE", help="Render a template to stdout")
    group.add_argument("--manifest", metavar="FILE", help="Validate MANIFEST.yaml")
    parser.add_argument("--values", metavar="YAML", help="Values file for --render mode")
    parser.add_argument("--summary", action="store_true", help="Print §0.4 summary line to stdout")
    args = parser.parse_args()

    try:
        if args.lint:
            sys.exit(cmd_lint(Path(args.lint), args.summary))
        elif args.render:
            values_path = Path(args.values) if args.values else None
            sys.exit(cmd_render(Path(args.render), values_path, args.summary))
        else:
            sys.exit(cmd_manifest(Path(args.manifest), args.summary))
    except Exception as ex:  # noqa: BLE001
        print(f"ERROR: unhandled exception: {ex}", file=sys.stderr)
        if args.summary:
            _summary(e.STATUS_ERROR, 0, 0)
        sys.exit(e.EXIT_ERROR)


if __name__ == "__main__":
    main()
