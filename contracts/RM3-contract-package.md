# RM3 Contract Package — Engineering Precedent Reasoning (Precedent Report)

- **Status:** Draft — Contract stage. **Contract specification only** — no JSON Schema, no bindings, no code, no
  implementation. The authoritative design the later schema/binding generation must follow.
- **Derives from (frozen):** `specs/milestones/RM3-engineering-precedent-reasoning.md` (§4 Outputs, §5 model, §6
  boundaries, §8 invariants). Does **not** modify the specification.
- **Governing:** Handbook Law 3/6/8/14/18/21; RM1 contract package (`contracts/RM1-contract-package.md`) for the
  reused primitives and conventions.
- **Additive & frozen-preserving:** RM1 and RM2 contracts are **frozen and unchanged**. RM3 introduces exactly one
  new Mini Prometheus domain-owned output — the **Precedent Report** — plus its entry sub-type and one enum. All
  shared primitives are **reused unchanged**.

---

## 1. Reused frozen primitives and conventions (not redefined)

RM3 reuses, **byte-unchanged**, the RM1 contract package's global conventions and `common` primitives (RM1
package §1): **Canonical JSON (RFC 8785)** serialization; `content_hash = sha256(canonical_json(identity_view))`
(lowercase hex, `sha256:`-prefixed); **deterministic ids** via `uuid5(NS_MP, content_hash)` with the frozen
`NS_MP = 4f5b56ae-3c77-4135-9f5c-1eef0ab1b252`; and the shared types **`Ref` `{id, content_hash}`**, **`Provenance`**,
**`ProducedBy`**, **`ContentHash`**, **`Uuid`**, **`SemVer`**, **`Rfc3339`**. RM3 defines **no** changes to any of
these; it only *uses* them.

RM3 also **references** (does not redefine) these frozen RM1 enums by their existing value space:
`ManufacturabilityVerdictStatus` (`MANUFACTURABLE|NOT_MANUFACTURABLE|PLAN_INVALID|INFRA_ERROR`),
`ManufacturabilityReasonCode` (the six frozen codes), and `EngineeringVerificationStatus`
(`velith_verified|engineer_declared`). Referencing them keeps RM1/RM2 compatibility intact.

## 2. New enum (the only enum RM3 introduces)

**`PrecedentSignal`** — *closed* enum, report-level derived signal:

| Value | Meaning |
|---|---|
| `SUPPORTING` | The nearest strongly-relevant precedent was `MANUFACTURABLE`. |
| `CAUTIONARY` | The nearest strongly-relevant precedent was `NOT_MANUFACTURABLE` (its reason codes are surfaced). |
| `NONE` | No precedent cleared the (model-versioned) relevance threshold. |

Closed taxonomy: adding/removing a member is a **MAJOR** change (same rule as RM1's closed taxonomies). *(No other
new enum is required; verdict/reason/verification values are the referenced frozen enums of §1.)*

---

## 3. `PrecedentEntry` — precedent-entry data (sub-type)

- **Ownership:** Mini Prometheus (domain content). Sub-object of `PrecedentReport`; it has **no** independent id
  or content_hash (its identity lives within the report; its grounding is `episode_ref.content_hash`).
- **Schema (fields):**

  | field | type | req | notes |
  |---|---|---|---|
  | `rank` | integer ≥ 0 | ✔ | 0-based position in the ranked list; contiguous `0..n-1` |
  | `episode_ref` | `Ref` | ✔ | reference to the stored `ManufacturingEpisode` this precedent is (id + its content_hash) |
  | `relevance_score` | integer, `0..1000` | ✔ | **per-mille relevance** (1000 = identical, `D=0`); integer to keep hashing deterministic (see §6) |
  | `verdict_status` | string ∈ `ManufacturabilityVerdictStatus` | ✔ | the precedent's **verified** verdict status (referenced frozen enum) |
  | `reason_codes` | string[] ⊆ `ManufacturabilityReasonCode` | ✔ | the precedent's verdict reason codes (may be empty) |
  | `precedent_verification_status` | string ∈ `EngineeringVerificationStatus` | ✔ | whether the precedent's design was `velith_verified` or `engineer_declared` (honesty) |

- **Versioning:** none of its own; versioned via the enclosing report's `schema_version` and `precedent_model_version`.
- **Invariants:** `episode_ref` is a valid ref-by-hash; `relevance_score ∈ [0,1000]`; `verdict_status` and every
  `reason_codes[i]` are members of the referenced frozen enums; `precedent_verification_status` is a valid member.
- **Validation:** enum membership; integer range; `episode_ref.content_hash` matches the `sha256:` pattern.
- **Serialization:** canonical JSON (per §1), as a nested object of the report.
- **Compatibility:** additive; references frozen enums only.

## 4. `PrecedentReport` — report-level data (the RM3 output)

- **Ownership:** Mini Prometheus (domain content — the RM3 advisory output). Published.
- **Schema (fields):**

  | field | type | req | notes |
  |---|---|---|---|
  | `schema_version` | SemVer | ✔ | debut `1.0.0` |
  | `report_id` | Uuid, **deterministic** = `uuid5(NS_MP, content_hash)` | ✔ | reproducible id |
  | `query_design_input_ref` | `Ref` | ✔ | reference to the query's `DesignInput` (id + content_hash) — ties the report to the exact query |
  | `precedents` | `PrecedentEntry[]` | ✔ | ranked; **may be empty** |
  | `signal` | `PrecedentSignal` | ✔ | report-level derived signal (§2) |
  | `signal_source_rank` | integer ≥ 0, **or null** | ✔ | the `rank` of the entry that produced the signal; **null** iff `signal = NONE` |
  | `precedent_model_version` | SemVer | ✔ | the versioned precedent model that produced ranking/relevance/signal |
  | `content_hash` | `ContentHash` | ✔ | over the identity view (§6) |
  | `provenance` | `Provenance` | ✔ | see §7 |

  **Deliberate omission (honesty invariant):** the report carries **no** "query verdict" field. It is
  *structurally impossible* to present a precedent's verdict as the query's own verdict (spec §6/§8 honesty).

