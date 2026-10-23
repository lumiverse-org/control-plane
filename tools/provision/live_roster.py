"""L3: Read-only live product roster accessor.

Reads the actual onboarded products from `docs/onboarding/products/<slot>/facts.tsv`.
Pure local file reads: zero network calls, zero shell commands, zero writes.

Exclusion of slot 06:
Slot 06 (Product-6) is excluded from the active roster of onboarded products:
- In escalation docs, CCR-001 (docs/escalation/CCR-001-business-criticality.md line 25)
  classifies `docs/onboarding/products/06/facts.tsv` as a "product intake fixture",
  and CCR-002 (docs/escalation/CCR-002-business-criticality-data-provenance.md lines 11 & 14)
  identifies the 7 real onboarded products (slots 01, 02, 03, 04, 05, 07, 08) and
  characterizes Product-06 as a placeholder fixture.
- In `_FOUNDER_DECISIONS.md`, FD-138 resolved the 3-tier vs 4-tier business_criticality enum
  contradiction and aligned slot 06 facts.tsv for the deterministic onboard-rank calculation,
  without establishing Product-6 as a live production product.
- There is no Founder Decision defining Product-6 as an active production service;
  the live repository estate consists of 7 real onboarded products (Product-1 through Product-8,
  excluding Product-6).
"""

from __future__ import annotations

from pathlib import Path

# Slot 06 / Product-6 is excluded from the active product roster (CCR-001, CCR-002).
EXCLUDED_SLOTS = frozenset({"06"})
EXCLUDED_PRODUCT_IDS = frozenset({"Product-6"})

_DEFAULT_ONBOARDING_ROOT = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "onboarding" / "products"
)


def live_registered_product_ids(onboarding_root: Path | None = None) -> tuple[str, ...]:
    """Return the sorted tuple of real product IDs from docs/onboarding/products/<slot>/facts.tsv.

    Reads each slot's facts.tsv, extracts the `product_id` field, and explicitly
    excludes slot 06 (Product-6) per CCR-001 and CCR-002.
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
