TASK ID:            L0-P0-006 / L0-07-06
CONTRACT FILE:      contracts/registry/product.contract.v2.json
CONTRACT VERSION:   2

WHAT THE CONTRACT SAYS NOW
"business_criticality": {
  "type": "string",
  "enum": [
    "low",
    "medium",
    "high",
    "critical"
  ]
}

WHAT THE TASK REQUIRES
MasterSpec §15.1 line 1531 and §15.2 lines 1536-1543 explicitly define business.criticality as a 3-tier enum (high | medium | low) deliberately distinct in vocabulary and purpose from classification.reliability_criticality (4 tiers: low | medium | high | critical). Lane 1 schema schemas/product/product.contract.v2.schema.json and L0-07 onboarding rank specify business_criticality with 3 tiers.

THE GAP, STATED AS A FACT
contracts/registry/product.contract.v2.json lines 185-193 incorrectly defined business_criticality with four tiers ("critical" included) by copying the reliability_criticality enum, contradicting MasterSpec §15.1/§15.2 and Lane 1's production validator schema.

BLAST RADIUS I CAN OBSERVE
- contracts/registry/product.contract.v2.json (schema definition)
- lanes/L0-01-phase-0-contracts.md (spec transcription)
- docs/onboarding/products/06/facts.tsv (product intake fixture)
- onboard-rank.sh (rank calculator)

I HAVE NOT EDITED contracts/**.
STATUS: APPROVED BY FOUNDER VIA FD-138 (2026-10-22)
