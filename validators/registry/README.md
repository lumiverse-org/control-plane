# validators/registry — CLI Contract (L1-903)

The one published interface Lane 2 is allowed to call (PARTITION rule 4). Frozen under
FD-094 (DECIDED): this is "Option B". Changing anything below is a Contract Change
Request, not a README edit.

## Invocation

```
python -m validators.registry.cli --root <p> --as-of <d> --records-root <p> --format json [--rule Rxx]
```

`--root` is required; `--as-of`, `--records-root`, `--format` and `--rule` are optional.
`--format` defaults to `text`. `--as-of` defaults to the system UTC date when omitted.

## Exit codes

- exit 0 — every rule that ran reported zero findings
- exit 1 — one or more rules reported a finding
- exit 2 — input error: `--root` is missing or not a directory, `--rule` names an unknown
  rule, or an unhandled exception is raised while loading or running a rule
- exit 3 — not used by this CLI. The pre-FD-094 design reserved exit 3 for an internal
  error kept separate from exit 2; Option B folds that case into exit 2 instead

## Output grammar

`--format json` prints one JSON object on stdout:

```
{"status": "PASS" | "FAIL", "rules_run": <int>, "findings": [<string>, ...]}
```

On an exit-2 input error it instead prints `{"status": "ERROR", "error": "<message>"}`.
`--format text` (the default) prints one `[PASS]`/`[FAIL] <rule-name>` line per rule run,
each failing rule's findings indented two spaces with a leading `- `, then one final
`Overall: PASS|FAIL (<n> rules)` line. A finding is a free-form string prefixed with its
rule id, for example `R01: duplicate id '<id>' in <file> and <file>`. This CLI never
prints the line `OK: <n> file(s) validated, 0 error(s)` and never prints a structured
`ERROR <RULE-ID> <path>:<json-pointer> <message>` line — both belonged to the pre-FD-094
design and were never built. Everything above goes to stdout; this CLI never writes to
stderr.

## Determinism

`--as-of <YYYY-MM-DD>` fixes "today" for every date-sensitive rule. Omit it and the CLI
uses the system UTC date, so CI should always pass `--as-of` explicitly for a reproducible
run. There is no separate `--today` flag — the pre-FD-094 design's `--today` override was
never built, and `--as-of` is Option B's only date-override flag.

## Stability

This grammar is frozen under FD-094 (DECIDED). Changing it is a Contract Change Request
under PARTITION rule 2, not an edit here. Lane 2 keys its required status check on the
exit code, never on parsing stdout prose.
