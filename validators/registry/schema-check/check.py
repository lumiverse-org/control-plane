#!/usr/bin/env python3
"""L1 Phase 2 schema-check harness (Python).
Modes:
  --lint <schema.json>                     annotation lint only
  --schema <schema.json> --instance <f>    validate one instance
  --suite                                  every schema in schemas/registry/index.json against its fixtures
Exit 0 = PASS, 1 = FAIL, 2 = usage/IO error.
"""
import sys, os, json, pathlib

try:
    import jsonschema
    import yaml
except ImportError as e:
    print(f"ERROR missing dependency: {e} -- run: pip install jsonschema pyyaml")
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent


def read_json(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def read_instance(p):
    raw = pathlib.Path(p).read_text(encoding="utf-8")
    if str(p).endswith(".json"):
        return json.loads(raw)
    return yaml.safe_load(raw)


ALLOWED_ORIGINS = {"declared", "derived"}


def lint(schema_path):
    s = read_json(schema_path)
    problems = []
    if "$id" not in s:
        problems.append("root: missing $id")
    if "$schema" not in s:
        problems.append("root: missing $schema")
    if not isinstance(s.get("x-residual-rule"), list):
        problems.append("root: missing x-residual-rule array")

    def walk(node, ptr):
        if not isinstance(node, dict):
            return
        if isinstance(node.get("properties"), dict):
            for k, v in node["properties"].items():
                p = f"{ptr}/properties/{k}"
                if not isinstance(v, dict):
                    problems.append(f"{p}: not a schema object")
                    continue
                if v.get("x-origin") not in ALLOWED_ORIGINS:
                    problems.append(f'{p}: x-origin must be "declared" or "derived"')
                if v.get("x-origin") == "derived":
                    if v.get("readOnly") is not True:
                        problems.append(f"{p}: derived property must set readOnly:true")
                    xdf = v.get("x-derived-from", "")
                    if not isinstance(xdf, str) or len(xdf) < 10:
                        problems.append(
                            f"{p}: derived property must carry x-derived-from citing the spec section"
                        )
        for v in node.values():
            walk(v, ptr)

    walk(s, "#")
    if problems:
        for p in problems:
            print(f"LINT-FAIL {p}")
        return False
    rel = pathlib.Path(schema_path).relative_to(ROOT)
    print(f"LINT-OK {rel}")
    return True


def _make_validator(schema_path):
    s = read_json(schema_path)
    common_path = (
        ROOT / "schemas" / "registry" / "_common" / "v1" / "common.schema.json"
    )
    store = {}
    if common_path.exists():
        cs = read_json(common_path)
        store[cs["$id"]] = cs
    resolver = jsonschema.RefResolver.from_schema(s, store=store)
    return jsonschema.Draft202012Validator(s, resolver=resolver)


def validate_one(schema_path, instance_path):
    try:
        validator = _make_validator(schema_path)
        instance = read_instance(instance_path)
        errors = list(validator.iter_errors(instance))
        for e in errors:
            print(f"ERR {e.json_path or '/'} {e.message}")
        return len(errors) == 0
    except Exception as e:
        print(f"ERROR {e}")
        return False


def suite():
    idx_path = ROOT / "schemas" / "registry" / "index.json"
    if not idx_path.exists():
        print("SUITE-FAIL missing schemas/registry/index.json")
        return False
    idx = read_json(idx_path)
    ok = True
    checked = 0
    for entry in idx["schemas"]:
        schema_path = ROOT / entry["schema"]
        if not schema_path.exists():
            print(f'SUITE-FAIL missing {entry["schema"]}')
            ok = False
            continue
        if not lint(schema_path):
            ok = False
        fixture_dir = schema_path.parent / "fixtures"
        if not fixture_dir.exists():
            print(f'SUITE-FAIL missing fixtures for {entry["schema"]}')
            ok = False
            continue
        files = sorted(f.name for f in fixture_dir.iterdir() if f.suffix == ".yaml")
        if not any(f.startswith("valid") for f in files) or not any(
            f.startswith("invalid-") for f in files
        ):
            print(
                f'SUITE-FAIL {entry["schema"]} needs >=1 valid*.yaml and >=1 invalid-*.yaml'
            )
            ok = False
        for f in files:
            expect_valid = f.startswith("valid")
            got = validate_one(schema_path, fixture_dir / f)
            checked += 1
            if got != expect_valid:
                label = "PASS" if expect_valid else "FAIL"
                print(f'SUITE-FAIL {entry["schema"]} :: {f} expected {label}')
                ok = False
    print(f"SUITE-CHECKED {checked}")
    print("SUITE-OK" if ok else "SUITE-FAIL")
    return ok


def _arg_of(args, name):
    try:
        i = args.index(name)
        return args[i + 1]
    except (ValueError, IndexError):
        return None


def main():
    args = sys.argv[1:]
    try:
        if "--suite" in args:
            sys.exit(0 if suite() else 1)
        if "--lint" in args:
            sys.exit(0 if lint(os.path.abspath(_arg_of(args, "--lint"))) else 1)
        s = _arg_of(args, "--schema")
        i = _arg_of(args, "--instance")
        if not s or not i:
            print(
                "USAGE: check.py [--suite | --lint <schema> | --schema <schema> --instance <file>]"
            )
            sys.exit(2)
        ok = validate_one(os.path.abspath(s), os.path.abspath(i))
        print("VALID" if ok else "INVALID")
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"ERROR {e}")
        sys.exit(2)


main()
