# RM3 Research Report — the single highest-value milestone after RM2

- **Type:** First-principles research. **No code, no repository changes, no specification/engineering-package/implementation-plan.**
- **Inputs:** Constitution (HANDBOOK_v1.1), the frozen roadmap (`docs/ROADMAP.md`), RM1/RM2 as built, ADR-0005/0006.
- **Constraint honored:** delivered outside the repo (per instruction). Proposed home on approval: `docs/research/`.

---

## 1. Baseline — what exists after RM1 + RM2

- **RM1 (`plan → verify → log`, 0.2.0):** engineer `ManufacturingRequest` (declared operations; geometry opaque)
  → deterministic `ProductionPlan` (routing) → manufacturability oracle (capability existence + material + linear
  precedence) → content-hashed `ManufacturingEpisode` logged.
- **RM2 (experience reuse, 0.3.0):** read side of the Experience Flow; **exact-key** retrieval
  `(design_input_identity_hash, capability_model_version)`; reuse prior verified plan/verdict with a
  reproducibility guard. **Compounding rung 1 = exact reuse.**

So today the system can *plan, verify, log, and re-serve an identical prior result*. It cannot yet: consume a
real verified engineering design; generalize experience beyond byte-identical requests; learn or adapt; reason
about geometry; schedule/optimize; or express calibrated uncertainty.

## 2. Constitutional frame — what "true engineering intelligence" requires

The Constitution defines the ecosystem's mission as a **stateful, grounded, self-improving** system whose
**competence compounds** (§1.1, §1.7). Its spine is explicit: **Principle 8 — "experience without improvement is
failure, however impressive a single output looks."** The intelligence trajectory it implies is:
state (RM1) → verified logging (RM1) → **retrieval of relevant experience** → **learning/adaptation** →
**calibrated, causal reasoning**. Grounding in real verified engineering (Velith→MP) and real platform
mechanisms (Noetica) are also required for the endpoint.

## 3. Gap inventory (every major missing capability, classified)

| Missing capability | Advances | Buildable now? |
|---|---|---|
| Real **Velith-verified design** input (not engineer-declared, opaque) | Grounding | **No — externally gated** (Velith unpublished as a package; its vertical is software/SWE, not manufacturable designs — D4/D5 rung 1) |
| Real **Noetica** mechanisms (substrate/provenance/Verifier/memory) | Platform grounding | **No — externally gated** (Noetica is grown by extraction, N.3; likely unpublished; RM2 is its extraction *seed*) |
| **Generalized experience retrieval** (similar, not identical, requests) | **Compounding (spine)** | **Yes — self-contained, no external gate** |
| **Adaptive planning / learning** (experience changes future plans) | Compounding | Not yet — needs a mature retriever + a learnable representation + calibration (research-adjacent) |
| **Manufacturability depth / DFM** (tolerance/process feasibility from geometry) | Verification quality | Partly — real DFM needs geometry (CAD kernel); declared-feature DFM is shallow/premature |
| **Scheduling & optimization** (allocate resources over time; batching for quantity) | Manufacturing content | Yes — self-contained, but a *leaf* (nothing depends on it) |
| **Calibrated / graded verdicts** (Law 16 distributions) | Honesty | No — needed only when the oracle is *approximate* (physics), which needs geometry |
| **STEP geometry / feature recognition** | Grounding in real parts | No — a milestone-cluster; robust feature recognition is research-grade |
| **Physical execution** (MES/robotics/Sim2Real) | Top of stack | Far future (Handbook §2.4 last) |

## 4. Candidate RM3 directions

