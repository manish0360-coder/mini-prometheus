# MP-S1 Specification — Declared Shop Capability Model

- **Status:** ✏️ **DRAFT, revision 2, for final Research Director review and owner authorisation.**
  - Not frozen. **Not authorised for implementation.**
  - Revision 1 (2026-11-06) was reviewed by the Research Director (preliminary independent review, 2026-11-06).
    That review accepted D1–D4 conditionally and required ten revisions. Revision 2 applies them; see §0.
  - AI-authored; the owner ratifies (Law 22).
- **Milestone:** MP-S1 (name accepted, D4). **ADR reserved:** 0022. **Baseline:** `main` @ `ee46767`.
- **Layer:** Mini Prometheus (Layer 4, manufacturing content). Constitution v1.1.0. Ownership per CAP-0001 (affirmed in
  ADR-0021, Q1).
- **Identity:** an engineer can declare their shop in a validated, versioned file:
  - machines and their capabilities;
  - the mapping from operations to capabilities;
  - materials, tolerance minimums and operation precedence;
  - what the shop deliberately cannot do;
  - who declared it and on what basis.

  Every plan made under that file carries two identities:
  - a **semantic shop content hash**, which identifies the capability basis;
  - a **shop declaration hash**, which identifies that basis together with its evidence class and declaration
    provenance.

  As a result, no change to content, evidence or declaration can cause a stale reuse.
- **Immovable:**
  - RM1–RM14 behaviour and RM8's 902-request corpus stay as they are.
  - The hard-coded `default_model()` and `constrained_model()` stay byte-identical, and all goldens and tagged
    evidence are preserved.
  - No new `ProcessOp`, verdict status or reason code.
  - The verdict contract is a consumed Noetica stub and is not extended.
  - Nothing changes in `precedent/`, `judgment/` or `experiment/`.
  - No geometry, feature recognition, Velith integration, Noetica reconstruction, or manufacturing optimisation.
- **Evidence (owner ruling Q5):**
  - Acceptance uses **synthetic** shop files only.
  - A `public_specification` file may be used, but always with that label.
  - No MP-S1 test or document claims real-shop validation. MP-E1 stays blocked.

---

## 0. Revision 2 change log (Research Director review, 2026-11-06)

| # | Required revision | Where addressed |
|---|---|---|
| R1 | Separate the semantic `shop_content_hash` from human-readable labels | §3.2: the content hash excludes `model_version`, evidence, declaration and notes |
| R2 | Bind evidence class and declaration provenance into downstream identity | §3.2 `shop_declaration_hash`; §3.3: plan ref, reuse key and schedule |
| R3 | Allow intentional unsupported capabilities; distinguish them from identifier errors | §3.1 explicit `unsupported_ops` and `unsupported_capabilities`; §3.2 refusal codes for undeclared gaps |
| R4 | Reject cyclic precedence | §3.1, §3.2 `PRECEDENCE_CYCLE` |
| R5 | Machine-specific material compatibility | §4.1: documented limitation, not modelled |
| R6 | Define `evidence_class` precisely; `shop_declared` never implies verification | §3.4 |
| R7 | Preserve RM1–RM14 and the RM8 902-request corpus | §7 AC1, AC2; §8 |
| R8 | Test changed materials, tolerances, capabilities and evidence against stale reuse | §7 AC4; §8 rows T4.x |
| R9 | Plans, verdicts, episodes and schedules carry the correct shop identity | §3.3; §7 AC7; §8 rows T7.x |
| R10 | Scope limited to shop capability declaration | §4 |

Also changed from revision 1:
- The content hash no longer includes the label or the evidence class (R1).
- Declared intent is explicit (R3), so unprovided capabilities, unreferenced capabilities and unmapped operations are
  now **refused unless declared**. Revision 1 accepted them with diagnostics.
- Failures use a closed issue-code taxonomy (D3 condition).
- Schedules carry the shop reference explicitly (R9).

## 1. Problem (evidence)

1. **A user cannot describe their shop.** The only capability models are two Python functions,
   `default_model()` and `constrained_model()`. Both CLIs offer `--capability-model {default,constrained}` only
   (`orchestration/runner.py` l.126–127, `schedule_runner.py` l.243–244).
2. **The model's identity is a hand-assigned label.** `MODEL_VERSION = "1.0.0"` and `"1.1.0"` are constants that are
   not derived from the model content (`capability_model.py` l.36–38). `with_unavailable_resources()` keeps the label
   by design (l.149–163). The label is the only basis identity that the RM2 reuse key
   (`experience/episode_index.py` l.13–27) and the scheduler checker (`checker.py` l.270–276) compare.
