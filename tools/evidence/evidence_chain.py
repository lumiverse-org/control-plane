"""
tools.evidence.evidence_chain
L2-T519: Evidence chain — the eleven questions (§32 L2803-2828)

Answers all eleven questions for one deployment record.
Fails if any answer is empty.
Asserts item 5 == item 11 (or S18 identity substitution).

Exit codes per §0.4: 0=OK, 2=FAIL, 3=ERROR
"""
import argparse
import sys
import os

try:
    import yaml
except ImportError:
    print("ERROR evidence_chain checked=0 failed=0")
    sys.exit(3)

TOOL_ID = "evidence_chain"
CHECKED = 11

# The eleven questions of §32 in order, mapped to their deployment record fields
QUESTIONS = [
    ("q1_git_commit",        "Which git commit?"),
    ("q2_pull_request",      "Which pull request?"),
    ("q3_gate2_approver",    "Who approved at Gate 2, and in which role?"),
    ("q4_ci_run",            "Which CI run produced it?"),
    ("q5_artifact_digest",   "What is the artifact digest?"),
    ("q6_staging_deploy",    "When was it deployed to staging?"),
    ("q7_staging_passed",    "Did staging verification pass?"),
    ("q8_prod_approver",     "Who approved production?"),
    ("q9_prod_deploy",       "When was it deployed to production?"),
    ("q10_smoke_passed",     "Did post-deployment smoke pass?"),
    ("q11_live_digest",      "What digest is running right now?"),
]


def _summary(status: str, checked: int, failed: int) -> None:
    print(f"{status} {TOOL_ID} checked={checked} failed={failed}")


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def check(record: dict) -> int:
    """
    Returns number of failed (unanswered) questions plus any 5-vs-11 mismatch.
    """
    failed = 0
    answers = {}

    for field, question in QUESTIONS:
        value = record.get(field)

        # Items 10 and 11: route through profile_evidence for non-service profiles
        if field in ("q10_smoke_passed", "q11_live_digest"):
            profile = record.get("conformance_profile", "service")
            if profile != "service":
                # For non-service profiles, the field may be a profile-specific key
                profile_value = record.get(f"{field}_profile_evidence")
                if not _is_empty(profile_value):
                    answers[field] = profile_value
                    continue
                # Fall through to check the original field

        if _is_empty(value):
            print(
                f"FAIL: evidence-chain question {field} is unanswered: {question}",
                file=sys.stderr,
            )
            failed += 1
        else:
            answers[field] = value

    # §32 invariant: item 5 and item 11 must match (service profile)
    profile = record.get("conformance_profile", "service")
    if profile == "service":
        q5 = answers.get("q5_artifact_digest")
        q11 = answers.get("q11_live_digest")

        if q5 and q11:
            s18 = record.get("s18_platform_rebuild")
            if s18:
                # S18 platform-rebuild: the recorded identity stands in for the digest.
                # All three components must be present.
                required_s18 = ["pinned_commit", "lockfile_hash", "build_configuration"]
                missing = [k for k in required_s18 if not s18.get(k)]
                if missing:
                    print(
                        f"FAIL: S18 platform-rebuild claimed but missing components: {missing}",
                        file=sys.stderr,
                    )
                    failed += 1
            elif q5 != q11:
                print(
                    f"FAIL: §32 invariant violated — item 5 digest '{q5}' != item 11 live digest '{q11}'",
                    file=sys.stderr,
                )
                failed += 1

    return failed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment", required=True)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.deployment):
        print(f"ERROR: deployment record not found: {args.deployment}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    try:
        with open(args.deployment, "r", encoding="utf-8") as fh:
            record = yaml.safe_load(fh)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: cannot parse deployment record: {exc}", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    if not isinstance(record, dict):
        print("ERROR: deployment record is not a YAML mapping", file=sys.stderr)
        _summary("ERROR", 0, 0)
        sys.exit(3)

    failed = check(record)

    if failed == 0:
        _summary("OK", CHECKED, 0)
        sys.exit(0)
    else:
        _summary("FAIL", CHECKED, failed)
        sys.exit(2)


if __name__ == "__main__":
    main()
