# RM4 Verification-Provenance Decision Note

**Type:** Read-only decision note (research/documentation only). No application code, schema, test,
dependency, frozen-spec, ADR, or Git state was modified. Only this file was written.
**Continues from:** `research/verification-contract-gap-audit.md`.
**Repo state:** `main` @ `ab8cc44`; working tree dirty but **CRLF-only** churn (`git diff -w` empty) —
semantically identical to HEAD. Nothing was changed.

---

## 0. Headline decision

**Decision A — preserve behavior; clarify wording only.**

Closer reading of the *frozen* RM3/RM4 specs shows the word "verified" is a **defined term meaning a
hash-verified recorded verdict**, and the implementation honours exactly that. My earlier gap audit
conflated two distinct senses of "verified" and overstated the finding; this note corrects it with exact
source. The residual issue is a **terminology collision** plus a **forward-looking transparency note** for
when real Velith (RM6) lands — neither of which justifies changing judgment logic now.

This note also records why **Decision B is not recommended today** and what evidence would reopen it.

---

## 1. Correction of the prior audit (stated plainly)

My prior note (`verification-contract-gap-audit.md` §1/§6A) claimed the code "does not honour the word
*verified*" and treated the mismatch as a defect. That was **partly wrong**. The specs define "verified"
in a sense the code *does* satisfy. I am correcting that here rather than defending it. The valid residue
of the prior finding is narrower: (a) the term "verified" is overloaded and can mislead a reader, and
(b) the critique output does not surface design-verification provenance — a transparency observation, not
a current contract violation.

---

## 2. Q1 — What RM4 was designed to judge, and forbidden from judging

**Designed to judge (frozen RM4 spec):**
- "**Judge a proposed manufacturing solution in the full context of its case** — to assess, grounded and
  deterministically, whether a proposed solution is sound given the case's declared intent, its normalized
  engineering design, and the verified precedent" (`specs/milestones/RM4-engineering-judgment.md` §1,
  line 14).
- First (and only current) form: **Engineering Critique** — situated **findings** + a summary
  **assessment** ∈ {SUPPORTIVE, CAUTIONARY, NEUTRAL} (§1 line 16; §4 line 35).
- It is "**advisory reasoning about a solution's soundness in context**; it is neither construction
  (planning) nor proof (verification) nor decision" (§1 line 14).

**Explicitly forbidden (RM4 spec §7, line 52):** no planning/re-planning or plan mutation; **"no
manufacturability verification/re-verification (never bypasses Velith, Law 9)"**; no retrieval/re-running
RM3; no persistence or retention framework (Law 6); **no decision authority**; no causal reasoning
(correlational only); no ML/learned critic; **no creation/publication/persistence/exposure of
EngineeringSituation**; **no new external contract**; never imports MiniFlyWire (Law 4); no held-out
evaluation harness.

**Honesty invariant (§8, line 56):** "honesty (advisory, **never asserted as the case's verdict**)."

**Conclusion (fact):** RM4 is advisory-only and is *constitutionally forbidden from verifying
manufacturability*. Any proposal that makes RM4 "verify" or re-weight on design-verification would violate
§7/Law 9. This tightly bounds admissible changes.

---

## 3. Q2 — Is `engineering_verification_status` load-bearing, informational, or ambiguous?

**Answer: informational provenance — NOT specified as a load-bearing judgment input. The apparent
ambiguity dissolves once "verified" is read as the specs define it.**

Evidence:
- RM4 §3 (inputs, line 31) lists the critic's inputs as "the RM1 episode (bundling the declared
  intent/design, the proposed `ProductionPlan`, and the grounded verdict) and the RM3 `PrecedentReport`…
  plus a … critic model." It **does not** name `engineering_verification_status` as a judgment input.