3. **A changed shop silently reuses a stale verdict. This was demonstrated on 2026-11-06.**
   - Method: a read-only probe in the Docker verifier at `ee46767`, using the RM1 bracket request (`Aluminum 6061`).
   - Model A = `default_model()`. Model B = A minus both aluminium materials. Both are labelled `1.0.0`.

   ```
   run 1 under A (run_with_reuse)        → MANUFACTURABLE, reused=False   (episode stored)
   fresh run under B (runner.run)        → NOT_MANUFACTURABLE [MATERIAL_UNSUPPORTED]
   run 2 under B (run_with_reuse, guard) → MANUFACTURABLE, reused=True     ← stale
   ```

   The reproducibility guard (`reuse_runner.py`) re-derives only the **plan**. Materials, tolerance minimums and
   declared precedence change the **verdict** without changing the plan, so the guard passes. This is the Case 3
   hazard from `docs/research/next-capability-gap-assessment.md` (addendum A3).

## 2. Objective

1. Load a shop capability model from a JSON file that is schema-validated, semantically checked and canonicalised.
2. Derive a semantic `shop_content_hash` and a `shop_declaration_hash` from it.
3. Carry both, with the evidence class, on every plan, and through the plan on episodes and schedules.
4. Make RM2 reuse and scheduling distinguish any two declarations that differ in content, evidence or declaration
   provenance.

## 3. Scope

### 3.1 New data contract: `ShopCapabilityModel` (schema `1.0.0`)

New file `contracts/schemas/manufacturing/shop_capability_model.schema.json`. It is MP-owned input and closed
(`additionalProperties: false` at every level).

| Field | Type | Rule |
|---|---|---|
| `schema_version` | SemVer | Exactly `"1.0.0"`. Anything else gives `UNSUPPORTED_SCHEMA_VERSION`. |
| `model_version` | SemVer | Human-readable label. It flows into `capability_model_version` as today. **Not part of the content hash.** |
| `evidence_class` | enum | `synthetic` \| `public_specification` \| `shop_declared`, defined in §3.4 |
| `declaration` | object | `declared_by` (string ≥ 1, a person or role), `declared_on` (RFC 3339 date), `sources` (array of strings; **≥ 1 required for `public_specification`**) |
| `notes` | string, optional | Free text. Excluded from **both** hashes. |
| `resources` | array, ≥ 1 | `{resource_id, capabilities[≥1]}`. `resource_id` matches `^[A-Za-z0-9][A-Za-z0-9_.-]*$`, so it has **no colon**, because the CLIs use `MACHINE:START:END` and `MACHINE:OP:OP:MIN`. |
| `op_capability` | object | Keys are `ProcessOp` values; each value is a capability id matching `^[a-z][a-z0-9_.-]*$` |
| `unsupported_ops` | array, optional | `ProcessOp` values the shop deliberately does not perform |
| `unsupported_capabilities` | array, optional | Capabilities mapped from an op that the shop deliberately has no machine for |
| `supported_materials` | array, ≥ 1 | Non-empty strings, unique case-insensitively (matching is case-insensitive in `material_supported`). Shop-wide; see §4.1. |
| `capability_tolerance_mm` | object, optional | Capability id → number > 0 and finite. Keys must be capabilities named in `op_capability`. |
| `ordering_constraints` | array, optional | `[before_op, after_op]` pairs of `ProcessOp`. No self-pairs, no duplicates, and **acyclic**. |

`unavailable_resources` is deliberately absent: it stays a per-run RM9 input (`--unavailable-resource`).

**Declared intent must be complete (R3).** These rules separate a deliberate gap from a typo:

- Every `ProcessOp` must appear in exactly one of `op_capability` or `unsupported_ops`. This **refuses an undeclared
  missing op.**
- Every capability in `op_capability` values must be either provided by at least one resource or listed in
  `unsupported_capabilities`, but not both. This **refuses an unprovided capability that was not declared**.
- Every capability a resource lists must be referenced by `op_capability`. This **refuses an unreferenced capability**,
  for example a typo such as `cap.mil`.
- Every entry in `unsupported_capabilities` must be referenced by `op_capability`. This refuses a declaration that
  doesn't match any mapping.

**Outcomes under declared gaps.** These are the existing behaviour; nothing new reaches the verdict taxonomy:

- A request using an op in `unsupported_ops` maps to today's `UNSUPPORTED_OP:<op>` sentinel capability. The verdict
  is `NOT_MANUFACTURABLE [CAPABILITY_MISSING]` (`capability_for_op`, `oracle.verify`).
- A request using an op whose capability is in `unsupported_capabilities` gives the same verdict through the
  no-provider path (`resource_for_capability is None`).

### 3.2 Loader, issue codes and identities

New module `manufacturing_constraints/shop_model.py`, part of the content package. It is a pure function of a parsed
document, with no file I/O and no defaults.

**Loading.** `load_shop_model(document) -> ProcessCapabilityModel` runs in this order:
1. Schema validation through the existing registry: `_validate._registry()`, a documented private reuse (D3).
2. The semantic rules in §3.1.
3. Canonicalisation:
   - resources sorted by id, with capability lists sorted and de-duplicated;
   - materials sorted as declared;
   - `unsupported_*` lists sorted;
   - ordering pairs sorted;
   - tolerances kept as JSON numbers.
4. Construction of the **existing** `ProcessCapabilityModel`. There is no second model type (Law 13).

**Typed failures (D3 condition).**
- Any violation raises `InvalidShopModelError(ValueError)`. It carries a **sorted, complete** list of
  `(ShopModelIssueCode, path, detail)`, not just the first issue, so the same document always gives the same error.
- `ShopModelIssueCode` is a closed internal enum. It is not a cross-layer contract.

| Issue code | Triggered by |
|---|---|
| `SCHEMA_VIOLATION` | any JSON-schema failure, with its JSON path |
| `UNSUPPORTED_SCHEMA_VERSION` | `schema_version` ≠ `1.0.0` |
| `DUPLICATE_RESOURCE` | repeated `resource_id` |
| `DUPLICATE_MATERIAL` | case-insensitive duplicate material |
| `OP_UNDECLARED` | a `ProcessOp` in neither `op_capability` nor `unsupported_ops` |
| `OP_CONTRADICTORY` | an op in both |
| `CAPABILITY_UNPROVIDED_UNDECLARED` | a mapped capability with no provider that is not in `unsupported_capabilities` |
| `CAPABILITY_CONTRADICTORY` | a capability both provided and declared unsupported |
| `CAPABILITY_UNREFERENCED` | a resource or `unsupported_capabilities` entry that no op maps to |
| `TOLERANCE_INVALID` | value ≤ 0 or not finite |
| `TOLERANCE_UNKNOWN_CAPABILITY` | key not in `op_capability` values |
| `PRECEDENCE_SELF_PAIR`, `PRECEDENCE_DUPLICATE`, `PRECEDENCE_CYCLE` | ordering rules (R4) |
| `DECLARATION_SOURCES_MISSING` | `public_specification` with no `sources` |

**No silent fallback.** No API or CLI path substitutes `default_model()` when a file is given and fails. The CLI exits
with code 2, writes no episode, and creates no store path.

**Two identities (R1, R2).** Both use the existing `_hashing.content_hash` over canonical JSON.

- `shop_content_hash = content_hash(semantic view)`.
  - The semantic view is `schema_version`, `resources`, `op_capability`, `unsupported_ops`,
    `unsupported_capabilities`, `supported_materials`, `capability_tolerance_mm` and `ordering_constraints`, all
    canonicalised.
  - It **excludes** `model_version`, `evidence_class`, `declaration` and `notes`.
  - It answers "what capability basis is this?". Two declarations of the same shop content share it, whatever their
    labels or evidence.
- `shop_declaration_hash = content_hash({shop_content_hash, model_version, evidence_class, declaration})`.
  - It excludes only `notes`.
  - It answers "which declaration of that basis is this?". Any change to content, label, evidence class, declarer,
    date or sources changes it.

**Model carriage.**
- `ProcessCapabilityModel` gains one optional field, defaulted to `None`: `source: ShopModelSource | None`. It holds
  `(shop_content_hash, shop_declaration_hash, evidence_class)`.
- The code models leave it `None`.
- `with_unavailable_resources()` keeps `source` (via `dataclasses.replace`). Availability is a per-run input recorded in
  the plan params (RM9); it is not part of the declaration.

### 3.3 Binding the shop identity to every output (R2, R9)

