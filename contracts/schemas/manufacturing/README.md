# contracts/schemas/manufacturing/ — RM1 schema manifest

Authoritative design: [`contracts/RM1-contract-package.md`](../../RM1-contract-package.md). The schema files
listed here are **generated to follow that design exactly** (Contract stage output); this README is the manifest,
not the schemas themselves.

Source of truth: JSON Schema draft 2020-12 (canonical-JSON instances, RFC 8785). Bindings in `contracts/python/`
and `contracts/native/` are generated from these by `tools/` — never hand-edited.

## Files to generate (each debuts at schema_version `1.0.0`)

| File | Contract | Owner | Identity fields (hash view) |
|---|---|---|---|
| `../common.schema.json` | `Ref`, `Provenance`, `ContentHash` | MP (shared) | n/a (primitives) |
| `manufacturing_request.schema.json` | `ManufacturingRequest` | MP | material, stock_form, declared_operations, quantity, tolerances, step_artifact_ref.content_hash |
| `design_input.schema.json` | `DesignInput` | MP | status, source.ref, material, stock_form, declared_operations, quantity, tolerances, design_artifact_ref.content_hash |
| `manufacturing_task.schema.json` | `ManufacturingTask` | MP | product_intent.summary, design_input_ref |
| `production_plan.schema.json` | `ProductionPlan` (+`ProcessStep`,`ResourceAssignment`) | MP | task_ref, capability_model_version, steps, resource_assignments |
| `manufacturability.schema.json` | `ManufacturabilityVerdictStatus`, `ManufacturabilityReasonCode` (closed enums) | MP | n/a (enums) |
| `manufacturing_episode.schema.json` | `ManufacturingEpisode` (data contract, Law 21) | MP | task, design_ref, status, plan.content_hash, verdict.status+reason_codes, capability_model_version |

Consumed stubs (generated under `../consumed/`, owned upstream — RM1 pins, never owns):
`consumed/velith/engineering_result.schema.json`, `consumed/noetica/verdict.schema.json`,
`consumed/noetica/provenance.schema.json`, `consumed/noetica/verifier.protocol.md`.

## Rules (from the contract package)

- Closed taxonomies (`StockForm`, `ProcessOp`, `ManufacturabilityVerdictStatus`, `ManufacturabilityReasonCode`)
  — member changes are **MAJOR**.
- Content hash = `sha256(canonical_json(identity_view))`; `produced_at`/`timing` always excluded.
- `plan_id`/`episode_id` are deterministic (`uuid5(NS_MP, content_hash)`).
- Persisted episodes never carry `INFRA_ERROR`.
- On any right-column change (see package §6): bump `schema_version`/`contracts/VERSION`, add a migration note,
  record in `CHANGELOG.md`.
