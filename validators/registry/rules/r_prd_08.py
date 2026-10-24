"""R-PRD-08, R-PRD-20..R-PRD-26 -- the seven conformance-profile
equivalent-evidence rules of Section 15.7, plus the profile-independent
staged-rollout ladder rule R-PRD-26 (Section 28.2).

Section 15.5: "A contract whose declarations do not satisfy the
equivalent-evidence requirements of its declared conformance_profile."
Section 15.7: "a client-app product is not failed for lacking a health
endpoint, and a service product cannot escape availability evidence by
mis-declaring its profile." (task L1-308)

Standalone, directly-tested rule functions -- see the module docstring
of ``r_svc_01.py`` for why these are not wired into the frozen Option B
(FD-094) ``R01``..``R18`` dispatch table in
``validators/registry/rules/registry.py``. The CLI grammar and
per-fixture ``echo "AT009_EXIT=$?"``/``echo "MISDECLARE_EXIT=$?"``
acceptance commands written into ``lanes/L1-05-tasks.md`` predate FD-094
and are superseded by it, exactly as ``validators/registry/tests/
test_r_prd_05.py`` and ``test_r_prd_11.py`` document: fixtures still
live where the task says (``validators/registry/fixtures/product/
conformance/<case>/``), but they are exercised by calling these
functions directly against a parsed ``product.yaml`` document, not
through ``validators/registry/cli.py``.

Rule table (task L1-308, Section 15.7):

    R-PRD-08  service           observability.health_endpoint and
                                 version_endpoint both non-null;
                                 recovery non-null.
    R-PRD-20  client-app        deployment.progressive_delivery ==
                                 'staged-rollout'; staged_rollout
                                 non-null; rollback_method non-null
                                 (Section 42.3: the staged-rollout halt
                                 *is* the rollback method); staged_rollout
                                 .crash_free_sessions present.
    R-PRD-21  library           verification.automated == 'required'.
                                 (The "Registry version plus consumer
                                 contract tests" half of this row is
                                 NOT checked -- see STOP 1 below.)
    R-PRD-22  batch             observability.metrics non-null.
                                 health_endpoint may be null.
    R-PRD-23  customer-hosted   recovery non-null.
                                 (The exceptions.yaml exemption half of
                                 this row is NOT checked -- see STOP 2.)
    R-PRD-24  white-label       environments.production non-null.
    R-PRD-25  static-site       recovery may be null;
                                 deployment.artifact_type non-null
                                 (already schema-guaranteed -- see the
                                 function docstring; this rule never
                                 actually fires).
    R-PRD-26  (any profile)     deployment.staged_rollout.stages_pct,
                                 when staged_rollout is non-null, must be
                                 strictly increasing and end at 100
                                 (Section 28.2's ordered ladder).

STOP 1 (unconditional, per lanes/L1-05-tasks.md:1870): Section 15.7
requires "Registry version plus consumer contract tests" for `library`,
and Section 20.1's service.yaml has a verification.consumer_contract_tests
field, but Section 15.1's product.yaml has no such field. Do NOT add one
to product.yaml here. File the blocker
`BLOCKER L1 L1-308: the library conformance profile needs
consumer_contract_tests evidence that product.yaml has no field for`
with the two candidate resolutions named and not chosen: (a) add the
field to the v2 product schema (a Section 60.2 schema change), or (b)
require a library product to also carry a service.yaml. R-PRD-21 ships
checking only verification.automated == 'required'; the consumer-contract
clause is proven missing by a strict xfail in test_r_prd_08.py.

STOP 2 (unconditional, per lanes/L1-05-tasks.md:1871): Section 15.7
permits customer-hosted to satisfy recovery by "a recorded exemption with
a compensating control", which is an exceptions.yaml entry (Section
54.1) -- a different file in a different repository path. R-PRD-23 ships
requiring recovery non-null unconditionally; the exceptions.yaml path is
proven missing by a strict xfail in test_r_prd_08.py. File the blocker
`BLOCKER L1 L1-308: customer-hosted recovery exemption requires
cross-file resolution into exceptions.yaml` for L0 to route.

Both blockers are filed AFTER a normal, passing GIT POSTAMBLE (SIZE: L
task ships with these two gaps declared, it does not stop on them --
see lanes/L1-05-tasks.md:1897, "append eight R-PRD- rows to RULES.md,
then file both blockers above", which comes after a passing SELF-VERIFY,
not instead of one).
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
import yaml

RULE_ID_SERVICE = "R-PRD-08"
RULE_ID_CLIENT_APP = "R-PRD-20"
RULE_ID_LIBRARY = "R-PRD-21"
RULE_ID_BATCH = "R-PRD-22"
RULE_ID_CUSTOMER_HOSTED = "R-PRD-23"
RULE_ID_WHITE_LABEL = "R-PRD-24"
RULE_ID_STATIC_SITE = "R-PRD-25"
RULE_ID_STAGED_ROLLOUT_LADDER = "R-PRD-26"
SPEC = "Section 15.7; Section 15.5; Section 42.3; Section 28.2; AT-009"
APPLIES_TO = ["product"]


def _product_id(product_doc: dict) -> str:
    return (product_doc.get("identity") or {}).get("id", "<unknown-product>")


def check_r_prd_08(product_doc: dict) -> list[str]:
    """R-PRD-08 -- service: observability.health_endpoint and
    version_endpoint both non-null; recovery non-null."""
    if product_doc.get("conformance_profile") != "service":
        return []
    obs = product_doc.get("observability") or {}
    pid = _product_id(product_doc)
    findings = []
    if obs.get("health_endpoint") is None:
        findings.append(
            f"R-PRD-08 {pid}: service product declares a null "
            f"observability.health_endpoint; Section 15.7 requires the "
            f"service interface"
        )
    if obs.get("version_endpoint") is None:
        findings.append(
            f"R-PRD-08 {pid}: service product declares a null "
            f"observability.version_endpoint; Section 15.7 requires the "
            f"service interface"
        )
    if product_doc.get("recovery") is None:
        findings.append(
            f"R-PRD-08 {pid}: service product declares a null recovery; "
            f"Section 15.7 requires the service interface"
        )
    return findings


def check_r_prd_20(product_doc: dict) -> list[str]:
    """R-PRD-20 -- client-app: progressive_delivery == 'staged-rollout';
    staged_rollout non-null; rollback_method non-null; staged_rollout
    .crash_free_sessions present (schema-guaranteed whenever
    staged_rollout is non-null -- kept for the invariant register, the
    same precedent as R-PRD-19 in r_prd_07.py)."""
    if product_doc.get("conformance_profile") != "client-app":
        return []
    deployment = product_doc.get("deployment") or {}
    pid = _product_id(product_doc)
    findings = []
    if deployment.get("progressive_delivery") != "staged-rollout":
        findings.append(
            f"R-PRD-20 {pid}: client-app product declares "
            f"deployment.progressive_delivery "
            f"'{deployment.get('progressive_delivery')}', not "
            f"'staged-rollout'; Section 15.7"
        )
    staged = deployment.get("staged_rollout")
    if staged is None:
        findings.append(
            f"R-PRD-20 {pid}: client-app product's deployment.staged_rollout "
            f"is null; Section 15.7"
        )
    if deployment.get("rollback_method") is None:
        findings.append(
            f"R-PRD-20 {pid}: client-app product declares a null "
            f"deployment.rollback_method; Section 42.3 -- the "
            f"staged-rollout halt is the rollback method"
        )
    if staged is not None and staged.get("crash_free_sessions") is None:
        findings.append(
            f"R-PRD-20 {pid}: client-app product's deployment.staged_rollout "
            f"has no crash_free_sessions; Section 15.7"
        )
    return findings


def check_r_prd_21(product_doc: dict) -> list[str]:
    """R-PRD-21 -- library: verification.automated == 'required' AND
    verification.consumer_contract_tests == 'required' (Section 15.7; CCR-004 resolved).
    """
    if product_doc.get("conformance_profile") != "library":
        return []
    verification = product_doc.get("verification") or {}
    pid = _product_id(product_doc)
    findings = []
    if verification.get("automated") != "required":
        findings.append(
            f"R-PRD-21 {pid}: library product declares verification.automated "
            f"'{verification.get('automated')}', not 'required'; Section 15.7"
        )
    if verification.get("consumer_contract_tests") != "required":
        findings.append(
            f"R-PRD-21 {pid}: library product declares verification.consumer_contract_tests "
            f"'{verification.get('consumer_contract_tests')}', not 'required'; Section 15.7"
        )
    return findings


def check_r_prd_22(product_doc: dict) -> list[str]:
    """R-PRD-22 -- batch: observability.metrics non-null.
    health_endpoint may be null -- not checked either way."""
    if product_doc.get("conformance_profile") != "batch":
        return []
    obs = product_doc.get("observability") or {}
    pid = _product_id(product_doc)
    if obs.get("metrics") is None:
        return [
            f"R-PRD-22 {pid}: batch product declares a null "
            f"observability.metrics; Section 15.7"
        ]
    return []


def _load_exceptions_registry() -> dict | None:
    for candidate in [
        Path("registries/exceptions.yaml"),
        Path("exceptions.yaml"),
        Path(__file__).resolve().parents[4] / "registries" / "exceptions.yaml",
    ]:
        if candidate.exists() and candidate.is_file():
            try:
                return yaml.safe_load(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass
    return None


def resolve_recovery_exemption(
    product_doc: dict,
    exceptions_doc: dict | None = None,
    as_of: str | date | None = None,
) -> tuple[bool, str | None]:
    """Cross-file resolver connecting product.yaml's recovery value to
    exceptions.yaml exemption records (Section 15.7, Section 54.1; CCR-004 resolved).

    Verification logic against Section 54.1 / exceptions.registry.v1 schema:
    1. Exemption lookup: Matches exemption by target ID (if product.yaml recovery
       declares an EXC-YYYY-NNN string) or by product membership in affected.products.
    2. Closure check: Verifies the exemption is open (`closure` is None).
       A non-null closure indicates a terminated exemption (e.g. expired, remediated).
    3. Compensating control check: Verifies `compensating_control` is declared,
       non-empty, and not 'none' (Section 15.7 mandatory requirement).
    4. Expiry check: Verifies `expiry` is declared and (if as_of is provided)
       has not elapsed past as_of (Section 54.2, Invariant 77).
    5. Product scope check: Verifies that if `affected.products` is populated,
       it includes the subject product's ID (Section 54.1).
    """
    pid = _product_id(product_doc)
    recovery = product_doc.get("recovery")

    # If recovery is a non-null object, local recovery declarations are satisfied
    if isinstance(recovery, dict):
        return True, None


    target_exemption_id = recovery.strip() if isinstance(recovery, str) else None

    if exceptions_doc is None:
        exceptions_doc = _load_exceptions_registry()

    if not exceptions_doc or not isinstance(exceptions_doc, dict):
        if target_exemption_id:
            return (
                False,
                f"R-PRD-23 {pid}: customer-hosted product references exemption '{target_exemption_id}', "
                f"but exceptions.yaml was not found; Section 15.7"
            )
        return (
            False,
            f"R-PRD-23 {pid}: customer-hosted product declares a null recovery "
            f"and exceptions.yaml was not found; Section 15.7"
        )

    matching_exc = None
    for exc in exceptions_doc.get("exceptions", []) or []:
        if not isinstance(exc, dict):
            continue
        exc_id = exc.get("id")
        if target_exemption_id:
            if exc_id == target_exemption_id:
                matching_exc = exc
                break
        else:
            affected = exc.get("affected") or {}
            prods = affected.get("products") or []
            if pid in prods:
                matching_exc = exc
                break

    if matching_exc is None:
        if target_exemption_id:
            return (
                False,
                f"R-PRD-23 {pid}: customer-hosted product references exemption '{target_exemption_id}' "
                f"which does not exist in exceptions.yaml; Section 15.7"
            )
        return (
            False,
            f"R-PRD-23 {pid}: customer-hosted product declares a null recovery "
            f"with no matching exemption in exceptions.yaml; Section 15.7"
        )

    exc_id = matching_exc.get("id", "<unknown>")

    # 1. Closure check
    closure = matching_exc.get("closure")
    if closure is not None:
        return (
            False,
            f"R-PRD-23 {pid}: customer-hosted product references exemption '{exc_id}' "
            f"which is closed ({closure}); Section 15.7, Section 54.2"
        )

    # 2. Compensating control check
    comp_control = matching_exc.get("compensating_control")
    if not comp_control or (isinstance(comp_control, str) and comp_control.strip().lower() in ("none", "")):
        return (
            False,
            f"R-PRD-23 {pid}: customer-hosted product references exemption '{exc_id}' "
            f"which lacks a compensating control; Section 15.7 requires a recorded exemption with a compensating control"
        )

    # 3. Expiry check
    expiry = matching_exc.get("expiry")
    if expiry is None:
        return (
            False,
            f"R-PRD-23 {pid}: customer-hosted product references exemption '{exc_id}' "
            f"which has no expiry; Section 54.2, Invariant 77"
        )
    if as_of:
        try:
            today_date = as_of if isinstance(as_of, date) else date.fromisoformat(str(as_of))
            expiry_date = expiry if isinstance(expiry, date) else date.fromisoformat(str(expiry))
            if expiry_date < today_date:
                return (
                    False,
                    f"R-PRD-23 {pid}: customer-hosted product references exemption '{exc_id}' "
                    f"which expired on {expiry}; Section 54.2"
                )
        except (ValueError, TypeError):
            pass

    # 4. Scope verification
    affected = matching_exc.get("affected") or {}
    prods = affected.get("products") or []
    if prods and pid not in prods:
        return (
            False,
            f"R-PRD-23 {pid}: exemption '{exc_id}' affected.products does not include '{pid}'; Section 54.1"
        )

    return True, None


def check_r_prd_23(product_doc: dict, exceptions_doc: dict | None = None) -> list[str]:
    """R-PRD-23 -- customer-hosted: recovery non-null OR a valid recorded
    exemption in exceptions.yaml with a compensating control (Section 15.7; CCR-004 resolved).
    """
    if product_doc.get("conformance_profile") != "customer-hosted":
        return []
    valid, finding = resolve_recovery_exemption(product_doc, exceptions_doc=exceptions_doc)
    if not valid and finding:
        return [finding]
    return []


def check_r_prd_24(product_doc: dict) -> list[str]:
    """R-PRD-24 -- white-label: environments.production non-null."""
    if product_doc.get("conformance_profile") != "white-label":
        return []
    envs = product_doc.get("environments") or {}
    pid = _product_id(product_doc)
    if envs.get("production") is None:
        return [
            f"R-PRD-24 {pid}: white-label product declares a null "
            f"environments.production; Section 15.7"
        ]
    return []


def check_r_prd_25(product_doc: dict) -> list[str]:
    """R-PRD-25 -- static-site. Both clauses of the Section 15.7 row are
    either permissive (recovery MAY be null -- nothing to require) or
    already schema-guaranteed (deployment.artifact_type is a schema-
    required, non-null, minLength-1 string --
    schemas/product/product.contract.v2.schema.json `deployment.
    required`), so a parsed document has already satisfied it before
    this function runs. This function never produces a finding; it is
    kept as its own rule id, matching R-PRD-19's precedent in
    r_prd_07.py of shipping a schema-redundant row for the RULES.md /
    invariant register, and because the task instructs implementing
    "exactly the seven profile rows", not six."""
    if product_doc.get("conformance_profile") != "static-site":
        return []
    return []


def check_r_prd_26(product_doc: dict) -> list[str]:
    """R-PRD-26 -- deployment.staged_rollout.stages_pct, whenever
    staged_rollout is non-null (on ANY conformance_profile -- this rule
    is not gated on R-PRD-20's client-app check), must be strictly
    increasing and end at 100 (Section 28.2's ordered ladder). Reports
    at most one finding per document, matching r_prd_11.check_r_prd_11's
    do-not-double-report precedent: a non-increasing list is reported as
    such without also reporting the ending-value clause."""
    staged = (product_doc.get("deployment") or {}).get("staged_rollout")
    if staged is None:
        return []
    stages = staged.get("stages_pct") or []
    pid = _product_id(product_doc)
    if any(b <= a for a, b in zip(stages, stages[1:])):
        return [
            f"R-PRD-26 {pid}: deployment.staged_rollout.stages_pct {stages} "
            f"is not strictly increasing; Section 28.2's staged rollout is "
            f"an ordered ladder"
        ]
    if not stages or stages[-1] != 100:
        return [
            f"R-PRD-26 {pid}: deployment.staged_rollout.stages_pct {stages} "
            f"does not end at 100; Section 28.2"
        ]
    return []


def check(product_doc: dict, exceptions_doc: dict | None = None) -> list[str]:
    """Run all eight rules in the task's own table order and return the
    combined findings."""
    findings = []
    findings.extend(check_r_prd_08(product_doc))
    findings.extend(check_r_prd_20(product_doc))
    findings.extend(check_r_prd_21(product_doc))
    findings.extend(check_r_prd_22(product_doc))
    findings.extend(check_r_prd_23(product_doc, exceptions_doc=exceptions_doc))
    findings.extend(check_r_prd_24(product_doc))
    findings.extend(check_r_prd_25(product_doc))
    findings.extend(check_r_prd_26(product_doc))
    return findings
