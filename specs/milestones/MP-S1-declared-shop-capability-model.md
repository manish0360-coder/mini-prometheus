# MP-S1 Specification — Declared Shop Capability Model

- **Status:** 🔒 **FROZEN. Revision 3.1. Implementation AUTHORISED by the owner on 2026-11-06, under a strict scope
  lock.** This is the specification of record (ADR-0022). Revision 3.1 resolved the Director's two final
  clarifications on revision 3 (§0.2).
  - Owner conditions:
    1. correctness first: the stale-verdict bug is the primary acceptance requirement;
    2. historical protection;
    3. scope control: the only pre-authorised reduction is moving §3.7 guarantee 2 to a later milestone;
    4. a full Docker gate on the exact committed tree;
    5. one milestone commit.
  - Revision 1 went to the Research Director's preliminary review (2026-11-06). That review accepted D1–D4
    conditionally and required ten revisions.
  - Revision 2 (committed `c4a85e1`) applied them.
  - The Director's final review of revision 2 raised three architectural questions and four confirmations. Revision 3
    answers them; see §0.1 and §13.
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
  - RM1–RM14 behaviour and the RM8 golden corpus stay as they are. That corpus is 902 rows: 451 requests, each under
    `default_model()` and the RM5 regime R*.
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
| R7 | Preserve RM1–RM14 and the RM8 902-row corpus | §7 AC1, AC2; §8 |
| R8 | Test changed materials, tolerances, capabilities and evidence against stale reuse | §7 AC4; §8 rows T4.x |
| R9 | Plans, verdicts, episodes and schedules carry the correct shop identity | §3.3; §7 AC7; §8 rows T7.x |
| R10 | Scope limited to shop capability declaration | §4 |

Also changed from revision 1:
- The content hash no longer includes the label or the evidence class (R1).
- Declared intent is explicit (R3), so unprovided capabilities, unreferenced capabilities and unmapped operations are
  now **refused unless declared**. Revision 1 accepted them with diagnostics.
- Failures use a closed issue-code taxonomy (D3 condition).
- Schedules carry the shop reference explicitly (R9).

## 0.1 Revision 3 change log (Research Director final review of revision 2)

| Item | Question | Resolution | Where |
|---|---|---|---|
| Q1 | Cross-shop precedent must not influence verdicts or count as capability evidence | Two guarantees. (1) **Structural:** no verdict path can read precedent. This is true today and becomes an enforced import-linter contract. (2) **Labelling:** a new pure annotation marks every precedent entry with its shop basis. Any entry, or any report-level signal, that rests on a foreign, unknown or unresolved basis is marked **non-authoritative and not capability evidence**. Retrieval is not filtered, because frozen RM3/RM4 code is not touched. | §3.7; AC6; T11.x |
| Q2 | A complete two-hash truth table, and proof that reuse keys use the right identity | A 14-row truth table, produced by running a throwaway prototype of the §3.2 formulas against the repo's own `_hashing.content_hash`. The reuse key uses `shop_declaration_hash`. | §3.2.1; AC3; AC4 |
| Q3 | Exact propagation of the shop identity through plan, verdict, episode and schedule, with no Noetica contract change, and tests showing nothing can silently lose or mismatch it | A propagation chain with five guards (G1–G5). The verdict, a consumed Noetica stub, is bound only through the episode. Negative tests cover every loss or mismatch path. | §3.3; AC7; T7.5–T7.11 |
| C1–C4 | Confirmations | Falsifiability per criterion; RM8 corpus without regeneration; gate evolutions preserve historical evidence; synthetic and public-specification evidence can't be presented as real-shop validation | §13 |

Also corrected: revision 2 said "902 requests". The RM8 golden (`tests/fixtures/rm8_default_behavior_golden.json`,
generated from `rm5-complete` `96eb81f`) holds **902 library rows: 451 requests × {`default` 1.0.0, `r_star` 2.0.0}**,
plus 2 legacy-CLI rows. AC2 now covers both models against the golden rows (§7).

## 0.2 Revision 3.1 change log (Director's final clarifications on revision 3)

| Item | Clarification | Resolution | Where |
|---|---|---|---|
| F1 | Should a human-readable label change invalidate RM2 reuse? | **Design changed, with reasons documented.** Shop metadata now falls into four documented classes. `model_version` is dropped from `shop_declaration_hash`. A new display-only `display_name` field affects nothing. A `model_version` change still misses reuse, but only because of the **frozen** RM1/RM2 identity it already feeds. | §3.2.2 |
| F2 | Can every externally exposed verdict be traced to declaration, plan, episode and evidence class? | Every exposure point is inventoried. A bare `Verdict` cannot carry the chain, and MP may not extend it. The gap is closed with an MP-owned **`VerdictTrace`** (internal) that every declared-shop exposure point returns or prints, with fail-closed consistency checks. Schedules have no episode **by RM11 design**, and that is stated as such. | §3.8; AC7; T12.x |

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
| `model_version` | SemVer | The **contracted version label**. It flows verbatim into `capability_model_version`, which the frozen RM1 contract makes part of plan identity, episode identity and the RM2 reuse key. It is **not display-only**, and it is part of neither MP-S1 hash (§3.2.2). |
| `display_name` | string, optional (≤ 120 characters) | **Display-only.** Printed by the CLIs. Not in either hash, not on the plan, no effect on reuse. |
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
  - It **excludes** `model_version`, `display_name`, `evidence_class`, `declaration` and `notes`.
  - It answers "what capability basis is this?". Two declarations of the same shop content share it, whatever their
    labels or evidence.
- `shop_declaration_hash = content_hash({shop_content_hash, evidence_class, declaration})`.
  - It excludes `model_version` (rev 3.1), `display_name` and `notes`.
  - It answers "which evidence basis supports that capability basis?". Any change to content, evidence class,
    declarer, date or sources changes it.
- **Invariant:** `shop_content_hash` is an input to `shop_declaration_hash`, so any content change also changes the
  declaration hash. The reverse does not hold.
- **Which identity is used where:**
  - The **reuse key and every binding check (G1–G5) use `shop_declaration_hash`.**
  - `shop_content_hash` is recorded for basis comparison only, for example the §3.7 precedent annotation. It never
    decides reuse.

#### 3.2.1 Two-hash truth table (Director Q2)