| Artifact | How it carries the shop identity | Code models (`source is None`) |
|---|---|---|
| **ProductionPlan** | New optional `capability_model_ref: {shop_content_hash, shop_declaration_hash, evidence_class}` (D1). Plan `schema_version` becomes `"1.1.0"` only when the ref is present. `plan_identity` already hashes every non-volatile field, so the ref is part of the plan's `content_hash`. `_hashing.py` is unchanged. | Field absent; `"1.0.0"`; byte-identical |
| **Verdict** | Verdict is a **consumed Noetica stub** (`consumed/noetica/verdict.schema.json`) and is not extended (Law 15). It is bound to the shop only **through the episode**, which pairs it with the plan content hash and therefore the ref. The oracle computes it from `(plan, model)`, where the plan carries the ref. AC7 tests that the stored verdict equals a fresh verdict under the declared model. | Unchanged |
| **ManufacturingEpisode** | No schema change. `episode_identity` already includes `plan.content_hash`, so the episode hash binds the declaration. `episode_store_reader` reads the optional plan ref so stored plans round-trip exactly. | Unchanged |
| **RM2 reuse** | `ReuseKey = (design_input_identity_hash, capability_model_version, shop_declaration_hash \| None)`. `design_input_key(di, version, *, shop_declaration_hash=None)` keeps its positional signature, so the existing RM2 tests run unchanged. Any change in content, evidence or declaration is a **miss**, followed by a re-plan (D2). | Third element `None`; behaviour unchanged |
| **MultiJobSchedule** (internal, not a contract) | `schedule_input_identity` already includes each job's plan hash. In addition, the schedule records `shop_model_ref` explicitly. It enters the identity and the digest **only when present**, as RM12 downtime and RM14 setups did. The independent checker re-derives it from the job plans and refuses mixed sets (refs differ, or a ref is mixed with none) as `METADATA_MISMATCH`. | Field absent; every RM11–RM14 identity and digest byte-identical |

### 3.4 `evidence_class`: precise definitions (R6)

The field records **who asserted the declaration and on what basis**. It never records that anyone checked it.
Mini Prometheus cannot check any declaration against a physical shop.

| Value | Definition | Requirement | Use in MP-S1 |
|---|---|---|---|
| `synthetic` | Invented to exercise software. It describes no real shop. | none | All acceptance fixtures |
| `public_specification` | Derived by the declarer from published machine or material data. It describes no specific shop's actual equipment or condition. | `declaration.sources` ≥ 1, citing the publications | Allowed, labelled; at most an illustrative fixture |
| `shop_declared` | Asserted by a person on behalf of a real shop about that shop's equipment. **Unverified by Mini Prometheus or any independent party.** | `declared_by`, `declared_on` | Schema-accepted; **no MP-S1 fixture, test claim or document uses it as evidence** |

**Presentation rule.**
- CLI output prints the shop identity as `shop model <shop_declaration_hash> (<evidence_class>, declared by <declared_by> on <declared_on>; not independently verified)`.
- The same wording goes in CLI help, the ADR and the completion report.
- No output may use the words "verified" or "validated" about a shop declaration.

### 3.5 CLI

- Both `runner` and `schedule_runner` gain `--capability-model-file PATH`.
  - It is mutually exclusive with `--capability-model`; giving both is an argument error.
  - It combines with `--unavailable-resource`, `--downtime`, `--setup`, `--setup-default` and `--rule`.
- File reading and JSON parsing live in `orchestration/`. A missing file, invalid JSON or `InvalidShopModelError`
  exits with code 2, prints every issue code with its path, and writes nothing.
- Tolerances: when the loaded model has tolerance data, the runner reads `tolerances.general_tolerance_mm`, as
  `constrained` mode does. The documented RM8 limitation of the default CLI stays unchanged.

### 3.6 Fixtures (all `synthetic`)

`tests/fixtures/shop_models/`:
- `default_1.0.0.json` expresses `default_model()` exactly: all seven ops mapped, all capabilities provided, no
  `unsupported_*`.
- `constrained_1.1.0.json` expresses `constrained_model()` exactly.
- `three_cell_synthetic.json` is a small shop that differs on purpose: two mills, `turn` in `unsupported_ops`, and a
  reduced material list.
- The `variants/` folder holds single-field mutations of `default_1.0.0.json` for AC4: material removed, tolerance
  tightened, capability removed, precedence added, evidence class changed, declarer changed, label changed, and notes
  changed.
- The `invalid/` folder holds one fixture per `ShopModelIssueCode`.

## 4. Explicit exclusions (R10)