- RM3 defines "verified" operationally as **hash-verified recorded verdict**, not Velith-verified design:
  - "Precedent corpus: Mini Prometheus's **own** prior verified `ManufacturingEpisode` records … read-only
    and **content-hash-verified on load**." (`specs/milestones/RM3-engineering-precedent-reasoning.md` §3,
    lines 52–53.)
  - Signal "derived from their **verified** verdicts: … *supporting* if [the nearest strongly-relevant
    precedent] was `MANUFACTURABLE`." (RM3 §5, lines 81–83.)
  - Honesty: "every surfaced precedent references a real, **hash-verified** stored episode." (RM3 lines
    105, 125.)
- RM3 treats Velith-verified *designs* as a **separate, future** concept: "When real **Velith-verified**
  engineering designs arrive (RM4→RM6), precedents widen to include verified [designs]…" (RM3 line 173).
- In the contract, `precedent_verification_status` is a **recorded** per-entry field
  (`precedent_report.schema.json` `$defs/PrecedentEntry`, required, line 55/71) with no stated semantic
  effect on `signal` (whose enum/derivation, lines 38–42, is verdict-based).

**So:** the two senses of "verified" are (1) *hash-verified recorded verdict* — what RM3/RM4 use and the
code implements; (2) *Velith-verified design* (`engineering_verification_status == velith_verified`) — a
provenance field the spec carries for honesty and future widening, **not** a current judgment input. The
contract is **not ambiguous** on which drives the signal; it is only **lexically ambiguous** because one
English word covers both.

---

## 4. Q3 — What does `SUPPORTIVE` actually mean?

**It means: a strongly-relevant precedent exists whose hash-verified recorded manufacturability verdict is
`MANUFACTURABLE`. It does NOT mean the precedent's design was independently/Velith-verified, and the spec
does not claim it does.**

Evidence (runtime):
- `precedent/reasoner.py::_derive_signal` (lines 88–91): returns `SUPPORTING` for the nearest entry with
  `relevance_score ≥ threshold` **and** `verdict_status == MANUFACTURABLE`. Verification status is not
  read.
- `judgment/critic_model.py::_precedent_consistency` (lines 155–164): emits a SUPPORTIVE finding when
  `report.signal is PrecedentSignal.SUPPORTING`, detail `"strongly-relevant precedent was MANUFACTURABLE
  (rank N)"`.
- RM3 §5 lines 81–83 define exactly this verdict-based derivation.

**Honesty already enforced:** RM3's own module docstring states the report "carries **no** query-verdict
field (structurally impossible to assert a precedent's verdict as the query's own); each precedent is
labeled *analogous* by its relevance score" (`precedent/reasoner.py` docstring, lines 17–19). So SUPPORTIVE
is explicitly *analogy-plus-recorded-verdict*, never a claim that the **query** is verified.

---

## 5. Q4 — Does the critique expose provenance/uncertainty well enough to distinguish `engineer_declared` from `velith_verified`?

**Answer: No — the critique object does not surface design-verification provenance.** (Transparency gap,
forward-looking; not a current contract violation.)

Evidence:
- `judgment/engineering_critique.py::EngineeringCritique` (lines 39–52) exposes: `critic_model_version`,
  `case_ref`, `findings`, `assessment`, `content_hash`, `provenance`. No `engineering_verification_status`.
- The SUPPORTIVE finding `detail` (`critic_model.py` line 162) names rank + verdict only — not whether the
  precedent or the query was `velith_verified`.
- `_critique_identity` (`engineering_critique.py` lines 84–98) excludes verification status from the
  content-hash identity; two cases differing only in verification status produce an **identical** critique
  fingerprint.

**Mitigating context (why this is not a defect today):**
- The critique is **internal, non-persisted, not a contract** (RM4 §4 line 35; §8 line 56) — it is not
  published to any external consumer that could be misled in production.
- A consumer that *does* need the distinction can read it from the episode
  (`engineering_verification_status`, required + hashed into episode identity) and the precedent report
  (`precedent_verification_status`, required per entry). The provenance **exists upstream**; it is simply
  not *re-surfaced* on the advisory object.

---

