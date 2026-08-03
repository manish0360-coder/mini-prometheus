# RM4 Specification — Engineering Judgment (first implementation: Engineering Critique)

- **Status:** Frozen (accepted; ADR-0008). **Specification only.**
- **Milestone:** RM4 (fourth runtime implementation milestone).
- **Frozen architectural identity:** **Engineering Judgment** — the deterministic, advisory capability of *judging a proposed manufacturing solution in the full engineering context of its case*. Its **first implementation** is **Engineering Critique** (the situated critical review of a proposed production plan). Future forms — comparison, ranking, evaluation, optimization advice — fit **beneath** Engineering Judgment as additional implementations **without changing RM4's identity**. RM4 is also the **first real consumer** of the internal **EngineeringSituation** primitive, and the **instrument through which that primitive's stable shape is revealed rather than predicted**.
- **Layer:** Mini Prometheus (Layer 4). Constitution v1.1.0. Builds additively on RM1 (plan → verify → log), RM2 (exact reuse), and RM3 (Engineering Precedent Reasoning).
- **Governing:** HANDBOOK_v1.1 (Laws 3/4/6/8/9/14/18/21/22/23; §1.6, §1.7, §1.9, §11.11, N.3); the frozen RM1/RM2/RM3 specifications; the RM3 architectural-review conclusion on EngineeringSituation; the RM3 Future Governance Note (Extraction Review Gate).
- **Immovable:** RM1, RM2, and RM3 are frozen; RM4 is purely additive. **EngineeringSituation remains INTERNAL to RM4** — no contract, no schema, no persistence, no external exposure.

---

## 1. RM4 identity

RM4's architectural identity is **Engineering Judgment**: the capability to **judge a proposed manufacturing solution in the full context of its case** — to assess, grounded and deterministically, whether a proposed solution is sound given the case's declared intent, its normalized engineering design, and the verified precedent Mini Prometheus has surfaced for it. Judgment is *advisory reasoning about a solution's soundness in context*; it is neither construction (planning) nor proof (verification) nor decision.

Engineering Judgment is deliberately defined **broader than any single form of judgment**. Its **first implementation, delivered in RM4, is Engineering Critique**: the situated critical review of a proposed production plan, producing advisory grounded findings and a summary assessment. Later capabilities are **additional implementations of the same identity** and must fit beneath it without redefining it — for example **comparison** (judging candidate solutions against one another), **ranking**, **evaluation** (scoring against explicit criteria), and **optimization advice** (advising where a solution could improve, without mutating it). What unifies every form: each consumes the coherent engineering situation of a case, each produces **advisory, grounded, deterministic** judgment, and **none** plans, verifies, or decides.

This is **compounding rung 3**. RM1 produced plans and grounded verdicts; RM2 reused *identical* experience; RM3 surfaced *analogous* precedent. RM4 is the first capability that **reasons over the whole case rather than a single artifact**, advancing the compounding spine (§1.7) toward the one goal: an AI Manufacturing Intelligence that reasons like an experienced manufacturing engineer and improves from verified experience.

RM4 has a **second, deliberate architectural purpose**: it is the **first real consumer** of the internal **EngineeringSituation** primitive, tasked with **revealing the primitive's stable shape rather than predicting it** — what the judgment actually reads and requires is the evidence from which the primitive's eventual shape is learned. RM4 does not create, publish, persist, or expose that primitive.

RM4 is **domain reasoning content** (Law 3): the notion of *what makes a manufacturing solution sound in context* is Mini Prometheus's. Any general situation-assembly machinery is *mechanism*, held MP-local only as a potential future extraction seed — never RM4's identity.

## 2. Scientific hypotheses (falsifiable)

