# RM1 Contract Package — Contract Design

- **Implemented:** ✅ by **RM1** (`rm1-complete`, 2026-07-23) — bindings realized in `src/mini_prometheus/`; verified by 31 tests. See `docs/milestones/RM1-completion-report.md`.
- **Status:** ❄ **FROZEN (2026-07-23).** Ratified decisions: demonstration domain = **Machined Part**;
  `ManufacturingRequest` is the primary engineer-facing input; STEP accepted as an **opaque attachment only**;
  `NS_MP` = **`4f5b56ae-3c77-4135-9f5c-1eef0ab1b252`** (permanent). Schemas + Python bindings generated from
  this package (suite `contracts/VERSION` 0.2.0). Treat as immutable unless a critical defect is found.
- **(was) Status:** Draft — Contract stage. This document is the authoritative design the schema files and
  generated bindings follow **exactly**.
- **Derives from (frozen):** `specs/milestones/RM1-plan-verify-log.md` §6 (contracts), §5 (success criteria),
  §7 (opaque input). Does **not** change the specification.
- **Governing law:** Handbook Law 14 (interfaces semantically versioned), Law 21 (data contracts versioned
  with equal rigor + migration), Law 15 (Verifier protocol Noetica-owned, oracle domain-owned), Law 18
  (provenance first-class), Law 6 (domains never re-implement Noetica). Constitution v1.1.0.
- **Ownership convention:** *MP-owned/published* = defined and versioned here. *Consumed stub* = the shape MP
  reads from an upstream layer, pinned by RM1 until the real upstream contract is published (then replaced by
  adapter/MAJOR bump). MP never owns a consumed contract.

---

## 0. Package layout & schema manifest

```
contracts/
├── VERSION                                   # suite SemVer: 0.1.0 → 0.2.0 (adds the RM1 manufacturing set)
├── schemas/
│   ├── common.schema.json                    # Ref, Provenance, ContentHash, shared primitives
│   ├── manufacturing/
│   │   ├── manufacturing_request.schema.json
│   │   ├── design_input.schema.json
│   │   ├── manufacturing_task.schema.json
│   │   ├── production_plan.schema.json       # incl. ProcessStep, ResourceAssignment
│   │   ├── manufacturability.schema.json     # VerdictStatus + ReasonCode closed enums
│   │   └── manufacturing_episode.schema.json
│   └── consumed/
│       ├── noetica/
│       │   ├── verdict.schema.json           # Noetica-owned envelope (stub)
│       │   ├── verifier.protocol.md          # interface (not data)
│       │   └── provenance.schema.json        # Noetica-owned (stub)
│       └── velith/
│           └── engineering_result.schema.json# Velith-owned (opaque stub)
├── python/                                   # GENERATED bindings (later; no logic)
└── native/                                   # GENERATED bindings (later; no logic)
```

Source of truth: **JSON Schema draft 2020-12**. Bindings in `python/` and `native/` are generated from these
by `tools/` (never hand-edited — repository-architecture §13). Protobuf mirror is deferred (future, additive).

---

## 1. Global conventions (defined once; every contract inherits these)

These cover the *serialization*, *versioning*, and *compatibility* facets for **all** contracts; each contract
below states only its **deviations, identity fields, and frozen fields**.

### 1.1 Serialization format
- **Schema language:** JSON Schema 2020-12.
- **Instance wire/format:** **Canonical JSON (RFC 8785 / JCS)** — UTF-8, object keys sorted lexicographically,
  no insignificant whitespace, shortest round-trippable number form, `true`/`false`/`null` literals. All hashing
  and equality use the canonical form.
- **Episode store:** newline-delimited canonical JSON (**JSONL**), one record per line, append-only.
- Human-readable (pretty) JSON is permitted at rest for non-hashed docs but the **canonical form is authoritative**
  for identity.

### 1.2 Identifiers & references
- All `*_id` fields are **UUIDv4** strings, except where a field is declared **deterministic** (derived via
  `uuid5(namespace_MP, content_hash)`), which is used for `plan_id` and `episode_id` so identical inputs yield
  identical ids.
- Every cross-contract reference is a **`Ref` = `{ id: string, content_hash: ContentHash }`** ("ref-by-hash"):
  a reference is only valid if the referent's recomputed `content_hash` matches. This makes provenance
  verifiable (Law 18) and prevents silent drift.
