"""L3-P4-01: the `provision` CLI (spec §12.6; §64.1; §101 invariant 79).

Four subcommands: `create-product`, `add-person`, `change-role`,
`remove-person`. Every one of them requires exactly one of `--fixture`
or `--live` (you must say which world you are planning against), and
every one of them is dry-run by default: nothing this CLI holds a
provisioning credential for is ever mutated unless the caller passes
the explicit `--apply` flag, and `--apply` is refused outright unless
`--live` is also given -- a fixture can never be "applied" to (§64.1:
"a configuration error must never grant excess authority").

Plan Building and Execution Status:
- `create-product` (L3-P4-07): real 13-automated/2-manual step plan building (spec §19.1)
  and real apply-execution wired to `tools.provision.executors` and `GitHubClient`.
  Under `--live --apply`, requires explicit `--org`, uses the permanent `declared/`
  directory as data source, and executes GitHub API mutations via `RealGitHubClient`.
  Incompatible with `--roster-source live` under `--apply`.
- `add-person` (L3-P4-09), `change-role` (L3-P7-01), `remove-person` (L3-P7-02):
  real plan builders that enumerate their respective operations' steps. Under
  `--live --apply`, these operations are explicitly refused with an early error
  (`OperationApplyNotImplemented`); apply-execution is not supported for them
  pending their respective write-step executors.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.provision.executors import GitHubClient, execute_step
from tools.provision.github_client import GitHubClientError, RealGitHubClient
from tools.provision.plan import Plan, StepKind

_COMMANDS = ("create-product", "add-person", "change-role", "remove-person")

# One line, appearing exactly once in top-level --help output, is the
# only mention of --apply outside each subcommand's own argument (the
# subcommands share identical --apply semantics, so it is documented
# once at the top rather than duplicated four times in --help text).
_EPILOG = (
    "Every subcommand is dry-run unless given --apply, which also requires --live: "
    "a fixture can never be applied to."
)


def _add_common_args(sub: argparse.ArgumentParser) -> None:
    source = sub.add_mutually_exclusive_group(required=True)
    source.add_argument("--fixture", default=None, help="plan against this fixture under reconciler/fixtures/")
    source.add_argument("--live", action="store_true", help="plan against the real organisation")
    sub.add_argument("--org", default=None, help="organisation name (only meaningful with --live)")
    sub.add_argument(
        "--apply",
        action="store_true",
        help="perform real writes instead of a dry run (requires --live)",
    )
    sub.add_argument("--dry-run", action="store_true", help="explicit no-op: this is already the default")
    sub.add_argument("--summary", action="store_true", help="print the PLAN summary line")
    sub.add_argument("--steps", action="store_true", help="print each planned step in the plan")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.provision.cli",
        description="Lane 3 provisioning: create-product, add-person, change-role, remove-person.",
        epilog=_EPILOG,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create-product", help="scaffold a new product: repo, Team, CODEOWNERS, protection")
    _add_common_args(p_create)
    p_create.add_argument("--product", required=True, help="the product id to create")
    p_create.add_argument(
        "--roster-source",
        choices=("fixture", "live"),
        default=None,
        help="roster source for steps 11-13: 'fixture' (default with --fixture) or 'live' (reads docs/onboarding/products; dry-run only, incompatible with --apply)",
    )
    p_create.add_argument("--executor", default=None, help="the acting devops identity (§19.1)")
    p_create.set_defaults(func=_cmd_create_product)

    p_add = sub.add_parser("add-person", help="onboard a person onto the organisation and any assignments")
    _add_common_args(p_add)
    p_add.add_argument("--login", required=True, help="the GitHub login being added")
    p_add.set_defaults(func=_cmd_add_person)

    p_change = sub.add_parser("change-role", help="move a person to a new role")
    _add_common_args(p_change)
    p_change.add_argument("--login", required=True, help="the GitHub login whose role is changing")
    p_change.add_argument("--to-role", required=True, help="the role the person is moving to")
    p_change.set_defaults(func=_cmd_change_role)

    p_remove = sub.add_parser("remove-person", help="offboard a person: revoke access and reassign ownership")
    _add_common_args(p_remove)
    p_remove.add_argument("--login", required=True, help="the GitHub login being removed")
    p_remove.set_defaults(func=_cmd_remove_person)

    return parser


class ApplyRequiresLive(RuntimeError):
    """--apply was given without --live: refused (§64.1)."""


class LiveRosterApplyForbidden(RuntimeError):
    """--apply was given with --roster-source live: refused (live roster planning is dry-run only)."""


class OrgRequiredForApply(ValueError):
    """--org was omitted when running with --live --apply: refused."""


class OperationApplyNotImplemented(RuntimeError):
    """--apply was requested on an operation without write-step executors."""


def _check_apply_requires_live(args: argparse.Namespace) -> None:
    if args.apply and not args.live:
        raise ApplyRequiresLive(
            "--apply cannot be used with --fixture: a fixture is not something you can "
            "mutate. --apply requires --live."
        )


def _check_operation_apply_allowed(operation: str, args: argparse.Namespace) -> None:
    if args.apply and args.live and operation != "create-product":
        raise OperationApplyNotImplemented(
            f"--live --apply is not supported for {operation}: "
            f"apply-execution is currently implemented only for create-product."
        )


def _fixture_root(args: argparse.Namespace) -> Path | None:
    if args.fixture is None:
        return None
    root = Path(__file__).resolve().parent.parent.parent / "reconciler" / "fixtures" / args.fixture
    if not root.is_dir():
        raise FileNotFoundError(f"no such fixture: {args.fixture!r} (looked under {root})")
    return root


def _run_operation(
    args: argparse.Namespace,
    operation: str,
    plan: Plan,
    client: GitHubClient | None = None,
    declared_dir: Path | None = None,
) -> int:
    """Common dry-run/apply plumbing shared by every subcommand.

    Every subcommand's *steps* differ; the apply/dry-run contract does
    not. This is the one place that decides whether a write step is
    allowed to actually run, and it is the one place `applied` is ever
    set True.
    """
    _check_apply_requires_live(args)
    applied = bool(args.apply and args.live)

    if applied and operation != "create-product":
        raise OperationApplyNotImplemented(
            f"--live --apply is not supported for {operation}: "
            f"apply-execution is currently implemented only for create-product."
        )

    if applied:
        org = getattr(args, "org", None)
        if not org or not org.strip():
            raise OrgRequiredForApply(
                "--org must be explicitly specified when running with --live --apply: "
                "refusing to default to a production organisation."
            )

    succeeded_steps: list[tuple[Any, dict[str, Any]]] = []
    failed_step: tuple[Any, Exception] | None = None

    if applied and plan.steps:
        # Resolve target declared root for local writes
        if declared_dir is None:
            declared_dir = Path(__file__).resolve().parent.parent.parent

        # Resolve GitHub client for live GitHub API mutations
        if client is None:
            client = RealGitHubClient(org=org.strip())

        product = getattr(args, "product", "")
        executor_identity = getattr(args, "executor", None)

        for step in plan.steps:
            try:
                res = execute_step(
                    step_id=step.id,
                    product=product,
                    fixture_dir=declared_dir,
                    client=client,
                    executor=executor_identity,
                )
                succeeded_steps.append((step, res))
            except Exception as exc:
                failed_step = (step, exc)
                break

    actual_writes = len(succeeded_steps) if applied else 0

    if failed_step is not None:
        failed_s, exc = failed_step
        print(f"FAILED during {operation} at step {failed_s.id}: {exc}", file=sys.stderr)
        if succeeded_steps:
            print(f"Steps succeeded before failure ({len(succeeded_steps)}/{len(plan.steps)}):", file=sys.stderr)
            for s, _ in succeeded_steps:
                print(f"  - [{s.kind.value}] {s.id}: OK", file=sys.stderr)
        summary = (
            plan.summary_line(operation, applied=True, writes=actual_writes)
            if hasattr(plan, "summary_line")
            else f"PLAN {operation} steps={len(plan.steps)} writes={actual_writes} manual={plan.count(StepKind.MANUAL)}"
        )
        print(f"{summary} (EXECUTION FAILED)", file=sys.stderr)
        return 1

    if hasattr(plan, "summary_line"):
        print(plan.summary_line(operation, applied=applied, writes=actual_writes))
    else:
        writes_str = actual_writes if applied else 0
        print(f"PLAN {operation} steps={len(plan.steps)} writes={writes_str} manual={plan.count(StepKind.MANUAL)}")

    if getattr(args, "steps", False):
        for idx, step in enumerate(plan.steps, start=1):
            print(f"  {idx:2d}. [{step.kind.value}] {step.id}: {step.description}")
        manual_steps = getattr(plan, "manual_steps", ())
        if manual_steps:
            for idx, step in enumerate(manual_steps, start=len(plan.steps) + 1):
                print(f"  {idx:2d}. [{step.kind.value}] {step.id}: {step.description}")

    if applied and getattr(plan, "manual_steps", ()):
        print("Action items (tracked manual steps):")
        for idx, step in enumerate(plan.manual_steps, start=1):
            print(f"  {idx}. [manual] {step.id}: {step.description}")

    if not applied:
        print(f"NOTE: dry-run (default) for {operation} -- pass --apply and --live to perform writes")

    return 0


def _cmd_create_product(
    args: argparse.Namespace,
    client: GitHubClient | None = None,
    declared_dir: Path | None = None,
) -> int:
    _fixture_root(args)

    # Incompatible: --roster-source live is dry-run only and cannot be applied
    if getattr(args, "roster_source", None) == "live" and args.apply:
        raise LiveRosterApplyForbidden(
            "--apply cannot be used with --roster-source live: live roster planning is dry-run only."
        )

    executor = getattr(args, "executor", None)
    if executor:
        from tools.provision.executors import record_executor
        record_executor(args.product, executor)

    # When --live --apply is passed (without --roster-source live),
    # build the real 13-step plan using the permanent declared/ directory.
    if args.live and args.apply:
        from tools.provision.create_product import build_create_product_plan_against_declared

        plan = build_create_product_plan_against_declared(args.product, declared_dir)
    elif getattr(args, "roster_source", None) == "live":
        if args.fixture is not None:
            raise ValueError(
                "--roster-source live cannot be used with --fixture: live roster planning requires --live."
            )
        from tools.provision.create_product import build_create_product_plan_against_live_roster

        plan = build_create_product_plan_against_live_roster(args.product)
    elif args.fixture is not None:
        from tools.provision.create_product import build_create_product_plan

        plan = build_create_product_plan(args.product, args.fixture)
    else:
        plan = Plan()

    return _run_operation(
        args,
        "create-product",
        plan,
        client=client,
        declared_dir=declared_dir,
    )


def _cmd_add_person(args: argparse.Namespace) -> int:
    _fixture_root(args)
    _check_operation_apply_allowed("add-person", args)
    # L3-P4-09: the real seven-step plan (spec 12.6, 12.1).
    from tools.provision.add_person import build_add_person_plan

    return _run_operation(args, "add-person", build_add_person_plan(args.login))


def _cmd_change_role(args: argparse.Namespace) -> int:
    _fixture_root(args)
    _check_operation_apply_allowed("change-role", args)
    # L3-P7-01: the real seven-step plan (spec 12.6).
    from tools.provision.change_role import build_change_role_plan

    return _run_operation(args, "change-role", build_change_role_plan(args.login, args.to_role))


def _cmd_remove_person(args: argparse.Namespace) -> int:
    _fixture_root(args)
    _check_operation_apply_allowed("remove-person", args)
    # L3-P7-02: the real eleven-step plan (spec 12.2, 12.6).
    from tools.provision.remove_person import build_remove_person_plan

    return _run_operation(args, "remove-person", build_remove_person_plan(args.login))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (
        ApplyRequiresLive,
        LiveRosterApplyForbidden,
        OrgRequiredForApply,
        OperationApplyNotImplemented,
        FileNotFoundError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
