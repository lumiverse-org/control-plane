"""L3-P4-08: CONFIGURE checklist and manual-step issue emitter.

Spec basis: Section 19.1 CONFIGURE stage -- "the scaffold emits a CONFIGURE
checklist issue enumerating every item below" -- and the CREATE PRODUCT
manual-step note: "or, where the provider offers no automation, tracked
manual steps emitted as issues so neither is silently missing." The two
manual steps this module renders issues for -- `alert_channel` and
`support_intake_mailbox` -- are the ones L3-P4-07's create-product plan
names.

Rendering a checklist never touches GitHub. `post_issue` posts one only
when both --apply and --live are set, and only through a GitHub client.
With no client, a missing token fails closed before any `gh` process.
The live client creates the issue with `gh api`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

# Section 19.1 CONFIGURE stage: exactly these seven items, verbatim, in this
# order, no more, no fewer.
CONFIGURE_ITEMS: tuple[str, ...] = (
    "environments",
    "verification contract",
    "observability",
    "backups",
    "classification",
    "budget band",
    "support intake",
)

# Section 19.1: "set by the Founder as a provisional estimate, refined at
# the first cost review" -- attached to the budget-band row verbatim.
BUDGET_BAND_NOTE = "set by the Founder as a provisional estimate, refined at the first cost review"

# The two manual steps L3-P4-07's create-product plan declares (Section
# 19.1: "or, where the provider offers no automation, tracked manual steps
# emitted as issues so neither is silently missing").
CREATE_PRODUCT_MANUAL_STEPS: tuple[str, ...] = ("alert_channel", "support_intake_mailbox")


@dataclass(frozen=True)
class ManualStep:
    """A manual step from a plan (e.g. L3-P4-07's create-product plan)."""

    id: str
    description: str


class PostingRefused(Exception):
    """Raised whenever an issue post is attempted without --apply and --live."""


class MissingToken(RuntimeError):
    """Live issue post refused because no GitHub token is available."""


class IssueTargetMissing(ValueError):
    """Live issue post refused because org, repo, or title was not given."""


def configure_checklist(product: str) -> str:
    """Render the CONFIGURE checklist issue body for `product`.

    Enumerates exactly the seven Section 19.1 CONFIGURE items, verbatim, in
    order. The budget-band row carries the Founder-provisional-estimate
    note verbatim, as Section 19.1 requires.
    """
    lines = [f"# CONFIGURE checklist -- {product}", ""]
    for item in CONFIGURE_ITEMS:
        if item == "budget band":
            lines.append(f"- [ ] {item} ({BUDGET_BAND_NOTE})")
        else:
            lines.append(f"- [ ] {item}")
    return "\n".join(lines) + "\n"


def manual_step_issue(step: ManualStep) -> str:
    """Render one manual-step issue body for `step`.

    One issue per manual step named by the create-product orchestrator
    (L3-P4-07) so a step with no available provider automation is tracked,
    never silently missing (Section 19.1).
    """
    return (
        f"# Manual step -- {step.id}\n\n"
        f"{step.description}\n\n"
        "This step has no automation on the current provider. It is tracked "
        "here as a manual step so it is never silently missing (Section 19.1).\n"
    )


def manual_step_issues(steps) -> list[str]:
    """Render one issue per manual step in `steps`, in the order given."""
    return [manual_step_issue(step) for step in steps]


def _title_from_body(body: str) -> str:
    """Use the first heading, or the first non-empty line, as the issue title."""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
        return stripped
    return ""


def _token_present() -> bool:
    return bool(os.environ.get("GH_TOKEN", "").strip() or os.environ.get("GITHUB_TOKEN", "").strip())


def post_issue(
    body: str,
    *,
    apply: bool,
    live: bool,
    client: Any | None = None,
    repo: str | None = None,
    title: str | None = None,
    org: str | None = None,
) -> dict[str, Any]:
    """Post `body` as a GitHub issue, only when both --apply and --live are set.

    Rendering a checklist never touches GitHub. Posting is gated on both
    flags (Section 64.1). An injected client is called directly and is
    what tests use. With no client, a missing token, org, or repo fails
    closed before `gh` is started. The live client then calls `gh api`.
    """
    if not (apply and live):
        raise PostingRefused("issue post refused: requires both --apply and --live")

    issue_title = (title if title is not None else _title_from_body(body)).strip()
    if client is None:
        if not _token_present():
            raise MissingToken(
                "issue post refused: GH_TOKEN and GITHUB_TOKEN are unset (fail closed)"
            )
        if not org or not str(org).strip():
            raise IssueTargetMissing(
                "issue post refused: org is required for a live post (fail closed)"
            )
        if not repo or not str(repo).strip():
            raise IssueTargetMissing(
                "issue post refused: repo is required for a live post (fail closed)"
            )
        if not issue_title:
            raise IssueTargetMissing(
                "issue post refused: title is required for a live post (fail closed)"
            )
        from tools.provision.github_client import RealGitHubClient

        client = RealGitHubClient(org=str(org).strip())

    if not repo or not str(repo).strip():
        raise IssueTargetMissing("issue post refused: repo is required (fail closed)")
    if not issue_title:
        raise IssueTargetMissing("issue post refused: title is required (fail closed)")
    return client.create_issue(repo=str(repo).strip(), title=issue_title, body=body)