- **`ContentHash`** = string `^sha256:[0-9a-f]{64}$`, computed as `sha256(canonical_json(identity_view))`.

### 1.3 Provenance (shared shape — `common.schema.json`)
Every derived object carries `provenance`:
```
provenance = {
  source_refs:  Ref[],           # what this was derived from (task, design_input, declared_operation…)
  rule_id:      string,          # planner/oracle rule that produced it
  rule_version: string(SemVer),
  capability_model_version: string(SemVer),
  produced_by:  { component: string, version: string(SemVer) },
  produced_at:  string(RFC3339)  # EXCLUDED from every content_hash (volatile)
}
```

### 1.4 Content-hash / identity rule
- `content_hash = sha256:` + `sha256(canonical_json(identity_view))`.
- The **identity_view** of each contract is its fields **minus** the declared *volatile/provenance* fields
  (timestamps, latencies, generated non-deterministic ids, `provenance.produced_at`). Each contract below
  names its identity fields explicitly.
- **Reproducibility (spec §5.5, mirrors Velith D16.1/D21):** identical inputs ⇒ identical identity_view ⇒
  identical `content_hash` ⇒ identical deterministic ids. A test asserts a varying `produced_at`/timing leaves
  `content_hash` unchanged.

### 1.5 Versioning strategy
- **Suite version** `contracts/VERSION` governs the whole package (pre-1.0: `0.MINOR.PATCH`, where MINOR may
  break). RM1 moves it **0.1.0 → 0.2.0** (additive: introduces the manufacturing set).
- **Per-schema version:** each schema's `$id` embeds a **major** (`…/v1/…`); each *record instance* carries a
  **`schema_version`** (full SemVer string). RM1 schemas debut at **`1.0.0`**.
- Data contracts (records that persist or cross the Experience Flow — `ManufacturingEpisode`) MUST carry
  `schema_version` for migration (Law 21). Pure in-process interface types still declare a `$id` major.

### 1.6 Compatibility policy (Law 14 + Law 21)
- **PATCH** — description/annotation only; no field/semantic change.
- **MINOR (backward-compatible)** — add an **optional** field, or add a member to a **non-identity, open** enum.
  Producers may emit it; consumers on the same major **must ignore unknown optional fields** (forward-compat).
- **MAJOR (breaking)** — remove/rename/retype a field; optional→required; change any **identity/hashed** field;
  remove an enum member; or change a **closed** taxonomy. Requires a new major `$id`, a **migration note**, and a
  deprecation window (§11.8). A change to identity fields also starts a **new hash lineage** (old hashes do not
  compare across majors).
- **Producer/consumer rules:** a producer sets `schema_version` and **never mutates a released schema in place**;
  a consumer reads against a **declared major** and tolerates unknown optional fields. An unversioned or
  unmigrated schema change is a constitutional violation (Law 14/21).
- **Closed taxonomies** (`ManufacturabilityVerdictStatus`, `ManufacturabilityReasonCode`): adding a member is a
  **MAJOR** for RM1 (they are frozen closed sets per spec §5.3), because consumers switch exhaustively on them.

---

## 2. Contract catalog (dependency order)

1. `common` (Ref, Provenance, ContentHash) — foundation.
2. **Consumed stubs:** Velith `EngineeringResult`; Noetica `Verdict`, `Verifier` protocol, `Provenance`.
3. `ManufacturingRequest` → 4. `DesignInput` → 5. `ManufacturingTask` → 6. `ProductionPlan` →
7. `Manufacturability` (enums) → 8. `ManufacturingEpisode`.

Each contract below is specified across all **seven required facets**: *ownership, schema, versioning,
invariants, validation, serialization, compatibility*. Where a facet is fully covered by §1 it says "per §1"
and states only the contract-specific part.

---

## 3. MP-owned contracts

### 3.1 `ManufacturingRequest` — the real engineer input (spec §7)

