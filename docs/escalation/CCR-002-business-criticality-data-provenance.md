TASK ID:            L0-07-06 / OT-P4 (Data Provenance)
CONTRACT FILE:      docs/onboarding/products/{01,02,03,04,05,06,07,08}/facts.tsv
CONTRACT VERSION:   2

WHAT THE CONTRACT SAYS NOW
MasterSpec §15.2 (lines 1536–1543) and Decision D4 (line 10080) state:
"Two criticality fields, deliberately distinct... business.criticality expresses business importance (portfolio economics, lifecycle decisions, platform investment)... classification.reliability_criticality expresses operational stringency (restore cadence, monitoring depth, verification depth, incident capacity reserve)... Collapsing them into one field forces one of the two decisions to be wrong."
Under MasterSpec §68.1, business importance derives from concrete Product Load Unit inputs (revenue, active customers, support burden, contractual SLAs).

WHAT THE TASK REQUIRES
Each onboarded real product (Product-01 through Product-08, with Product-06 now confirmed real and not a fixture) must carry an individually assessed, founder-reviewed business_criticality value ("high" | "medium" | "low") based on actual portfolio economics, distinct from its operational reliability_criticality.

FOUNDER CONFIRMATION (2026-10-24)
The Founder confirmed the business criticality values for the 8 real products:
- Assetssync.cloud = high
- solvox.ai = high
- lumigrc.com = high
- ricru.ai = medium
- Cyberambassador.co.in = medium
- CyberPhishdrill.com = medium
- LumiSocial = medium
- Channel Partner Platform = low

INVESTIGATION FINDINGS (2026-10-24)
1. **Slot 06 Verified as Real:** Investigation confirmed slot 06 is NOT a fixture. It was seeded in commit 578586e under FD-110 across all 8 intake slots (72 obligations: 8 slots * 9 floor items). It possesses an active repo under `products/Product-6`, Prometheus target port 8086, and `contracts/estate.yaml` entry. No test suite uses it as a mock. The "fixture" label was an authoring assertion in CCR-001 line 25.
2. **Cardinality Alignment:** Exactly 8 named products match exactly 8 slots (01..08). Business criticality distribution (3 high, 4 medium, 1 low) matches root `facts.tsv` (3 high, 4 medium, 1 low).
3. **Slot Mapping Gap:** The 1:1 mapping between the 8 product names and slots 01..08 is not established in the codebase:
   - Root `facts.tsv` orders rank 1 as Product-1 (slot 01) and rank 2 as Product-2 (slot 02).
   - `onboard-rank.sh` calculates rank 1 as slot 06 and rank 2 as slot 01.
   - Products `lumigrc.com`, `ricru.ai`, `Cyberambassador.co.in`, `CyberPhishdrill.com`, `LumiSocial`, and `Channel Partner Platform` have zero prior mentions in repository files or git history.
   - Per AGENTS.md anti-hallucination discipline, no slot mapping may be guessed.

BLAST RADIUS I CAN OBSERVE
- docs/onboarding/products/{01..08}/facts.tsv (product intake facts)
- onboard-rank.sh (rank calculator: §96.5 sequences by reliability_criticality, then business_criticality, then cost band)
- Portfolio investment, lifecycle tiering, and staffing allocations under MasterSpec §68.1

I HAVE NOT EDITED ANY facts.tsv (Awaiting authoritative slot mapping).
STATUS: PENDING FOUNDER INPUT — Business criticality ratings confirmed by Founder for all 8 named products; slot 06 confirmed real; awaiting Founder's authoritative 1:1 mapping of product names to slots 01..08 before writing facts.tsv.

