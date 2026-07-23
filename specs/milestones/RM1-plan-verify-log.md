# RM1 — Manufacturing Plan → Verify → Log (engineering specification)

- **Status:** Draft — Specification stage. Specification only; **no code** in this document.
- **Milestone:** RM1 (re-scoped first runtime milestone, replacing the withdrawn Situation State slice per ADR-0004 / CAP-0001).
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Owner:** Manufacturing team; Verifier-protocol + contract review: Architecture Board + Staff.
- **Governing sources:** `constitution/HANDBOOK_v1.1.md` §2.4 (MP charter), Law 3/4/6/9/12/14/15/18/21; `constitution/ARCHITECTURE_DECISION.md` STEP 5–7; `docs/governance/constitutional-evolution-report.md` Part 3; primary precedent `Velith/docs/DECISIONS.md` D3, D4, D6, D16.1, D16.3, D21.

---

## 1. Purpose — the smallest thing that demonstrates Mini Prometheus's purpose

Mini Prometheus exists "to turn verified engineering results into **manufacturable plans**" (Handbook
§2.4 Mission). The smallest end-to-end capability that demonstrates exactly this is a single manufacturing
task run to completion:

> **Consume one real engineer design request (or a Velith-verified design) → produce a manufacturing
> ProductionPlan → deterministically verify its manufacturability → log a provenance-complete
> manufacturing episode.**

