"""
L2-T544  Records-write client
§97.2 L8843-8926 — the deployment-record and event writes are required,
failing steps of deploy-production.yml rather than trailing best-effort ones.
§40.1 L3644-3686 — records-writer credential obtained through declared path.
§101 invariant 48 — records are never edited in place.

Lane 2 owns the call; Lane 4 owns the schema, the store, and the writer
semantics (PARTITION.md line 20). This module is a client, not a second writer.

No literal credential appears in this module. Credential obtained through
the path declared under D-L2-03 in contracts/workflow-io/records-writer.yaml.

Exit codes:
  0  OK    checked=<field count> failed=0
  2  FAIL  checked=<field count> failed=<n>
  3  ERROR checked=0 failed=0
"""
from __future__ import annotations
import argparse, hashlib, os, sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

try:
    from tools.evidence import STATUS_OK, STATUS_FAIL, STATUS_ERROR, EXIT_OK, EXIT_FAIL, EXIT_ERROR
except ImportError:
    STATUS_OK, STATUS_FAIL, STATUS_ERROR = "OK", "FAIL", "ERROR"
    EXIT_OK, EXIT_FAIL, EXIT_ERROR = 0, 2, 3

TOOL_ID = "records_client"

# Required fields for a deployment record (§97.2 / Lane 4 schema)
REQUIRED_FIELDS: dict[str, list[str]] = {
    "deployment": [
        "digest",
        "artifact_name",
        "deployed_by",
        "deployed_at",
        "environment",
        "git_commit",
        "pull_request",
        "approved_by",
        "run_id",
    ],
}


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _load_payload(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"payload not found: {path}")
    if yaml is None:
        raise ImportError("pyyaml is required")
    with open(p) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError("payload must be a YAML mapping")
    return data


def _get_credential_path() -> str:
    """Obtain credential path from declared interface — never a literal token."""
    # The secret name and target repository are declared under D-L2-03.
    # In a workflow context this is ${{ secrets.RECORDS_WRITER_TOKEN }}.
    # Here we resolve from the contracts declaration.
    contracts_path = Path("contracts/workflow-io/records-writer.yaml")
    if not contracts_path.exists():
        raise FileNotFoundError(
            "D-L2-03 contract absent: contracts/workflow-io/records-writer.yaml"
        )
    if yaml is None:
        raise ImportError("pyyaml is required")
    with open(contracts_path) as fh:
        decl = yaml.safe_load(fh)
    secret_name = decl.get("secret_name")
    if not secret_name:
        raise ValueError("records-writer contract missing secret_name field")
    return secret_name


def validate_payload(kind: str, payload: dict) -> tuple[int, int]:
    """Return (checked, failed)."""
    required = REQUIRED_FIELDS.get(kind, [])
    checked = len(required)
    failed = sum(1 for f in required if not payload.get(f))
    for f in required:
        if not payload.get(f):
            print(f"FAIL: required field {f!r} missing or empty in {kind} record", file=sys.stderr)
    return checked, failed


def _record_path(kind: str, payload: dict) -> Path:
    """Derive deterministic write path from payload fields."""
    env = payload.get("environment", "unknown")
    ts = payload.get("deployed_at", "unknown").replace(":", "-").replace("T", "_")
    digest_suffix = hashlib.sha256(str(payload).encode()).hexdigest()[:8]
    return Path(f"records/{kind}s/{env}/{ts}-{digest_suffix}.yaml")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Records-write client (Lane 2 call, Lane 4 schema).")
    ap.add_argument("--kind", required=True, choices=list(REQUIRED_FIELDS), help="Record kind")
    ap.add_argument("--payload", required=True, help="Path to payload YAML")
    ap.add_argument("--dry-run", action="store_true", help="Validate and print without writing")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)

    try:
        payload = _load_payload(args.payload)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    checked, failed = validate_payload(args.kind, payload)

    if failed > 0:
        if args.summary:
            _summary(STATUS_FAIL, checked, failed)
        sys.exit(EXIT_FAIL)

    if args.dry_run:
        print(f"DRY-RUN: payload valid; would write to {_record_path(args.kind, payload)}",
              file=sys.stderr)
        if args.summary:
            _summary(STATUS_OK, checked, failed)
        sys.exit(EXIT_OK)

    # Live write path: obtain credential, refuse to overwrite existing file
    record_path = _record_path(args.kind, payload)
    if record_path.exists():
        print(
            f"FAIL: record already exists at {record_path} — §101 invariant 48 prohibits overwrite",
            file=sys.stderr,
        )
        if args.summary:
            _summary(STATUS_FAIL, checked, 1)
        sys.exit(EXIT_FAIL)

    try:
        secret_name = _get_credential_path()
    except Exception as exc:
        print(f"ERROR: cannot resolve records-writer credential: {exc}", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    # In a real run the secret value is passed via the environment by the workflow,
    # never inlined here. Token: ${{ secrets.<secret_name> }} in the caller.
    token = os.environ.get(secret_name)
    if not token:
        print(f"ERROR: secret {secret_name!r} not set in environment", file=sys.stderr)
        if args.summary:
            _summary(STATUS_ERROR, 0, 0)
        sys.exit(EXIT_ERROR)

    record_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:
        raise ImportError("pyyaml is required")
    with open(record_path, "w") as fh:
        yaml.safe_dump(payload, fh, default_flow_style=False)

    print(f"OK: record written to {record_path}", file=sys.stderr)
    if args.summary:
        _summary(STATUS_OK, checked, failed)
    sys.exit(EXIT_OK)


if __name__ == "__main__":
    main()
