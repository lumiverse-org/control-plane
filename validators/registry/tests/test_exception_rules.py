"""Tests for R-EXC-01..05 (L1-602, Section 54.2, invariant 77, AT-037/038/039, SIG-19).

Exercises `validators/registry/rules/r_exc_01.py` .. `r_exc_05.py` directly
against the 23 fixtures under `validators/registry/fixtures/exc_rules/**`
(8 valid + 15 invalid), rather than through `validators.registry.rules
.discover()` or the CLI's `--records-root` flag. This mirrors the
adaptation `test_exceptions_full_schema.py` already made for L1-601, for
the same reason:

FD-094 (DECIDED, `_FOUNDER_DECISIONS.md`) is the frozen interface
(`contracts/validator-contract.md`): the live rule-dispatch engine is
`validators/registry/cli.py` + `validators/registry/rules/registry.py`
("Option B", rule ids `R01`-`R18` with sub-codes, flat files
`r{nn}_{name}.py`). `validators/registry/README.md`'s ARCHITECTURE NOTE
is explicit: "Do not resurrect the module-discovery/RULE_ID/APPLIES_TO
harness described in lanes/L1-05-tasks.md task L1-005 ('Option D') --
FD-094 explicitly supersedes it." `validators/registry/rules/__init__.py`
is (correctly) empty in this repository -- there is no `discover()` to
import, and the frozen rule-id space does not admit an `R-EXC-0n` token,
so `r_exc_01.py`..`r_exc_05.py` are standalone modules in the same vein as
`r_svc_01.py`, `r_pat_01.py` and `r_tol_01.py` (all pre-existing in this
lane), each exposing its own `check_document(doc, ...)` for direct testing.

L1-602's own literal SELF-VERIFY block invokes
`python -m validators.registry.cli --records-root <fixture> --format json`
and `python -c "from validators.registry.rules import discover; ..."`.
Both were run for real against this implementation and both fail for the
reason above -- not because of anything wrong with the five rules below,
but because that CLI path and that import target do not exist in this
codebase's decided architecture. That gap (missing `R-EXC-00`/L1-108,
missing `discover()`/L1-005, both superseded or not-yet-built) is
recorded in the task's PR notes; it is not `r_exc_01`..`r_exc_05`'s FILES
to fix.

**Recorded mechanical defect, `all_five_rules_fire`:** the task's own case
table asks for "one entry violating all five rules" / "five errors". This
is not achievable: R-EXC-01 requires `closure is null` while R-EXC-02
requires `closure == 'trigger_satisfied'` -- mutually exclusive on one
entry's `closure` field. Likewise R-EXC-03 requires `type` IN the
non-discretionary set while R-EXC-02 and R-EXC-05 both require `type` NOT
IN it -- also mutually exclusive on one entry's `type` field. The maximum
number of these five rules that can co-fire on a single exception entry
is three (R-EXC-01 + R-EXC-03 + R-EXC-04, e.g. an expired, open,
no-trigger `bootstrap` exception with a broken compensating control); this
fixture and its test assert exactly that, not five. This joins the same
class of arithmetic/logic defect already logged in
`lanes/L1-98-DEEP-REVIEW.md` (M-E) for L1-601 and L1-603 in this very
cluster -- implemented faithfully against what the rules as specified can
actually produce, rather than forcing a count they cannot reach.
"""
import os

import yaml

from validators.registry.rules import r_exc_01, r_exc_02, r_exc_03, r_exc_04, r_exc_05

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "exc_rules")

_RULE_MODULES = (r_exc_01, r_exc_02, r_exc_03, r_exc_04, r_exc_05)


