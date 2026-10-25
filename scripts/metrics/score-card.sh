#!/usr/bin/env bash
# score-card.sh — L4 metrics dump viewer (FD-085)
# Prints the raw recorded-metrics YAML for a product/period (or all products).
# NOTE: despite the historical "scorecard generator" name, this performs no
# scoring, aggregation, or threshold comparison — it is a read-only dump of
# whatever record-metric.sh wrote. Use validate-metrics.sh to check that a
# record exists and parses; this script does not re-check that.
#
# DEFERRED / OUT OF SCOPE (Composite metric scoring):
# Weighted-metric-vs-target scoring is deliberately NOT specified in V1 scope
# and is prohibited from being invented locally. Master Spec v4.0 §91 (Retention,
# No-Surveillance, Fairness and Anti-Goodhart) explicitly bans single composite
# productivity scores (enforced by registry rule validators and banned-fixture suites).
# Furthermore, Master Spec §103 (Measure Computations) defines Level 1, Level 2,
# and Level 3 operational measures, evaluating each measure independently against
# its own discrete threshold without blending them into a composite score (see also
# L4-05-pipeline-and-boards.md D-L4-P5-01/D-L4-P5-02). The Phase 7 metric pipeline
# (lanes/L4-03-metric-register.md) evaluates per-measure declarations separately.
# Consequently, records/metrics/<product>/<period>.yaml records remain discrete
# metric snapshots, and this script correctly operates as a read-only inspector/dump
# rather than applying an unauthorized composite scoring algorithm.
# Usage: bash scripts/metrics/score-card.sh [product-id|all] [YYYY-MM]
# Args are positional (not --product/--period flags, unlike record-metric.sh).
set -euo pipefail
shopt -s nullglob

PRODUCT="${1:-all}"
PERIOD="${2:-$(date +%Y-%m)}"

# Warn (don't fail) if a metrics file exists but isn't parseable YAML with a
# metrics: block — previously such a file was cat'd verbatim with no warning.
check_well_formed() {
  python -c "
import sys, yaml
doc = yaml.safe_load(open(sys.argv[1])) or {}
sys.exit(0 if isinstance(doc.get('metrics'), dict) and doc['metrics'] else 1)
" "$1" 2>/dev/null || echo "WARNING: $1 is not parseable YAML with a non-empty metrics: block"
}

echo "=== Metrics dump: $PRODUCT / $PERIOD ==="
echo ""

if [[ "$PRODUCT" == "all" ]]; then
  for DIR in records/metrics/*/; do
    PROD=$(basename "$DIR")
    METRIC_FILE="$DIR${PERIOD}.yaml"
    if [[ -f "$METRIC_FILE" ]]; then
      echo "--- $PROD ---"
      check_well_formed "$METRIC_FILE"
      cat "$METRIC_FILE"
      echo ""
    else
      echo "--- $PROD --- (no data for $PERIOD)"
    fi
  done
else
  METRIC_FILE="records/metrics/$PRODUCT/${PERIOD}.yaml"
  if [[ -f "$METRIC_FILE" ]]; then
    check_well_formed "$METRIC_FILE"
    cat "$METRIC_FILE"
  else
    echo "No metrics found for product=$PRODUCT period=$PERIOD"
    echo "Record with: bash scripts/metrics/record-metric.sh --product $PRODUCT --metric <name> --value <n>"
  fi
fi
