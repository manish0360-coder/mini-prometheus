# RM4 Completion Report — Engineering Judgment (first implementation: Engineering Critique)

- **Milestone:** RM4 (fourth runtime implementation milestone).
- **Status:** ✅ Complete and frozen — 2026-08-03. Runtime `0.4.0`. Tag: pending `rm4-complete`.
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged** — RM4 adds no contract).
- **Frozen artifacts:** `specs/milestones/RM4-engineering-judgment.md` (spec), `docs/design/RM4-engineering-package.md`
  (engineering package), ADR-0008 (acceptance).

## 1. What RM4 delivered

**Engineering Judgment** — the deterministic, advisory capability of *judging a proposed manufacturing solution in
the full context of its case*. Its first implementation is **Engineering Critique**: given a case's RM1 plan/verdict
and RM3 precedent report, RM4 assembles the internal `EngineeringSituation`, applies a versioned critic model, and
returns an advisory `EngineeringCritique` (findings + summary assessment). This is **compounding rung 3** — the first
capability that reasons over the *whole case* rather than a single artifact.

```
(RM1 episode, RM3 precedent report)
   → EngineeringSituation (assemble; internal, fail-closed coherence)
   → EngineeringCritique  (critic_model → findings → assessment; advisory)
```

## 2. Delivered across the six commits

| Commit | Deliverable | Files (new) |
|---|---|---|
| **C1** | Internal `EngineeringSituation` (coherent case state; strictly internal) | `judgment/__init__.py`, `judgment/engineering_situation.py`, `tests/unit/test_engineering_situation.py` |
| **C2** | Deterministic versioned `critic_model` (finding families + assessment) | `judgment/critic_model.py`, `tests/unit/test_critic_model.py` |
| **C3** | `engineering_critique` (first implementation of Engineering Judgment) | `judgment/engineering_critique.py`, `tests/unit/test_engineering_critique.py` |
| **C4** | `judgment_runner` composition (situation → critique) | `orchestration/judgment_runner.py`, `tests/integration/test_engineering_judgment.py` |
| **C5** | Boundary gates + CI wiring | `tests/boundary/test_judgment_boundaries.py`, `.github/workflows/ci.yml` (edit) |
| **C6** | Governance close-out | this report, ADR-0008, CHANGELOG `[0.4.0]`, roadmap, release notes, version bump, frozen spec/package |

## 3. Verification evidence

- **131 tests pass** (RM3's + 39 RM4: 6 situation, 8 critic-model, 8 critique, 6 pipeline integration, 7 boundary,
  plus regressions); `mypy src` clean (36 files); pinned toolchain (ruff 0.6.9 / mypy 1.11.2 / pytest 8.3.3).
- **Determinism:** identical `(episode, precedent_report)` + identical `critic_model_version` ⇒ identical critique
  `content_hash` (`produced_at`/provenance excluded).
- **Situated value:** a plan whose own RM1 verdict is `MANUFACTURABLE`, but which strongly resembles a
  `NOT_MANUFACTURABLE` precedent, yields a **CAUTIONARY** critique — a signal isolated RM1 verification cannot produce.
- **Read-only / fail-closed:** the pipeline writes nothing and mutates no store; a cross-case pairing raises
  `SituationCoherenceError`. **Additive:** RM1/RM2/RM3 byte-unchanged; **no contract** (`contracts/VERSION == 0.4.0`).

## 4. Boundaries held (see ADR-0008)

No planning, no manufacturability verification, no retrieval (RM4 consumes RM1/RM3 *output types* only — it never
re-plans, re-verifies, or re-retrieves, and never touches the RM2 read side); no persistence; no ML/embeddings; no
MiniFlyWire (Law 4); no Noetica store engine (Law 6). Enforced by AST boundary tests + import-linter.

## 5. Primitive Revelation (RM4's second architectural purpose)

RM4 was the **first real consumer** of the internal `EngineeringSituation` primitive, tasked with *revealing* its
stable shape rather than predicting it. **Observed load-bearing constituent set:** `{design_input, plan, verdict,
precedent_report}` — all four are actually required by the critic model's finding families (intent-coverage uses
design+plan; internal-verdict uses verdict; precedent-consistency uses the precedent report). The set was **stable**
across all three finding families and did not change during implementation (hypothesis H2, so far, not falsified).

**Extraction status:** `EngineeringSituation` remains **internal to RM4** — no contract, no persistence, no external
identity. Per the frozen spec §12, extraction to a first-class contract is triggered only by a **second independent
consumer** or a cross-boundary coherence requirement, decided through the Extraction Review Gate. Neither has
occurred; extraction is correctly **deferred**.

*RM4 is closed. Do not modify unless a critical defect is discovered.*