Out of scope:
- geometry and STEP parsing;
- feature recognition and feature-to-operation reasoning (MP-F1);
- Velith integration (RM6), Noetica reconstruction or adapters (RM7);
- optimisation of routing, cost, time or scheduling;
- new operations, tools, fixtures, work-holding, machine envelopes or rates;
- machine state over time, calendars, or availability in the file;
- persistence or registries of shop files;
- migrating the code models to file loading;
- RM3/RM4 awareness of shop basis (§4.2);
- real-shop evaluation (MP-E1, blocked).

### 4.1 Documented limitation: material compatibility is shop-wide (R5)

- `supported_materials` is a single shop-wide list, exactly as in today's model. The oracle's material check
  (`material_supported`) asks whether the shop processes the material. It does **not** ask whether the assigned machine
  can process it.
- So a declaration in which one machine cannot cut a listed material is **not expressible**. A verdict may be
  `MANUFACTURABLE` even though the assigned machine could not process the material.
- MP-S1 states this limitation in the schema description, CLI help, ADR and completion report.
- Making material compatibility machine-specific would change oracle and planner semantics and break the code-model
  equivalence (AC2). It is a candidate follow-up, not MP-S1 scope.
- Adding an unenforced per-machine field now was rejected: it would look like a check that does not happen.

### 4.2 Documented limitation: precedent and judgment are basis-agnostic

- RM3 retrieval and RM4 judgment (byte-frozen at `rm4-complete`) may surface a precedent made under a different
  shop declaration.
- After MP-S1 the basis is visible on every stored plan (`capability_model_ref`), so a later milestone can qualify such
  precedents using `shop_content_hash`.
- MP-S1 does not.

## 5. Architecture review

- **Ownership:** a shop's declared manufacturing capability is manufacturing content (Handbook §2.4). It is not
  Noetica state-substrate machinery and not Velith engineering content.
- **Placement:**
  - The pure loader goes in `manufacturing_constraints/`. File I/O and the CLI go in `orchestration/`.
  - The existing import-linter contracts already forbid `manufacturing_constraints` from importing orchestration,
    integrations or intake.
  - There are no new edges between existing packages.
  - The planner imports `CapabilityModelRef` from `contracts.python.manufacturing.production_plan_schema` directly, as
    RM3/RM4 do for `PrecedentReport`. So `_contracts.py` stays frozen.
- **No duplicated abstraction (Law 13):** one model type, one hashing mechanism, one schema registry.
- **Data contract law (Law 21):**
  - The new schema is versioned.
  - The plan change is additive and optional.
  - Every 0.4.0 document validates unchanged under 0.5.0.
  - An absent ref means a code model identified by label only.
- **Determinism:** loading and both hashes are pure functions of the document.
- **Rejected alternatives:**

| Alternative | Why rejected |
|---|---|
| Encode the hash in `capability_model_version` | The SemVer pattern forbids build metadata |
| Put the hash in `provenance.source_refs` | Provenance is excluded from plan identity |
| Put the ref in `ProcessStep.params` | It still changes `contracts/` for the shop schema, so it saves no governance, and it repeats one fact on every step |
| Define the shop format in code only | Breaks contract-first and Law 21 |
| One hash only | Either labels and evidence leak into the basis identity (fails R1), or evidence changes can be reused stale (fails R2) |
| Hash the code models | Changes every golden |

## 6. D1–D4 decision mapping

| Decision | Research Director ruling | How revision 2 satisfies it |
|---|---|---|
| **D1** Contract 0.5.0 | Accept conditionally: preserve 0.4.0 compatibility, existing semantics and generated-binding consistency | The suite becomes 0.5.0 with additive changes only: one new schema and one optional `ProductionPlan` property. Every 0.4.0 schema file except `production_plan.schema.json` stays byte-identical. Every 0.4.0 instance validates under 0.5.0 (AC8). Regenerated bindings for unchanged schemas are byte-identical, and the drift check is green. |
| **D2** RM2 byte-freeze | Accept conditionally: evolve only the necessary gate; preserve tagged evidence; equivalent behavioural protection; no weakening of RM2, RM8 or goldens | Exactly one file leaves the byte-diff set (`reuse_runner.py`). It is replaced by a **pinned-content gate**: the file's LF-normalised sha256 must equal one pinned digest, which is the ratified version with the one-line key change. The ADR records that version's diff against `rm2-complete`. RM2 tests and AC4 are added on top. Tags, golden files and probes are never regenerated (§9). |
| **D3** Schema registry | Accept: reuse the registry; deterministic typed failures; no silent default fallback | §3.2: registry reuse; closed `ShopModelIssueCode`; complete sorted issue lists; no fallback; CLI exit code 2 with no writes (AC5) |
| **D4** Naming | Accept MP-S1, reserve ADR-0022 | Used throughout; ADR-0022 at implementation |