## 6. Q5 — Verify: do all currently-possible supportive judgments rely on declared-only evidence? (traced, not inferred from the Velith block)

**Corrected, evidence-based answer (two independent legs; neither relies on "Velith is blocked"):**

**Leg 1 — measured corpus contents (not inference).** The precedent corpora the system is actually
exercised against are **100% `engineer_declared`:**
- `tests/fixtures/rm5_corpus/episodes.jsonl`: `velith_verified = 0`, `engineer_declared = 450`.
- `tests/fixtures/rm15_corpus/episodes.jsonl`: `velith_verified = 0`, `engineer_declared = 960`.
(Counted directly from the files.) So every supportive judgment produced in RM5/RM15 measurement
**demonstrably** rests on `engineer_declared` precedent — a measured fact about the corpora, independent of
any external-integration status.

**Leg 2 — judgment is indifferent to verification status (code-traced).** `_derive_signal`
(`reasoner.py` 88–91) and `_precedent_consistency` (`critic_model.py` 138–165) never read verification
status; `_critique_identity` excludes it. So even a `velith_verified` precedent would yield the **same**
signal, finding, and critique hash. The conclusion holds for *any* corpus, not just today's.

**Precision correction to the prior audit.** The absolute phrasing "all currently *possible* supportive
judgments rely on declared-only evidence" is **too strong**: a `velith_verified` episode is **not
type-impossible** — `integrations/velith/adapter.py::from_engineering_result` (line 52) produces one from a
Velith `EngineeringResult`, reachable via `orchestration/runner.py::run_from_velith` and exercised by a
compliance fixture (RM1 spec §9 line 159, "fixture-loaded"; referenced in `tests/conftest.py`,
`tests/integration/test_plan_verify_log.py`). The defensible statements are the two legs above:
(1) today's corpora are all-declared [measured]; (2) judgment ignores the status regardless [code]. The
default/primary path `intake/request_intake.py::intake` (line 47) also **hard-codes** `engineer_declared`,
so every request-originated episode is declared by construction.

---

## 7. Q6 — Downstream consumers; could any mistake advisory judgment for validated engineering truth?

**Consumers of the critique (code-traced):** `orchestration/judgment_runner.py::run_judgment` →
`experiment/arms.py` (`_judge`, line 64, reads `critique.assessment` + `critique.content_hash`) →
`experiment/runner.py`, `experiment/enriched_runner.py`, `experiment/protocol.py`. No other module imports
`judgment/`. The critique is **never persisted** and **exposed in no contract** (RM4 §4/§8).

**Could any mistake it for validated truth?**
- **Today: contained.** The only consumer is the **measurement experiment**, which maps
  `assessment` (SUPPORTIVE/CAUTIONARY/NEUTRAL) to a manufacturability-equivalent class to *measure
  compounding* — a controlled, leakage-audited context, not a production claim. The honesty invariant (§8),
  advisory-only, and situation-internal constraints prevent the critique from being asserted as a verdict.
- **Forward-looking risk (real but not yet actualized).** If a *future* external consumer (post-RM6, or a
  decision/evaluation rung) reads `assessment == SUPPORTIVE` as "independently validated," the critique
  object gives it **no verification provenance or uncertainty marker** to prevent that misread (Q4). This
  is the one legitimate carry-forward concern — and it is exactly what RM6 (real Velith) will make
  material, because only then do `velith_verified` precedents actually populate corpora.

---

## 8. The intended contract (as determinable) — and the precise residual ambiguity

**Determinable intended contract (not ambiguous):**
- RM4 is **advisory, deterministic judgment of contextual soundness**; it **must not verify** (Law 9, §7).
- "Verified precedent/verdict" = **a real, hash-verified recorded manufacturability verdict** (RM3 §3/§5).
  The signal is correctly derived from recorded verdicts; the code conforms.
- `engineering_verification_status` / `precedent_verification_status` are **recorded provenance for honesty
  and future widening**, not current judgment inputs (RM3 line 173; RM4 §3).

