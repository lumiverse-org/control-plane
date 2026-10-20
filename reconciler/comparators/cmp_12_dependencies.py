"""L3-P0-CMP12 (ported from L3-01-14) - CMP-12: a declared dependency
versus the shared-service registry (spec 53.1 row 12; 20.1: "A product
cannot declare a dependency on a shared service that does not exist in
the registry"; invariant 55).

The only comparator in this set that issues no API call at all: both
sides - a product's `dependencies.internal` list and the shared-service
registry - are declared state, read from the fixture's declared/ tree,
never from `actual`. A registry-only comparison goes vacuous exactly as
easily as an API one does (a glob that stops matching, a directory
renamed), so it still counts rows and still fails the run's `services`
count if it narrows (section 53.1's count rule, EC-109).

CMP-12 therefore counts one row per declared service, so that
`compared` for the `services` key reaches the number of services
actually declared; `Dependencies.registry_key` names that key for any
caller (e.g. a future per-registry-key run-record breakdown) that needs
to know which count this comparator's return value belongs to.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from reconciler.model import DriftClass, Finding, Level
from reconciler.registry import comparator

_FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


def _declared_services(declared: Any) -> list[dict[str, Any]]:
    """The declared side of CMP-12: every row of the shared-service
    registry. Prefers a `.services` attribute on `declared` (a future
    DeclaredState may load shared-services.yaml directly); otherwise
    reads the fixture's own declared/shared-services.yaml by
    `declared.fixture_name`, exactly as DeclaredState locates every
    other declared/ document today."""
    services = getattr(declared, "services", None)
    if services is not None:
        return list(services)
    fixture_name = getattr(declared, "fixture_name", None)
    if not fixture_name:
        return []
    path = _FIXTURES_ROOT / fixture_name / "declared" / "shared-services.yaml"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return list(data.get("services") or [])


@comparator("cmp_12_dependencies", fail_class=DriftClass.BLOCKING)
def compare(declared, actual, as_of):
    # No use of `actual` anywhere below - CMP-12 issues no API call;
    # both sides of the comparison are declared state (spec 53.1).
    services = _declared_services(declared)
    known = {s.get("name") for s in services if s.get("name")}
    compared = len(services)
    first_seen = f"{as_of.isoformat()}T00:00:00Z"

    findings: list[Finding] = []
    for product_name, product_yaml in declared.products.items():
        deps = (product_yaml.get("dependencies") or {}).get("internal") or []
        unknown = [dep for dep in deps if dep not in known]
        if not unknown:
            continue
        findings.append(
            Finding(
                id=f"cmp_12_dependencies:{product_name}:unknown",
                comparator="cmp_12_dependencies",
                scope=product_name,
                drift_class=DriftClass.BLOCKING,
                level=Level.BLOCK,
                evidence=(
                    f"{product_name} declares dependencies.internal={deps!r} "
                    f"but {unknown!r} does not exist in the shared-service registry "
                    f"(known services={sorted(known)!r}); section 20.1 - CI enforces this"
                ),
                first_seen=first_seen,
            )
        )

    return findings, compared


class Dependencies:
    """Metadata namespace for CMP-12, kept alongside the registered
    `compare` function so a caller can inspect this comparator's
    identity and registry key without importing reconciler.registry's
    module-level dicts."""

    comparator_id = "cmp_12_dependencies"
    registry_key = "services"
    compare = staticmethod(compare)