- **Ownership:** MP — manufacturing product-intent intake (Handbook §2.4 input). Published.
- **Schema:**

  | field | type | req | notes |
  |---|---|---|---|
  | `schema_version` | SemVer string | ✔ | `1.0.0` |
  | `request_id` | UUIDv4 | ✔ | |
  | `material` | string | ✔ | non-empty; free text + optional code in `material_code` |
  | `material_code` | string | ✕ | optional controlled-vocab handle |
  | `stock_form` | enum `StockForm` = {`bar`,`plate`,`sheet`,`block`,`tube`} | ✔ | RM1 minimal closed set |
  | `declared_operations` | `DeclaredOperation[]` | ✔ | ordered, **minItems 1** |
  | `quantity` | integer | ✔ | **≥ 1** |
  | `tolerances` | `{ general_tolerance_mm: number≥0 }` | ✕ | |
  | `step_artifact_ref` | `{ media_type:"model/step", id:string, content_hash:ContentHash }` | ✕ | **opaque**, never parsed (spec §7) |
  | `metadata` | object (`author`,`created_at`) | ✕ | excluded from identity |

  `DeclaredOperation = { op: ProcessOp, target?: string, params?: object }`.
  `ProcessOp` (closed enum, RM1): {`face_mill`,`drill`,`pocket_mill`,`turn`,`deburr`,`inspect`,`cut_stock`}.
- **Versioning:** per §1.5; debut `1.0.0`.
- **Invariants:** `quantity ≥ 1`; `declared_operations` non-empty; every `op ∈ ProcessOp`; `material` non-empty;
  if `step_artifact_ref` present it carries a `content_hash`.
- **Validation:** reject empty/unknown `op`; non-integer or `<1` quantity; negative tolerance; malformed
  `content_hash`. STEP bytes are **not** read (a boundary rule; enforced by the §8 boundary test in the spec).
- **Serialization:** per §1.1.
- **Identity fields:** `{material, material_code, stock_form, declared_operations, quantity, tolerances,
  step_artifact_ref.content_hash}` (excludes `request_id`, `metadata`).
- **Compatibility:** per §1.6. Frozen: `stock_form`/`ProcessOp` are **closed** (member add = MAJOR for RM1).

### 3.2 `DesignInput` — normalized opaque design carried into planning

- **Ownership:** MP. Produced by **intake** (from `ManufacturingRequest`, status `engineer_declared`) **or** by
  `integrations/velith` (from Velith `EngineeringResult`, status `velith_verified`). One contract, both paths
  (spec §7). Published.
- **Schema:**

  | field | type | req | notes |
  |---|---|---|---|
  | `schema_version` | SemVer | ✔ | `1.0.0` |
  | `design_input_id` | UUIDv4 | ✔ | |
  | `engineering_verification_status` | enum {`velith_verified`,`engineer_declared`} | ✔ | spec §5.8 |
  | `source` | `{ kind: enum{manufacturing_request,velith_engineering_result}, ref: Ref }` | ✔ | |
  | `material` / `stock_form` / `declared_operations` / `quantity` / `tolerances` | as §3.1 | ✔ | normalized planner input |
  | `design_artifact_ref` | `{ media_type, id, content_hash }` | ✕ | **opaque** (e.g. STEP or Velith artifact) |
  | `provenance` | Provenance | ✔ | |
- **Versioning:** per §1.5; `1.0.0`.
- **Invariants:** `engineering_verification_status` **consistent with** `source.kind`
  (`manufacturing_request↔engineer_declared`, `velith_engineering_result↔velith_verified`);
  `declared_operations` non-empty; opaque artifact never parsed.
- **Validation:** status/source consistency check; `source.ref.content_hash` matches the referent; normalized
  fields satisfy §3.1 constraints.
- **Serialization:** per §1.1.
- **Identity fields:** `{engineering_verification_status, source.ref, material, stock_form,
  declared_operations, quantity, tolerances, design_artifact_ref.content_hash}` (excludes `design_input_id`,
  `provenance`).
- **Compatibility:** per §1.6. `engineering_verification_status` is a **closed** enum (frozen — spec §5.8).

### 3.3 `ManufacturingTask`

- **Ownership:** MP. Published.
- **Schema:** `{ schema_version:SemVer(✔), task_id:UUIDv4(✔), product_intent:{ summary:string }(✔),
  design_input_ref: Ref (✔) }`.
- **Versioning:** per §1.5; `1.0.0`.
- **Invariants:** `design_input_ref` present with hash; `task_id` unique per task.
- **Validation:** `design_input_ref.content_hash` equals `hash(DesignInput)`; `product_intent.summary` non-empty.
- **Serialization:** per §1.1.
- **Identity fields:** `{product_intent.summary, design_input_ref}` (excludes `task_id`).
- **Compatibility:** per §1.6.

