# Mini Prometheus — Next-Capability Gap Assessment

**Type:** Read-only research recommendation. No application code, schema, test, dependency, frozen-spec,
ADR, or Git state was modified. Only this file was written. No milestone is authorized; this stops at a
research recommendation.
**Repo state:** `main` @ `ab8cc44`; working tree CRLF-only churn (`git diff -w` empty) = semantically
identical to HEAD; untracked = `research/`, `uv.lock` (both preserved).
**Prior decisions carried forward:** RM4 verification-provenance = **Decision A** (preserve; wording-only),
recorded in `research/rm4-verification-provenance-decision.md`. Not reopened here.

---

## 1. What Mini Prometheus can prove today (boundary, condensed)

From the end-to-end trace in `research/verification-contract-gap-audit.md` §3–4 (not re-derived here):

- **Proven:** schema/structural validity; capability existence, material support, declared-precedence,
  and declared-tolerance-vs-capability-minimum checks **against the declared capability model**;
  deterministic single- and multi-job scheduling with an **independently re-derived lower-bound
  certificate** (RM10–14); byte-exact artifact identity + provenance (RDAI-1); and an advisory,
  deterministic **situated critique** (RM4).
- **Assumed (not proven):** that the **declared** inputs — operations, material, tolerances, durations,
  and the **capability model itself** — faithfully and *currently* describe the real part and shop.
  Geometry, real DFM, tolerance-on-the-solid, real cycle times, and quality are explicitly out of scope.

**The sharpest demonstrable boundary:** every verdict/plan/schedule is **conditional on the declared
capability model**, and the system's treatment of that conditioning is **inconsistent across
subsystems** (§3). That inconsistency — not geometry — is where the next small, in-turf capability lives.

---

## 2. The asymmetry that frames the gap (source-demonstrated fact)

`capability_model_version` is recorded on every plan, verdict, episode, and schedule. Three subsystems
treat it very differently:

| Subsystem | Treats capability-model provenance as decision-relevant? | Source |
|---|---|---|
| **RM2 exact reuse** | **Yes.** Reuse key = `(design_input_identity_hash, capability_model_version)`; a prior verdict is reused only under the **same** model. | `experience/episode_index.py` l.13–27 |
| **RM11–14 scheduling** | **Yes.** A schedule or a job planned under a different model → `METADATA_MISMATCH` issue. | `manufacturing_scheduling/checker.py` l.270–276 |
| **RM3 precedent → RM4 judgment** | **No.** Retrieval scores design-feature similarity only (`relevance`), never model version; the signal/finding come from the precedent's recorded verdict **regardless of the model that produced it or the model governing the query**. | `precedent/retriever.py::rank` l.64–70; `precedent/reasoner.py::_derive_signal` l.88–91; `judgment/critic_model.py::_precedent_consistency` l.138–165 |

**Consequence (fact):** a precedent whose `MANUFACTURABLE` verdict was produced under capability model *A*
can drive a `SUPPORTING` signal — and a `SUPPORTIVE` engineering judgment — for a query evaluated under a
different model *B*, with **nothing recorded or surfaced** to indicate the precedent's manufacturability
basis differs from the one now in force. The project already decided (twice) that this kind of mixing is
decision-relevant; the precedent/judgment path is the one place that decision was not carried through.

No existing code performs any staleness/drift/contradiction reasoning (`grep` for
`stale|drift|contradict|inconsisten|superseded|revalidat` finds only the RM10 timeline check and reuse
runner — unrelated).

---

## 3. Candidate gaps (≤3), ranked

### Candidate A (ranked #1) — **Precedent-basis consistency: qualify precedent/judgment by capability-model drift**

- **Human/engineering problem.** An engineer (or the system) leans on a prior case — "we judged this
  manufacturable before" — whose basis was a **different shop capability configuration** (a machine since
  retired, a tolerance capability since changed, a different rule set). The old judgment may no longer
  hold. The engineer is given no signal that the precedent's *basis* has drifted.