- **Versioning:** per §1; debut `schema_version = 1.0.0`. As an MP output/data record it carries `schema_version`
  for migration (Law 21). `precedent_model_version` versions the reasoning model (analogous to
  `capability_model_version` in RM1), so reports are reproducible and comparable across model revisions.
- **Invariants:**
  1. `precedents` are ordered by `relevance_score` **descending**, tie-broken by `episode_ref.content_hash`
     **ascending**; `rank` values are contiguous `0..n-1` in that order.
  2. `signal = NONE` ⇔ `signal_source_rank = null`. `signal = SUPPORTING` ⇒ `signal_source_rank` references an
     existing entry whose `verdict_status = MANUFACTURABLE`; `signal = CAUTIONARY` ⇒ references an existing entry
     whose `verdict_status = NOT_MANUFACTURABLE`.
  3. `content_hash` re-verifies; `report_id = uuid5(NS_MP, content_hash)`.
  4. Empty `precedents` ⇒ `signal = NONE`, `signal_source_rank = null`.
  5. No `query verdict` field exists (structural honesty).
- **Validation:** ordering + rank contiguity; signal/source consistency; enum membership (via entries); ref hash
  formats; SemVer formats.
- **Serialization:** canonical JSON (per §1). If a report is ever persisted, it is written append-only as one
  canonical-JSON object per line (same discipline as episodes); **persistence is optional and out of scope for
  RM3** (RM3 is read-only advisory).
- **Identity view (for `content_hash`):** `{schema_version, query_design_input_ref, precedents (rank,
  episode_ref, relevance_score, verdict_status, sorted reason_codes, precedent_verification_status), signal,
  signal_source_rank, precedent_model_version}`. **Excludes** `report_id` (derived), `content_hash` (self), and
  `provenance` (contains volatile `produced_at`).
- **Compatibility:** additive; introduces no change to any RM1/RM2 type.

## 5. Determinism rules (contract-level)

- **Relevance as an integer** (`0..1000`, per-mille) — chosen to avoid floating-point non-determinism in canonical
  JSON hashing. The exact `distance → relevance` mapping is governed by `precedent_model_version` (the model,
  frozen as versioned in the spec) and is **not** defined here.
- **Total, reproducible ordering:** sort by `relevance_score` desc, then `episode_ref.content_hash` asc — a total
  order, so identical inputs yield identical `rank`s.
- **Deterministic signal:** derived from the ranked entries and their verified verdicts under
  `precedent_model_version`; recorded with `signal_source_rank` as its provenance.
- **Hash stability:** identical query + identical precedent corpus + identical `precedent_model_version` ⇒
  identical `content_hash` and `report_id`; `produced_at`/provenance are excluded from identity.

## 6. Provenance population (Law 18)

`PrecedentReport.provenance` reuses the frozen `Provenance` shape:
- `source_refs` = `[query_design_input_ref]` followed by each surfaced `episode_ref` (what the report was derived
  from).
- `rule_id = "precedent.reasoning"`, `rule_version` = the reasoning component version, `produced_by = {component,
  version}`, `produced_at` = RFC 3339 (excluded from identity).
- `capability_model_version` (a **required** field of the frozen `Provenance`) is set to the sentinel **`"0.0.0"`**
  meaning *"not applicable — this record is precedent reasoning; its governing model is the top-level
  `precedent_model_version`."* This preserves the frozen `Provenance` shape unchanged (no contract modification).

## 7. Compatibility with RM1 and RM2

- **No change** to any RM1/RM2 contract, enum, or `common` primitive. RM3 only *adds* `PrecedentReport`,
  `PrecedentEntry`, and `PrecedentSignal`, and *references* frozen RM1 enums by value.
- **Suite version:** `contracts/VERSION` moves **`0.2.0 → 0.3.0`** (MINOR — additive contract set). Each new RM3
  schema debuts at its own `1.0.0`.
- Consumers of RM1/RM2 contracts are unaffected (nothing they read changed); a consumer that does not know
  `PrecedentReport` simply never encounters it.

## 8. Traceability

| Contract element | RM3 spec | Convention source |
|---|---|---|
| `PrecedentReport` (report-level) | §4 Outputs; §6.6 (separate report vs entry) | RM1 package §1 |
| `PrecedentEntry` (entry-level) | §4 Outputs | RM1 package §1 |
| `PrecedentSignal` enum | §4 (supporting/cautionary/none) | RM1 closed-taxonomy rule |
| relevance/ranking determinism | §5, §8 invariants | RM1 content-hash rule |
| omit query-verdict (honesty) | §6/§8 honesty | Law 18 |
| provenance + versioning | §4/§8 | Law 18, Law 21 |
| additive; RM1/RM2 frozen | §Immovable | Law 14 |

---

*RM3 contract specification only. No JSON Schema, no bindings, no code, no implementation, no engineering package.
On approval, the schema files + generated bindings are produced to follow this package, and `contracts/VERSION`
bumps to `0.3.0`.*