## 7. Acceptance criteria (falsifiable)

1. **AC1, history preserved (R7).** With no `--capability-model-file`, every behavioural golden is byte-identical:
   - the RM8 902-plan default golden (library and legacy-CLI digests);
   - the RM10 golden, the RM11 golden, RM12 downtime, the RM13 135-instance corpus and RM14 changeover;
   - the full suite.

   The only assertions that change are the contract-tree and `VERSION` pins, and only as specified in §9.
2. **AC2, file equivalence.** For **each of the 902 requests** in the RM8 golden corpus, loading `default_1.0.0.json`
   gives the same verdict status, reason codes and `produced_by` as `default_model()`. Each plan is identical to the
   golden plan apart from `capability_model_ref`, plan `schema_version` and the resulting hash. For the same 902
   requests, `constrained_1.1.0.json` gives the same verdicts, reason codes and `produced_by` as
   `constrained_model()`. Both sides are computed live in the test, because no frozen golden exists for the
   constrained model (`tests/rm8_behavior_probe.py` pins the default model only).
3. **AC3, two identities.**
   - Permuting keys, lists or whitespace leaves both hashes unchanged (property-tested).
   - Editing `notes` leaves both unchanged.
   - Editing `model_version`, `evidence_class` or any `declaration` field changes `shop_declaration_hash` only.
   - Editing any semantic field changes both.
4. **AC4, no stale reuse (R8).** A two-run protocol for each `variants/` fixture V of `default_1.0.0.json`:
   - run 1: `run_with_reuse` under the base file. The base is `default_1.0.0.json`, so the tolerance and precedence
     variants **add** a constraint;
   - run 2: `run_with_reuse` under V, with the same request and store;
   - then a reference run: `runner.run` under V with a fresh store.

   Run 2 must equal the reference run in status and reason codes, with `reused=False`:

   | Variant | Expected run 2 |
   |---|---|
   | material removed (the §1.3 case) | `NOT_MANUFACTURABLE [MATERIAL_UNSUPPORTED]` |
   | tolerance minimum added on `cap.mill` (0.005 mm), under a request declaring `general_tolerance_mm` 0.01 with a milling op | `NOT_MANUFACTURABLE [TOLERANCE_UNSUPPORTED]` |
   | capability moved to `unsupported_capabilities` | `CAPABILITY_MISSING` |
   | precedence pair added that the request violates | `PLAN_INVALID [PRECEDENCE_VIOLATION]` |
   | evidence class changed | the same verdict as run 1, but **re-planned** (`reused=False`) and the plan ref carries the new class |
   | declarer or date changed | the same verdict, re-planned |
   | label only | the same verdict, re-planned; the conservative miss is accepted |
   | notes only | **reused** (`reused=True`), because notes are not identity |

   A companion test pins **today's** stale hit for code-level models with equal labels and `source=None`, and labels it
   legacy label-only identity. MP-S1 does not change code-model reuse.
5. **AC5, typed fail-closed.**
   - Each `invalid/` fixture raises `InvalidShopModelError` containing exactly its expected issue code(s), in a
     deterministic order.
   - The CLI exits with code 2, writes no episode, and creates no store path.
   - A spy asserts that `default_model()` is never called on that path.
6. **AC6, evidence wording.**
   - Plans carry `capability_model_ref.evidence_class`.
   - Both CLIs print the §3.4 line, including "not independently verified".
   - A test asserts that no fixture uses `shop_declared`, and that no CLI output or help text says "verified" or
     "validated" about a shop declaration.
7. **AC7, every artifact carries the right identity (R9).** Under `three_cell_synthetic.json`:
   - the plan's ref equals the loader's `(shop_content_hash, shop_declaration_hash, evidence_class)`;
   - the stored episode's plan ref round-trips through `episode_store_reader`, and its `content_hash` re-derives;
   - the stored verdict equals a fresh oracle verdict under the same declared model;
   - a schedule over three jobs records the same `shop_model_ref`, and its input identity changes when any one job is
     planned under a variant declaration;
   - the checker rejects mixed-ref job sets with `METADATA_MISMATCH`.
8. **AC8, contract compatibility (D1).**
   - Every 0.4.0 schema file is byte-identical except `production_plan.schema.json`.
   - That file equals its 0.4.0 form plus exactly one optional property and its `$defs` entry, checked structurally
     (§9).
   - Every existing fixture instance validates under 0.5.0.
   - The drift check is green, and the bindings for unchanged schemas are byte-identical.
