"""
tools.evidence.verify_digest_chain
L2-T550: Estate-wide verify-digest-chain sweep (§46.1 L4090-4131)

For every product in the estate, verifies the evidence chain closes.
An empty estate is ERROR, not clean.
Gates resumption of production deploys.

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
import argparse
import sys
import os
import glob

try:
    import yaml
    from tools.evidence import evidence_chain as ec_module
except ImportError:
    print("ERROR verify_digest_chain checked=0 failed=0")
    sys.exit(3)

TOOL_ID = "verify_digest_chain"


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def sweep(estate_dir: str) -> tuple[int, int]:
    """
    Returns (checked, failed).
    Raises SystemExit(3) on empty estate or fatal error.
    """
    if not os.path.isdir(estate_dir):
        print(f"ERROR: estate directory not found: {estate_dir}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    # Discover all product deployment records in the estate
    product_files = sorted(glob.glob(os.path.join(estate_dir, "*.yaml")))
    if not product_files:
        print(
            "ERROR: estate directory contains no product records — "
            "an empty estate is not a clean estate (§46.1)",
            file=sys.stderr,
        )
        _summary("ERROR", 0, 0)
        sys.exit(3)

    checked = len(product_files)
    failed = 0

    for product_file in product_files:
        product_name = os.path.basename(product_file).replace(".yaml", "")
        try:
            with open(product_file, "r", encoding="utf-8") as fh:
                record = yaml.safe_load(fh)
        except Exception as exc:  # noqa: BLE001
            print(
                f"ERROR: cannot parse product record '{product_name}': {exc}",
                file=sys.stderr,
            )
            failed += 1
            continue

        if not isinstance(record, dict):
            print(
                f"FAIL: product '{product_name}' record is not a YAML mapping",
                file=sys.stderr,
            )
            failed += 1
            continue

        # Run evidence_chain check for this product
        failure_count = ec_module.check(record)
        if failure_count > 0:
            print(
                f"FAIL: product '{product_name}' chain does not close "
                f"({failure_count} unanswered question(s))",
                file=sys.stderr,
            )
            failed += 1
        else:
            print(f"OK: product '{product_name}' chain is closed", file=sys.stderr)

    return checked, failed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--estate", required=True, help="Directory of product deployment records")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    checked, failed = sweep(args.estate)

    if failed == 0:
        _summary("OK", checked, 0)
        sys.exit(0)
    else:
        _summary("FAIL", checked, failed)
        sys.exit(2)


if __name__ == "__main__":
    main()
