"""L3: Read-only live product roster accessor.

Reads the actual onboarded products from `docs/onboarding/products/<slot>/facts.tsv`.
Pure local file reads: zero network calls, zero shell commands, zero writes.

Exclusion of slot 06:
Slot 06 (Product-6) is a known test fixture/placeholder rather than an onboarded
real product, as established across the repository:
- CCR-002 (docs/escalation/CCR-002-business-criticality-data-provenance.md):
  "Each onboarded real product (Product-01 through Product-08, excluding placeholder fixture Product-06)..."
- FD-138 (_FOUNDER_DECISIONS.md): notes Product-06 is a fixture with synthetic fields.
All real product roster counts in the platform (e.g. 7 real products) explicitly exclude slot 06.
"""

from __future__ import annotations

from pathlib import Path

# Established exclusion: slot 06 / Product-6 is a placeholder fixture (CCR-002, FD-138).
EXCLUDED_SLOTS = frozenset({"06"})
EXCLUDED_PRODUCT_IDS = frozenset({"Product-6"})

_DEFAULT_ONBOARDING_ROOT = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "onboarding" / "products"
)


def live_registered_product_ids(onboarding_root: Path | None = None) -> tuple[str, ...]:
    """Return the sorted tuple of real product IDs from docs/onboarding/products/<slot>/facts.tsv.

    Reads each slot's facts.tsv, extracts the `product_id` field, and explicitly
    excludes slot 06 (Product-6) per CCR-002 and FD-138.
    """
    root = onboarding_root if onboarding_root is not None else _DEFAULT_ONBOARDING_ROOT
    if not root.is_dir():
        return ()

    product_ids: list[str] = []
    for slot_dir in sorted(root.iterdir()):
        if not slot_dir.is_dir():
            continue
        if slot_dir.name in EXCLUDED_SLOTS:
            continue

        facts_file = slot_dir / "facts.tsv"
        if not facts_file.is_file():
            continue

        text = facts_file.read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].strip() == "product_id":
                pid = parts[1].strip()
                if pid and pid not in EXCLUDED_PRODUCT_IDS:
                    product_ids.append(pid)
                break

    return tuple(sorted(product_ids))