def _run_case(case_rel_dir):
    """Load one fixture case and run all five R-EXC-0x rules against it.

    Returns (today, sorted_rule_ids_that_fired, findings).
    """
    case_dir = os.path.join(FIXTURES_DIR, case_rel_dir)
    with open(os.path.join(case_dir, "exceptions.yaml"), encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    with open(os.path.join(case_dir, "expect.yaml"), encoding="utf-8") as f:
        expect = yaml.safe_load(f)
    today = expect["today"]
    source = os.path.join(case_dir, "exceptions.yaml")

    findings = []
    for mod in _RULE_MODULES:
        if mod is r_exc_01:
            _, doc_findings = mod.check_document(doc, today, source=source)
        else:
            _, doc_findings = mod.check_document(doc, source=source)
        findings.extend(doc_findings)

    fired = sorted(f.split(" ", 1)[0] for f in findings)
    return expect, fired, findings


def _assert_case(case_rel_dir):
    expect, fired, findings = _run_case(case_rel_dir)
    expected = sorted(expect["expect_errors"])
    assert fired == expected, (
        f"{case_rel_dir}: expected rule ids {expected}, got {fired}\n"
        + "\n".join(findings)
    )
    if expected:
        assert expect["expect_exit"] == 1
    else:
        assert expect["expect_exit"] == 0
    return findings


# ---------------------------------------------------------------------------
# Valid cases (8)
# ---------------------------------------------------------------------------


def test_valid_current_open():
    _assert_case("valid/current_open")


def test_valid_closed_expired():
    _assert_case("valid/closed_expired")


def test_valid_bootstrap_trigger_satisfied():
    _assert_case("valid/bootstrap_trigger_satisfied")


def test_valid_control_with_record_and_cadence():
    _assert_case("valid/control_with_record_and_cadence")


def test_valid_control_none_declared():
    _assert_case("valid/control_none_declared")


def test_valid_renewals_two_open():
    _assert_case("valid/renewals_two_open")


def test_valid_expires_today():
    """The boundary is strict `<`: an exception expiring today is not expired."""
    _assert_case("valid/expires_today")


def test_valid_bootstrap_renewals_three():
    _assert_case("valid/bootstrap_renewals_three")


# ---------------------------------------------------------------------------
# Invalid cases (15)
# ---------------------------------------------------------------------------


def test_expired_open():
    findings = _assert_case("expired_open")
    assert "EXC-2026-041" in findings[0]
    assert "2026-05-31" in findings[0]
    assert "Section 54.2, AT-037, SIG-19" in findings[0]


def test_expired_open_far_past():
    _assert_case("expired_open_far_past")


def test_trigger_satisfied_on_break_glass():
    _assert_case("trigger_satisfied_on_break_glass")


def test_trigger_satisfied_on_policy_waiver():
    _assert_case("trigger_satisfied_on_policy_waiver")


def test_bootstrap_no_trigger():
    _assert_case("bootstrap_no_trigger")


def test_standing_delegation_no_trigger():
    _assert_case("standing_delegation_no_trigger")


def test_control_no_record():
    _assert_case("control_no_record")


def test_control_cadence_none_with_real_control():
    _assert_case("control_cadence_none_with_real_control")


def test_renewals_three_break_glass():
    _assert_case("renewals_three_break_glass")


def test_renewals_four_temporary_access():
    _assert_case("renewals_four_temporary_access")


def test_two_offenders_one_file():
    _assert_case("two_offenders_one_file")


def test_expired_and_no_trigger():
    _assert_case("expired_and_no_trigger")


def test_control_no_record_and_expired():
    _assert_case("control_no_record_and_expired")


def test_renewals_three_and_expired():
    _assert_case("renewals_three_and_expired")


def test_all_five_rules_fire():
    """See module docstring: three rules co-fire, not five -- R-EXC-02/05
    require type outside the non-discretionary set while R-EXC-03 requires
    type inside it, and R-EXC-01 requires closure null while R-EXC-02
    requires closure 'trigger_satisfied'. Both pairs are mutually exclusive
    on one entry, so five simultaneous errors on one entry is unreachable."""
    _assert_case("all_five_rules_fire")