**How this was produced.** A throwaway prototype of the formulas above was run on 2026-11-06, outside the repo. It
loads the repo's own `src/mini_prometheus/_hashing.py` by file path, applies each change to a declaration mirroring
`default_model()`, and compares the reuse key `(design_hash, model_version, shop_declaration_hash)` against the base.
This is evidence for the specified formulas, not for an implementation. AC3 and AC4 repeat every row against the real
loader.

| # | Change from the base declaration | `shop_content_hash` | `shop_declaration_hash` | Reuse key | RM2 outcome |
|---|---|---|---|---|---|
| 1 | JSON key reordering, top level and nested | same | same | same | **hit, reused** |
| 2 | Whitespace only (compact vs indented; the raw bytes differ) | same | same | same | **hit** |
| 3 | List order (resources, a machine's capabilities, materials) | same | same | same | **hit** |
| 4 | Machine capability: `lathe01` removed, `cap.lathe` declared unsupported | changes | changes | changes | miss → re-plan |
| 5 | Machine capability: `cap.drill` added to a second machine | changes | changes | changes | miss → re-plan |
| 6 | Material: `aluminum` and `aluminum 6061` removed | changes | changes | changes | miss → re-plan |
| 7 | Tolerance: `cap.mill` 0.02 added | changes | changes | changes | miss → re-plan |
| 7a | Tolerance: the same 0.02 written as `0.020` (relative to row 7) | same | same | same | **hit** |
| 7b | Tolerance: 0.02 → 0.01 (relative to row 7) | changes | changes | changes | miss → re-plan |
| 8 | Precedence: `cut_stock` before `drill` added | changes | changes | changes | miss → re-plan |
| 9 | Evidence class: `synthetic` → `public_specification` (with a source) | **same** | changes | changes | miss → re-plan |
| 10 | Declarer changed | **same** | changes | changes | miss → re-plan |
| 11 | Declaration date changed | **same** | changes | changes | miss → re-plan |
| 12 | Label: `model_version` 1.0.0 → 1.0.1 | **same** | **same** (rev 3.1; rev 3 said "changes") | changes, via the frozen `capability_model_version` component | miss → re-plan (§3.2.2) |
| 12a | `display_name` only (rev 3.1) | same | same | same | **hit** |
| 13 | Notes only | same | same | same | **hit** |

What the prototype output shows:
- **Reuse uses the right identity.** The reuse key changes exactly when `shop_declaration_hash` changes (rows 4–12),
  and stays put when it doesn't (rows 1–3, 7a, 13).
- Rows 9–12 show labels, evidence and declaration provenance stay out of the semantic basis (R1), while still blocking
  stale reuse (R2).
- The printed invariant check passed: no row changes the content hash without also changing the declaration hash.
- Row 12 misses only through the key's existing, frozen `capability_model_version` component. Row 12a, display-only,
  is a hit.
- Rows 1–13 come from the revision 3 prototype run. Rows 12 and 12a come from the revision 3.1 comparison run in
  §3.2.2.

#### 3.2.2 Label and display metadata (Director F1): classes, trade-off and comparison

**The question.** Should changing a human-readable shop label invalidate RM2 reuse?

**Reasoning.**
- A reuse **hit** returns a stored verdict. If the hit is false, the user gets a **stale manufacturing decision**,
  which is unsafe. If a **miss** is false, the system re-plans: it costs a re-computation and one extra episode, but
  the verdict is the same, so it is safe.
- The asymmetry favours including anything that could change the decision or its evidence. Anything that provably
  can't do either is excluded.

**What I found in the code.**
- Revision 3 treated `model_version` as a plain label, but it isn't one.
- The planner writes it into `ProductionPlan.capability_model_version` (`planner.py` l.241, l.248).
  `plan_identity` keeps that field (`_hashing.py`: it strips only `plan_id`, `content_hash` and `provenance`).
  `episode_identity` includes it, and it is the second component of the frozen RM2 `ReuseKey`.
- So a `model_version` change invalidates reuse **whatever MP-S1 hashes**.
- Making it display-only would mean removing `capability_model_version` from plan identity and from the reuse key.
  That breaks the frozen RM1 contract and every golden. **Rejected.**

**Revision 3.1 design: four metadata classes.**

| Class | Fields | Content hash | Declaration hash | Reuse effect |
|---|---|---|---|---|
| Semantic capability | `schema_version`, `resources`, `op_capability`, `unsupported_*`, `supported_materials`, `capability_tolerance_mm`, `ordering_constraints` | in | in (via the content hash) | miss |
| Evidence basis | `evidence_class`, `declaration.{declared_by, declared_on, sources}` | out | **in** | miss |
| Contracted version label | `model_version` | out | **out** (rev 3.1) | miss, via the frozen RM1/RM2 identity only |
| Display-only | `display_name` (new), `notes` | out | out | **none, reused** |

**Why `declared_on` stays in the evidence basis.**
- A dated declaration is a distinct assertion. Keeping the date is what lets an audit say **which declaration was in
  force** when a verdict was made.
- The cost: re-affirming an unchanged shop on a new date re-plans once, a safe miss.
- Excluding the date would make two separately dated declarations by the same person indistinguishable.

**Rev 3 vs rev 3.1 comparison.** This is from a throwaway prototype run on 2026-11-06 against the repo's
`_hashing.py`. The reuse key is `(design, capability_model_version, shop_declaration_hash)`.

| Change | Content hash (3 / 3.1) | Declaration hash (3 / 3.1) | Reuse (3 / 3.1) |
|---|---|---|---|
| `display_name` changed | — / same | — / same | — / **hit** (in rev 3 this field didn't exist, and the closed schema would have refused it) |
| `notes` changed | same / same | same / same | hit / hit |
| `model_version` 1.0.0 → 1.0.1 | same / same | **changes / same** | miss / miss (rev 3.1: frozen component only) |
| `evidence_class` → `public_specification` | same / same | changes / changes | miss / miss |
| `declared_by` changed | same / same | changes / changes | miss / miss |
| `declared_on` changed | same / same | changes / changes | miss / miss |
| `sources` changed | same / same | changes / changes | miss / miss |
| material removed | changes / changes | changes / changes | miss / miss |

**Effect of the change.**
- The declaration hash now means exactly "the evidence basis of this capability basis", as the Director preferred.
- Cosmetic naming has a home (`display_name`) that never invalidates a decision.
- No reuse outcome becomes less safe: every row that missed in revision 3 still misses.
- **Guidance recorded in the schema description:** bump `model_version` only for a real revision of the declaration.
  Use `display_name` for naming.

**Model carriage.**
- `ProcessCapabilityModel` gains one optional field, defaulted to `None`: `source: ShopModelSource | None`. It holds
  `(shop_content_hash, shop_declaration_hash, evidence_class)`.
- The code models leave it `None`.
- `with_unavailable_resources()` keeps `source` (via `dataclasses.replace`). Availability is a per-run input recorded in
  the plan params (RM9); it is not part of the declaration.

### 3.3 Binding the shop identity to every output (R2, R9, Director Q3)

**Propagation chain.** The identity originates in exactly one place and is checked at five guards. **No
Noetica-owned contract is modified.**

```
ShopCapabilityModel file
  └─ load_shop_model ──► ProcessCapabilityModel.source = (content_hash, declaration_hash, evidence_class)
                           [the ONLY place that creates or sets a shop identity or evidence class]
       │
       ├─ G1 planner.plan(di, model) ──► ProductionPlan.capability_model_ref = ref(model.source)
       │                                 schema_version 1.1.0; the ref is inside plan_identity → plan.content_hash
       │
       ├─ G2 runner.run: require plan.capability_model_ref == ref(model) BEFORE oracle.verify
       │       mismatch → ShopIdentityMismatchError, re-raised OUTSIDE the INFRA_ERROR handler; nothing written
       │
       ├─ oracle.verify(plan, model) ──► Verdict   (consumed Noetica stub: NO shop field, NOT extended, Law 15)
       │
       ├─ episode_store.build_episode(plan, verdict) ──► episode_identity includes plan.content_hash (so the ref)
       │                                                 and verdict status + reason codes
       │
       ├─ G3 episode_store_reader.load: for every plan carrying a ref (or schema_version 1.1.0) → re-derive the
       │       plan content_hash AND require (ref present) ⇔ (schema_version 1.1.0); else EpisodeIntegrityError
       │       (the existing episode re-verification alone would miss a ref-only edit, because episode_identity
       │        uses the STORED plan.content_hash field)
       │
       ├─ G4 RM2 reuse: key = (design hash, label, declaration_hash read from the stored plan ref)
       │       on a hit, the reproducibility guard re-derives the plan; the ref is in plan identity, so equality
       │       proves stored ref == current ref
       │
       └─ G5 scheduling: job_set applies G2 per job; schedule.shop_model_ref = ref(model);
               the independent checker gets the expected ref, re-derives it from every job plan, and refuses any
               difference (missing, different or mixed) as METADATA_MISMATCH; schedule_input_identity covers plan
               hashes and shop_model_ref
```

**What the verdict's binding means.**
- A Verdict has no identity hash of its own, and MP may not add one: it is a consumed Noetica envelope.
- Its shop identity is **the episode it is stored in**. The episode hash commits to the verdict's status and reason
  codes together with the plan hash, and the plan hash commits to the shop declaration.
- G2 guarantees that the verdict was computed under the model whose ref the plan carries.
- The verdict's free-text `detail` field is **not** used to carry identity.

**Honest limit.**
- The guards detect accidental loss, partial edits and mismatches.
- They do **not** detect a deliberate, internally consistent forgery of a whole episode. There are no signatures.
  Signing belongs to Noetica's provenance mechanism and is out of scope.

**Per-artifact summary:**

| Artifact | How it carries the shop identity | Code models (`source is None`) |
|---|---|---|
| **ProductionPlan** | New optional `capability_model_ref: {shop_content_hash, shop_declaration_hash, evidence_class}` (D1). Plan `schema_version` becomes `"1.1.0"` only when the ref is present. `plan_identity` already hashes every non-volatile field, so the ref is part of the plan's `content_hash`. `_hashing.py` is unchanged. | Field absent; `"1.0.0"`; byte-identical |
| **Verdict** | Verdict is a **consumed Noetica stub** (`consumed/noetica/verdict.schema.json`) and is not extended (Law 15). It is bound to the shop only **through the episode**, which pairs it with the plan content hash and therefore the ref. The oracle computes it from `(plan, model)`, where the plan carries the ref. AC7 tests that the stored verdict equals a fresh verdict under the declared model. | Unchanged |
| **ManufacturingEpisode** | No schema change. `episode_identity` already includes `plan.content_hash`, so the episode hash binds the declaration. `episode_store_reader` reads the optional plan ref so stored plans round-trip exactly. | Unchanged |
| **RM2 reuse** | `ReuseKey = (design_input_identity_hash, capability_model_version, shop_declaration_hash \| None)`. `design_input_key(di, version, *, shop_declaration_hash=None)` keeps its positional signature, so the existing RM2 tests run unchanged. Any change in content, evidence or declaration is a **miss**, followed by a re-plan (D2). | Third element `None`; behaviour unchanged |
| **MultiJobSchedule** (internal, not a contract) | `schedule_input_identity` already includes each job's plan hash. In addition, the schedule records `shop_model_ref` explicitly. It enters the identity and the digest **only when present**, as RM12 downtime and RM14 setups did. The independent checker gets the expected ref (`schedule_issues(..., *, shop_model_ref=None)`, a keyword-only addition), re-derives it from the job plans, and refuses as `METADATA_MISMATCH` any job plan or schedule field that is missing it, differs from it, or mixes it with none. | Field absent; every RM11–RM14 identity and digest byte-identical |

### 3.4 `evidence_class`: precise definitions (R6)

The field records **who asserted the declaration and on what basis**. It never records that anyone checked it.
Mini Prometheus cannot check any declaration against a physical shop.

| Value | Definition | Requirement | Use in MP-S1 |
|---|---|---|---|
| `synthetic` | Invented to exercise software. It describes no real shop. | none | All acceptance fixtures |
| `public_specification` | Derived by the declarer from published machine or material data. It describes no specific shop's actual equipment or condition. | `declaration.sources` ≥ 1, citing the publications | Allowed, labelled; at most an illustrative fixture |
| `shop_declared` | Asserted by a person on behalf of a real shop about that shop's equipment. **Unverified by Mini Prometheus or any independent party.** | `declared_by`, `declared_on` | Schema-accepted; **no MP-S1 fixture, test claim or document uses it as evidence** |

**Presentation rule.**
- CLI output prints the shop identity as `shop model "<display_name>" <shop_declaration_hash> (<evidence_class>, declared by <declared_by> on <declared_on>; not independently verified)`. The `display_name` part is omitted when the field is absent.
- The same wording goes in CLI help, the ADR and the completion report.
- No output may use the words "verified" or "validated" about a shop declaration.
- **No code path upgrades or derives `evidence_class`.** It is copied verbatim from the file by the loader and nowhere
  else. A test asserts that the loader module is the only writer of `ShopModelSource`.
- MP cannot stop a user from mislabelling a file. It records the class as asserted and never presents any class as
  validation.

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
- `r_star_2.0.0.json` expresses the RM5 regime R* (`experiment/corpus.r_star()`, label `2.0.0`): default minus
  `lathe01`. Under the declared-intent rules it **must** list `cap.lathe` in `unsupported_capabilities`, so it also
  serves as the R3 example of a deliberate gap.
- `constrained_1.1.0.json` expresses `constrained_model()` exactly.
- `three_cell_synthetic.json` is a small shop that differs on purpose: two mills, `turn` in `unsupported_ops`, and a
  reduced material list.
- The `variants/` folder holds single-field mutations of `default_1.0.0.json` for AC4: material removed, tolerance
  tightened, capability removed, precedence added, evidence class changed, declarer changed, label changed, and notes
  changed.
- The `invalid/` folder holds one fixture per `ShopModelIssueCode`.

### 3.7 Cross-shop precedent (Director Q1)

**Guarantee 1: precedent can never influence a manufacturability verdict.** This is structural.
- It holds today:
  - `oracle.verify(plan, capability_model)` has no precedent input.
  - `manufacturing_constraints/`, `manufacturing_planning/`, `manufacturing_scheduling/`, `orchestration/runner.py`
    and `orchestration/schedule_runner.py` import nothing from `precedent/` or `judgment/`. A repo grep on
    2026-11-06 found no match.
  - `PrecedentReport` carries **no query-verdict field** (its frozen contract description says so).
  - RM4 critique is advisory and never feeds back into the verdict.
- MP-S1 turns this from convention into enforcement. A new import-linter contract (a `pyproject.toml` entry) states
  that `manufacturing_constraints`, `manufacturing_planning`, `manufacturing_scheduling`, `orchestration.runner`,
  `orchestration.reuse_runner`, `orchestration.schedule_runner` and the new `shop_model` module must not import
  `precedent`, `judgment`, `orchestration.precedent_runner` or `orchestration.judgment_runner`.

**Guarantee 2: cross-shop precedent is explicitly labelled and is never capability evidence.**
- Retrieval filtering would mean changing RM3 code, which is byte-frozen at `rm4-complete`, so it is out of scope.
  Instead, MP-S1 adds a **pure annotation** in a new, unfrozen module, `orchestration/precedent_basis.py`:
  - `annotate_precedent_basis(report, episodes, current_model) -> PrecedentBasisAnnotation` resolves each
    `PrecedentEntry.episode_ref` against the given episodes. The match is by `content_hash`, so resolution is
    fail-closed: an unmatched ref is marked unresolved, never assumed.
  - It compares the precedent plan's `capability_model_ref` with `current_model.source`, and returns one basis per
    entry:

    | Basis | Condition | `capability_evidence` |
    |---|---|---|
    | `SAME_DECLARATION` | equal `shop_declaration_hash` | advisory only; the precedent was judged under this exact declaration |
    | `SAME_CONTENT_OTHER_DECLARATION` | equal `shop_content_hash`, different declaration | **false**, non-authoritative |
    | `OTHER_SHOP` | different `shop_content_hash` | **false**, non-authoritative |
    | `UNKNOWN_BASIS` | the precedent or the query has no ref (legacy or code model) | **false**, non-authoritative |
    | `UNRESOLVED` | `episode_ref` not found in the given episodes | **false**, non-authoritative |

  - **Report-level signal rule.** If **any** entry's basis is not `SAME_DECLARATION`, the annotation marks the
    report's `signal` (SUPPORTING/CAUTIONARY) as `NON_AUTHORITATIVE_CROSS_BASIS`. Otherwise it marks it
    `SAME_DECLARATION_ADVISORY`. This is deliberately conservative: it does not re-derive which entry drove the
    signal, because that would duplicate RM3's reasoner logic (Law 13).
  - The annotation carries the fixed text *"Precedent judged under a different, unknown or unresolved shop
    declaration is not evidence of capability in the current shop."*
- `run_precedent_for_shop(request, *, capability_model, store_path, ...) -> (PrecedentReport, PrecedentBasisAnnotation)`
  calls the **unchanged** `run_precedent` and then annotates. It is the documented entry point whenever a declared shop
  model is in use.
- The frozen `PrecedentReport` and `EngineeringCritique` objects and their hashes are **not** modified. The annotation
  is a separate internal object: not a contract, not persisted, deterministic.

**Limit.** A caller that uses the frozen `run_precedent` or `run_judgment` directly gets no annotation. MP-S1 adds no
precedent or judgment CLI; none exists today. The completion report states that annotated retrieval is the only
supported path for declared shops.

### 3.8 Standalone verdict traceability (Director F2)

**The gap.**
- A `Verdict` is a consumed Noetica envelope with the fields `grounded`, `is_error`, `status`, `reason_codes`,
  `detail` and `produced_by` (`contracts/schemas/consumed/noetica/verdict.schema.json`). It has no plan, episode or
  shop field, and MP may not add one (Law 15).
- So **a verdict handed on by itself cannot be traced**. Today every API returns it next to the plan and episode, but
  nothing binds them together or checks that they agree.

**Every place MP exposes a verdict, checked in source on 2026-11-06:**

| # | Exposure | Carries today | Gap |
|---|---|---|---|
| X1 | `runner.run` / `run_from_request` / `run_from_velith` → `RunResult` | verdict, plan, episode, path | No binding or consistency check; the shop identity is only implicit |
| X2 | `reuse_runner.run_with_reuse` → `ReuseRunResult` | verdict, plan, episode, `source_episode` | Same |
| X3 | `runner` CLI | prints `STATUS episode -> path` | No plan, shop or evidence information |
| X4 | `INFRA_ERROR` result (X1, X2) | verdict only. The plan and episode are `None`, and by RM1 rule nothing is persisted. | It is not a manufacturability decision, but it doesn't say which shop was attempted |
| X5 | Scheduling refusal `JOB_NOT_MANUFACTURABLE` (`job_set.py` l.68–78; the CLI prints the issues) | the job verdict's status and reason codes as text | **No episode by RM11 design** (scheduling is pure and read-only); no plan or shop reference in the text |
| X6 | `PrecedentEntry.verdict_status` and `reason_codes` (RM3) | `episode_ref` | Traceable through the episode; the basis comes from §3.7 |
| — | `experiment/` (RM5/RM15) | internal leaf over stored episodes | Not externally exposed; out of scope |

**How it is closed, without touching Noetica contracts.**
- An MP-owned **`VerdictTrace`** in a new module, `orchestration/verdict_trace.py`. It is internal, not a contract,
  pure and deterministic. Fields:
  - `status`, `reason_codes`, `verdict_produced_by` (copied from the verdict);
  - `record` ∈ {`EPISODE`, `SCHEDULE_READ_ONLY`, `NONE_INFRA_ERROR`};
  - `plan_ref` (id and content hash) or none;
  - `episode_ref` (id and content hash) or none;
  - `shop_ref` (content hash, declaration hash, evidence class) or none;
  - `trace_hash`, the content hash of all of the above.
- Builders, all **fail closed** with `VerdictTraceError`:
  - **`trace_run(result, capability_model)`** for X1, X2 and X4.
    - Requires `result.episode.verdict` to equal `result.verdict` field for field.
    - Requires `result.episode.plan.content_hash` to equal `result.plan.content_hash`.
    - Requires the plan's ref to equal `ref(capability_model.source)`.
    - On a reuse hit, uses the reused episode, and `source_episode` must equal it.
    - For `INFRA_ERROR` it returns `record = NONE_INFRA_ERROR`, no plan or episode, and the **attempted** `shop_ref`.
    - It is duck-typed over both result types, so the pinned `reuse_runner.py` needs no further change.
  - **`trace_job(plan, verdict, capability_model)`** for X5.
    - Requires the plan's ref to equal the model's.
    - Returns `record = SCHEDULE_READ_ONLY`, with no episode.
- **CLI (X3, X5), only with `--capability-model-file`.**
  - The runner prints one trace line:
    `STATUS [reasons] plan <plan hash> episode <episode hash> shop model "<name>" <declaration hash> (<evidence class>, declared by …; not independently verified) trace <trace_hash> -> <path>`.
  - The schedule runner adds plan hash, shop declaration hash and evidence class to every job refusal line.
  - Without the flag, the output is byte-identical (the RM8 legacy-CLI golden and the RM11 CLI tests).
- **Persisted form:** the episode already holds the whole chain: verdict, plan with its ref, evidence class, and the
  episode hash. G3 re-verifies it on load. `VerdictTrace` is the supported **in-memory and printed** form for
  declared-shop verdicts.

**What this demonstrates, per required link:**

| Link | X1/X2 (episode) | X4 (infra error) | X5 (schedule) | X6 (precedent) |
|---|---|---|---|---|
| Exact shop declaration | `shop_ref.declaration_hash`, checked against the model | attempted `shop_ref` | `shop_ref`, checked | the precedent plan's ref, via §3.7 |
| Exact production plan | `plan_ref`, checked against the episode | none (no plan was produced) | `plan_ref` | the episode's plan |
| Corresponding episode | `episode_ref`, checked | none (RM1: errors are never persisted) | **none by RM11 design**, stated as `SCHEDULE_READ_ONLY` | `episode_ref` |
| Evidence class | `shop_ref.evidence_class` | same | same | the precedent plan's ref |

**Remaining limitation, stated plainly.**
- A library caller can still read `result.verdict` and pass the bare envelope on.
- Preventing that would mean changing the Noetica envelope (forbidden) or MP's existing result types (a breaking API
  change). So MP-S1 **documents** `VerdictTrace` as the only supported external form for declared-shop verdicts.
- A bare `Verdict` is defined as **not traceable on its own**.
- `VerdictTrace` becomes a versioned MP output contract only when a real external consumer exists (Law 14 then
  applies). That is not now.

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

### 4.2 Documented limitation: retrieval itself is basis-agnostic

- RM3 retrieval and RM4 judgment (byte-frozen at `rm4-complete`) still **rank and use** precedent regardless of shop
  basis.
- MP-S1 does not filter them. Instead it guarantees that precedent never reaches a verdict, and it labels cross-basis
  precedent as non-authoritative (§3.7).
- Basis-aware retrieval or judgment is a later milestone. It would need a ratified evolution of the RM3/RM4 gate.

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

### 5.1 Files expected to change at implementation

Listed for review; none is changed by this spec.

| File | Change | Gate |
|---|---|---|
| `contracts/schemas/manufacturing/shop_capability_model.schema.json` | new | drift check; T8.1 manifest |
| `contracts/schemas/manufacturing/production_plan.schema.json` | + optional `capability_model_ref` (+ `$defs`) | T8.1 structural check |
| `contracts/python/**` | regenerated | drift check |
| `contracts/VERSION` | `0.5.0` | §9 |
| `manufacturing_constraints/capability_model.py` | + optional `source` | RM8 library golden |
| `manufacturing_constraints/shop_model.py` | new loader, issue codes, hashes | — |
| `manufacturing_planning/planner.py` | G1 | RM8 / RM10 goldens |
| `orchestration/runner.py` | G2; CLI flag | RM8 legacy-CLI golden |
| `experience/episode_index.py` | 3-part key (keyword-only extra) | RM2 tests (unchanged) |
| `experience/episode_store_reader.py` | read the ref; G3 | RM2 tests (unchanged) |
| `orchestration/reuse_runner.py` | key with declaration hash | §9 pinned content |
| `manufacturing_scheduling/{job_set,checker,model}.py` | G5; `shop_model_ref` only when present | RM11–RM14 goldens and corpus; checker-independence contract |
| `orchestration/schedule_runner.py` | CLI flag | RM11 CLI tests |
| `orchestration/precedent_basis.py` | new annotation (§3.7) | — |
| `orchestration/verdict_trace.py` | new `VerdictTrace`, `trace_run`, `trace_job` (§3.8) | — |
| `pyproject.toml` | + one import-linter contract (§3.7) | import-linter |
| `tools/verify_installed_wheel.py` | installed `--capability-model-file` | packaging |
| `tests/...` | per §8; the one-assertion evolutions in §9 | — |

## 6. D1–D4 decision mapping

| Decision | Research Director ruling | How revision 2 satisfies it |
|---|---|---|
| **D1** Contract 0.5.0 | Accept conditionally: preserve 0.4.0 compatibility, existing semantics and generated-binding consistency | The suite becomes 0.5.0 with additive changes only: one new schema and one optional `ProductionPlan` property. Every 0.4.0 schema file except `production_plan.schema.json` stays byte-identical. Every 0.4.0 instance validates under 0.5.0 (AC8). Regenerated bindings for unchanged schemas are byte-identical, and the drift check is green. |
| **D2** RM2 byte-freeze | Accept conditionally: evolve only the necessary gate; preserve tagged evidence; equivalent behavioural protection; no weakening of RM2, RM8 or goldens | Exactly one file leaves the byte-diff set (`reuse_runner.py`). It is replaced by a **pinned-content gate**: the file's LF-normalised sha256 must equal one pinned digest, which is the ratified version with the one-line key change. The ADR records that version's diff against `rm2-complete`. RM2 tests and AC4 are added on top. Tags, golden files and probes are never regenerated (§9). |
| **D3** Schema registry | Accept: reuse the registry; deterministic typed failures; no silent default fallback | §3.2: registry reuse; closed `ShopModelIssueCode`; complete sorted issue lists; no fallback; CLI exit code 2 with no writes (AC5) |
| **D4** Naming | Accept MP-S1, reserve ADR-0022 | Used throughout; ADR-0022 at implementation |

## 7. Acceptance criteria (falsifiable)

1. **AC1, history preserved (R7).** With no `--capability-model-file`, every behavioural golden is byte-identical:
   - the RM8 golden: 902 library rows (451 requests × `default` and `r_star`) and 2 legacy-CLI rows;
   - the RM10 golden, the RM11 golden, RM12 downtime, the RM13 135-instance corpus and RM14 changeover;
   - the full suite.

   The only assertions that change are the contract-tree and `VERSION` pins, and only as specified in §9.
2. **AC2, file equivalence against the frozen golden, read-only.** For **each of the 902 golden library rows**:
   - the test uses the row's request (the probe's own enumeration: the engineer fixture plus `corpus._requests()`) and
     the fixture for the row's model (`default_1.0.0.json` or `r_star_2.0.0.json`);
   - it runs the library path at the probe's fixed timestamp;
   - the full verdict dict must **equal** the golden row's `verdict`;
   - the plan, with `capability_model_ref` removed and `schema_version` reset to `1.0.0` and then re-hashed, must
     reproduce the golden `plan_content_hash` and the `plan_full` digest;
   - the episode rebuilt from that stripped plan must reproduce `episode_content_hash` and `episode_full`.

   The golden file and the probe are only **read**, never regenerated or edited. Their existing digest pins stay in
   force.

   No frozen golden exists for `constrained_model()`, so for the same 451 requests `constrained_1.1.0.json` is
   compared **live** with `constrained_model()`, verdict for verdict and stripped plan for stripped plan.