9. **AC9, gate.** In the Docker verifier, all of these are green:
   - pytest, mypy `src`, import-linter (no new or broken contracts), the contract drift check;
   - the installed-wheel check (including `--capability-model-file` from the wheel);
   - the RM8 zero-diff;
   - the evolved gates in §9.

## 8. Test matrix

| ID | Area | Test | Kind | Proves |
|---|---|---|---|---|
| T1.1 | History | Full existing suite, unchanged files | regression | AC1 |
| T1.2 | History | RM8 902-plan golden: library and CLI digests | golden | AC1, R7 |
| T1.3 | History | RM10, RM11, RM12, RM13 (135), RM14 goldens and corpus | golden | AC1 |
| T2.1 | Equivalence | 902 requests: `default_1.0.0.json` vs `default_model()` | corpus | AC2 |
| T2.2 | Equivalence | constrained fixture vs `constrained_model()` | corpus | AC2 |
| T3.1 | Identity | Permutation and whitespace invariance of both hashes | property | AC3 |
| T3.2 | Identity | Field-by-field sensitivity table: which hash changes | unit | AC3, R1, R2 |
| T4.1–T4.8 | Stale reuse | One test per §7 AC4 variant | integration | AC4, R8 |
| T4.9 | Stale reuse | Legacy code-model label-only behaviour pinned | integration | AC4 (scope honesty) |
| T5.1 | Fail-closed | One test per `ShopModelIssueCode` | unit | AC5, R3, R4 |
| T5.2 | Fail-closed | CLI exit code 2, no store, no default fallback (spy) | integration | AC5, D3 |
| T5.3 | Declared gaps | `unsupported_ops` and `unsupported_capabilities` give `CAPABILITY_MISSING` | integration | R3 |
| T6.1 | Evidence | CLI wording; no `shop_declared` fixture; no "verified" wording | unit | AC6, R6 |
| T7.1 | Binding | Plan ref equals loader identities | unit | AC7 |
| T7.2 | Binding | Episode round-trip and hash re-derivation | integration | AC7 |
| T7.3 | Binding | Stored verdict equals fresh verdict under the declared model | integration | AC7 |
| T7.4 | Binding | Schedule `shop_model_ref`, identity sensitivity, mixed-ref refusal | integration | AC7 |
| T8.1 | Contracts | 0.4.0 files unchanged and structural plan-schema diff | boundary | AC8, D1 |
| T8.2 | Contracts | All existing fixtures validate under 0.5.0 | contract | AC8 |
| T9.1 | Gates | `reuse_runner.py` pinned-content digest (ratified version) | boundary | D2 |
| T9.2 | Packaging | Installed wheel, `--capability-model-file` | packaging | AC9 |
| T10.1 | Mutation | Mutants that drop the ref from plan identity, drop the hash from the reuse key, skip the cycle check, or fall back to the default model | mutation | the tests above are not vacuous |

## 9. Regression-gate evolution (exact; to be ratified in ADR-0022)

General rules:
- **No tag, golden file, probe or frozen fixture is regenerated or edited.**
- Each evolution replaces a byte pin with a check that is at least as strong for every pre-existing artifact.

| Gate today | Why MP-S1 trips it | Evolution | Protection kept or strengthened |
|---|---|---|---|
| CI "RM1/RM2 behavioral core unchanged": `git diff --exit-code rm2-complete` over a file set including `orchestration/reuse_runner.py` | One-line reuse-key change | Remove **only** `reuse_runner.py` from that set. Add a boundary test, which runs in CI and in the Docker verifier without needing `.git`: the LF-normalised sha256 of `reuse_runner.py` must equal one **pinned digest**, the ratified file content. ADR-0022 records the exact diff against `rm2-complete`. | All other RM1/RM2 files stay byte-frozen. `reuse_runner.py` stays byte-frozen too, only at its new ratified content. That is as strict as before, and any further change trips the gate. |
| `tests/unit/test_rm8_default_zero_diff.py`: `contracts_digest` over the whole `contracts/` tree (`tests/rm8_behavior_probe.py` l.103–111) | New schema file, one changed schema, regenerated bindings | Keep the `library` and `cli_default` digest assertions **unchanged**. Replace only the `contracts_digest` equality with the T8.1 manifest check, details below. | The default-model behaviour pins are untouched. Contract protection moves from "nothing changed" to "nothing pre-existing changed except one declared additive property". |
| `tests/boundary/test_{experience,experiment,judgment,rm8,rm11}_boundaries.py`: `VERSION == "0.4.0"` (5 assertions) | `VERSION` becomes 0.5.0 | Each becomes: `VERSION` ≥ 0.4.0 **and** the T8.1 manifest check. | Each test keeps its original meaning ("this milestone added no contract and the contracts it relied on are intact"), and that is now checked by file content, not by a version string. |
| CI step "Contract suite frozen at the ratified version (0.4.0)" | Same | `test "$(cat contracts/VERSION)" = "0.5.0"` | Same strength, new ratified value |

