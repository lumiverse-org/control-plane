# Per-product workflow caller templates — Spec §19.1 L1826-1882, §33.2 L2854-2869

## Purpose

`create-product` (Lane 3, Subsystem D) copies these files into a new product
repository under `.github/workflows/`, substituting the `{{UPPER_SNAKE_CASE}}`
placeholders declared in `PLACEHOLDERS.yaml` from `product.yaml` values.

**The substituting component is `create-product` (Lane 3).** Lane 2 authors the
templates and lints them with `tools/evidence/render_template.py`. Lane 2 never
performs substitution into a product repository — that would be a foreign-path
write (PARTITION.md rule 1, §0.1 of L2-05-tasks.md).

## Placeholder rules (binding, no exceptions)

1. Every token used in a template must be declared in `PLACEHOLDERS.yaml`.
2. Every declared token must be used by at least one template.
3. **No token may appear inside a GitHub Actions `${{ }}` expression.**
   A `{{TOKEN}}` inside `${{ }}` produces invalid YAML after substitution.
4. Templates are consumed by `{{WORKFLOWS_TAG}}` (a pinned tag), never by branch.
   Consuming by branch defeats the tag protection and the blast-radius apparatus
   of §33.3 and invariant 72.

## Required workflows per product repository (§33.2)

| Template | Required when |
|---|---|
| `ci.yml` | always |
| `build.yml` | always |
| `deploy-staging.yml` | always |
| `deploy-production.yml` | always |
| `migrate.yml` | always |
| `restore-test.yml` | always |
| `restore-production.yml` | product declares a `recovery:` block (§44.5) |
| `background-queue.yml` | conditional on §37.6 benchmark gate |
| `rollback.yml` | D-L2-05 (decision required) |

## Lint

```bash
python -m tools.evidence.render_template --lint templates/workflows --summary
```

## fail-closed rule

If `render_template` cannot validate a template (missing PLACEHOLDERS.yaml,
unreadable file, malformed YAML after substitution), it exits 3 (`ERROR`) and
the calling workflow step fails. There is no "assume pass" branch.

## checked= count

`render_template --lint` counts template `.yml` files examined. A run over an
empty directory is `OK render_template checked=0 failed=0`, exit 0 — not an error.
