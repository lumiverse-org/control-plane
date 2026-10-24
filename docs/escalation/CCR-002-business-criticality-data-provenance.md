TASK ID:            L0-07-06 / OT-P4 (Data Provenance)
CONTRACT FILE:      docs/onboarding/products/{01,02,03,04,05,07,08}/facts.tsv
CONTRACT VERSION:   2

WHAT THE CONTRACT SAYS NOW
MasterSpec §15.2 (lines 1536–1543) and Decision D4 (line 10080) state:
"Two criticality fields, deliberately distinct... business.criticality expresses business importance (portfolio economics, lifecycle decisions, platform investment)... classification.reliability_criticality expresses operational stringency (restore cadence, monitoring depth, verification depth, incident capacity reserve)... Collapsing them into one field forces one of the two decisions to be wrong."
Under MasterSpec §68.1, business importance derives from concrete Product Load Unit inputs (revenue, active customers, support burden, contractual SLAs).

WHAT THE TASK REQUIRES
Each onboarded real product (Product-01 through Product-08, excluding placeholder fixture Product-06) must carry an individually assessed, founder-reviewed business_criticality value ("high" | "medium" | "low") based on actual portfolio economics, distinct from its operational reliability_criticality.

FOUNDER CONFIRMATION (2026-10-24)
The Founder confirmed the business criticality values for the real products:
- Assetssync.cloud = high
- solvox.ai = high
- lumigrc.com = high
- ricru.ai = medium
- Cyberambassador.co.in = medium
- CyberPhishdrill.com = medium
- LumiSocial = medium
- Channel Partner Platform = low

THE GAP, STATED AS A FACT
1. **Slot 06 is a Placeholder Fixture:** Slot 06 is consistently established as a non-real intake placeholder fixture across CCR-001 (line 25: "product intake fixture"), FD-138 (enum correction on slot 06 facts.tsv for rank calculation), and `tools/provision/live_roster.py` (explicitly excluded by `live_registered_product_ids`, proven by `test_slot_06_is_genuinely_excluded` in `test_live_roster.py`). No real product repository `Product-6` exists in this repository.
2. **7 Real Product Slots (01, 02, 03, 04, 05, 07, 08):** All 7 real onboarded products currently have a business_criticality value in facts.tsv that was bulk-seeded identical to reliability_criticality (01: high/high, 02: medium/medium, 03: high/high, 04: high/high, 05: medium/medium, 07: low/low, 08: high/high).
3. **Slot Mapping Gap:** The 1:1 mapping between the Founder-named products and the 7 real product slots (01, 02, 03, 04, 05, 07, 08) is not established in the codebase:
   - Root `facts.tsv` orders rank 1 as Product-1 (slot 01) and rank 2 as Product-2 (slot 02).
   - `onboard-rank.sh` calculates rank 1 as slot 06 (placeholder) and rank 2 as slot 01.
   - Products `lumigrc.com`, `ricru.ai`, `Cyberambassador.co.in`, `CyberPhishdrill.com`, `LumiSocial`, and `Channel Partner Platform` have zero prior mentions in repository files or git history.
   - Per AGENTS.md, no mapping may be guessed or fabricated.

BLAST RADIUS I CAN OBSERVE
- docs/onboarding/products/{01,02,03,04,05,07,08}/facts.tsv (product intake facts)
- onboard-rank.sh (rank calculator: §96.5 sequences by reliability_criticality, then business_criticality, then cost band)
- Portfolio investment, lifecycle tiering, and staffing allocations under MasterSpec §68.1

I HAVE NOT EDITED ANY facts.tsv.
STATUS: PENDING FOUNDER INPUT — Slot 06 confirmed non-real placeholder fixture; business criticality ratings confirmed for real products; awaiting Founder's authoritative mapping of product names to the 7 real slots (01, 02, 03, 04, 05, 07, 08) before writing facts.tsv.