3. **AC3, two identities.** Every row of the §3.2.1 truth table is asserted against the real loader. In addition:
   - permutations of keys, lists and whitespace are property-tested;
   - the invariant "a content change implies a declaration change" is property-tested over random single-field edits;
   - the reuse key is shown to change exactly when `shop_declaration_hash` does.
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
   | `model_version` only | the same verdict, re-planned. The miss comes only from the frozen `capability_model_version` key component (§3.2.2), and `shop_declaration_hash` is unchanged. |
   | `display_name` only | **reused** (`reused=True`), because it is display-only |
   | notes only | **reused** (`reused=True`), because notes are not identity |

   A companion test pins **today's** stale hit for code-level models with equal labels and `source=None`, and labels it
   legacy label-only identity. MP-S1 does not change code-model reuse.
5. **AC5, typed fail-closed.**
   - Each `invalid/` fixture raises `InvalidShopModelError` containing exactly its expected issue code(s), in a
     deterministic order.
   - The CLI exits with code 2, writes no episode, and creates no store path.
   - A spy asserts that `default_model()` is never called on that path.
6. **AC6, evidence can't be presented as validation, and cross-shop precedent is never capability evidence.**
   - Plans carry `capability_model_ref.evidence_class`, copied verbatim. The loader is the only writer of
     `ShopModelSource`, checked by an AST test.
   - Both CLIs print the §3.4 line, including "not independently verified".
   - No fixture uses `shop_declared`. No CLI output or help text calls a shop declaration "verified" or "validated".
   - For each of the five §3.7 bases, a precedent store built to produce it gets that label from
     `annotate_precedent_basis`, with `capability_evidence` false for every basis except `SAME_DECLARATION`.
   - A report mixing bases gets the signal marked `NON_AUTHORITATIVE_CROSS_BASIS`.
   - A query shop's verdict is byte-identical whether the store holds cross-shop precedent or none. That proves
     Guarantee 1 behaviourally, on top of the new import-linter contract.
