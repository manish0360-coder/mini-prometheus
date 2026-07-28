# RM3 Specification — Engineering Precedent Reasoning

- **Status:** DRAFT for architectural review. **Specification only** — no code, no engineering package, no implementation plan, no repository changes.
- **Milestone:** RM3 (third runtime implementation milestone).
- **Frozen architectural identity:** **Engineering Precedent Reasoning** (ratified). The retrieval/distance machinery is an *implementation mechanism* and a *future Noetica extraction seed* — **not** RM3's identity (§7 / §Retrieval-mechanism note).
- **Layer:** Mini Prometheus (Layer 4). Constitution v1.1.0. Builds additively on RM1 (`0.2.0`) + RM2 (`0.3.0`).
- **Governing:** HANDBOOK_v1.1 (§1.1, §1.6, §1.7, §1.9, §2.4, Laws 3/4/6/8/9/14/18/21, §11.11, N.3); Velith DECISIONS D7/D8/D25; ADR-0005/0006; the frozen RM2 spec.
- **Immovable:** RM1 and RM2 are frozen; RM3 is purely additive (no modification to any RM1/RM2 module).

---

## 1. Purpose

Give Mini Prometheus the ability to **reason from engineering precedent**: for a new `ManufacturingRequest`,
find the most *relevant prior verified manufacturing cases* and use them to inform the current case — surfacing
supporting or cautionary precedent grounded in real, verified past verdicts. This is **compounding rung 2**: RM2
reused only *identical* experience (near-zero real-world hit rate); RM3 makes accumulated experience actually
*count* by generalizing to *analogous* cases, moving Mini Prometheus toward reasoning like an experienced
manufacturing engineer who recognizes "this is like a part we made before."

### 1.1 Governing scientific hypothesis (review Amendment 1)

RM3 rests on one explicit, **falsifiable scientific hypothesis**: that a **deterministic structural similarity
over `DesignInput` features** (material, stock form, ordered declared-operation sequence, quantity, tolerances)
is **sufficiently correlated with manufacturability outcomes** to provide *useful engineering precedent*. RM3
assumes this correlation holds well enough for surfaced precedents and signals to be engineering-relevant; it does
**not** assume the correlation is exact. Because the claim is falsifiable, a **later milestone will experimentally
validate or reject it** — if precedent relevance proves uncorrelated with manufacturability, the precedent model
is revised or rejected. This subsection makes the hypothesis explicit only; it defines **no** evaluation
methodology, thresholds, or research plan.

## 2. Responsibilities

RM3 **owns** (Mini Prometheus manufacturing *content* — domain reasoning; the responsibility matrix assigns
reasoning *content* to the domain layers):
- the notion of a **manufacturing precedent** and what makes two engineering cases *relevant*;
- a **deterministic, versioned precedent model** (the engineering relevance/distance definition — §5);
- **precedent selection, surfacing, and consistency reasoning** — ranking relevant precedents and deriving a
  supporting/cautionary signal from their verified verdicts.

RM3 **consumes** (treated strictly as implementation mechanism):
- RM2's read side (episode reader + index) and a deterministic top-K **retrieval mechanism** — the Noetica
  extraction seed (§7);
- the frozen RM1/RM2 contracts and internal hashing/validation mechanisms.

RM3 **composes additively** with RM1 (`plan → verify → log`) and RM2 (exact reuse): it adds a precedent-reasoning
output *alongside* the existing plan/verdict; it changes neither.

## 3. Inputs

- **Query:** a `ManufacturingRequest` (normalized to its `DesignInput` via RM1 intake). Geometry remains opaque.
- **Precedent corpus:** Mini Prometheus's **own** prior verified `ManufacturingEpisode` records (RM2's episode
  store), read-only and content-hash-verified on load.
- **Precedent model:** a versioned definition of engineering relevance (`precedent_model_version`), analogous to
  RM1's capability-model versioning.

## 4. Outputs

- A **Precedent Report** (new, MP-owned output): for the query, a **deterministically ranked** set of the top-K
  relevant precedents — each carrying a **Ref** to its stored episode, its **relevance score**, and its **verified
  verdict summary** (status + reason codes) — plus a derived **precedent signal** (supporting / cautionary /
  none), the `precedent_model_version`, provenance, and a `content_hash`.
- The report is **advisory context**, not a decision: RM3 does **not** alter the query's RM1 plan or verdict.
- **This introduces one small additive MP-owned contract** (the Precedent Report). *(Contrast RM2, which needed
  none. The exact schema is a Contract-stage artifact, not defined here.)* Existing frozen contracts are unchanged.

## 5. Deterministic precedent model

The precedent model is **deterministic, versioned, and free of machine learning** (no embeddings, no learned
weights, no vector search — §6).

