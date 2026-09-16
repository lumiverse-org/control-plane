"""Tests for R-FRM-01, R-FRM-02, R-FRM-03 (L1-802, Section 77.1 / 77.4,
AT-077, AT-078, SIG-23).

Exercised by calling ``validators.registry.rules.r_frm_01`` /
``r_frm_02`` / ``r_frm_03`` directly against parsed
``framework*.yaml`` / ``roles.yaml`` fixture groups, rather than through
``validators/registry/cli.py`` or a ``discover()`` harness -- see the
module docstrings of ``r_frm_01.py`` / ``r_frm_02.py`` / ``r_frm_03.py``
and, for precedent, ``test_service_schema.py``'s note that FD-094
(DECIDED) supersedes the L1-005 ``discover()``/``RULE_ID``/``APPLIES_TO``
harness and the CLI "OK: N file(s) validated" / "ERROR <rule>" grammar
in favour of Option B (``validators/registry/cli.py``, R01-R18). Those
two pieces of infrastructure (``validators/registry/rules/__init__.py``'s
``discover()``, and the frozen-grammar ``cli.py``/``report.py``) are not
present on ``origin/integration`` at all -- L1-005 and L1-003 as written
in ``lanes/L1-05-tasks.md`` were never built, superseded by FD-094 before
they were. This task's three rule modules (r_frm_01/02/03.py) are
standalone functions, not wired into the R01-R18 dispatch table -- see
their module docstrings for why extending that frozen catalogue is out of
scope here.

Fixtures live at ``validators/registry/fixtures/frm/<case>/``, each a
directory holding one or more ``framework*.yaml`` documents (glob-sorted;
multi-document cases exercise R-FRM-01/R-FRM-02's cross-file logic),
an optional ``roles.yaml`` (schema: ``roles.registry.v1.schema.json`` --
fixture-local data, not a copy of any live ``registries/`` file, since
no ``registries/roles.yaml`` of that shape exists yet on integration),
and an ``expect.yaml`` recording the case's ``today``/``expect_exit``/
``expect_errors`` for the human record even though this task's tests
assert directly in Python rather than through a generic expect.yaml-
driven harness (also superseded by FD-094, same reasoning as above).

16 test functions: 6 valid, 10 invalid, matching the task's own case
table exactly.

Marker-shape note (see r_frm_03.py's docstring): the task's own case
table illustrates ``marker_wrong_wording/`` with the delta
``stretch_target: "Not defined in the framework"``, but Section 77.4's
marker-shape set as given in ``lanes/L1-05-tasks.md`` (the "closed and
mechanical" list right above the case table) does not contain that
phrase, so it would not be marker-shaped under the rule the same
document defines. This fixture instead uses
``"Not defined in framework v1."`` -- a wrong-case, wrongly-punctuated
near miss that *is* in the closed set (item 3: with a trailing period)
and is not byte-identical to the required literal -- so the case still
demonstrates "wrong wording catches R-FRM-03" without requiring the rule
to widen its closed set ad hoc, which Section 77.4 itself forbids doing
automatically for the marker literal.
"""
import glob
import os

import yaml

from validators.registry.rules import r_frm_01, r_frm_02, r_frm_03

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "frm")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _case_dir(case):
    return os.path.join(FIXTURES_DIR, case)


def _framework_docs_and_sources(case):
    case_dir = _case_dir(case)
    paths = sorted(glob.glob(os.path.join(case_dir, "framework*.yaml")))
    docs = [_load(p) for p in paths]
    # Repo-root-relative, forward-slash sources, matching the task's own
    # CORRECT OUTPUT example verbatim for the marker_lowercase case.
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    sources = [
        os.path.relpath(p, repo_root).replace(os.sep, "/") for p in paths
    ]
    return docs, sources


def _role_ids(case):
    roles_path = os.path.join(_case_dir(case), "roles.yaml")
    if not os.path.exists(roles_path):
        return None
    doc = _load(roles_path)
    return [r["id"] for r in doc["roles"]]


def _today(case):
    expect = _load(os.path.join(_case_dir(case), "expect.yaml"))
    return expect["today"]


def _all_findings(case):
    docs, sources = _framework_docs_and_sources(case)
    role_ids = _role_ids(case)
    today = _today(case)
    findings = []
    findings += r_frm_01.check(docs, role_ids, today)
    findings += r_frm_02.check(docs)
    findings += r_frm_03.check(docs, sources)
    return findings


# ---------------------------------------------------------------------------
# valid (6)
# ---------------------------------------------------------------------------


def test_valid_one_active_per_role():
    case = "valid/one_active_per_role"
    assert os.path.exists(os.path.join(_case_dir(case), "roles.yaml"))
    assert _all_findings(case) == []


def test_valid_superseded_non_overlapping():
    case = "valid/superseded_non_overlapping"
    docs, _ = _framework_docs_and_sources(case)
    assert len(docs) == 2
    assert _all_findings(case) == []


