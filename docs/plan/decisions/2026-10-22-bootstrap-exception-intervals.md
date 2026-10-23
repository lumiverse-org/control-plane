# DECISION — bootstrap exception intervals — 2026-10-22

decision_id: L0D-17 (calibrated configuration)
subject: bootstrap exception lifetime and review offset
value: expiry = start + 91 days; review_date = expiry - 30 days
basis: |
  Transcribed from the MasterSpec v4.0 Section 95.2 exhibit, spec L8666-L8668:
  start 2026-09-01, expiry 2026-12-01, review_date 2026-11-01. No value was chosen.
  Section 54.2 (spec L4797) independently requires a bounded expiry whatever the number is.
open: |
  L0 confirms or replaces these initial values. See DECISION REQUIRED #3 in
  implementation/lanes/L0-06-bootstrap-mode.md. Until then these are the values in force.
