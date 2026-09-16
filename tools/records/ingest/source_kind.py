#!/usr/bin/env python3
"""INGEST --source-kinds limb. Invariant 46, Master Spec line 9513."""
import os
import sys
import yaml

PATH = "metrics/ingest/source-kinds.yaml"
ROOT = "metrics/ingest"
KINDS = ["collector", "record_store"]


def fail(msg):
    print("INGEST FAIL source-kinds %s" % msg)
    sys.exit(1)


def walk_keys(node, forbidden, hits, where):
    if isinstance(node, dict):
        for k, v in node.items():
            if k in forbidden:
                hits.append("%s:%s" % (where, k))
            walk_keys(v, forbidden, hits, where)
    elif isinstance(node, list):
        for v in node:
            walk_keys(v, forbidden, hits, where)


def main():
    try:
        d = yaml.safe_load(open(PATH, encoding="utf-8"))
        col = yaml.safe_load(open("metrics/ingest/collectors.yaml",
                                  encoding="utf-8"))["collectors"]
    except Exception as e:
        print("INGEST ERROR source-kinds-unreadable:%s" % type(e).__name__)
        sys.exit(3)

    if sorted(d.get("kinds") or {}) != KINDS:
        fail("kinds-not-the-closed-pair")
    if d.get("closed_set") is not True:
        fail("kind-set-not-closed")
    if d["kinds"]["record_store"].get("may_be_a_source_of_truth") is not True:
        fail("record-store-not-a-source-of-truth")
    if d["kinds"]["collector"].get("may_be_a_source_of_truth") is not False:
        fail("collector-declared-a-source-of-truth")
    for line in (9513, 9776):
        if line not in (d.get("rule_spec_lines") or []):
            fail("invariant-46-anchor-missing:%d" % line)

    src = d.get("sources") or {}
    if sorted(src) != sorted(col):
        fail("sources-do-not-match-collectors-yaml")
    for name, s in src.items():
        if s.get("kind") != "collector":
            fail("collector-typed-as-record-store:%s" % name)
        if s.get("is_source_of_truth") is not False:
            fail("collector-claimed-as-source-of-truth:%s" % name)
        if s.get("may_be_sole_source_of_a_metric") is not False:
            fail("collector-claimed-as-sole-source:%s" % name)
        f = s.get("declaration_file") or ""
        if not os.path.isfile(f):
            print("INGEST ERROR source-kinds-declaration-missing:%s" % name)
            sys.exit(3)

    forbidden = set(d.get("forbidden_value_keys") or [])
    if not forbidden:
        fail("forbidden-value-key-set-empty")
    hits = []
    for fn in sorted(os.listdir(ROOT)):
        if not fn.endswith(".yaml"):
            continue
        try:
            doc = yaml.safe_load(open(os.path.join(ROOT, fn), encoding="utf-8"))
        except Exception:
            print("INGEST ERROR source-kinds-unparseable:%s" % fn)
            sys.exit(3)
        if fn != os.path.basename(PATH):
            walk_keys(doc, forbidden, hits, fn)
        k = (doc or {}).get("source_kind")
        if k is not None and k not in KINDS:
            fail("unknown-source-kind:%s:%s" % (fn, k))
    if hits:
        fail("hand-maintained-value-key:" + ",".join(sorted(hits)))

    print("INGEST OK source-kinds kinds=2 collectors=3 forbidden=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