def test_valid_not_defined_literal_exact():
    case = "valid/not_defined_literal_exact"
    docs, _ = _framework_docs_and_sources(case)
    assert docs[0]["kpis"][0]["stretch_target"] == "Not defined in Framework v1"
    assert _all_findings(case) == []


def test_valid_custom_structure_no_targets():
    # Also carries the L1-801 review_cadence_not_defined corpus, per the
    # task's ORDERING NOTE (acceptance row 5).
    case = "valid/custom_structure_no_targets"
    docs, _ = _framework_docs_and_sources(case)
    assert docs[0]["kras"] == []
    assert docs[0]["kpis"] == []
    assert docs[0]["review_cadence"] == "Not defined"
    assert _all_findings(case) == []


def test_valid_multi_framework_transition():
    case = "valid/multi_framework_transition"
    docs, _ = _framework_docs_and_sources(case)
    assert len(docs) == 2
    assert any(d.get("multi_framework_transition") for d in docs)
    # Without the flag, this would be an R-FRM-01 n=2 offence -- confirm
    # the flag is precisely what suppresses it.
    role_ids = _role_ids(case)
    today = _today(case)
    unflagged = [dict(d, multi_framework_transition=False) for d in docs]
    assert r_frm_01.check(unflagged, role_ids, today) != []
    assert _all_findings(case) == []


def test_valid_no_roles_file_silent():
    case = "valid/no_roles_file_silent"
    assert not os.path.exists(os.path.join(_case_dir(case), "roles.yaml"))
    assert _role_ids(case) is None
    assert _all_findings(case) == []


# ---------------------------------------------------------------------------
# invalid (10)
# ---------------------------------------------------------------------------


def test_two_active_same_role_triggers_r_frm_01():
    findings = _all_findings("two_active_same_role")
    assert len(findings) == 1
    assert "R-FRM-01" in findings[0]
    assert "role 'developer' has 2 active frameworks" in findings[0]
    assert "SIG-23" in findings[0]


def test_zero_active_for_role_triggers_r_frm_01():
    findings = _all_findings("zero_active_for_role")
    assert len(findings) == 1
    assert "R-FRM-01" in findings[0]
    assert "role 'designer' has 0 active frameworks" in findings[0]
    assert "SIG-23" in findings[0]


def test_retroactive_effective_date_triggers_r_frm_02():
    findings = _all_findings("retroactive_effective_date")
    assert len(findings) == 1
    assert "R-FRM-02" in findings[0]
    assert "framework v2 takes effect on 2026-06-01" in findings[0]
    assert "before v1 retired on 2026-06-30" in findings[0]
    assert "AT-078" in findings[0]


def test_effective_before_predecessor_retirement_triggers_r_frm_02():
    findings = _all_findings("effective_before_predecessor_retirement")
    assert len(findings) == 1
    assert "R-FRM-02" in findings[0]
    assert "framework v2 takes effect on 2026-06-30" in findings[0]
    assert "before v1 retired on 2026-07-01" in findings[0]


def test_marker_lowercase_triggers_r_frm_03_exact_message():
    findings = _all_findings("marker_lowercase")
    assert len(findings) == 1
    expected = (
        "R-FRM-03 validators/registry/fixtures/frm/marker_lowercase/framework.yaml"
        ":/kpis/0/stretch_target field 'stretch_target' on 'KPI-DCA' reads "
        "'not defined in framework v1'; Section 77.4 requires the exact marker "
        '"Not defined in Framework v1" where the framework in force defines no value'
    )
    assert findings[0] == expected


def test_marker_wrong_wording_triggers_r_frm_03():
    findings = _all_findings("marker_wrong_wording")
    assert len(findings) == 1
    assert "R-FRM-03" in findings[0]
    assert "reads 'Not defined in framework v1.'" in findings[0]


def test_marker_tbd_triggers_r_frm_03():
    findings = _all_findings("marker_tbd")
    assert len(findings) == 1
    assert "R-FRM-03" in findings[0]
    assert "field 'target'" in findings[0]
    assert "reads 'TBD'" in findings[0]


def test_marker_na_triggers_r_frm_03():
    findings = _all_findings("marker_na")
    assert len(findings) == 1
    assert "R-FRM-03" in findings[0]
    assert "field 'definition'" in findings[0]
    assert "reads 'N/A'" in findings[0]


def test_two_roles_two_offenders_triggers_r_frm_01_twice():
    findings = _all_findings("two_roles_two_offenders")
    assert len(findings) == 2
    assert all("R-FRM-01" in f for f in findings)
    joined = " | ".join(findings)
    assert "role 'developer' has 2 active frameworks" in joined
    assert "role 'designer' has 0 active frameworks" in joined


def test_three_frameworks_one_role_triggers_r_frm_01_once():
    findings = _all_findings("three_frameworks_one_role")
    assert len(findings) == 1
    assert "R-FRM-01" in findings[0]
    assert "role 'developer' has 3 active frameworks" in findings[0]