**Precise residual ambiguity (the only one):** a single English word, "verified," denotes two different
things across the specs — *hash-verified verdict* (operative now) and *Velith-verified design* (future).
This lexical overload is what misled the first audit and could mislead future readers/consumers. It is a
**wording** problem, not a logic or contract-semantics problem.

---

## 9. Decision

**A — Preserve behavior; clarify wording only.** No change to judgment logic, signal derivation, schemas,
or the critique object's fields.

**Rationale:**
1. The code conforms to the frozen specs' *defined* meaning of "verified" (§3, §4).
2. Conditioning judgment on `velith_verified` is explicitly a **future widening** gated on real Velith
   (RM3 line 173; RM6 planned/blocked), and making RM4 re-weight on design-verification brushes against
   §7/Law 9 (RM4 must not verify) and the project's standing guard against premature abstraction.
3. There is **no supply** of verified-design precedents to condition on today (§6, Leg 1), so a logic
   change would be untestable on real data and would add a dormant branch — exactly the speculative
   abstraction the Constitution forbids.

**Clarification actions (wording/documentation only — NOT performed here; proposed for a separate,
ratified doc change):**
- Add a one-line glossary note wherever RM3/RM4 use "verified" that distinguishes *hash-verified verdict*
  (current, drives the signal) from *Velith-verified design* (`engineering_verification_status`; future
  widening, RM6). Candidate sites: RM4 spec §1 line 14; RM3 spec §3/§5; `critic_model.py` docstring
  lines 11–13 ("the strongly-relevant verified precedent").
- No code, schema, or test change. (Editing a *frozen spec*, even for wording, is itself a
  Laws-22/23 ratified change — see §11.)

**Decision B is NOT recommended now**, but the exact trigger to reopen it is defined in §10 so the
forward-looking risk (Q4/Q7) is not lost.

---

## 10. If B were ever taken (not now): falsifiable criteria + smallest additive change

Recorded so the RM6 team inherits a ready, bounded option. **Do not implement.** Reopen **only** when real
Velith (RM6) actually populates corpora with `velith_verified` precedents (a *second-consumer*/real-data
trigger analogous to RM4 §12 extraction discipline).

**Smallest additive change (transparency, not re-weighting — stays within §7/Law 9):**
- Carry the supporting precedent's `precedent_verification_status` into the `PRECEDENT_CONSISTENCY`
  finding's `detail` (and/or a new finding field), and include it in `_critique_identity`. Guard with a
  `critic_model_version` bump (e.g. `1.0.0 → 1.1.0`). **Do not** change `_derive_signal` or the
  SUPPORTIVE/CAUTIONARY logic — the assessment stays verdict-based; only *provenance is surfaced*. This
  preserves "RM4 never verifies" while letting a consumer tell declared from verified.

**Falsifiable acceptance criteria:**
1. Construct two `EngineeringSituation`s identical except the supporting precedent's
   `precedent_verification_status` (`velith_verified` vs `engineer_declared`).
   - **Pre-change (current, must hold):** `critique().content_hash` **equal**; findings identical.
   - **Post-change (gap closed):** `critique().content_hash` **differs**, and the finding names the status.
   - Measured quantity: a single boolean (hash equality) + a finding-field diff.
2. **Regression invariant:** under `critic_model_version 1.0.0`, every existing RM4/RM5/RM15 output is
   **byte-identical** (frozen goldens + the all-`engineer_declared` corpora unchanged); the new behavior
   appears only under the bumped version. Falsified if any 1.0.0 golden moves.
3. **Honesty invariant preserved:** assessment distribution over the current corpora is unchanged (the
   change is additive provenance, not re-weighting). Falsified if any assessment value changes under 1.0.0.

---

## 11. Compatibility risks and required independent review