7. **AC7, no artifact can silently lose or mismatch its shop identity (R9, Director Q3).**

   **Positive cases**, under `three_cell_synthetic.json`:
   - the plan's ref equals the loader's `(shop_content_hash, shop_declaration_hash, evidence_class)`;
   - the stored episode round-trips through `episode_store_reader`, with the ref intact and the plan and episode hashes
     re-derived;
   - the stored verdict equals a fresh oracle verdict on the stored plan under the declared model;
   - a reuse hit returns an episode whose plan ref equals the current model's ref;
   - a three-job schedule records the same `shop_model_ref` and checks clean;
   - its input identity changes when any one job is planned under a variant declaration.

   **Negative cases.** Each must fail loudly, not silently:

   | Case | Required failure |
   |---|---|
   | ref deleted from a stored plan line | `EpisodeIntegrityError` (G3) |
   | ref's declaration hash, content hash or evidence class edited | `EpisodeIntegrityError` (G3) |
   | `schema_version` 1.1.0 without a ref, or a ref with 1.0.0 | `EpisodeIntegrityError` (G3) |
   | plan and model mismatch injected into `runner.run` | `ShopIdentityMismatchError`, no episode written, no INFRA_ERROR swallow (G2) |
   | schedule or job-plan ref missing, different or mixed against the expected ref | `METADATA_MISMATCH` (G5) |
   | a store mixing two declarations for the same design and label | each run reuses only its own declaration's episode, never the other's (G4) |

   **Verdict traceability (§3.8):**
   - For every exposure X1–X5 under a declared shop, the matching builder returns a `VerdictTrace` whose links equal
     the source artifacts.
   - `trace_hash` is stable across runs.
   - Each injected inconsistency raises `VerdictTraceError`: episode verdict ≠ result verdict; episode plan ≠ result
     plan; plan ref ≠ model ref; `source_episode` ≠ reused episode.
   - The trace line appears with `--capability-model-file`, and the CLI output is byte-identical without it.
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
| T1.2 | History | RM8 golden: 902 library rows and 2 CLI rows, digests unchanged | golden | AC1, R7 |
| T1.3 | History | RM10, RM11, RM12, RM13 (135), RM14 goldens and corpus | golden | AC1 |
| T2.1 | Equivalence | 451 golden rows under `default` vs `default_1.0.0.json`, read-only | corpus | AC2 |
| T2.2 | Equivalence | 451 golden rows under `r_star` vs `r_star_2.0.0.json`, read-only | corpus | AC2, R3 |
| T2.3 | Equivalence | 451 requests: `constrained_1.1.0.json` vs `constrained_model()`, live | corpus | AC2 |
| T3.1 | Identity | Permutation and whitespace invariance of both hashes | property | AC3 |
| T3.2 | Identity | The §3.2.1 truth table, row by row (14 rows) | unit | AC3, R1, R2, Q2 |
| T3.3 | Identity | Content change implies declaration change; key changes iff the declaration hash changes | property | AC3, Q2 |
| T4.1–T4.8 | Stale reuse | One test per §7 AC4 variant | integration | AC4, R8 |
| T4.9 | Stale reuse | Legacy code-model label-only behaviour pinned | integration | AC4 (scope honesty) |
| T5.1 | Fail-closed | One test per `ShopModelIssueCode` | unit | AC5, R3, R4 |
| T5.2 | Fail-closed | CLI exit code 2, no store, no default fallback (spy) | integration | AC5, D3 |
| T5.3 | Declared gaps | `unsupported_ops` and `unsupported_capabilities` give `CAPABILITY_MISSING` | integration | R3 |
| T6.1 | Evidence | CLI wording; no `shop_declared` fixture; no "verified" wording | unit | AC6, R6 |
| T6.2 | Evidence | The loader is the only writer of `ShopModelSource` | AST | AC6, C4 |
| T7.1 | Binding | Plan ref equals loader identities (G1) | unit | AC7 |
| T7.2 | Binding | Episode round-trip; plan and episode hashes re-derive (G3) | integration | AC7 |
| T7.3 | Binding | Stored verdict equals fresh verdict under the declared model | integration | AC7, Q3 |
| T7.4 | Binding | Schedule `shop_model_ref`; identity sensitivity (G5) | integration | AC7 |
| T7.5 | Loss | Ref deleted from a stored plan → `EpisodeIntegrityError` | negative | AC7, Q3 |
| T7.6 | Mismatch | Ref field edited → `EpisodeIntegrityError` | negative | AC7, Q3 |
| T7.7 | Mismatch | Inconsistent `schema_version` and ref presence → `EpisodeIntegrityError` | negative | AC7 |
| T7.8 | Mismatch | Injected plan/model mismatch in `runner.run` → `ShopIdentityMismatchError`; no episode; not INFRA_ERROR | negative | AC7, Q3 |
| T7.9 | Mismatch | Checker: missing, different or mixed refs → `METADATA_MISMATCH` | negative | AC7, Q3 |
| T7.10 | Reuse | Mixed-declaration store: each run reuses only its own declaration | integration | AC7, AC4 |
| T7.11 | Reuse | On a hit, the returned plan ref equals the current model's ref | integration | AC7 |
| T12.1 | Trace | `trace_run` on a fresh run (X1): links equal the artifacts; `trace_hash` stable | integration | AC7, F2 |
| T12.2 | Trace | `trace_run` on a reuse hit and a reuse miss (X2) | integration | AC7, F2 |
| T12.3 | Trace | `trace_run` on `INFRA_ERROR` (X4): `NONE_INFRA_ERROR` with the attempted `shop_ref` | integration | AC7, F2 |
| T12.4 | Trace | `trace_job` and refusal lines for scheduling (X5): `SCHEDULE_READ_ONLY` | integration | AC7, F2 |
| T12.5 | Trace | Four injected inconsistencies → `VerdictTraceError` | negative | AC7, F2 |
| T12.6 | Trace | CLI trace line with the flag; byte-identical output without it | integration | AC7, AC1 |
| T3.4 | Identity | Four metadata classes: `display_name` and `notes` hit; `model_version` misses only via the frozen key component; evidence fields miss | unit | AC3, AC4, F1 |
| T11.1 | Precedent | Each of the five bases, and its `capability_evidence` value | integration | AC6, Q1 |
| T11.2 | Precedent | A mixed-basis report's signal is `NON_AUTHORITATIVE_CROSS_BASIS` | unit | AC6, Q1 |
| T11.3 | Precedent | The verdict is unaffected by cross-shop precedent in the store | integration | AC6, Q1 |
| T11.4 | Precedent | Import-linter contract: verdict paths cannot import precedent or judgment | boundary | Q1 |
| T8.1 | Contracts | 0.4.0 files unchanged and structural plan-schema diff | boundary | AC8, D1 |
| T8.2 | Contracts | All existing fixtures validate under 0.5.0 | contract | AC8 |
| T9.1 | Gates | `reuse_runner.py` pinned-content digest (ratified version) | boundary | D2 |
| T9.2 | Packaging | Installed wheel, `--capability-model-file` | packaging | AC9 |
| T10.1 | Mutation | Mutants that each must be caught: drop the ref from plan identity; drop the declaration hash from the reuse key; key on the content hash instead of the declaration hash; skip G2; skip G3; checker ignores the ref; skip the cycle check; `trace_run` skips the episode/plan/ref consistency check; `display_name` leaks into a hash; fall back to the default model; annotation marks `OTHER_SHOP` as evidence | mutation | the tests above are not vacuous |

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
| `model_version` change still re-plans (§3.2.2) | A version-label edit re-plans because `capability_model_version` is frozen RM1/RM2 identity. MP-S1 no longer adds to that. | Accepted. It is a safe miss. Removing it would break the RM1 contract and every golden. `display_name` is the cosmetic field. |
| `declared_on` in the evidence basis | Re-affirming an unchanged shop on a new date re-plans once | Accepted, for auditability of which declaration was in force |
| Bare `Verdict` extraction (§3.8) | A library caller can still pass on the envelope without its trace | Documented. `VerdictTrace` is the only supported external form. A contract follows when a real consumer exists. |
| Schedule verdicts have no episode (§3.8) | Traceable to plan and shop, not to an episode | By RM11 design (read-only). Stated as `SCHEDULE_READ_ONLY`. |
| Strict declared-intent rules (R3) | A real shop file must list every op and capability explicitly, which is more friction | Accepted. The friction is what separates intent from typos. The fixtures show the burden is seven op entries. |
| Shop-wide materials (§4.1) | A verdict can overstate feasibility when one machine cannot process a material | Documented limitation; candidate follow-up |
| Basis-agnostic retrieval (§4.2) | RM3/RM4 still rank and use cross-declaration precedent | It can't reach a verdict (enforced) and is labelled non-authoritative (§3.7). Callers bypassing `run_precedent_for_shop` get no label; documented. |
| Conservative report-level signal rule (§3.7) | One foreign entry marks the whole signal non-authoritative, even when the decisive entry was same-declaration | Accepted. Exact attribution would duplicate RM3 logic (Law 13). It errs toward "not evidence". |
| No forgery protection (§3.3) | Hashes detect loss and mismatch, not a consistent forgery | Signing is Noetica's provenance mechanism; out of scope; stated |
| G3 cost | Re-deriving plan hashes on load adds work per ref-carrying line | Linear and small; legacy lines are unaffected |
| Float canonicalisation | Tolerances are hashed through Python `json`, so a cross-language consumer may serialise differently | Contract note: consumers must re-canonicalise, or treat MP's hash as authoritative |
| Gate evolution precedent | Three gate evolutions in one milestone could normalise relaxing gates | Each evolution is narrower or stronger (§9) and ratified in ADR-0022. The pinned-content and manifest patterns replace "allow change" with "allow exactly this change". |
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
| 2026-11-06 | Research Director (final review) | Revision 2 (`c4a85e1`) | Substantially improved. Three questions (cross-shop precedent, two-hash truth table, verdict identity) and four confirmations required before freeze. |
| 2026-11-06 | Research Director | Revision 3 | Substantially accepted in principle. Two final clarifications: display-label identity and standalone verdict traceability. |
| 2026-11-06 | Owner | Revision 3.1 | **FROZEN and implementation AUTHORISED** under a strict scope lock with five conditions (correctness first, historical protection, scope control, full Docker gate on the committed tree, one milestone commit). Implemented and accepted in ADR-0022; deviations recorded there. |