- **H1 — Situated critique.** Critiquing a proposed plan against the *complete, coherent engineering situation* of its case yields **more useful, better-grounded** judgment than critiquing it in isolation (as RM1's structural verification does): some sound-looking plans carry risk **only visible in context** (e.g., a structurally valid plan resembling a strongly-relevant precedent that was *not manufacturable*). A later milestone experimentally tests whether situated critiques correlate with real outcomes better than isolated checks; if not, the critic model or situation assembly is revised or rejected. **Measurable success criterion:** on paired cases, the critique's assessment agrees with the strongly-relevant precedent's verdict on ≥95% of cases with zero cautionary false alarms on controls (assessed by a later evaluation milestone; RM4 runs no harness).
- **H2 — Extraction by observation.** The **stable shape** of EngineeringSituation can be **discovered by observing what a real consumer (the RM4 critic) requires**, and that shape will prove reusable. Falsifiable in reverse: if the load-bearing constituents keep changing as the critic evolves, the shape is not yet stable and extraction remains unjustified.

## 3. Inputs

RM4 receives the case's **already-produced** artifacts, read-only: the RM1 episode (bundling the declared intent/design, the proposed `ProductionPlan`, and the grounded verdict) and the RM3 `PrecedentReport` for the same case; plus a deterministic, **versioned** critic model (`critic_model_version`). RM4 does **not** take the raw precedent corpus, the capability model, or any planner/oracle machinery — it consumes the *outputs* of RM1 and RM3, never their mechanisms, and never re-runs them.

## 4. Outputs

An advisory **Engineering Critique**: situated **findings**, each **grounded by reference to the situation constituent that produced it**; a summary **assessment** (supportive/cautionary/neutral); the `critic_model_version`; provenance; and a reproducible content-hash identity so identical inputs yield an identical critique. It is **advisory context, not a decision** — RM4 alters no RM1 plan/verdict and no RM3 report. The critique is the only externally-visible output; the internal EngineeringSituation is never surfaced. RM4 introduces **no** new external contract (deferred to the §12 extraction discipline).

## 5. Internal EngineeringSituation

- **What it is.** EngineeringSituation is **the coherent engineering state of one manufacturing case** — a referentially-consistent representation of "this engineering case, as it now stands." It is defined by what it *is* (one case's coherent state), **not** by a fixed list of parts.
- **Observed constituents are contingent, not definitional.** The constituents RM4 assembles today — the case's declared intent/design, its proposed plan, its grounded verdict, and its precedent report — are present **because Engineering Judgment (RM4), the primitive's first consumer, requires them** (today via Engineering Critique). This set is *observed*, not part of the primitive's definition.
- **Future constituents only by evidence-driven extraction, never anticipation.**
- **Strictly INTERNAL.** Not a contract, not a schema, not persisted; **no external identity**; consumed only within `judgment/`, discarded after each critique.
- **State, not behavior** (Law 3). One invariant: **mutual referential coherence** — all constituents belong to the same case (checked by matching existing content-hash references; no new hash minted). Assembled by **aggregation, never re-derivation**; **fails closed** on an incoherent/incomplete case.
- **Role:** give judgment a coherent substrate, and **reveal** (through what the critic reads) the load-bearing shape a future contract would take.

## 6. Responsibilities

RM4 owns (MP manufacturing content): internal situation assembly (read-only, coherence-checked); the deterministic, versioned **critic model** (what constitutes a situated finding); **situated critique** production (grounded, honest); and **primitive revelation** (documenting the load-bearing constituent set).

## 7. Explicit non-responsibilities

No planning/re-planning, no plan mutation/optimization; no manufacturability verification/re-verification (never bypasses Velith, Law 9); no retrieval/re-running RM3; no persistence or memory/retention framework (Law 6); no decision authority; no causal reasoning (correlational only); no ML/embeddings/learned critic; no creation/publication/persistence/exposure of EngineeringSituation; no new external contract; never imports MiniFlyWire (Law 4); no held-out evaluation harness.

## 8. Engineering invariants

Determinism (identical case + `critic_model_version` ⇒ identical content-hashed critique); read-only (writes nothing, mutates no store); grounded (every finding references a real situation constituent); additive (RM1/RM2/RM3 + contracts byte-unchanged; no new contract); situation internality (never leaves RM4, no external identity); honesty (advisory, never asserted as the case's verdict); coherence/fail-closed; advisory-only (no decision mutation).

## 9. Determinism rules

Versioned critic model; deterministic, order-stable situation assembly; total, reproducible finding order with a deterministic tie-break; bounded integer severities (no float identity hazard); reproducible content-hash identity with volatile fields excluded.

## 10. Boundary rules

- **Identity = content; mechanism = Noetica-bound (Law 3, Law 8).** Engineering Judgment — the judgment content, whose first form is the Engineering Critique — is domain content and is RM4's identity. Any general situation-assembly/aggregation machinery is *mechanism*, MP-local only; if it generalizes it becomes a Noetica extraction seed — never RM4's identity.
- Law 6 (no Noetica store/lifecycle engine); no ML/homunculus; Law 4/Law 9; dependency direction (RM4 depends on RM1/RM2/RM3 read-only; nothing in them depends on RM4); primitive containment (EngineeringSituation stays inside RM4); honesty (grounded, advisory).

## 11. Acceptance criteria

A deterministic advisory critique grounded in the internal situation; determinism holds; **situated value** demonstrated (a finding only visible in context — a structurally-valid plan that contradicts a strongly-relevant cautionary precedent); read-only holds; situation internality holds; boundaries hold; honesty holds; **primitive revelation** delivered (the observed load-bearing constituent set documented, and whether it stabilized).

## 12. Future extraction criteria

EngineeringSituation becomes a first-class contract **only on evidence**. **Trigger:** a *second independent consumer* requires the same coherent situation, **or** the coherence invariant must be enforced across a module boundary — whichever first. **Evidence:** a stable revealed constituent set (H2), a precise coherence invariant, and a documented second-consumer need. **Ownership** decided via the Extraction Review Gate (MP domain content vs Noetica platform mechanism, Law 3/8/N.3). **Governance:** a separately-ratified change (Laws 22/23) — the constitution already names "Situation State" in MP's ownership, so extraction realizes an existing concept. Until then, EngineeringSituation stays internal; premature extraction repeats the withdrawn-Situation-State error.

---

*Frozen RM4 specification (accepted, ADR-0008). Delivered across six commits (C1–C6); EngineeringSituation internal throughout; extraction gated on the §12 criteria.*
