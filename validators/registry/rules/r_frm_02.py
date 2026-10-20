"""R-FRM-02 -- a framework's effective_date is retroactive against the
document it supersedes for the same role (Section 77.4, AT-078).

AT-078: a successor framework may not take effect before its predecessor,
for the same role, has retired. Section 77.4 frames this as the
change-authority guarantee behind a role's framework history: nothing
backdates itself over a period that already ran under the prior version.

Supersession is scoped per role (two documents "supersede" each other for
a role only if both name that role in ``affected_roles``) and ordered by
``effective_date``: for consecutive documents sharing a role, the earlier
one is the predecessor. A predecessor with no ``retirement_date`` (still
open-ended) has not been superseded yet, so the pair is not checked --
there is nothing to be retroactive against.

Standalone, directly-tested rule function -- see r_svc_01.py's module
docstring (L1-404) for why this is not wired into the frozen Option B
(FD-094) R01-R18 dispatch engine.
"""
from __future__ import annotations

import datetime

RULE_ID = "R-FRM-02"
SPEC = "Section 77.4 / AT-078"
APPLIES_TO = ["framework"]


def _as_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value))


def check(framework_docs: list) -> list:
    """Return one finding per (role, predecessor, successor) triple where
    the successor's ``effective_date`` is earlier than the predecessor's
    ``retirement_date``.
    """
    role_to_docs: dict = {}
    for doc in framework_docs:
        for role in doc.get("affected_roles") or []:
            role_to_docs.setdefault(role, []).append(doc)

    findings = []
    for role, docs in role_to_docs.items():
        ordered = sorted(docs, key=lambda d: _as_date(d["effective_date"]))
        for predecessor, successor in zip(ordered, ordered[1:]):
            retirement = predecessor.get("retirement_date")
            if retirement is None:
                continue
            if _as_date(successor["effective_date"]) < _as_date(retirement):
                findings.append(
                    f"R-FRM-02 framework {successor.get('framework_version', '<unknown>')} "
                    f"takes effect on {successor['effective_date']}, before "
                    f"{predecessor.get('framework_version', '<unknown>')} retired on "
                    f"{retirement}; AT-078 forbids a retroactive activation"
                )
    return findings