**How the T8.1 manifest check works:**
1. A new frozen fixture, `tests/fixtures/contracts_0.4.0_manifest.json`, is generated **once** from the `rm14-complete`
   tag by a committed probe script. Its own digest and the probe's digest are pinned in the test, mirroring the RM8
   golden pattern. `git diff --stat` shows the `contracts/` tree is identical from `rm4-complete` through
   `rm14-complete` to `ee46767`. That is why one manifest serves all five boundary tests and the RM8 golden's
   contracts clause.
2. The manifest holds a per-file LF-normalised sha256 of every 0.4.0 contracts file. For `production_plan.schema.json`
   it also holds a canonical-JSON hash.
3. The check asserts:
   - every manifest file is present and byte-equal, except `production_plan.schema.json` and its generated binding;
   - deleting `properties.capability_model_ref` and `$defs.CapabilityModelRef` from the current
     `production_plan.schema.json` gives JSON whose canonical hash equals the manifest's;
   - the binding is covered by the drift check.

The Docker verifier has no `.git`, which is why a frozen manifest is used instead of reading the tag at test time.

## 10. Unresolved trade-offs and risks

| Item | Trade-off or risk | Current position |
|---|---|---|
| Label in the declaration hash | A label-only edit forces a re-plan, a conservative miss | Accepted (AC4). It is never wrong, only slower. |
| Strict declared-intent rules (R3) | A real shop file must list every op and capability explicitly, which is more friction | Accepted. The friction is what separates intent from typos. The fixtures show the burden is seven op entries. |
| Shop-wide materials (§4.1) | A verdict can overstate feasibility when one machine cannot process a material | Documented limitation; candidate follow-up |
| Basis-agnostic precedent (§4.2) | Cross-declaration precedent can still support a judgment | Documented; visible via `capability_model_ref` for a later milestone |
| Float canonicalisation | Tolerances are hashed through Python `json`, so a cross-language consumer may serialise differently | Contract note: consumers must re-canonicalise, or treat MP's hash as authoritative |
| Gate evolution precedent | Three gate evolutions in one milestone could normalise relaxing gates | Each evolution is narrower or stronger (§9) and ratified in ADR-0022. The pinned-patch and manifest patterns replace "allow change" with "allow exactly this change". |
| Private registry reuse (D3) | `_validate._registry()` is private, so a future change to `_validate.py` could break the loader | `_validate.py` is byte-frozen, so the risk is low. A boundary test pins the reuse. |
| `shop_declared` misread as validation | Users may trust a self-declared file too much | §3.4 wording, enforced by AC6. MP-E1 remains the only route to real evidence. |
| Synthetic-only acceptance | Proves software correctness, not usefulness | Stated plainly. Usefulness is MP-E1's question, which is blocked. |
| Day-one shop facts that are missing (machine envelope, spindle and tooling, per-machine materials) | MP-S1 may still be too thin for a real shop | Deliberately excluded until a real user (MP-E1) shows which fact matters first |

## 11. Definition of done

- One commit implementing §3 with the §8 tests and the §9 gate evolutions. It includes:
  - ADR-0022, which ratifies the gate evolutions;
  - `docs/milestones/MP-S1-completion-report.md`;
  - roadmap and changelog entries, and contracts `0.5.0`.
- The Docker verifier log for AC1–AC9 is recorded in the report.
- Pushed, with local and remote refs equal and a clean working tree.
- The final Research Director review and owner authorisation are recorded before implementation starts. The AI review
  is recorded as reviewed, not ratified (Law 22).

## 12. Review record

| Date | Reviewer | Scope | Outcome |
|---|---|---|---|
| 2026-11-06 | Research Director (preliminary independent review) | Revision 1 | MP-S1 approved as next candidate. D1/D2 accepted conditionally, D3/D4 accepted. Ten mandatory revisions. Not frozen, not authorised. |
| — | Research Director (final review) | Revision 2 | Pending |
| — | Owner | Authorisation | Pending |
