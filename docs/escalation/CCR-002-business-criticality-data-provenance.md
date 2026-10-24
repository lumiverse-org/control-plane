TASK ID:            L0-07-06 / OT-P4 (Data Provenance)
CONTRACT FILE:      docs/onboarding/products/{01,02,03,04,05,07,08}/facts.tsv
CONTRACT VERSION:   2

WHAT THE CONTRACT SAYS NOW
MasterSpec §15.2 (lines 1536–1543) and Decision D4 (line 10080) state:
"Two criticality fields, deliberately distinct... business.criticality expresses business importance (portfolio economics, lifecycle decisions, platform investment)... classification.reliability_criticality expresses operational stringency (restore cadence, monitoring depth, verification depth, incident capacity reserve)... Collapsing them into one field forces one of the two decisions to be wrong."
Under MasterSpec §68.1, business importance derives from concrete Product Load Unit inputs (revenue, active customers, support burden, contractual SLAs).

WHAT THE TASK REQUIRES
Each onboarded real product (Product-01 through Product-08, excluding placeholder fixture Product-06) must carry an individually assessed, founder-reviewed business_criticality value ("high" | "medium" | "low") based on actual portfolio economics, distinct from its operational reliability_criticality.

THE GAP, STATED AS A FACT
All 7 real onboarded products (docs/onboarding/products/01, 02, 03, 04, 05, 07, 08) currently have a business_criticality value in facts.tsv that is byte-identical to that product's reliability_criticality value (01: high/high, 02: medium/medium, 03: high/high, 04: high/high, 05: medium/medium, 07: low/low, 08: high/high). Git history (commits 578586e and 852c816 on 2026-09-22) confirms these were seeded in bulk without independent business assessment. No entry in _FOUNDER_DECISIONS.md or docs/escalation/*.md has resolved or validated the individual business_criticality ratings for these 7 real products (FD-138 resolved only the schema enum mismatch on fixture Product-06).

BLAST RADIUS I CAN OBSERVE
- docs/onboarding/products/{01,02,03,04,05,07,08}/facts.tsv (product intake facts)
- onboard-rank.sh (rank calculator: §96.5 sequences by reliability_criticality, then business_criticality, then cost band)
- Portfolio investment, lifecycle tiering, and staffing allocations under MasterSpec §68.1

I HAVE NOT EDITED contracts/** OR ANY facts.tsv.
STATUS: PENDING FOUNDER REVIEW (escalated)