This is the manufacturing-layer instantiation of the verification-first loop the whole ecosystem is
built on. It is the deliberate mirror of **Velith's own M1** (`propose → verify → log`, one task —
DECISIONS D16.3), lifted one layer up: **`plan → verify → log`**, where the *input* is an existing
design (an engineer's real part, or a Velith-verified result) rather than a raw problem. RM1 proves the
pipe end-to-end on a **real engineer input** (§7); it does not attempt manufacturing intelligence yet
(loop mechanics, not domain depth — the same discipline Velith applied at D4/D6).

## 2. Alignment with the ratified ownership boundaries

| Requirement | How RM1 satisfies it | Evidence |
|---|---|---|
| Align with ratified ownership | RM1 owns only **manufacturing content**: the design→plan mapping, the concrete manufacturability oracle, the ProductionPlan, the manufacturing episode. | Handbook §2.4; Report Part 3 |
| Consume Velith, don't re-implement engineering | The Velith `EngineeringResult`/`DesignArtifact` is consumed **opaque** (D24 opaque-materials) through `integrations/velith`; RM1 **never re-verifies the design** and never derives engineering. | Law 6/9; D24 |
| Don't re-implement Noetica mechanisms | RM1's oracle **implements Noetica's `Verifier` protocol** (interface only) and emits a `Verdict`; it does **not** rebuild the substrate, store engine, or provenance engine. | **Law 15** (oracle domain-owned, protocol Noetica-owned); Law 6 |
| Never import MiniFlyWire | Not referenced anywhere; enforced by import-linter. | Law 4 |
| Produce a tangible manufacturing artifact | A serialized, machine- and human-readable **ProductionPlan** (a manufacturing process routing) for the fixture part, plus its verdict and episode. | Handbook §2.4 public interface `ProductionPlan` |

## 3. Scope

**In scope (the minimal spine):**
1. A `ManufacturingTask` carrying a **real engineer-provided Manufacturing Request** — minimal metadata (material, stock form, declared features/operations, quantity, tolerances) — with an **optional STEP file** attached as the *opaque* reference design artifact. The Velith-verified path uses the **same** `DesignInput` contract with `engineering_verification_status = velith_verified` and is exercised by a compliance fixture. See §7.
2. A **deterministic** planner mapping the (opaque) design + an explicit **process/capability model** to a `ProductionPlan` (ordered, resource-assigned process steps).
3. A **deterministic manufacturability oracle** (MP-owned) checking the plan against the capability/constraint model, implementing Noetica's `Verifier` protocol, emitting a `Verdict`.
4. A **content-hashed manufacturing episode** (provenance-complete) written to an append-only store as an Experience-Flow data record.

**Out of scope (deferred, explicitly):**
- **STEP geometry interpretation / feature recognition** — parsing B-rep geometry needs a CAD kernel (e.g. OpenCASCADE). RM1 carries the STEP file **opaque** (never parses it); geometry-driven DFM is a later milestone ("wrap, don't rebuild" — the planner runs off the engineer's *declared* metadata).
- Real Velith **package** integration (RM2+); RM1 exercises the Velith-verified path via a contract fixture — mirrors Velith D16.3.
- Model-based (LLM) planning — RM1's planner is deterministic (see §9 trade-off); the model seam is named, not built (mirrors Velith D16.4).
- Noetica **state substrate / store-lifecycle engine** consumption — RM1 needs no persistent cross-episode state; the episode is emitted as owned content, the lifecycle framework (retention/compression) is Noetica's and deferred (Law 21 / §11.11).
- Physical execution, MES/PLC/robotics adapters, Sim2Real, digital-twin sync — later milestones (Handbook §2.4 future evolution).
- Multiple tasks, batch runs, optimization, scheduling across resources beyond one routing.

## 4. The RM1 loop and the tangible artifact

```
 Engineer ManufacturingRequest (+ optional opaque STEP)      [demonstrated path]
   — or — Velith EngineeringResult (fixture)                 [verified path, fixture-tested]
            │  integrations/ ingestion  (→ opaque DesignInput + verification_status; NO re-verification)
            ▼
   manufacturing_planning        ── deterministic ──▶  ProductionPlan
   (DesignInput + ProcessCapabilityModel)                (ordered ProcessSteps + ResourceAssignments)
            │                                                     │
            ▼                                                     ▼
   manufacturing_constraints  ── Verifier protocol ──▶  Verdict  (closed taxonomy)
   (capability/constraint model + concrete oracle)
            │
            ▼
   orchestration ── emit ──▶ ManufacturingEpisode (content-hashed, provenance-complete, append-only)
```

**Tangible manufacturing artifact:** the verified `ProductionPlan` — an ordered manufacturing process
routing for the fixture part (e.g. for a simple machined bracket: `load_stock → face_mill → drill(2×) →
deburr → inspect`, each step bound to a required machine capability and traced to the design feature it
realizes). It is serialized, content-hashed, and could be handed to a shop/MES. The episode is the second
concrete output.

## 5. Success criteria (RM1 is "logically complete" when all hold)

1. **End-to-end on real input:** given a **real engineer Manufacturing Request** (+ optional opaque STEP), the loop produces a well-formed `ProductionPlan` and a `Verdict` with no manual steps — a plan an engineer can use for *their* part.
2. **Consumes, doesn't re-derive:** the design is treated opaque; no engineering verification is performed by MP (asserted by a boundary test — no verify-call on the design).
3. **Grounded verdict, closed taxonomy:** the oracle returns one of `MANUFACTURABLE`, `NOT_MANUFACTURABLE`, `PLAN_INVALID`, `INFRA_ERROR`. A non-manufacturable plan is a **grounded outcome (success exit), not an error** (mirrors Velith D16.7).
4. **Provenance-complete:** every `ProcessStep` and the `Verdict` trace to their source design feature + the planning rule + the capability-model version (Law 18).
5. **Reproducible identity:** same design + same process/capability-model version ⇒ **same plan, same verdict, same `content_hash`**; volatile timing is excluded from the hash (mirrors Velith D16.1/D21).
6. **Ownership clean:** no MiniFlyWire import (Law 4); planning/constraint packages depend on `contracts/` only; the oracle implements Noetica's `Verifier` protocol (Law 15). Enforced by import-linter + a protocol-conformance test.
7. **Tangible artifact emitted:** the `ProductionPlan` and `ManufacturingEpisode` are written and re-readable, with the episode surviving process exit.
8. **Honest verification status:** the plan/verdict claim **manufacturability only** and record `engineering_verification_status` (`velith_verified` | `engineer_declared`); RM1 never implies the design's *engineering* correctness was checked when it was not (Law 18, Principle 10).

## 6. Contracts (define in this milestone; not implemented here)

**MP-owned, published (`contracts/schemas/manufacturing/`):**
- `ManufacturingRequest` — the real engineer input: `{ material, stock_form, declared_features_or_ops[], quantity, tolerances, step_artifact_ref? (opaque) }`.
- `ManufacturingTask` — `{ task_id, product_intent (minimal), design_input_ref }`.
- `DesignInput` — the opaque design carried into planning + `engineering_verification_status ∈ {velith_verified, engineer_declared}` (provenance). Produced *either* from a `ManufacturingRequest` (+optional STEP) *or* from a Velith `EngineeringResult`.
- `ProductionPlan` — ordered `ProcessStep[]`; each `ProcessStep = { op, required_capability, inputs, provenance_ref }`; plus `ResourceAssignment[]`.
- `ManufacturabilityReasonCode` — closed enum backing the verdict's detail.
- `ManufacturingEpisode` — Experience-Flow **data contract** (Law 21): `{ task, design_ref+hash, engineering_verification_status, plan, verdict, capability_model_version, content_hash, provenance }`; versioned.

**Consumed (interface/type only — not re-implemented):**
- Noetica `Verifier` protocol + `Verdict` type (Law 15) — MP's oracle implements the protocol.
- Noetica `Provenance` fields (Law 18) — populated as content.
- Velith `EngineeringResult` / `DesignArtifact` (ARCHITECTURE_DECISION STEP 7) — opaque input.

**Internal (NOT contracts — §13 of repo architecture):** the `ProcessCapabilityModel` representation, the deterministic planner rules, the oracle's check logic.

**Content-hash rule:** hash covers reproducible identity — `{task, design_ref+hash, plan, capability_model_version}`; excludes timing/latency (mirrors Velith D21). A test asserts a varying timestamp leaves the hash unchanged.

## 7. The input — real engineer request (and why STEP is carried opaque)

**RM1 accepts a real engineer-generated input, not an internal fixture.** The load-bearing input is a
minimal **`ManufacturingRequest`**: material, stock form, a short list of declared features/operations,
quantity, tolerances — which a practicing engineer can author in minutes for a real part, and which the
deterministic planner consumes directly. An engineer may **optionally attach a STEP file**; RM1 carries it
**opaque** as the reference `DesignArtifact` (content-hashed, provenance, shop hand-off) but **does not
parse its geometry** — feature recognition from B-rep needs a CAD kernel and is deferred ("wrap, don't
rebuild"; §3 out-of-scope).

Why this is the right input (not the earlier internal fixture): it gives a practicing engineer immediate,
tangible value — a manufacturability verdict and a process routing for **their own part** — which is the
North Star, while changing **nothing** about RM1's loop, contracts, boundaries, or simplicity. The design
is still treated **opaque** (D24), so the input *source* is an adapter concern, not an architectural one.

**Boundaries preserved:**
- *Velith not bypassed.* Manufacturability ≠ engineering verification; RM1 performs **no** engineering
  (Law 6/9). The Velith-verified path remains the **same** `DesignInput` contract with
  `engineering_verification_status = velith_verified`, exercised by a compliance fixture — so the
  north-star composition `Velith → MP` stays typed and testable at zero extra implementation. The
  engineer-direct path is labelled `engineer_declared` and never claims engineering correctness (Law 18).
- *No upstream-availability gate.* RM1 still depends only on the Velith/Noetica **contracts**, not their
  published packages (CAP-0001 Field 8) — but now the *demonstrated* path uses a real engineer input, so
  RM1 has real value on day one. Wiring the pinned Velith **package** for the verified path is RM2+.
- *Simplicity intact.* No CAD kernel; the deterministic planner and oracle are unchanged; a `ManufacturingRequest`
  is a small structured record.

## 8. Verification strategy

- **Contract-compliance suite** (`tests/contracts/manufacturing/`, implementation-agnostic): plan well-formedness (every step has a capability + provenance); verdict ∈ closed taxonomy; content-hash stability; episode round-trips.
- **Hermetic integration test** (`tests/integration/test_plan_verify_log.py`): the real plan→verify→log path on a sample `ManufacturingRequest`, asserting a **stable verdict and content hash** (direct analog of Velith's `test_spike_episode.py`). A parallel case runs the Velith-verified path from a fixture `EngineeringResult` (same `DesignInput`, `velith_verified`), proving both intake paths converge.
- **Negative test:** a `ManufacturingRequest` with a declared operation whose required capability is absent ⇒ `NOT_MANUFACTURABLE`, success exit, no error.
- **Determinism test:** two runs on identical inputs ⇒ identical `content_hash`.
- **Boundary/architecture tests (CI-enforced):** import-linter proves (a) no MiniFlyWire import (Law 4), (b) planning/constraint packages import `contracts/` only, (c) the oracle implements the Noetica `Verifier` protocol (Law 15), (d) the Velith result is consumed opaque with **no** design-verification call (Law 6/9).
- **CI gate** (`.github/workflows/ci.yml`, real stages replacing placeholders): build → unit → contract-compliance → integration → boundary. Non-skippable; red blocks merge.

## 9. Design trade-off — deterministic planner (RM1) vs. model-based (later)

RM1's planner is **deterministic and rule-based**, not model-based. Rationale, on precedent: the first
milestone must prove *loop mechanics*, and a deterministic planner makes the whole loop reproducible
end-to-end (success criterion 5) with **zero model dependency** — echoing Velith D3/D4/D6. When a
model-based planner is later introduced (a named seam, per Velith D16.4), the design **relocates
determinism into the oracle** exactly as Velith did (D16.1): the plan becomes stochastic, but the
verify→log path stays reproducible given a fixed plan. RM1 therefore builds the loop so that swap is
additive, not a rewrite.

## 10. Implementation plan (files/modules to create — no code in this spec)

1. **Contracts:** `contracts/schemas/manufacturing/{manufacturing_request,manufacturing_task,design_input,production_plan,manufacturing_episode}.*` + generated bindings; pin contract stubs of the consumed Velith/Noetica types.
2. **Intake:** a small MP-owned intake at the entry boundary maps a `ManufacturingRequest` (+ optional opaque STEP) → `DesignInput` (`engineer_declared`). This is MP **product-intent intake** (Handbook §2.4 input), *not* an upstream integration. Separately, `integrations/velith/` maps a Velith `EngineeringResult` → `DesignInput` (`velith_verified`, fixture-loaded). Both yield the same opaque contract; neither re-verifies engineering. `integrations/` stays Velith + Noetica only.
3. **`src/mini_prometheus/manufacturing_planning/`** — deterministic planner: `DesignInput` + `ProcessCapabilityModel` → `ProductionPlan`. *(Opens this package as the RM1 package — see §12.)*
4. **`src/mini_prometheus/manufacturing_constraints/`** — the `ProcessCapabilityModel` (content) + the concrete manufacturability oracle implementing Noetica's `Verifier` protocol.
5. **`src/mini_prometheus/orchestration/`** — composition root: adapter → planner → oracle → episode emitter.
6. **Episode emission** — content-hashed `ManufacturingEpisode` appended to a gitignored store (bind-mounted file, mirroring Velith M1); RM1-minimal, the full `experience/` package is a later milestone.
7. **Tests & fixtures:** `tests/contracts/manufacturing/`, `tests/unit/`, `tests/integration/test_plan_verify_log.py`, `tests/fixtures/` (a verified design fixture + a capability model + expected plan/verdict/hash).
8. **CI:** real `ci.yml` stages.

Build order (frozen workflow): contracts → planner → oracle → orchestration/emit → tests → CI.

## 11. Prerequisites and risks

- **Prerequisite (resolved for RM1):** no dependency on published Velith/Noetica packages — RM1 uses contract-shaped fixtures (§7). Real package integration is a hard gate for **RM2**, not RM1.
- **Risk — over-modeling the process/capability model.** Mitigation: RM1 ships the *smallest* capability model that makes one fixture routing checkable; richer models are later (no premature abstraction, D12/D15 discipline).
- **Risk — the oracle drifting toward engineering verification.** Mitigation: the oracle checks **manufacturability of the plan** only (capabilities, precedence), never the design's engineering correctness (that is Velith's, already verified). Enforced by the boundary test (§8d).
- **Risk — treating one sample request as a benchmark, or implying engineering verification.** Mitigation: RM1 proves the loop and delivers a plan for a real part; it is not a benchmark, and `engineering_verification_status` keeps the manufacturability claim honest (§5.8, Law 18).
- **Risk — scope creep into STEP geometry parsing.** Mitigation: STEP is carried opaque (§3 out-of-scope); a boundary test asserts the planner never reads STEP geometry.

## 12. Repository/doc reconciliation on ratification (not done here)

RM1 opens `src/mini_prometheus/manufacturing_planning/` as the **first** implemented package — MP's
chartered "heart" (§2.4). The indicative phase label in `docs/architecture/repository-architecture.md`
currently shows `manufacturing_planning [M2]`; on RM1 ratification that label should be updated to P1/RM1.
This is a minor, ADR-tracked doc reconciliation flagged here for the owner — **not** performed in this
specification, and not a constitutional change.

## 13. Open questions for review

1. **Demonstration domain / request shape:** machined part (process routing) or 2-component PCB (SMT assembly)? Both let an engineer author a minimal `ManufacturingRequest`; PCB is closer to Velith's D5 rung-2 "manufacturable artifact (Gerbers)". Recommendation: machined part for maximal determinism; confirm. (STEP is carried opaque either way — confirm that's acceptable, or whether RM1 should require metadata only.)
2. **Verdict taxonomy wording:** adopt `MANUFACTURABLE / NOT_MANUFACTURABLE / PLAN_INVALID / INFRA_ERROR` as the closed RM1 set (mirrors Velith's outcome/error split)? 
3. **Episode store location for RM1:** a local append-only JSONL (Velith-M1 style) as owned content emission, with the Noetica lifecycle framework deferred — confirm this respects your reading of Law 21/§11.11.

---

*Specification stage only. On acceptance, proceeds to Contract → Implementation → Testing → Verification → Commit → Review per the frozen workflow. Consumes Velith and Noetica by contract; re-implements neither; imports MiniFlyWire never.*
