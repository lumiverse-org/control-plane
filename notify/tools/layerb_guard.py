#!/usr/bin/env python3
"""Layer-B content guard on the notification router (Spec Section 90.2,
machine-identities row; invariants 106 and 109).

Section 90.2's machine-identities row ends with a sentence this guard makes
mechanical: "People intelligence is never relayed over messaging surfaces."

This guard loads the twenty-six Layer A/B data-category rows plus the
machine-identities row from access/model/permission-matrix.yaml
(`rows[].data_category`, and `machine_identity_row.data_category`), and
checks a notification payload against every one of them. A refusal is
matched on a whole-token basis (a data category's own words, in order, as a
contiguous run of tokens) so that an unrelated word sharing a substring with
a category never trips the guard, and it is fail-closed: an absent or
unparseable permission matrix always refuses, because the guard must never
pass a payload it could not check.

On refusal this prints exactly:
    LAYER B GUARD REFUSED: payload field <field> matches data category <category>
and exits 1. The category is named; the payload content behind the match is
never printed, so a caught field never round-trips into a log or a terminal.

Usage: layerb_guard.py --payload <json> [--matrix <path>]
Exit codes: 0 payload clear, 1 refused or fail-closed.
"""
import argparse
import json
import os
import re
import sys

import yaml

DEFAULT_MATRIX_PATH = os.path.join("access", "model", "permission-matrix.yaml")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class GuardFailClosed(Exception):
    """Raised whenever the matrix cannot be loaded or trusted."""


def _tokens(text):
    return TOKEN_RE.findall(str(text).lower())


def load_categories(matrix_path):
    """Returns the list of data-category strings this guard checks against:
    every `rows[].data_category` plus `machine_identity_row.data_category`,
    in file order. Raises GuardFailClosed on anything short of a readable,
    well-formed matrix that names at least one category -- this function
    never returns an empty guard."""
    try:
        with open(matrix_path, "r", encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise GuardFailClosed("permission matrix unreadable: %s (%s)"
                               % (matrix_path, exc))

    if not isinstance(doc, dict):
        raise GuardFailClosed("permission matrix is not a mapping: %s"
                               % matrix_path)

    categories = []
    for row in doc.get("rows") or []:
        if isinstance(row, dict):
            category = row.get("data_category")
            if category:
                categories.append(str(category))

    machine_row = doc.get("machine_identity_row")
    if isinstance(machine_row, dict):
        category = machine_row.get("data_category")
        if category:
            categories.append(str(category))

    if not categories:
        raise GuardFailClosed("permission matrix names no data categories: %s"
                               % matrix_path)
    return categories


def _matches_category(text, category_tokens):
    if not category_tokens:
        return False
    text_tokens = _tokens(text)
    span = len(category_tokens)
    if len(text_tokens) < span:
        return False
    for start in range(len(text_tokens) - span + 1):
        if text_tokens[start:start + span] == category_tokens:
            return True
    return False


def find_violation(payload, categories):
    """Walks `payload` (dicts and lists, recursively) and returns
    (field, category) for the first key or string content that matches a
    data category on a whole-token basis, or None if the payload is clear."""
    indexed = [(category, _tokens(category)) for category in categories]
    if isinstance(payload, (dict, list)):
        return _walk(payload, "", indexed)
    if isinstance(payload, str):
        for category, tokens in indexed:
            if _matches_category(payload, tokens):
                return ("payload", category)
    return None


def _walk(node, path, indexed):
    if isinstance(node, dict):
        for key, item in node.items():
            field = "%s.%s" % (path, key) if path else str(key)
            for category, tokens in indexed:
                if _matches_category(str(key), tokens):
                    return (field, category)
            found = _check_or_descend(item, field, indexed)
            if found is not None:
                return found
    elif isinstance(node, list):
        for index, item in enumerate(node):
            field = "%s[%d]" % (path, index) if path else "[%d]" % index
            found = _check_or_descend(item, field, indexed)
            if found is not None:
                return found
    return None


def _check_or_descend(item, field, indexed):
    if isinstance(item, str):
        for category, tokens in indexed:
            if _matches_category(item, tokens):
                return (field, category)
        return None
    if isinstance(item, (dict, list)):
        return _walk(item, field, indexed)
    return None


def check_payload(payload, matrix_path=DEFAULT_MATRIX_PATH):
    """Returns (field, category) on refusal, or None on a clear payload.
    Raises GuardFailClosed if the matrix cannot be loaded -- callers must
    treat that as a refusal, never as a pass."""
    categories = load_categories(matrix_path)
    return find_violation(payload, categories)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX_PATH,
                         help="path to permission-matrix.yaml")
    parser.add_argument("--payload", required=True,
                         help="JSON object to check")
    args = parser.parse_args(argv)

    try:
        categories = load_categories(args.matrix)
    except GuardFailClosed as exc:
        print("LAYER B GUARD REFUSED: fail-closed, %s" % exc)
        return 1

    try:
        payload = json.loads(args.payload)
    except (TypeError, json.JSONDecodeError):
        print("LAYER B GUARD REFUSED: fail-closed, --payload is not valid JSON")
        return 1

    violation = find_violation(payload, categories)
    if violation is not None:
        field, category = violation
        print("LAYER B GUARD REFUSED: payload field %s matches data "
              "category %s" % (field, category))
        return 1

    print("LAYER B GUARD: payload clear against %d data categories"
          % len(categories))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