## 13. Final-review confirmations

### C1. All nine acceptance criteria are falsifiable

| AC | Observable that would falsify it |
|---|---|
| AC1 | Any existing golden or corpus digest differs, or any existing test fails |
| AC2 | Any of the 902 golden rows differs in verdict dict, stripped plan hash or digest, or episode hash or digest; or a constrained-model verdict differs |
| AC3 | Any truth-table row gives the wrong same/changes value; a property counterexample; or the key and the declaration hash disagree |
| AC4 | Any variant's run 2 returns `reused=True` (notes excepted) or a verdict different from the fresh reference run |
| AC5 | An invalid fixture loads, gives a different issue code or order, the CLI exits anything other than 2, writes a file, or calls `default_model()` |
| AC6 | Banned wording in output; a `shop_declared` fixture; a second writer of `ShopModelSource`; a wrong basis label or `capability_evidence` value; or a verdict changes with cross-shop precedent present |
| AC7 | Any positive case fails, or any negative case passes silently, instead of raising or reporting the stated failure |
| AC8 | A 0.4.0 file changes beyond the declared property; an old instance fails validation; or the drift check is red |
| AC9 | Any gate red in the Docker verifier |

Each criterion names a deterministic, binary observable, and T10.1 mutants confirm the tests can fail.

