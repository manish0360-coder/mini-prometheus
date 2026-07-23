# contracts/python/ — GENERATED bindings (do not hand-edit)

Typed dataclasses + `StrEnum`s generated from `contracts/schemas/**.schema.json` by
`tools/generate_contracts.py`. **No business logic** (types only). Editing a file here by hand is a CI
failure (repository-architecture.md §13) — change the schema and regenerate.

## Regenerate

```
python3 tools/generate_contracts.py
```

Requires `datamodel-code-generator` (see `pyproject.toml` [dev]) and **Python ≥ 3.11** (uses stdlib
`StrEnum`, matching the project's `requires-python`).

## Layout (mirrors the schemas)

```
common_schema.py                              # Ref, Provenance, ContentHash, SemVer, Uuid, Rfc3339
manufacturing/manufacturing_request_schema.py # ManufacturingRequest, StockForm, ProcessOp, DeclaredOperation, …
manufacturing/design_input_schema.py          # DesignInput, EngineeringVerificationStatus, DesignSource, …
manufacturing/manufacturing_task_schema.py    # ManufacturingTask
manufacturing/production_plan_schema.py        # ProductionPlan, ProcessStep, ResourceAssignment
manufacturing/manufacturability_schema.py     # ManufacturabilityVerdictStatus, ManufacturabilityReasonCode (closed)
manufacturing/manufacturing_episode_schema.py # ManufacturingEpisode (data contract, Law 21)
consumed/noetica/verdict_schema.py            # Verdict envelope (Noetica-owned stub)
consumed/noetica/provenance_schema.py         # Noetica provenance alias
consumed/velith/engineering_result_schema.py  # EngineeringResult (Velith-owned opaque stub)
```

Native bindings (`contracts/native/`) are generated when the native crate opens (M2, benchmark-justified);
not produced for RM1 (Python-only), avoiding speculative code.