- **A precedent** is a stored verified `ManufacturingEpisode` (a past manufacturing case: its design intent,
  plan, and grounded verdict).
- **Relevance** is a **deterministic distance** `D(query_design_input, precedent_design_input)` over explicit
  engineering features only: material (and material code), stock form, the **ordered declared-operation
  sequence**, quantity, and tolerances. Geometry is excluded (opaque). Weights and the metric are **fixed and
  carried in `precedent_model_version`**; `D = 0` ⇔ identical manufacturing intent (the RM2 exact-reuse case, of
  which RM3 is the generalization).
- **Ranking** is a **total order**: precedents sorted by ascending distance, with a **deterministic tie-break**
  (e.g., by episode `content_hash`) so ordering is stable and reproducible.
- **Precedent reasoning** selects the top-K within a versioned relevance threshold and derives the signal from
  their **verified** verdicts: *cautionary* if the nearest strongly-relevant precedent was `NOT_MANUFACTURABLE`
  (surfacing its reason codes), *supporting* if it was `MANUFACTURABLE`, *none* if no precedent clears the
  threshold. Thresholds/K are part of `precedent_model_version`.
- **Reproducibility:** identical query + identical corpus + identical `precedent_model_version` ⇒ identical ranked
  precedents, scores, signal, and report `content_hash` (timestamps/timing excluded from identity, per the
  contract hashing rules).

## 6. Constitutional boundaries