### 3.4 `ProductionPlan` (+ `ProcessStep`, `ResourceAssignment`) — the tangible artifact

- **Ownership:** MP — manufacturing content ("the heart", §2.4). Published.
- **Schema:**

  `ProductionPlan`:
  | field | type | req | notes |
  |---|---|---|---|
  | `schema_version` | SemVer | ✔ | `1.0.0` |
  | `plan_id` | UUIDv4 **deterministic** = `uuid5(NS_MP, content_hash)` | ✔ | reproducible (§1.2) |
  | `task_ref` | Ref | ✔ | |
  | `steps` | `ProcessStep[]` | ✔ | **minItems 1**, ordered |
  | `resource_assignments` | `ResourceAssignment[]` | ✔ | may be empty only if plan is NOT_MANUFACTURABLE-bound |
  | `capability_model_version` | SemVer | ✔ | model that produced/validates the plan |
  | `content_hash` | ContentHash | ✔ | over identity view |
  | `provenance` | Provenance | ✔ | |

  `ProcessStep = { index:int≥0, op:ProcessOp, required_capability:string(non-empty), inputs:string[],
  params?:object, provenance_ref: Ref }`.
  `ResourceAssignment = { step_index:int, resource_id:string, capability_id:string }`.
- **Versioning:** per §1.5; `1.0.0`.
- **Invariants:** `steps` non-empty; `index` values are **contiguous 0..n−1** in array order; every step has a
  non-empty `required_capability` and a `provenance_ref`; every `resource_assignment.step_index` refers to an
  existing step and its `capability_id` satisfies that step's `required_capability`; RM1 precedence is the linear
  step order; `content_hash` equals recomputation; `plan_id == uuid5(NS_MP, content_hash)`.
- **Validation:** contiguity check; capability non-empty; `provenance_ref` resolves to a `declared_operation` in
  the `DesignInput`; assignment references valid; hash recomputation matches.
- **Serialization:** per §1.1.
- **Identity fields:** `{task_ref, capability_model_version, steps(op, required_capability, inputs, params,
  provenance_ref.id+hash), resource_assignments}` — **excludes** `plan_id` (derived), `content_hash` (self),
  `provenance` timing.
- **Compatibility:** per §1.6. Changing the identity set (e.g. adding a hashed step field) = MAJOR + new lineage.

### 3.5 `Manufacturability` — verdict status & reason codes (MP content in Noetica's envelope, Law 15)

- **Ownership:** MP owns the **domain taxonomy** (Law 15: concrete oracle + its outcome vocabulary are
  domain-owned); the `Verdict` **envelope** is Noetica's (§4.2). Published.
- **Schema (closed enums):**
  - `ManufacturabilityVerdictStatus` = {`MANUFACTURABLE`, `NOT_MANUFACTURABLE`, `PLAN_INVALID`, `INFRA_ERROR`}
    — **exactly** spec §5.3; frozen. Outcome/error split (mirrors Velith D16.7): `MANUFACTURABLE`,
    `NOT_MANUFACTURABLE`, `PLAN_INVALID` are **grounded outcomes** (success exit, episode written);
    `INFRA_ERROR` is the **only error** (non-zero exit, **no** episode).
  - `ManufacturabilityReasonCode` = {`CAPABILITY_MISSING`, `PRECEDENCE_VIOLATION`, `RESOURCE_UNAVAILABLE`,
    `TOLERANCE_UNSUPPORTED`, `MATERIAL_UNSUPPORTED`, `PLAN_MALFORMED`} — closed.
- **Versioning:** per §1.5; `1.0.0`.
- **Invariants:** a `NOT_MANUFACTURABLE`/`PLAN_INVALID` verdict carries **≥1** reason code; `MANUFACTURABLE`
  carries none; reason codes ∈ closed set.
- **Validation:** status ∈ set; reason-code presence rule above; unknown member ⇒ schema-invalid.
- **Serialization:** per §1.1 (string enums).
- **Compatibility:** **closed taxonomy** — any member add/remove = **MAJOR** (§1.6). This is deliberate: the spec
  froze the status set.

### 3.6 `ManufacturingEpisode` — Experience-Flow **data contract** (Law 21)

