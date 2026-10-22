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
    """R-PRD-21 -- library: verification.automated == 'required'.

    STOP 1 (module docstring): Section 15.7 also requires "Registry
    version plus consumer contract tests" for library, and product.yaml
    has no field to carry that evidence. That half is intentionally NOT
    checked here -- see BLOCKER L1 L1-308 (consumer_contract_tests) and
    the strict xfail in test_r_prd_08.py that documents the gap."""
    if product_doc.get("conformance_profile") != "library":
        return []
    verification = product_doc.get("verification") or {}
    pid = _product_id(product_doc)
    if verification.get("automated") != "required":
        return [
            f"R-PRD-21 {pid}: library product declares verification.automated "
            f"'{verification.get('automated')}', not 'required'; Section 15.7"
        ]
    return []


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


def check_r_prd_23(product_doc: dict) -> list[str]:
    """R-PRD-23 -- customer-hosted: recovery non-null, shipped
    unconditionally.

    STOP 2 (module docstring): Section 15.7 also permits an
    exceptions.yaml-recorded exemption with a compensating control to
    satisfy this clause instead of a non-null recovery block.
    exceptions.yaml (Section 54.1) is a different file in a different
    repository path; that cross-file lookup is intentionally NOT
    implemented here -- see BLOCKER L1 L1-308 (exceptions.yaml routing)
    and the strict xfail in test_r_prd_08.py that documents the gap."""
    if product_doc.get("conformance_profile") != "customer-hosted":
        return []
    pid = _product_id(product_doc)
    if product_doc.get("recovery") is None:
        return [
            f"R-PRD-23 {pid}: customer-hosted product declares a null "
            f"recovery; Section 15.7"
        ]
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


def check(product_doc: dict) -> list[str]:
    """Run all eight rules in the task's own table order and return the
    combined findings."""
    findings = []
    findings.extend(check_r_prd_08(product_doc))
    findings.extend(check_r_prd_20(product_doc))
    findings.extend(check_r_prd_21(product_doc))
    findings.extend(check_r_prd_22(product_doc))
    findings.extend(check_r_prd_23(product_doc))
    findings.extend(check_r_prd_24(product_doc))
    findings.extend(check_r_prd_25(product_doc))
    findings.extend(check_r_prd_26(product_doc))
    return findings