- **Identity = content, mechanism = Noetica-bound.** RM3's architectural identity is *domain reasoning content*
  (Law 3: content is the domain's). The retrieval/distance machinery is a **mechanism**, held MP-local only as
  the **extraction seed** for Noetica's memory/retrieval mechanism (Law 8, N.3) — never RM3's identity (§7).
- **Law 6 — no Noetica re-implementation.** No general memory/retrieval framework, vector database, retention,
  compression, or pruning (that is Noetica's lifecycle framework, §11.11; deferred). RM3 is a minimal,
  deterministic, read-only reader over MP's own episodes.
- **No ML / no homunculus (§1.6, §1.9).** Relevance is a deterministic structural distance, not a learned model.
  RM3 is bounded to *precedent selection, surfacing, and consistency* — it is **not** a general "Reasoner", not
  adaptive planning, not learning.
- **Law 4 / Law 9.** Never imports MiniFlyWire. Never bypasses Velith for engineering: RM3 reasons over MP's own
  *manufacturing* precedents (manufacturability verdicts), not engineering verification.
- **D7/D8/D25 compatibility.** RM3 is **read-only** and writes nothing that could contaminate a future held-out
  lock; the distance is defined so that, when a compounding *experiment* is later run, distance-based held-out
  exclusion (D25) can be layered on. RM3 itself runs **no** evaluation harness.
- **Honesty (Law 18, Principle 10).** Every surfaced precedent references a real, hash-verified stored episode and
  is labeled **analogous** with its relevance score; RM3 never asserts a precedent's verdict as the query's own
  verdict, and never fabricates precedent.

## 7. Retrieval mechanism — explicitly *not* the architectural identity

The top-K retrieval and the distance function are **implementation mechanism** only. RM3's frozen identity is
**Engineering Precedent Reasoning** (the domain capability of reasoning from verified precedent). Consequences,
fixed at the architecture level:
- the mechanism may be **replaced** — in particular by **Noetica's published retrieval/memory mechanism** once it
  is extracted (Law 8, N.3) — **without changing RM3's identity, responsibilities, or the Precedent Report
  contract**;
- documentation, contracts, tests, and naming must present RM3 as *precedent reasoning that consumes retrieval*,
  never as "similarity retrieval." Mislabeling would reassign a domain milestone to the platform-mechanism layer
  — the ownership error CAP-0001/ADR-0004 corrected.

## 8. Invariants

1. **Determinism:** identical query + corpus + `precedent_model_version` ⇒ identical, content-hashed Precedent Report.
2. **Read-only:** a precedent query writes no episode and mutates no store; corpus line count is unchanged.
3. **Grounded:** every precedent references a real stored episode (content-hash verified); relevance is in the
   defined bounded range; ranking is a total order with deterministic tie-break.
4. **Generalizes RM2:** `D = 0` ⇔ the RM2 exact-key case; RM3 subsumes that case without modifying RM2.
5. **No decision mutation:** RM1's plan and verdict for the query are unchanged; RM3 output is advisory context only.
6. **Additive:** RM1 and RM2 modules are byte-unchanged; existing contracts frozen; RM3 adds only the Precedent
   Report contract.
7. **Honesty:** precedents are labeled analogous with relevance; a precedent verdict is never presented as the
   query's own verdict.

## 9. Acceptance criteria (specification-level "done")

RM3 is complete when, against Mini Prometheus's own episode corpus:
- a query yields a **deterministic Precedent Report** — ranked top-K relevant precedents with relevance scores,
  verified verdict summaries, and a supporting/cautionary/none signal;
- **determinism** holds (identical inputs ⇒ identical content-hashed report);
- **generalization** is demonstrated: a *non-identical but relevant* prior request is surfaced as a precedent
  (which RM2 exact reuse would miss), and an *identical* request appears at `D = 0`;
- the **cautionary signal** is demonstrated (a strongly-relevant `NOT_MANUFACTURABLE` precedent surfaces its
  reason codes);
- **read-only** holds (corpus unchanged by a query);
- **boundaries** hold (no MiniFlyWire import; no store/retention engine; no ML/embeddings/vector DB; RM1/RM2
  unchanged; only the additive Precedent Report contract introduced);
- **honesty** holds (precedents labeled analogous; no precedent verdict asserted as the query's verdict).

## 10. Explicit non-goals

- No change to RM1's `plan → verify` or RM2's exact reuse.
- **No adaptive planning, no learning, no plan optimization** from precedent (RM4+ / later intelligence rungs).
- **No ML/embeddings/vector search** — deterministic structural distance only (Law 6).
- **No general memory/retrieval framework, retention, compression, or pruning** — Noetica's lifecycle framework
  (§11.11), deferred; RM3's retriever is only the extraction seed.
- **No held-out evaluation harness / compounding experiment** — a separate later scientific step (D7/D8).
- **No real Velith/Noetica package integration** (RM4/RM5), **no geometry/feature recognition**, **no execution**.
- **No calibrated/graded verdicts or causal reasoning** — later rungs, gated on an approximate oracle.
- **Correlational only (review Amendment 2).** RM3 performs **correlational** precedent reasoning only. It
  intentionally does **not** perform **causal** reasoning about manufacturability. Causal engineering reasoning
  remains a future milestone.

## 11. Relationship to MiniFlyWire → Noetica → Velith → Mini Prometheus

- **MiniFlyWire (research lab):** precedent/analogical reasoning-from-experience is a cognitive *primitive* it
  studies and validates. RM3 is the manufacturing-domain *application form* of that primitive. Transfer is by
  re-implementation of validated ideas — **never imported** (Law 4).
- **Noetica (platform):** the retrieval/distance *mechanism* under RM3 is the **extraction seed** for Noetica's
  memory/retrieval mechanism (Law 8, N.3). When Noetica publishes it, RM3 swaps its local retriever for Noetica's
  interface with **no change to RM3's identity or contracts**. RM3 continues to consume Noetica's Verdict /
  Provenance / Verifier-protocol contracts (as the frozen stubs, unchanged from RM1/RM2).
- **Velith (grounding):** today RM3 reasons over MP's own *manufacturing* precedents (grounded manufacturability
  verdicts). When real Velith-verified engineering designs arrive (RM4), precedents widen to include verified
  *engineering* cases, and precedent reasoning spans engineering → manufacturing. RM3 never bypasses Velith for
  engineering (Law 9).
- **Mini Prometheus (flagship):** RM3 is Mini Prometheus **domain reasoning content** — the manufacturing
  precedent-reasoning capability — advancing the compounding spine (§1.7) toward the one goal: an AI Manufacturing
  Intelligence that reasons like an experienced manufacturing engineer and improves from verified experience.

---

## Appendix A — Future Governance Note (review Amendment 3; NON-NORMATIVE)

> **This appendix is future governance *guidance* only. It is NOT an RM3 requirement, NOT part of the frozen
> RM3 architecture, and imposes no obligation on RM3.** It does not change any decision, ownership, contract,
> responsibility, invariant, acceptance criterion, or the deterministic precedent model above.

RM3's local retrieval/distance machinery is intentionally an **Extraction Seed** — an MP-local mechanism that is
expected to be extracted upward into Noetica's memory/retrieval mechanism in the future (Law 8, N.3). Extraction
seeds create a standing governance question: *as a seed grows, does the capability still belong inside Mini
Prometheus, or should it now extract into Noetica?*

**Recommendation (for a future Constitutional Amendment / CAP, not for RM3):** introduce an **"Extraction Review
Gate"** into the governance process. Under it, **any future milestone that extends an extraction seed must
explicitly determine whether the extended capability still belongs inside Mini Prometheus (domain content) or
should now be extracted into Noetica (platform mechanism)** — preserving the mechanism/content boundary (Law 3)
and the grow-by-extraction discipline (Law 8) as seeds mature.

This is guidance for the project owner to consider at a later milestone; adopting it would require a ratified CAP
(Laws 22/23) and is out of scope for RM3.

---

*Formal RM3 specification. No code, no engineering package, no implementation plan, no repository changes. On
approval, freeze into `specs/milestones/`, then proceed Contract → Implementation → Testing → Verification →
Commit → Review.*
