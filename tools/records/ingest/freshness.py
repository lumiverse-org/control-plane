#!/usr/bin/env python3
"""INGEST --freshness limb. Master Spec 51.2 line 4459; 52.2 line 4524."""
import os
import sys
import yaml

PATH = "metrics/ingest/freshness.yaml"
ROOT = "metrics/ingest"
RETENTION = "metrics/retention/retention-classes.yaml"
FROZEN = {
    "unarmed — not yet instrumented",
    "unarmed — insufficient history",
    "armed — source stale",
}


def fail(msg):
    print("INGEST FAIL freshness %s" % msg)
    sys.exit(1)


def strings(node, out):
    if isinstance(node, dict):
        for v in node.values():
            strings(v, out)
    elif isinstance(node, list):
        for v in node:
            strings(v, out)
    elif isinstance(node, str):
        out.append(node)


def main():
    if not os.path.isfile(RETENTION):
        print("INGEST ERROR retention-classes-unreachable")
        sys.exit(3)
    try:
        d = yaml.safe_load(open(PATH, encoding="utf-8"))
        col = yaml.safe_load(open("metrics/ingest/collectors.yaml",
                                  encoding="utf-8"))["collectors"]
    except Exception as e:
        print("INGEST ERROR freshness-unreadable:%s" % type(e).__name__)
        sys.exit(3)

    c = d.get("collectors") or {}
    if sorted(c) != sorted(col):
        fail("freshness-collectors-do-not-match-collectors-yaml")
    dl = c.get("devlake") or {}
    if dl.get("freshness_slo") != "Ingest completes at least daily":
        fail("devlake-slo-not-the-line-4459-string")
    if dl.get("measured_by") != "Age of the newest ingested row":
        fail("devlake-measure-not-the-line-4459-string")
    if dl.get("breach_class") != "Amber":
        fail("devlake-breach-class-not-amber")
    if dl.get("stale_rendering") != "armed — source stale":
        fail("devlake-stale-rendering-not-frozen-vocabulary")
    if dl.get("spec_line") != 4459:
        fail("devlake-slo-anchor-not-4459")
    for name in ("prometheus", "scorecard"):
        if c[name].get("freshness_slo") != "none-declared-in-spec":
            fail("slo-invented-for-a-collector-the-spec-gives-none:%s" % name)
        if c[name].get("l4_declares_no_slo") is not True:
            fail("l4-claims-an-slo-it-must-not-invent:%s" % name)

    vocab = [v.get("value") for v in (d.get("arming_vocabulary") or [])]
    if set(vocab) != FROZEN or len(vocab) != 3:
        fail("arming-vocabulary-not-the-frozen-three")
    if d.get("closed_vocabulary") is not True:
        fail("arming-vocabulary-not-closed")
    if d.get("retention_class_declared_here") is not False:
        fail("retention-class-declared-outside-its-owner-file")

    bad = []
    for fn in sorted(os.listdir(ROOT)):
        if not fn.endswith(".yaml"):
            continue
        try:
            doc = yaml.safe_load(open(os.path.join(ROOT, fn), encoding="utf-8"))
        except Exception:
            print("INGEST ERROR freshness-unparseable:%s" % fn)
            sys.exit(3)
        vals = []
        strings(doc, vals)
        for s in vals:
            t = s.strip()
            if (t.startswith("armed") or t.startswith("unarmed")) and t not in FROZEN:
                bad.append("%s:%s" % (fn, t[:40]))
    if bad:
        fail("arming-string-outside-frozen-vocabulary:" + ",".join(sorted(bad)))

    print("INGEST OK freshness slo=1 none-declared=2 arming_strings=3 violations=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