- **Ownership:** MP **produces** the content (Handbook §2.4 "emit the Experience Flow"); Noetica owns the
  **lifecycle framework** (retention/compression) — **deferred**, not consumed by RM1. Published data contract.
- **Schema:**

  | field | type | req | notes |
  |---|---|---|---|
  | `schema_version` | SemVer | ✔ | `1.0.0`; **migration key** (Law 21) |
  | `episode_id` | UUIDv4 **deterministic** = `uuid5(NS_MP, content_hash)` | ✔ | |
  | `task` | `ManufacturingTask` (embedded) | ✔ | |
  | `design_ref` | Ref | ✔ | |
  | `engineering_verification_status` | enum (as §3.2) | ✔ | honesty (spec §5.8) |
  | `plan` | `ProductionPlan` (embedded) | ✔ | |
  | `verdict` | Noetica `Verdict` (§4.2) w/ MP status/reasons | ✔ | |
  | `capability_model_version` | SemVer | ✔ | |
  | `content_hash` | ContentHash | ✔ | |
  | `provenance` | Provenance | ✔ | |
  | `timing` | `{ created_at:RFC3339, plan_ms:number, verify_ms:number }` | ✔ | **EXCLUDED from hash** |
- **Versioning:** per §1.5; `1.0.0`. As a persisted/upward data contract, schema changes require a **migration
  path** (Law 21).
- **Invariants:** `content_hash` recomputes; `verdict.status` ∈ taxonomy; **persisted episodes never carry
  `INFRA_ERROR`** (that path writes no episode); `engineering_verification_status` equals the plan's design
  status; `plan.task_ref` equals `hash(task)`.
- **Validation:** hash recomputation; verdict/design consistency; `schema_version` present and known.
- **Serialization:** **JSONL** append-only (per §1.1); each line one canonical-JSON episode.
- **Identity fields:** `{task identity, design_ref, engineering_verification_status, plan.content_hash,
  verdict.status + sorted reason_codes, capability_model_version}` — **excludes** `episode_id`, `content_hash`
  (self), `timing`, `provenance` timing (mirrors Velith D21).
- **Compatibility:** Law 21 — additive optional field = MINOR (no migration); any change to identity/required
  fields or `timing` semantics = MAJOR + migration + `schema_version` bump; consumers read against declared major.

---

## 4. Consumed contract stubs (Noetica/Velith — MP owns none of these)

RM1 depends on the **contract shape**, not the published package (spec §7). Each stub is pinned by RM1 and
**replaced by the real upstream contract** when published (via `integrations/` adapter, or a MAJOR bump with
migration). RM1 code imports the stub only.

### 4.1 Velith `EngineeringResult` / `DesignArtifact` (Velith-owned; opaque to MP)
- **Ownership:** Velith. **Schema (stub, read-only):** `{ result_id, content_hash, verified:true,
  verifier:{id,version}, design_artifact:{ media_type, ref, content_hash } }`. MP reads `result_id`,
  `content_hash`, `verified`, and the **opaque** `design_artifact`; MP **never parses** the artifact and **never
  re-verifies** (Law 6/9).
- **Versioning/serialization/compatibility:** owned upstream; RM1 pins one major; when real Velith publishes,
  the `integrations/velith` adapter maps real → this stub (or the stub is retired via MAJOR + migration).
- **Invariants (as consumed):** `verified == true` is required for the `velith_verified` path; `content_hash`
  present.

### 4.2 Noetica `Verdict` (Noetica-owned envelope; Law 15)
- **Ownership:** Noetica. **Schema (stub):** `{ grounded:bool, is_error:bool, status:string, reason_codes:
  string[], detail?:string, produced_by:{component,version} }`. MP fills `status`/`reason_codes` from its
  **own** closed taxonomies (§3.5). The **outcome/error distinction** (`is_error`) is Noetica's envelope
  semantics; RM1 maps `INFRA_ERROR → is_error:true` (no episode), all others `is_error:false`.
- **Compatibility:** owned upstream; RM1 pins one major; MP must not extend the envelope (Law 6).

### 4.3 Noetica `Verifier` protocol (interface, not data; Law 15)
- **Ownership:** Noetica owns the **protocol**; MP owns the **concrete oracle** implementing it.
- **Interface (stub, `verifier.protocol.md`):** `verify(plan: ProductionPlan, capability_model) -> Verdict`,
  pure/deterministic for RM1 (spec §9). MP's manufacturability oracle **implements** this signature; a
  protocol-conformance test asserts it (spec §5.6).