- **Evidence & strength.**
  - **Internal — strong, source-demonstrated:** the §2 asymmetry. Two subsystems guard model provenance;
    the precedent/judgment path does not. This is a concrete, falsifiable inconsistency in MP's own code.
  - **External — moderate/analogical:** the "stale decision basis" pain is real in manufacturing
    (`research/*prior-art*`: superseded-drawing / disposition discourse), **but** that discourse is about
    *drawing revisions*, not *capability-model* drift. Marked analogical, not direct — do not overclaim.
- **Existing solutions & differentiation.** PLM/PDM track part/doc **revision effectivity** ("which rev
  applies to this work order") — not "is a prior *manufacturability judgment* still valid given shop
  capabilities changed." d2m/Palmetto/OCCT are geometry/feature tools — unrelated. MP's **own** scheduler
  does the schedule-level check but not the precedent/judgment level. **Not duplicated anywhere.**
- **Architecture fit.** Strong. Squarely MP-owned (Constraint Network / Situation State / Experience Flow;
  ADR-0003: "the Constraint Network reasons over the World Model"). Additive; `capability_model_version`
  is already on every episode and reachable in the situation; can be delivered as an RM4-style **advisory
  qualification** (surface/annotate, not re-verify) — honoring Law 9 and "no new external contract."
- **Smallest falsifiable test.** Build two episodes with near-identical declared intent: precedent *P*
  `MANUFACTURABLE` under model vA; evaluate query *Q* under model vB (vA≠vB), *P* strongly-relevant.
  Run RM3→RM4. **Current (predicted, to be confirmed):** `SUPPORTING` signal + `SUPPORTIVE` assessment
  with **no** record that *P*'s `capability_model_version` ≠ *Q*'s. Measured quantity: a single boolean
  (does any precedent entry/signal/finding reflect model-version match?). Gap closed when a cross-model
  precedent is **qualified** (e.g., a cautionary/annotated finding), not silently equated.
- **Cost & dependencies.** Low; pure/read-only; no external dependency; no CAD kernel; no new contract.
- **What could prove it wrong.** (i) If a real deployment **pins a single capability model forever**,
  drift never occurs and the capability is vacuous — *this is the key missing evidence.* (ii) If the
  correct fix turns out to be a trivial **filter** (drop cross-model precedents) rather than a
  *qualification*, it is a one-line scoping change / latent-bug fix, not a new capability. (iii) If RM2's
  model-scoped reuse + feature-distance already make cross-model precedents operationally negligible.

### Candidate B (ranked #2) — **Verified minimal-repair certificate for an adverse verdict**

- **Problem.** On `NOT_MANUFACTURABLE`/`PLAN_INVALID`, the engineer wants "what is the **smallest declared
  change** that would make this manufacturable?" MP emits `reason_codes` but no actionable minimal repair.
- **Evidence & strength.** Moderate/indirect: manufacturing disposition discourse shows engineers spend
  real effort deciding what to change; no direct evidence this *specific* form is demanded.
- **Differentiation.** DFM/PLM flag issues; few produce a **deterministically-verified minimal-repair
  certificate** (a repair re-checked by re-running the oracle). Mildly novel.
- **Architecture fit.** Good (engineering reasoning), uses the existing oracle as its own checker.
- **Smallest test.** For a corpus of adverse cases, compute a candidate minimal repair, re-run the oracle,
  assert it flips to `MANUFACTURABLE` and that no smaller repair does. Measured: flip rate + minimality.
- **Cost.** Low–moderate (search over a small declared space).
- **What could prove it wrong.** The oracle's checks are **simple and few**, so the repair is often
  trivially implied by the reason code (CAPABILITY_MISSING → add that capability). If so, the "reasoning"
  adds little over just reading `reason_codes` — **real risk the value is thin.**

### Candidate C (ranked #3) — **Experience-base contradiction detection**

- **Problem.** Precedent trust assumes the corpus is self-consistent: near-identical declared intents
  should not carry contradictory verdicts.
- **Evidence & strength.** **Weak — likely vacuous.** Under the deterministic oracle (RM4 §9) + the
  model-scoped reuse key, identical `(design identity, model)` **cannot** yield divergent verdicts by
  construction; "near-identical-but-divergent" collapses into ordinary relevance distance, already handled
  by RM3. There is little room for a genuine contradiction that isn't either impossible or already a
  Candidate-A model-drift case.
- **Differentiation / fit / cost.** Fit good, cost low, but the problem it targets is mostly closed
  already. Included for completeness; **not recommended.**

---

## 4. Comparison matrix

| Criterion | **A — Precedent-basis drift** | B — Minimal-repair certificate | C — Experience contradiction |
|---|---|---|---|
| Problem clarity | High | High | Medium |
| Evidence (internal) | **Strong (source-demonstrated asymmetry)** | Weak | Very weak (mostly precluded) |
| Evidence (external/demand) | Moderate, analogical | Moderate, indirect | Weak |
| Differentiation vs PLM/CAD/d2m/Palmetto/OCCT | Strong (none reason over verdict-basis) | Mild | Low |
| Duplicates existing repo work? | No | No | Largely yes (determinism+reuse) |
| Architecture fit (MP-owned turf) | **Strong** | Good | Good |
| Smallest falsifiable test | Cheap, boolean | Cheap–moderate | Cheap but low-yield |
| Cost / dependencies | **Low** | Low–moderate | Low |
| Biggest falsifier | Model pinned ⇒ vacuous | Repair trivially implied | Contradiction impossible by design |

---

## 5. Recommendation

**Conditional GO — advance Candidate A to a falsifiable validation spec only. Do NOT authorize a
milestone yet.** B is a fallback; C is a no-go.

**Why GO-to-validate (not GO-to-build):** the internal evidence (§2 asymmetry) is strong and
source-demonstrable, A sits squarely in MP's owned reasoning turf, it is cheap and additive, and it is not
provided by any external system. That justifies spending the **cheap confirming test** now.

**Why not straight to a milestone:** the decisive piece of evidence is still missing — **does
`capability_model_version` actually drift within a real deployment over time, and does *qualifying* (vs
filtering) cross-model precedents measurably improve judgment?** Until that is answered, building risks
either a vacuous capability (model pinned) or a mislabeled one-line filter. Per the project's
anti-premature-abstraction discipline, the honest next action is validation, not construction.

**Exact next action for the Research Director:** authorize a *read-only validation spec* for Candidate A
that (1) runs the §3-A falsifiable test to confirm current behavior from source, and (2) gathers one piece
of operational evidence that capability-model drift is real for an intended deployment (or a reviewer
judgment that qualification is valuable). Only if both land does A become a milestone candidate — and even
then as an **advisory qualification** (surface model-basis mismatch), never a re-verification (Law 9).

---

## 6. Independent-review prompts (not yet reviewed by anyone)

*Provided for the Director to send. Neither ChatGPT nor DeepSeek has reviewed this; do not represent them
as having done so.*

**For ChatGPT / DeepSeek (focused):**
> Mini Prometheus is a deterministic manufacturing-reasoning runtime. It records `capability_model_version`
> on every plan, verdict, episode, and schedule. Its exact-reuse layer keys on `(design_identity,
> capability_model_version)`, and its scheduler flags cross-model inputs as `METADATA_MISMATCH`. But its
> precedent retrieval ranks by design-feature similarity only (ignoring `capability_model_version`), and
> its advisory judgment derives `SUPPORTING`/`CAUTIONARY` from a precedent's recorded verdict regardless of
> the capability model that produced it or the one governing the query.
> Questions: (1) Is "a prior manufacturability judgment may be stale because the shop's declared capability
> model changed since" a real, distinct engineering problem, or is it already covered by PLM/PDM revision
> effectivity, MES, or standard change-management? Cite specifics. (2) Is *qualifying* cross-model
> precedents (surfacing the basis mismatch as an advisory caution) more correct than *filtering* them out,
> or is filtering sufficient? (3) What is the cheapest evidence that would show capability-model drift is
> (or is not) operationally real, so that building this is (or is not) justified? (4) Any way this
> duplicates geometry comparison (d2m/OCCT), feature recognition (Palmetto), or ordinary scheduling?
> Be skeptical; identify what would make this a waste of effort.

---

## 7. Source index

- Boundary: `research/verification-contract-gap-audit.md` §3–4 (trace + guarantee matrix).
- `src/mini_prometheus/experience/episode_index.py` l.13–27 — reuse key includes `capability_model_version`.
- `src/mini_prometheus/manufacturing_scheduling/checker.py` l.270–276 — `METADATA_MISMATCH` on cross-model
  schedule/job.
- `src/mini_prometheus/precedent/retriever.py` l.48–70 — `rank`/`relevance`: design-feature similarity
  only; no `capability_model_version`.
- `src/mini_prometheus/precedent/reasoner.py` l.88–91 — `_derive_signal`: verdict-based, model-agnostic.
- `src/mini_prometheus/judgment/critic_model.py` l.138–181 — `_precedent_consistency`, `_internal_verdict`.
- `src/mini_prometheus/manufacturing_constraints/oracle.py` — verdict checks are plan+model-derivable only.
- `specs/milestones/RM3-engineering-precedent-reasoning.md` §5 l.72–84 — signal from "verified verdicts";
  relevance features l.74–77.
- `docs/adr/0003-runtime-implementation-order.md` l.31–32 — Situation State → World Model → Constraint
  Network ownership chain (A's architectural home).
- `constitution/HANDBOOK_v1.1.md` §7.2 l.945–951 — engineering = universal cognition over an engineering
  world model (no new operators) — bounds A to reasoning-content, not a new engine.
- `docs/ROADMAP.md` RM15+ row — existing futures (model-based planner seam; organic-data caveat); A is
  distinct from these and smaller.
- Rejected-by-constraint comparators: d2m / Palmetto / Open CASCADE (geometry/feature — different axis);
  PLM/PDM (revision effectivity — not verdict-basis reasoning).

*No application code, schema, test, dependency, frozen spec, ADR, or Git state was changed. This note is
the only artifact produced.*

---

# Addendum — Falsification review of the capability-model-drift hypothesis (2026-10-23)

Read-only. Nothing changed but this note. HEAD still `ab8cc44`; working tree CRLF-only vs HEAD;
untracked `research/`, `uv.lock` preserved. This addendum **narrows** §3-A; the original §1–§7 stand.

## A1. What `capability_model_version` actually is (traced)

**Fact:** it is a hand-assigned string **label**, not a fingerprint of capability content.
`capability_model.py` l.36–38 defines `MODEL_VERSION = "1.0.0"` and `MODEL_VERSION_CONSTRAINED = "1.1.0"`
as module constants; `default_model()` (l.58–80) and `constrained_model()` (l.97–119) set `version=` to
those constants literally. The string flows verbatim into `plan/verdict/episode/schedule.
capability_model_version` (`planner.py` l.241,248; `episode_store.py`; `checker.py`). It is **never**
derived from, or bound to, the actual `op_capability` / `resources` / `supported_materials` /
`capability_tolerance_mm` / `ordering_constraints` data (`grep` for a model content-hash: none — the only
content-hashing in the repo is of designs/plans/episodes, not of the capability model).

Two direct consequences, both from source:

- **Different version ⇏ relevant capability change.** `constrained_model()` (1.1.0) reuses
  `default_model()`'s `op_capability`, `resources`, and `supported_materials` **unchanged** (l.107–112);
  it only *adds* a sparse tolerance map and ordering constraints. So a 1.0.0↔1.1.0 difference can mean
  *nothing was removed or narrowed* — only that extra declarative data exists.
- **Same version ⇏ same capability data.** Nothing binds the constant to the content, so an edit to a
  model's data without bumping the constant yields identical `capability_model_version` across materially
  different capabilities. `with_unavailable_resources()` makes this explicit (l.149–163): it changes the
  effective available resources but **deliberately leaves `version` unchanged** ("availability is a per-run
  input").

**So the version string is simultaneously over-sensitive (flags harmless additive relabels) and
under-sensitive (misses unversioned content edits and per-run availability).** It is not a reliable
capability-basis signal. *This invalidates the original §3-A framing ("qualify by version mismatch").*

## A2. Does a version mismatch imply a relevant capability change? (evidence)

**No.** Evidence:
- `constrained_model` adds-only (l.107–118) → version differs, required capabilities for any given
  precedent unchanged.
- **No model in the repository removes or narrows a capability.** The only two
  `ProcessCapabilityModel(...)` constructors are `default_model` and `constrained_model` (grep confirmed);
  neither drops a resource/capability nor tightens an existing tolerance. The "capability removed/narrowed"
  scenario the hypothesis worries about has **zero in-repo instances**.
- Behavioral goldens (`tests/fixtures/rm8_default_behavior_golden.json`, `tests/boundary/
  test_rm8_boundaries.py`) pin `default_model`'s *outputs*, so an output-changing edit to `default_model`
  breaks CI — a **test-suite** guard (not a runtime property), and only for `default_model`.

## A3. Three cases — behavior per subsystem (confirmed vs hypothetical)

Legend: **[C]** = confirmed from code logic; **[H]** = hypothetical (no such artifact exists in-repo).

**Case 1 — different versions, no relevant capability changed** (e.g. `default_model` 1.0.0 vs
`constrained_model` 1.1.0, precedent uses only `{cut_stock, face_mill, inspect}` at a loose tolerance):
- RM2 reuse **[C]:** keys differ (version differs) → *no reuse* even though the precedent's basis is
  identical → a **harmless false negative** (conservative; misses a valid reuse, never wrong).
- Scheduler **[C]:** `checker.py` l.270–276 → `METADATA_MISMATCH` → refuses to mix → **false alarm**
  (the bases are equivalent for this precedent).
- RM3/RM4 **[C]:** ignore version entirely → precedent flows on design similarity; verdict used as-is.

**Case 2 — different versions, a capability the precedent requires was removed/narrowed:**
- **[H] — no such model exists.** If one did: RM2 would (correctly, incidentally) not reuse; scheduler
  would flag mismatch; **RM3/RM4 would still surface the precedent as SUPPORTING/SUPPORTIVE with no
  indication its required capability is gone** — the genuinely dangerous behavior, but only reachable via
  future model evolution that does not yet exist.

**Case 3 — same version, underlying capability data changes unexpectedly** (edit a model's resources/
tolerances without bumping the constant; or `with_unavailable_resources` which keeps the version):
- RM2 reuse **[C]:** reuse key *matches* (same version + same design identity) → **reuses a verdict
  produced under different actual capabilities → silently wrong.** For `default_model`, an output-changing
  edit is caught by the behavioral golden **in CI**, not at runtime; for any other/future model, unguarded.
  (Availability via `with_unavailable_resources` is captured in the plan's step params per RM9, so its
  effect is recorded even though the version string is unchanged — a partial mitigation specific to
  availability.)
- Scheduler **[C]:** version strings equal → **no `METADATA_MISMATCH`** → silently mixes differing bases.
- RM3/RM4 **[C]:** ignore version → unaffected either way.

## A4. What the real problem is (decision)

**Not "version mismatch unpropagated to RM3/RM4."** The honest diagnosis is a **combination with a single
root cause:**
- **Root cause:** `capability_model_version` is a **label not bound to capability content**, so it is an
  unreliable proxy for basis identity (A1).
- **Symptom 1 — missing capability-basis comparison:** nowhere does the system compare the *actual
  capability content a precedent was judged under* against the content now in force. Version-string checks
  (RM2, scheduler) stand in for this and are both over- and under-sensitive. RM3/RM4 do nothing.
- **Symptom 2 — stale precedent reuse (Case 3):** real in principle, but today **partly mitigated** by
  behavioral goldens (for `default_model`) and by RM9's plan-recorded availability; **no in-repo trigger**.

So the correct object of any future work is a **content-bound capability-model identity + a
precedent-relevant basis comparison**, *not* a version-string drift detector. (This reuses the repo's
existing content-hash mechanism applied to the capability model; it is not new file-identity machinery and
not geometry.)

## A5. Smallest falsifiable test that separates meaningful failure from harmless version difference

Compare the **projection of each model onto the precedent's actually-required capabilities** — the
`op_capability` entries the precedent's ops map to, their providers in `resources`, and any
`capability_tolerance_mm` entry that actually gates the precedent's requested tolerance — and ignore the
version string entirely.
- **Harmless (must NOT flag):** `default_model` vs `constrained_model`, precedent = `{cut_stock,
  face_mill, inspect}` at a loose tolerance → the projection (caps `cap.saw`,`cap.mill`,`cap.cmm` + their
  providers; no gating tolerance) is **identical** across both models despite `1.0.0 ≠ 1.1.0`.
  Measured quantity: projection-equality boolean = **True** while version-equality = **False**.
- **Meaningful (must flag):** a model that drops `mill01`/`cap.mill` or tightens `cap.mill` tolerance above
  the precedent's requirement → projection **differs** for a mill-using precedent, even if the version
  string is left unchanged. Measured: projection-equality = **False** while version-equality may be True.

The single discriminating statistic is **projection-equality vs version-equality**: wherever they disagree
is exactly where the version string is the wrong signal. This test is read-only, deterministic, and needs
no new model — Case-1 direction is demonstrable today from the two existing models.

## A6. Evidence still missing to show it matters operationally

1. **Does capability content actually change over a deployment's life** (a machine retired, a tolerance
   re-characterized), and is the version bumped when it does? Today's two models show the discipline is
   *not* content-driven (adds-only yet bumps; availability changes don't bump).
2. **Is any precedent ever evaluated across such a change** (frequency ≥ some threshold)? No instance
   exists in-repo (Case 2 is hypothetical).
3. **Is there a consumer that would act on a stale-basis precedent?** The RM4 critique is internal and
   non-persisted; no external/production consumer exists yet (would arrive with RM6+).
4. **Is the behavioral-golden + per-run-availability mitigation already sufficient** in practice for the
   only concrete sub-hazard (Case 3)?

Until #1 and #3 produce at least one real instance, the dangerous case (Case 2 / unguarded Case 3) is
**latent, not operational.**

## A7. Decision

**NARROW THE HYPOTHESIS. Do not proceed to independent review yet; not a no-go.**

Rationale, evidence-first (not momentum): the falsification review *strengthened* the internal finding but
*re-pointed* it — the version string is a demonstrably wrong signal, so the original §3-A framing must be
discarded. The correctly-framed problem (content-bound capability-model identity + precedent-relevant basis
comparison) is real and in-turf, **but** its dangerous manifestation has **zero in-repo instances**, is
**partly mitigated** today, and has **no consumer** that is harmed. Spending independent-review budget — or
building — now would optimize a latent, non-operational problem and risk a false-alarm-prone version-drift
detector. That contradicts "don't create work to stay busy."

**Narrowed hypothesis (carry forward):** *"Mini Prometheus lacks a content-bound capability-model identity;
basis comparison, where it exists (RM2, scheduler), relies on an author-assigned version label that is
neither necessary nor sufficient for a real capability change. A reliable basis comparison must project
onto the precedent's required capabilities, not the version string."*

**Exact next action for the Research Director (cheapest, read-only):** authorize running the A5 discriminator
as a read-only probe (confirm projection-equality ≠ version-equality on the two existing models — predicted
from code, not yet executed). **Gate any independent review or milestone on A6 #1 + #3**: at least one real
capability-removing/narrowing model (or a logged unversioned-edit incident) **and** a consumer that acts on
precedent. Absent those, hold. If/when they appear, the §3-A fallback becomes the content-bound-identity
framing above — delivered as advisory qualification (surface basis mismatch), never re-verification (Law 9).

*No application code, schema, test, dependency, frozen spec, ADR, or Git state was changed by this
addendum.*
