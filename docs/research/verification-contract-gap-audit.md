# Mini Prometheus — Verification Contract Gap Audit

**Type:** Read-only audit (research/documentation only). No application code, schema, test, dependency,
roadmap, frozen spec, ADR, or Git state was modified. This file is a new research document; nothing else
was touched.

**Auditor role:** Chief Systems Engineer, Mini Prometheus.
**Method:** direct inspection of working-tree source, schemas, specs, and tests. Facts are cited to file
and function. Inference and hypothesis are labelled as such.

---

## 1. Executive finding

Mini Prometheus already protects the honesty property its RM1 spec names (§8: *"the plan/verdict claim
manufacturability only … RM1 never implies the design's engineering correctness was checked when it was
not"*) **at the persistence layer** — every episode records `engineering_verification_status`
(`velith_verified` | `engineer_declared`), and that field is folded into the episode's content-hash
identity. That part is sound.

The smallest real gap is one layer up, in **Engineering Judgment (RM4)**. The RM4 spec and the critic
model both describe judgment as reasoning over *"the verified precedent"* (RM4 spec §1 line 14; H1 line
26; `critic_model.py` docstring lines 11–13). The implementation does **not** honour the word *verified*:

- `precedent/reasoner.py::_derive_signal` derives the SUPPORTING/CAUTIONARY signal from **relevance +
  verdict status only** — it never reads `precedent_verification_status`, even though it records that
  field on every entry.
- `judgment/critic_model.py::_precedent_consistency` surfaces that signal as a SUPPORTIVE/CAUTIONARY
  finding, again without reading verification status.
- `judgment/engineering_critique.py::_critique_identity` excludes verification status from the critique's
  content-hash identity.

Therefore a strongly-relevant precedent that was **never reality-verified** (`engineer_declared`) produces
a judgment byte-identical to one backed by a `velith_verified` precedent. Combined with the fact that
**Velith is externally blocked** (ROADMAP: Velith `m8-complete`, `0.0.0`, no consumable API; RM6 planned),
the precedent corpus today contains essentially **no** `velith_verified` cases — so every SUPPORTIVE
judgment the system can currently produce rests on engineer-declared precedent while being framed, in
spec and docstring, as "verified precedent."

This is a **honest-scope / provenance-propagation gap in MP's own reasoning layer**, not a geometry, DFM,
tolerance, or CAD-interpretation gap. It is the smallest defensible, falsifiable gap found. The
recommendation (§9) is **NARROW: spec/research resolution only, no implementation yet.**

---

## 2. Current repository state and inspected commit

- **Branch:** `main`
- **HEAD:** `ab8cc449081c3fd6f36634824daaee267b4aad03` — `test(rdai1): end-to-end STEP artifact
  traceability into serialized episode (C2)` (2026-10-23).
- **Working tree:** **dirty**, but the dirt is **pure line-ending (CRLF) churn**. `git diff --stat` shows
  30 tracked files with an exactly symmetric `3633 insertions(+), 3633 deletions(-)`; `git diff -w` and
  `git diff --ignore-cr-at-eol` both return **empty**. One untracked file: `uv.lock`. **Conclusion
  (fact):** the on-disk content audited here is semantically identical to committed `ab8cc44`. All
  existing changes were preserved; no Git operation was run.
- **Contracts suite version:** `contracts/VERSION` = `0.4.0` (frozen). **Runtime:** `pyproject.toml`
  version `0.12.0`.
- **Milestone frontier (ROADMAP + tags):** RM1–RM5, RM8–RM14 complete; RM15 enriched-oracle
  re-evaluation present in `experiment/`; RDAI-1 C1/C2 committed. RM6 (real Velith) and RM7 (real
  Noetica) **planned/blocked**. Geometry-driven DFM is explicitly **deferred / out of scope**
  (`specs/milestones/RM1-plan-verify-log.md` §3).

---

## 3. End-to-end execution trace

Path followed in source, request → episode:

1. **Intake** — `intake/request_intake.py::intake` maps a `ManufacturingRequest` (+ optional opaque STEP
   `step_artifact_ref`) → `DesignInput`, hard-setting `engineering_verification_status =
   engineer_declared` (line 47). The Velith path `integrations/velith/adapter.py::from_engineering_result`
   sets `velith_verified` (line 52). Both yield the **same** opaque `DesignInput`; neither re-verifies
   engineering (RM1 spec §9 line 159).
2. **Plan** — `manufacturing_planning/planner.py::plan` maps declared operations 1:1 to `ProcessStep`s
   (index 0..n-1), assigns each a capability and the first **available** provider from the capability
   model, and (only under the relevant opt-in model/flags) carries RM8 tolerance, RM9 availability, and
   RM10 timeline data in the **open** `ProcessStep.params`. Deterministic; content-hashed. **It never
   reads STEP geometry** (RM1 spec §3 out-of-scope; boundary test asserted, spec §13 line 175).
3. **Verify** — `manufacturing_constraints/oracle.py::ManufacturabilityOracle.verify`. Docstring,
   verbatim: *"Checks are plan+model derivable only: well-formedness/precedence, capability existence, and
   material support."* Produces `MANUFACTURABLE` unless a structural, capability, material, declared-
   precedence, declared-tolerance, declared-availability, or timeline-consistency check fires. **No input
   other than `(plan, capability_model)`** — it does not see the design artifact, geometry, or
   `engineering_verification_status`.
4. **Log** — `orchestration/episode_store.py::build_episode` + `emit`. The episode embeds the full
   `DesignInput`, the plan, the verdict, and (top-level, **required**) `engineering_verification_status`.
   `_hashing.py::episode_identity` includes `engineering_verification_status` in the content-hash identity
   (line ~92). RDAI-1 traceability (`tests/integration/test_rdai_step_traceability.py`) proves the STEP
   **byte** hash survives verbatim into `design_input.design_artifact_ref.content_hash` and is committed
   through `design_ref` into the episode hash.
5. **Precedent (RM3)** — `precedent/reasoner.py::reason` builds a `PrecedentReport`; each `PrecedentEntry`
   records `precedent_verification_status` (line 75). `_derive_signal` (lines 79–91) picks the nearest
   strongly-relevant decisive precedent: `MANUFACTURABLE → SUPPORTING`, `NOT_MANUFACTURABLE → CAUTIONARY`
   — **using relevance + verdict status only.**
6. **Judgment (RM4)** — `judgment/engineering_situation.py::assemble` aggregates
   `(episode, precedent_report)` into an internal `EngineeringSituation` holding `design_input`, `plan`,
   `verdict`, `precedent_report` (so verification status **is available** in-situation).
   `judgment/critic_model.py::evaluate` runs three families — `_intent_coverage`, `_precedent_consistency`,
   `_internal_verdict` — and `assess` summarises (cautionary dominates). `engineering_critique.py::critique`
   orders findings, derives the assessment, and content-hashes the critique.

---

## 4. Guarantee matrix: claimed vs implemented vs tested vs unverified

| Category | What the implementation genuinely proves | What it assumes | What remains unverified |
|---|---|---|---|
| **Structural / schema validity** | Every artifact is `validate()`d against its frozen JSON-Schema; steps are contiguous `0..n-1`; carried timelines are internally consistent (`oracle._timeline_inconsistent`). **Tested** (`test_oracle.py`, `test_planner.py`, schema-compliance suite). | The schema encodes the intended structure. | Nothing material here — this category is solid. |
| **Process capability & constraint checks** | Each required capability has a provider in the **declared capability model**; material is in the model's supported set; declared precedence pairs are respected; a declared `required_tolerance_mm` is ≥ the capability's declared minimum. **Tested** (`test_oracle.py`). | The capability model is accurate; the declared ops/material/tolerance **describe the real part**. | Whether the real part actually needs those ops; whether the declared tolerance is achievable **on the geometry**. The tolerance check is **number-vs-number** (declared request value vs declared capability minimum), not a measurement on a solid. |
| **Resource availability & scheduling** | Deterministic availability-aware routing (RM9); single-job serialized timeline from engineer-declared `duration_min` (RM10); multi-job schedules with an **independently checked lower-bound certificate**, explicitly `NOT_OPTIMIZED` (RM11–RM14). **Tested** (goldens + regression corpora). | Operation **durations are engineer-declared inputs**, not estimated or verified; downtime/changeover are declared. | Real cycle times; real machine state; anything an actual MES would reconcile. The system correctly refuses to invent these. |
| **Design artifact identity & provenance** | A STEP file's **raw-byte** SHA-256 → opaque `DesignArtifactRef`, committed verbatim into the episode identity (RDAI-1 C1/C2). `engineering_verification_status` is recorded and hashed into episode identity. **Tested** (`test_step_intake.py`, `test_rdai_step_traceability.py`). | Byte identity is the intended notion of "same artifact." | Whether two byte-different files are **geometrically** equivalent, or byte-identical ones semantically equal — out of scope by design. |
| **Actual CAD geometry interpretation** | **Nothing.** STEP is carried **opaque**; a boundary test asserts the planner never parses it. | — | **All of it.** No B-rep, features, topology, or geometric tolerancing is read. Explicitly deferred (needs a CAD kernel; RM1 §3). |
| **Manufacturing feasibility, tolerance compliance, quality** | **Nothing on the physical artifact.** `MANUFACTURABLE` means *"this declared routing is structurally consistent with the declared capability model."* | That declared intent faithfully stands in for the physical part. | Real manufacturability, real tolerance compliance, DFM, and quality. The spec is explicit (§8) that this is **not** claimed. |

**Fact:** across the whole stack, `engineering_verification_status` is **recorded** (intake, episode,
precedent entry) but **never conditions any verdict, signal, finding, or assessment.** It is the one piece
of recorded provenance that the reasoning layer declines to use.

---

## 5. d2m and Palmetto comparison, with limitations

**Limitation (stated plainly):** neither `d2m` nor `Palmetto` is present in the Mini Prometheus working
directory, and no repository link was available to this audit session. I therefore **could not inspect
their actual implementation, documentation, or tests** as requested in §B. The characterisations below are
the Director's own (as provided) plus general domain knowledge; **their specific guarantees and test
behaviour are reported as unverified-this-session** and must be confirmed by direct inspection before any
decision relies on them. I did not invent test contents or accuracy figures.

- **d2m (as characterised):** STEP geometry comparison + manufacturing-trust prototypes; its tests
  reportedly distinguish *nominal geometry comparison* from *manufacturing readiness*. Conceptually this
  is a **different guarantee** from MP's: d2m produces **geometric-difference evidence between two solids**
  (a capability MP explicitly does not have and, per Director constraint, must not rebuild). It does not,
  on this characterisation, produce an *honest, verification-provenance-conditioned engineering judgment*.
- **Palmetto (as characterised):** CAD feature recognition + rule-based DFM, with **real-world accuracy
  and coverage not independently established.** Again a **different** capability (feature/DFM extraction),
  and its unestablished accuracy is itself a reason not to treat it as a closed guarantee.

**Assessment (inference, clearly labelled):** the gap identified in §1/§7 is about propagating MP's
**existing recorded verification provenance** into MP's **own judgment** — it requires **no geometry, no
feature recognition, no STEP comparison.** On the available characterisation, it is therefore **not**
covered by d2m or Palmetto, which operate on geometry/features rather than on MP's judgment honesty. This
conclusion does not depend on d2m/Palmetto internals, so the inability to inspect them does not weaken it;
it only means the "already covered elsewhere?" check for *geometry* gaps (which this audit is **not**
recommending) remains open.

---

## 6. Contract / runtime mismatches

**Mismatch A (primary, demonstrated from source).** *Documented "verified precedent" vs unconditioned
behaviour.*
- **Claim:** RM4 spec §1 (line 14) — judgment reasons over *"the **verified** precedent Mini Prometheus
  has surfaced"*; H1 (line 26) frames the success criterion over precedent verdicts; `critic_model.py`
  docstring (lines 11–13) — PRECEDENT_CONSISTENCY consumes *"the strongly-relevant **verified**
  precedent."*
- **Runtime:** `reasoner._derive_signal` (lines 88–91) and `critic_model._precedent_consistency`
  (lines 138–165) read only relevance + `verdict_status`; `engineering_critique._critique_identity`
  (lines 84–98) omits verification status from the critique's content hash. `precedent_verification_status`
  is recorded (`reasoner._entry` line 75) but never consumed.
- **Consequence (fact):** two `EngineeringSituation`s identical except the supporting precedent's
  `precedent_verification_status` (`velith_verified` vs `engineer_declared`) yield **byte-identical**
  findings, assessment, and critique `content_hash`. (Predicted from the code path; not executed, per the
  no-implementation constraint. No existing test asserts otherwise — `grep` over
  `tests/**/test_*critic*|*situation*|*judg*` finds **zero** references to verification status.)
- **Severity:** honesty/Law-18 scope. Not a crash, not a data-corruption bug. It lets a SUPPORTIVE
  judgment be read as resting on verified experience when, today, it cannot.

**Observation B (by-design, not a defect).** The default CLI path does **not** read `request.tolerances`
(`runner.py::_main` lines 150–153); only `--capability-model constrained` carries tolerance. This is a
**documented** limitation (RM8), not a mismatch.

**Observation C (scoping note, not a defect).** Timeline/tolerance/availability semantics ride in the
**open** `ProcessStep.params` (`production_plan.schema.json` — `params: additionalProperties: true`), so a
pure schema validation cannot assert their semantics; the oracle re-derives/checks them at runtime. This
is an intentional open-seam design; flagged only for completeness.

**No other contract defect was demonstrable from source.** The RM1 persistence-layer honesty mechanism is
correctly implemented.

---

## 7. Smallest defensible gap, with falsifiable acceptance criteria

**Gap (precise, falsifiable):**
> Mini Prometheus's Engineering Judgment (RM4) does not make a precedent's recorded
> `engineering_verification_status` load-bearing. A SUPPORTIVE assessment derived from an
> `engineer_declared` (never reality-verified) precedent is indistinguishable — in finding content and in
> the critique's content-hash identity — from one derived from a `velith_verified` precedent, despite spec
> and docstring describing the input as "the verified precedent."

- **Human / engineering problem it solves.** A downstream engineer (or a later evaluation/decision rung)
  reading a SUPPORTIVE engineering judgment should be able to tell whether the supporting experience was
  **verified against reality** or **merely declared by an engineer.** Those carry very different
  epistemic weight on a real shop floor; conflating them is exactly the over-reading RM1 §8 forbids.
- **Existing behaviour & failure mode.** Signal and finding are computed without verification status;
  the critique hash excludes it. With Velith blocked, the corpus is ~entirely `engineer_declared`, so the
  distinction the spec relies on is, in practice, always collapsed to the declared side while labelled
  "verified."
- **Exact evidence needed to close it.** The verification status is **already present** in the situation
  (`design_input.engineering_verification_status`; per-entry `precedent_verification_status`). Closing the
  gap requires only that judgment **carry or condition on** it — e.g., a SUPPORTIVE
  `PRECEDENT_CONSISTENCY` finding records the supporting precedent's verification status, and that status
  enters `_critique_identity`. No new data source, no geometry.
- **Already covered elsewhere?** No. **Velith** *produces* the status (it is the reality authority) but
  cannot make MP's judgment honest about it — that is MP reasoning-layer responsibility. **Noetica** is
  platform substrate, not manufacturing judgment. **d2m / Palmetto / OCCT** operate on geometry/features,
  a different axis. **PLM/PDM** track revisions/approvals, not an advisory critique's evidence provenance.
- **Minimum viable validation test (specification only — not implemented here).**
  Construct two `EngineeringSituation`s, `S_verified` and `S_declared`, identical in design, plan, verdict,
  and in the supporting precedent **except** its `precedent_verification_status`. Run `critique()` on each.
  - **Measured quantity:** equality of the two critiques' `content_hash` (a single boolean), plus a diff
    of the `PRECEDENT_CONSISTENCY` finding.
  - **Current expected result (demonstrates the gap):** `content_hash` **equal**, findings **identical**.
  - **Post-fix expected result (gap closed):** `content_hash` **differs** (and/or the finding names the
    verification status), proving verification provenance is load-bearing in judgment.
  This is fully falsifiable, deterministic, and requires no geometry, CAD kernel, or external package.

---

## 8. Risks, counterarguments, and alternative explanations

- **Counterargument 1 — "It's a docstring imprecision, not a logic defect."** Defensible. `RankedPrecedent`
  and the reasoner's own signal docstring do **not** say "verified"; only the RM4 spec and critic docstring
  do. If the project's intent is that "verified" was loose wording, the minimal correction is a **text
  change**, not new logic. The audit's job is to surface the mismatch; which side moves is the Director's
  call. Either way the honest-scope question is real.
- **Counterargument 2 — "By design for v1.0.0; the entry already carries the status for a future
  version."** Also defensible — `precedent_verification_status` is recorded precisely so a later critic can
  use it. Then the gap is a **planned-but-open** honesty item, and the right artefact is a spec/ADR note,
  not code now. (Consistent with §9's NARROW recommendation.)
- **Counterargument 3 — "Velith is blocked, so there are no verified precedents anyway; the distinction is
  moot today."** This actually **strengthens** the honesty concern: because the corpus is all
  `engineer_declared`, every SUPPORTIVE judgment the system can emit is framed as "verified precedent"
  while resting on declared evidence. The fix costs nothing geometric and future-proofs the moment Velith
  unblocks.
- **Risk of over-reaction.** Do **not** turn this into "make MP verify geometry/DFM." That would duplicate
  d2m/Palmetto/OCCT and violate the frozen out-of-scope boundary. The gap is strictly about honest
  propagation of **existing** provenance.
- **Alternative explanation for the symmetric diff.** The dirty working tree is CRLF churn (proven in §2),
  **not** in-progress logic; the audit reflects committed semantics.
- **Evidence limitation.** d2m/Palmetto internals were not inspectable this session (§5); the finding does
  not depend on them, but the "covered elsewhere?" check for any *geometry* gap remains formally open.

---

## 9. Recommendation: proceed, narrow, or stop

**NARROW — resolve by specification, do not implement yet.**

There **is** a genuine, source-demonstrated gap (§6A/§7), but it is small and its correct resolution is a
governance decision, not an engineering sprint. Recommended path:

1. Decide the intent of "verified precedent" in the RM4 spec and `critic_model` docstring: is verification
   status **meant** to be load-bearing in judgment?
   - **If yes:** schedule a minimal, additive change (no new contract) that carries
     `precedent_verification_status` into the `PRECEDENT_CONSISTENCY` finding and into
     `_critique_identity`, guarded by a `critic_model_version` bump, with the §7 falsifiable test as the
     acceptance gate. Keep RM1–RM3 byte-unchanged.
   - **If no:** correct the spec/docstring wording so it no longer claims "verified," and record the
     decision in an ADR. This alone closes the *mismatch*.
2. Do **not** add any geometry, DFM, STEP-comparison, feature-recognition, or CAD-kernel capability. Those
   are out-of-scope, partly covered by d2m/Palmetto, and not what this gap is about.

This protects Mini Prometheus from (a) silently over-claiming verified experience, and (b) the far larger
error of building a geometry/DFM capability that already exists elsewhere and that the evidence does not
justify owning here.

---

## 10. Proposed next step (research / spec only; no implementation)

Open a short **decision note / draft ADR** titled *"Is verification provenance load-bearing in Engineering
Judgment?"* that:
- states the §6A mismatch with the exact source citations;
- presents the two resolutions (condition-on-status vs correct-the-wording) with trade-offs;
- includes the §7 falsifiable test as the acceptance criterion for the "yes" branch;
- is reviewed by the independent reviewers before **any** code is authorised.

No code, schema, test, contract, roadmap, or Git change is proposed at this step.

---

## 11. Source references

**Mini Prometheus source (working tree @ `ab8cc44`):**
- `src/mini_prometheus/manufacturing_constraints/oracle.py` — `ManufacturabilityOracle.verify`,
  `_timeline_inconsistent`, `_declared_precedence_violated`, `_tolerance_unsupported` (plan+model-only
  checks; no geometry; no verification status).
- `src/mini_prometheus/manufacturing_planning/planner.py` — `plan`, `_attach_timeline` (1:1 declared→step;
  open-params carriage; never reads STEP).
- `src/mini_prometheus/orchestration/runner.py` — `run`, `run_from_request`, `_main` (composition root;
  default path does not read `tolerances`).
- `src/mini_prometheus/intake/request_intake.py` — `intake` (sets `engineer_declared`, line 47).
- `src/mini_prometheus/integrations/velith/adapter.py` — `from_engineering_result` (sets
  `velith_verified`, line 52).
- `src/mini_prometheus/orchestration/episode_store.py` — `build_episode`, `emit`.
- `src/mini_prometheus/_hashing.py` — `episode_identity` (includes `engineering_verification_status`),
  `design_input_identity` (opaque artifact → content_hash only).
- `src/mini_prometheus/precedent/reasoner.py` — `_entry` (records `precedent_verification_status`, l.75),
  `_derive_signal` (ignores it, l.88–91).
- `src/mini_prometheus/judgment/engineering_situation.py` — `assemble`, `EngineeringSituation`.
- `src/mini_prometheus/judgment/critic_model.py` — docstring "verified precedent" (l.11–13),
  `_precedent_consistency` (l.138–165), `_internal_verdict`, `assess`.
- `src/mini_prometheus/judgment/engineering_critique.py` — `critique`, `_critique_identity` (excludes
  verification status, l.84–98).

**Schemas:**
- `contracts/schemas/manufacturing/manufacturability.schema.json` — closed status/reason-code taxonomies.
- `contracts/schemas/manufacturing/production_plan.schema.json` — `ProcessStep.params`
  `additionalProperties: true` (open seam).
- `contracts/schemas/manufacturing/manufacturing_episode.schema.json` — required top-level
  `engineering_verification_status`; `design_input` optional & excluded from identity.
- `contracts/schemas/manufacturing/design_input.schema.json` — `EngineeringVerificationStatus` enum;
  `DesignArtifactRef` ("OPAQUE … Never parsed by RM1").

**Specs / docs:**
- `specs/milestones/RM1-plan-verify-log.md` — §3 out-of-scope (STEP opaque); §8 honest verification status.
- `specs/milestones/RM4-engineering-judgment.md` — §1 "verified precedent" (l.14); H1 success criterion
  (l.26); honesty boundaries (l.48, 56, 69).
- `docs/ROADMAP.md` — milestone frontier; Velith blocked (`0.0.0`, no API); RM6/RM7 planned.

**Tests:**
- `tests/integration/test_rdai_step_traceability.py`, `tests/unit/test_step_intake.py` — artifact
  byte-identity & traceability.
- `tests/unit/test_oracle.py`, `tests/unit/test_planner.py` — capability/constraint/timeline checks.
- `tests/unit/test_critic_model.py`, `tests/unit/test_engineering_situation.py`,
  `tests/unit/test_engineering_judgment.py` — judgment layer; **none** assert sensitivity to verification
  status (`grep` confirmed zero references).

**External (characterised, NOT inspected this session — see §5):** `d2m` (STEP geometry comparison /
manufacturing-trust prototypes); `Palmetto` (CAD feature recognition / rule-based DFM, accuracy
unestablished). No repository URLs were available to the audit; their specific guarantees remain to-verify.
