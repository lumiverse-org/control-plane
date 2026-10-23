# records-writer — Declared Credential Shape as Code

Fifth secrets tier (MasterSpec Section 40.1). Decision **D89**; supersedes the
path-scoped-bypass mechanism of **D76** in part. Tracked under Lane 4 Task `L4-P1-T12`.

## Credential Declaration

| Property | Declared Value |
|---|---|
| Kind | GitHub App installation token |
| App Slug | `records-writer-lumiverse-org` |
| App ID | `5422825` |
| Installation ID | `174038206` |
| Repository Permissions | `{"contents": "write", "metadata": "read"}` (nothing else) |
| Organization Permissions | None |
| Repository Selection | `selected`, exactly one repository: `lumiverse-org/control-plane-records` |
| Reaches any registry? | **No.** `people.yaml`, `roles.yaml`, `exceptions.yaml` and `policies.yaml` live in `control-plane`, where this credential has no installation at all. |
| Approves anything? | **No.** It writes records; it approves nothing (D76 as amended by D89). |
| Bypass actor anywhere? | **No.** Neither ruleset on the records repository lists any bypass actor. |
| Rotation Cadence | Quarterly (Section 40.1, "Fifth-tier operations") |
| Private Key Location | Outside git working tree in `SECRETS_DIR/records-writer.pem` (mode 700 directory). **Never in any repository.** |

## Host-Custody Exception (FD-136)

Per **FD-136** (recorded 2026-10-22):
- Fifth-tier credential envelopes (`access/secrets/fifth-tier/records-writer.yaml` and siblings) specify `expected_source_host: "ops-vm-control-plane-01"`.
- Because `ops-vm-control-plane-01` does not yet exist, a deliberate, tracked exception permits custody and token minting from the designated secure operator host until the Ops VM is provisioned.
- The envelope check `access/secrets/envelope/check-envelope.sh`'s `expected_source_host` failure for this credential is expected behavior under this exception, not an untracked defect.

## Reapplication and Rebuild

Branch and tag rulesets are stored alongside this document:
- `tools/records/rulesets/records-append-only.json`
- `tools/records/rulesets/records-tags-immutable.json`

Installation token minting helper:
- `tools/records/rw-token.sh` (delegates to `tools/records/lib/mint_token.py`)
- Mints a short-lived (~1 hour) token from `SECRETS_DIR/records-writer.pem`. Holds zero secret material.