### C2. The RM8 corpus is tested without regenerating historical goldens

- `tests/fixtures/rm8_default_behavior_golden.json` (from `rm5-complete` `96eb81f`) and `tests/rm8_behavior_probe.py`
  are **read**, never written.
- Their existing digest pins in `test_rm8_default_zero_diff.py` (the golden is the frozen baseline, and the probe is
  the one that generated it) stay unchanged and keep running.
- AC2 compares new outputs against the stored rows.
- Only the separate `contracts_digest` assertion evolves (§9). The golden's stored `contracts_digest` value is left
  as is.

### C3. The three gate evolutions preserve historical evidence

- **Tags** (`rm1-complete` … `rm15-corpus-frozen`) are never moved or deleted. The historical byte state stays
  checkable with `git diff <tag>` forever.
- **Golden files, probes and frozen fixtures** stay byte-identical, and their digest pins keep running.
- **RM2 gate:** every other file stays byte-frozen against `rm2-complete`. `reuse_runner.py` is re-frozen at the
  ratified content, and ADR-0022 records its exact diff from the tag.
- **RM8 contracts clause and the five `VERSION` pins:**
  - They are replaced by a manifest generated **once from `rm14-complete`** and frozen by digest.
  - It proves file by file that every 0.4.0 contract file is unchanged, except one structurally checked additive
    property.
  - That is the same fact the old pins expressed, checked more precisely.
- **Plainly stated:** six existing test assertions change: five `VERSION` pins and one `contracts_digest` equality.
  Two CI steps change as well: one file leaves the RM2 byte-diff set, and the suite-version value is updated. The
  tagged snapshots keep the original assertions intact as historical evidence. The edits need ratification in
  ADR-0022.

### C4. Synthetic and public-specification evidence cannot be presented as real-shop validation

- Every acceptance fixture is `synthetic`. `public_specification` requires cited sources. No fixture is
  `shop_declared` (AC6).
- The class is copied verbatim and never upgraded or derived. The only writer is the loader (T6.2).
- Every CLI line says "not independently verified". The words "verified" and "validated" are banned for shop
  declarations (AC6).
- The completion report and ADR-0022 must state:
  - MP-S1 proves software correctness on synthetic declarations only;
  - MP-E1, real-shop evaluation, remains **blocked** (ADR-0021 Q5).
- Cross-shop precedent is labelled non-authoritative and is never capability evidence (§3.7).
- Residual: MP cannot stop a user mislabelling a file. It never turns a label into a claim of validation.