- **Compatibility:** protocol signature changes are upstream MAJOR events; RM1 pins one major.

### 4.4 Noetica `Provenance` (Noetica-owned; Law 18)
- **Ownership:** Noetica. RM1 populates the shape in §1.3 as **content**; it does **not** implement a provenance
  engine/store (Law 6). Pinned stub; real Noetica provenance contract replaces it later.

---

## 5. Cross-contract invariants (must hold across the package)

1. `DesignInput.engineering_verification_status` ⇔ `DesignInput.source.kind` (§3.2).
2. `ManufacturingTask.design_input_ref.content_hash == hash(DesignInput)`.
3. `ProductionPlan.task_ref.content_hash == hash(ManufacturingTask)`.
4. Every `ProcessStep.provenance_ref` resolves to a `declared_operation` present in the `DesignInput`.
5. `capability_model_version` is **identical** across `ProductionPlan`, the `Verdict` producer, and the
   `ManufacturingEpisode`.
6. `ManufacturingEpisode.plan.content_hash == hash(ProductionPlan)` and `.design_ref == task's design ref`.
7. `engineering_verification_status` is carried **unchanged** from `DesignInput` → `ProductionPlan.provenance`
   → `ManufacturingEpisode` (honesty chain, spec §5.8, Law 18).
8. **No `INFRA_ERROR` episode is ever persisted** (spec §5.3; §3.6 invariant).
9. Reproducibility: identical `ManufacturingRequest`(or Velith result) + identical `capability_model_version`
   ⇒ identical `content_hash` at every stage and identical deterministic ids (spec §5.5).

---

## 6. Change-control matrix (what implementation may / may not change)

| May change freely (internal, not a contract) | May change only via version bump + migration |
|---|---|
| `ProcessCapabilityModel` representation | any published schema field, type, or requiredness |
| deterministic planner rules; oracle check logic | the identity/hashed field set of any contract (MAJOR + new hash lineage) |
| generated `python/`/`native/` bindings | the closed taxonomies `StockForm`, `ProcessOp`, `ManufacturabilityVerdictStatus`, `ManufacturabilityReasonCode` (MAJOR) |
| non-contract helper structures | canonicalization / content-hash rule (§1.1/§1.4) — MAJOR, ecosystem-wide |
| episode store *file layout* (path/rotation) | the `ManufacturingEpisode` data contract (Law 21 migration) |

Any change in the right column is a versioned event (Law 14/21) recorded in `CHANGELOG.md` + `contracts/VERSION`;
a change to a **consumed** stub is driven by the upstream owner, mapped in `integrations/`.

---

## 7. Traceability

| Contract | RM1 spec | Handbook |
|---|---|---|
| ManufacturingRequest, DesignInput | §6, §7 | §2.4 (product-intent intake) |
| ManufacturingTask, ProductionPlan | §4, §6 | §2.4 (`ManufacturingTask`,`ProductionPlan`) |
| Manufacturability enums, Verdict | §5.3, §6 | Law 15 |
| ManufacturingEpisode | §6, §5.7 | Law 21, §11.11 |
| Consumed Velith/Noetica stubs | §6, §7 | Law 6/9/14/15 |
| content-hash / determinism | §5.5 | Velith D16.1/D21 (precedent) |

## 8. Open items (for the owner; do not block schema generation)

1. **Namespace UUID (`NS_MP`)** for deterministic ids — assign a fixed project UUID constant (recorded in
   `common.schema.json` description). Recommendation: generate once and freeze.
2. **`ProcessOp` / `StockForm` initial members** — the RM1 closed sets above are minimal for a machined-part
   demonstration (§13 of the spec). Confirm the demonstration domain (machined part vs. PCB) so the enum members
   are right the first time (a later domain = MAJOR on these closed enums).
3. **Canonical JSON library choice** is an implementation detail (RFC 8785); the *rule* is fixed here.

---

*Contract stage. Defines every RM1 contract across ownership, schema, versioning, invariants, validation,
serialization, and compatibility. No code, no schema bodies, no bindings. Implementation generates the schema
files and bindings to follow this package exactly, then proceeds Implementation → Testing → Verification.*
