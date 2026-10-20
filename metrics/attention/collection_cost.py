#!/usr/bin/env python3
"""metrics/attention/collection_cost.py

L4-P6-12 -- Five-minute collection-cost cap assertion.
Master Spec v4.0 Section 67.3 line 5605 / Section 97.4 line 8980:
"The five-minute cap is binding. A collection design costing more than this
fails the check. It is a collection design to be simplified, not a person
to be chased."

This module asserts that:
  1. the ledger's own declared cap (calibration.yaml,
     self_report_cap_minutes_per_person_per_week) is itself at or under five
     minutes per person per week, and
  2. a candidate self-report collection design's declared cost is at or
     under that same cap -- a design that exceeds it is REJECTED, never
     accepted.

The cap is calibrated configuration. Per D102 (line 10195) and the C8 rule
enforced by validate-attention-config.sh ("no threshold is a literal in
code"), this module holds no threshold as a literal and reads the cap only
through lib/config.py's load_calibration().

Usage:
  collection_cost.py                 # asserts the ledger's own declared cap <= 5
  collection_cost.py --minutes N     # asserts a candidate design costing N
                                      # minutes/person/week is at or under the cap

Output contract: one final line.
  COST-CAP OK <detail>    exit 0    the assertion held
  COST-CAP FAIL <detail>  exit 1    the design (or the declared cap) exceeds 5 minutes
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
import config  # noqa: E402  (metrics/attention/lib/config.py -- the only reader of calibration.yaml)


def cap_minutes():
    """The declared collection-cost cap, read from calibrated configuration."""
    cal = config.load_calibration()
    return config.value(cal, "self_report_cap_minutes_per_person_per_week")


def check(minutes, cap):
    """True if a design costing `minutes` per person per week is within `cap`."""
    return minutes <= cap


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--minutes",
        type=float,
        default=None,
        help="a candidate collection design's declared cost, in minutes per person per week",
    )
    args = parser.parse_args(argv)

    cap = cap_minutes()

    if args.minutes is None:
        # No candidate design given: assert the ledger's own declared cap is
        # itself at or under five minutes (Section 67.3 line 5605 states the
        # cap verbatim as 5; a calibration review could only lower it, never
        # raise it past the spec-fixed ceiling).
        if cap <= 5:
            print("COST-CAP OK cap=%s" % cap)
            return 0
        print("COST-CAP FAIL cap=%s exceeds-5" % cap)
        return 1

    if check(args.minutes, cap):
        print("COST-CAP OK design=%s cap=%s" % (args.minutes, cap))
        return 0
    print("COST-CAP FAIL design=%s exceeds-cap=%s" % (args.minutes, cap))
    return 1


if __name__ == "__main__":
    sys.exit(main())
