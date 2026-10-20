#!/usr/bin/env python3
"""The Phase-2 schema loader. Master Spec Section 101 invariant 85 (pinned
third-party dependencies); Section 99.1 line 9195 ("a schema-and-validator
suite"). Lane task L4-06-tasks.md L4-P2-02.

Every schema file this lane ships is loaded through here, and only through
here, before any other tool trusts it. `load_schema` proves two things and
nothing else:

  1. The file is syntactically valid JSON (a JSON parse error is rejected,
     never swallowed).
  2. The parsed document is a structurally valid JSON Schema under the
     2020-12 dialect (jsonschema's own meta-schema check).

A file that fails either check is rejected. Nothing here evaluates a schema
against a record instance -- that is lib/validate.py's job. This module
answers exactly one question: is this schema file loadable at all.

Usage: schemaload.py <schema.json> [<schema.json> ...]
Exit 0 and print "LOADED <path>" per file if every file loads; exit 1 and
print "REJECTED <path>: <reason>" for each one that does not. A file that
cannot even be read is rejected the same way -- fail closed, never skipped
(Section 40.1 line 3671).
"""
import json
import pathlib
import sys

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


class SchemaLoadError(Exception):
    """The file at `path` could not be loaded as a syntactically valid JSON
    Schema document. The message names the path and the reason."""


def load_schema(path):
    """Load and syntax-check one schema file.

    Returns the parsed schema as a dict on success. Raises SchemaLoadError
    on any failure: an unreadable path, a JSON syntax error, or a document
    that is not a valid Draft 2020-12 schema. Never returns a partially
    parsed or unchecked document.
    """
    p = pathlib.Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaLoadError("%s: unreadable: %s" % (path, exc)) from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SchemaLoadError(
            "%s: not syntactically valid JSON: %s" % (path, exc)
        ) from exc
    try:
        Draft202012Validator.check_schema(doc)
    except SchemaError as exc:
        raise SchemaLoadError(
            "%s: not a valid Draft 2020-12 schema: %s" % (path, exc.message)
        ) from exc
    return doc


def main(argv):
    if len(argv) < 2:
        print("USAGE: schemaload.py <schema.json> [<schema.json> ...]")
        return 2
    failed = 0
    for target in argv[1:]:
        try:
            load_schema(target)
        except SchemaLoadError as exc:
            print("REJECTED %s" % exc)
            failed += 1
            continue
        print("LOADED %s" % target)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