**Compatibility risks:**
- **Frozen-spec edits are not free.** Even the §9 wording clarifications touch *frozen* RM3/RM4 specs and
  `critic_model` docstrings; per Laws 22/23 and the RM4 "frozen (ADR-0008)" status, a wording change needs
  a ratified doc change + ADR, not a silent edit.
- **Determinism/hashing (only if B is ever taken):** adding a field to `_critique_identity` changes the
  critique `content_hash` under the new `critic_model_version`; the version bump is what keeps 1.0.0
  reproducibility intact. Any change outside a version bump would break the RM4/RM5/RM15 frozen goldens.
- **Law 9 boundary:** B must remain *surfacing provenance*, never *re-verifying* or *re-weighting on
  design verification*; crossing that line converts RM4 into a verifier and violates §7.
- **No contract change either way:** `precedent_verification_status` already exists in
  `precedent_report.schema.json`; surfacing it in the (internal) critique needs no schema change.

**Required independent review (before ANY action, including wording):**
- The standing independent reviewers (Gemini / DeepSeek) plus the Research Director, per the project's
  gating discipline.
- Specifically confirm: (1) the two-senses-of-"verified" reading of RM3/RM4 is accepted; (2) Decision A is
  adopted and the wording-clarification scope is authorized as a ratified doc/ADR change (or deferred);
  (3) Decision B remains parked against the RM6 real-data trigger with the §10 criteria.

---

## 12. Source index

- `specs/milestones/RM4-engineering-judgment.md` — §1 (l.14, identity & "verified precedent"), §3 (l.31,
  inputs), §4 (l.35, advisory/internal output), §7 (l.52, non-responsibilities / Law 9), §8 (l.56,
  honesty invariant); status "Frozen (ADR-0008)".
- `specs/milestones/RM3-engineering-precedent-reasoning.md` — §3 (l.52–53, corpus "content-hash-verified"),
  §4 (l.59–62, report), §5 (l.72–84, signal from "verified verdicts"), honesty (l.105, 125), future
  widening "Velith-verified designs" (l.173).
- `docs/adr/0008-rm4-acceptance.md` — l.25 (no re-derivation/re-verify), l.31 (constituent set), l.38
  (situated value: MANUFACTURABLE plan vs NOT_MANUFACTURABLE precedent → CAUTIONARY).
- `src/mini_prometheus/precedent/reasoner.py` — `_entry` (l.75, records status), `_derive_signal`
  (l.88–91, verdict-based), docstring honesty (l.17–19).
- `src/mini_prometheus/judgment/critic_model.py` — docstring (l.11–13), `_precedent_consistency`
  (l.138–165), `_internal_verdict` (l.168–181), `assess` (l.102–113).
- `src/mini_prometheus/judgment/engineering_critique.py` — `EngineeringCritique` (l.39–52),
  `_critique_identity` (l.84–98).
- `src/mini_prometheus/judgment/engineering_situation.py` — `assemble` (l.68–101; holds design_input +
  precedent_report, so status is available in-situation but unused).
- `src/mini_prometheus/orchestration/judgment_runner.py` — `run_judgment` (composition).
- `src/mini_prometheus/experiment/arms.py` — `_judge` (l.62–69, consumes `critique.assessment`).
- `src/mini_prometheus/intake/request_intake.py` — l.47 (`engineer_declared` hard-set).
- `src/mini_prometheus/integrations/velith/adapter.py` — l.36–52 (`velith_verified` producible; fixture).
- `src/mini_prometheus/orchestration/runner.py` — `run_from_velith` (l.99–108).
- `contracts/schemas/manufacturing/precedent_report.schema.json` — `PrecedentSignal` (l.38–42),
  `PrecedentEntry.precedent_verification_status` (l.55, 71).
- `tests/fixtures/rm5_corpus/episodes.jsonl` (450 declared / 0 verified);
  `tests/fixtures/rm15_corpus/episodes.jsonl` (960 declared / 0 verified).

*No application code, schema, test, dependency, frozen spec, ADR, or Git state was changed. This note is
the only artifact produced.*