- **C1 — Real Velith integration** (verified-design path via the pinned Velith package). *(Roadmap's tentative RM3.)*
- **C2 — Real Noetica integration** (substrate/provenance/Verifier/memory via pinned package).
- **C3 — Generalized (similarity-based) experience retrieval** — compounding rung 2: retrieve *relevant* prior
  episodes for a non-identical request and surface them (nearest precedent + its verdict), over a deterministic
  structural distance. Extends RM2's read side.
- **C4 — Manufacturing scheduling** — extend RM1's routing to deterministic multi-resource sequencing/allocation
  and quantity batching (MP's chartered "planning **and** scheduling" heart, §2.4).
- **C5 — Adaptive planning / learning** — use experience to change future plans.
- **C6 — Manufacturability depth (declared-feature DFM)** — richer oracle without geometry.

## 5. Comparison (first-principles, six axes)

| Axis | C1 Velith | C2 Noetica | **C3 Retrieval** | C4 Scheduling | C5 Learning | C6 DFM depth |
|---|---|---|---|---|---|---|
| **Computational necessity** | Eventually (grounding) | Eventually (platform) | **High now** — RM2's exact reuse is near-useless on real (varying) requests; retrieval is what makes compounding *real* | Medium (usable output) | High (endpoint) but not yet | Medium |
| **Architectural leverage** | Low (adapter already proven) | Low-Med | **Highest** — the retrieval substrate that learning, calibration, and Noetica's memory extraction all sit on | Low (leaf) | High but downstream | Low-Med |
| **Dependency ordering** | Blocked (external) | Blocked (external, furthest) | **Unblocked; builds directly on RM2** | Unblocked | Needs retriever first | Needs geometry |
| **Long-term scalability** | High | High | **High — on the critical path to intelligence** | Medium | High | Medium |
| **Verification complexity** | Low-Med *if published* | Med | **Medium** — deterministic distance + ranking; no ML, no held-out interaction in RM3 | Med-High (deterministic optimization is fiddly) | High | Med |
| **Constitutional compatibility** | High (canonical) but honesty-gated by the manufacturable-rung | High but blocked | **High** — MP content; Law-6 boundary (no store engine); extraction seed (Law 8); D25/D7/D8-compatible if deterministic & read-only | High (content) but a "deepen" item (roadmap RM5+) | High endpoint, premature now | High but premature/shallow |

## 6. Rejections (justified)

- **C1 Real Velith — reject as RM3 (defer to RM4).** Doubly blocked: Velith is not published as a consumable
  package, *and* its current vertical emits verified software patches, not manufacturable physical designs
  (D4/D5 rung 1) — so real integration now yields provenance plumbing but no manufacturing value, and would stall
  on an external gate. It is *necessary for the endpoint* but not the next *buildable, value-adding* step. (Same
  reasoning that reprioritized RM2.)
- **C2 Real Noetica — reject (defer).** The furthest-gated dependency: "Noetica the platform" is grown by
  extraction from the domain apps (N.3); RM2 is its seed. Integrating a not-yet-extracted platform is impossible
  and inverts the extraction order (Law 8).
- **C4 Scheduling — reject as RM3 (defer to content-deepening RM5+).** Genuinely MP-owned and useful, but a
  *leaf* (nothing depends on it) and it does **not** advance the compounding spine — adding a better single
  output is exactly what Principle 8 says is *not* the priority. Better after the intelligence substrate exists.
- **C5 Learning — reject (premature).** Requires a mature retriever, a learnable planner representation, and
  calibration — none present. Attempting it now risks the "not a research project" boundary (§1.9).
- **C6 DFM depth — reject (premature/shallow).** Real DFM needs geometry (deferred); declared-feature DFM guesses
  a model with no real driver (premature abstraction, D12/D15).

## 7. Recommendation — **RM3 = Generalized (similarity-based) experience retrieval (compounding rung 2)**

**Why it must come before the alternatives (first principles):**

1. **It is the only unblocked candidate that advances the Constitution's spine.** Compounding is the falsifiable
   commitment (§1.7, Principle 8). RM1+RM2 do not yet compound *in practice*: exact-key reuse hits only on
   byte-identical requests, which real engineers almost never submit. Generalized retrieval is what turns "we
   logged it" into "we can find and use relevant prior experience" — finishing the capability RM2 began, not
   speculating a new one.
2. **Dependency ordering makes it prerequisite, not optional.** Retrieval of *relevant* experience is
   computationally **prior** to adaptive planning (C5), calibration, and Noetica's memory extraction — you cannot
   learn from or adapt to experience you cannot retrieve. Scheduling (C4) is a leaf that unblocks nothing;
   Velith/Noetica (C1/C2) are externally blocked. So among all candidates, C3 is the one whose absence blocks the
   most of the future while itself being buildable today.
3. **Highest architectural leverage, lowest external risk.** It extends the read side RM2 just built (reader +
   index), needs no external package, and is the extraction seed for Noetica's retrieval mechanism (Law 8, N.3) —
   the same seed pattern the Constitution endorses.
4. **Immediately useful, and constitutionally clean if scoped right.** Its RM3 consumer is *precedent surfacing*:
   for a new request, surface the nearest prior episode(s) and their verdicts (e.g., "a 92%-similar part was
   `NOT_MANUFACTURABLE`: `CAPABILITY_MISSING`"). That helps an engineer now and warms the path for adaptive
   planning later — so it is not retrieval-without-a-consumer (avoids premature abstraction).

**Constitutional design constraints the eventual RM3 must honor** (stated as research findings, not a spec):
a **deterministic structural distance** over `DesignInput` fields (material, stock form, declared-operation
sequence, quantity, tolerance) — **no embeddings/ML, no vector DB** (that would be a Noetica store engine, Law 6);
a **read-only** retriever that writes nothing (so it never contaminates a future held-out lock, D7/D8) and is
**compatible with distance-based held-out exclusion when the compounding *experiment* is later run** (D25 — which
defers distance-based *exclusion in evaluation*, not retrieval-to-inform); and it stays the minimal MP-owned
**extraction seed** for Noetica, not a general memory framework.

## 8. Intentional deferrals (and why)

- **Real Velith integration → RM4**, gated on Velith publishing a consumable package *and* reaching a
  manufacturable rung (PCB/mechanical). Grounding matters, but cannot be built or add value yet.
- **Real Noetica integration → after Noetica is extracted/published**, per the extraction order (N.3, Law 8).
- **Adaptive planning / learning → after** the retriever exists and an approximate/graded oracle exists.
- **Calibrated/graded verdicts → with the approximate (physics) oracle**, which needs geometry.
- **Manufacturability depth / STEP geometry / feature recognition → a later CAD-wrapping milestone-cluster**
  ("wrap, don't rebuild"), too large and research-grade for one milestone now.
- **Scheduling/optimization → content-deepening (RM5+)**, once the intelligence substrate exists.
- **Physical execution (MES/robotics/Sim2Real) → far future** (top of the stack).

## 9. Roadmap implication (for owner ratification — not a change performed here)

The frozen roadmap lists RM3 = real Velith. This research, on first principles, recommends **RM3 = generalized
experience retrieval**, with **real Velith → RM4** (gated) — the same evidence-based reprioritization applied to
RM2 (compounding over an externally-blocked integration). This is a *proposed* revision requiring your ratification;
no roadmap edit has been made.

---

*Research report only. No specification, engineering package, or implementation plan produced. No repository
modified.*
