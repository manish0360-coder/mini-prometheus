# ADR 0009 — RM5 (Compounding Validation Experiment) implementation and acceptance

- **Status:** Accepted
- **Date:** 2026-09-15
- **Deciders:** Project owner / Director (acceptance); Chief Systems Engineer (author); Gemini (independent review)
- **Constitution in force:** v1.1.0
- **Related:** `docs/milestones/RM5-completion-report.md`, `src/mini_prometheus/experiment/`,
  `tests/fixtures/rm5_corpus/`, `tests/unit/test_rm5_reproducibility.py`, ADR-0008 (RM4)

## Context

The roadmap slot originally labelled "RM5 = wire the real pinned Velith package" was **externally blocked** (Velith
`m8-complete`, version `0.0.0`, no consumable release, no `EngineeringTask`/`EngineeringResult` API; manufacturing is
its decade-scale destination). Real-Velith integration moves to **RM6+**. RM5 was reprioritized to a rigorous,
fully-unblocked internal validation of the compounding spine (Constitution §1.7): does accumulated verified
experience measurably improve RM4 judgment against the deterministic RM1 oracle, on strictly held-out
analogous-but-non-identical cases, within one fixed regime R*?

## Decisions (as built)

1. **Identity = Compounding Validation Experiment; a measurement milestone, not a capability.** No cognitive
   primitive, no public contract/schema, no change to RM1–RM4. New leaf package `experiment/`.
2. **One fixed regime R* = `default_model()` minus `lathe01`** (valid-SemVer label `2.0.0`; full regime recorded in
   the checkpoint). Frozen, content-addressed held-out partition; the committed fixture is the source of truth and is
   **not regenerated** during evaluation.
3. **Three arms; primary causal contrast Arm 3 − Arm 2; validity control Arm 1 == Arm 2.** Arms differ only in the
   precedent input, composing RM3 retrieval/reasoning + RM4 judgment read-only (no reasoning re-implemented).
4. **Frozen protocol, exact rationals.** Assessment↔oracle mapping, per-case predicates, the RM4-H1-grounded
   false-alarm ceiling (0), hard validity gates separated from non-mutating hypothesis criteria, and the mandatory
   Statement of Claims — all pinned; the report `content_hash` is frozen in CI.
5. **No contract.** `contracts/VERSION` stays `0.4.0`. Runtime bumps `0.4.0 → 0.5.0` (governance/versioning only).
6. **Results are observations of record and were not modified.** H2 (false-alarm ceiling) NOT met (3/45) and strict
   monotonic compounding NOT met (final step decreases) are **valid scientific findings**, preserved exactly.

## Acceptance

RM5 is **accepted and frozen**. Delivered across C0+C1 (`10fca38`), C2–C4 (`2e1118f`), C5 (`a4d11eb`), and this C6
close-out. **Controls passed:** Arm 1 == Arm 2 121/121; cross-partition duplicates 0; deterministic checkpoint
`sha256:9aec55…`; RM1–RM4 byte-unchanged; reproducible report `sha256:2b7c48…`. **Primary result:** Arm 2 76/121,
Arm 3 118/121, marginal **+42/121 (+0.3471)**, concentrated on MANUFACTURABLE (42/45; NOT-class marginal 0/76).
Coverage 45/45 and 76/76; false alarms 3/45; excluded duplicates 0. **Independent review (Gemini):**
`SCIENTIFICALLY SOUND AS A LIMITED INTERNAL VALIDATION` (circularity LOW; synthetic-corpus generalization MEDIUM; no
mandatory correction). Full verification: full `pytest` green, `mypy src` clean, import-linter 3/3 kept, boundary/CI
gates green, contracts frozen at `0.4.0`.

## Claim boundary (preserved)

RM5 establishes a positive finite-corpus precedent effect **within the deterministic oracle-internal world only**. It
does **not** establish real-world manufacturing correctness, DFM correctness, cost/quality improvement, superiority to
human engineers, or deployment readiness, and it does not demonstrate strict monotonic compounding.

## Consequences

- `experiment/`, the fixture, the frozen protocol, and the measured result are frozen; change only on a discovered
  critical defect. The reproducibility test must not be "updated" to accommodate a changed result without explicit,
  reviewed decision.
- Next: **RM6** — consume the real Velith/Noetica pinned packages when published (external gate), and revisit the
  near-miss / synthetic-corpus generalization caveat on organic data.

## Alternatives rejected

Forcing the compounding curve monotonic or removing the 3 false alarms (would falsify observations); introducing a
new contract/schema for the report (over-reach — it is a runtime measurement object); regenerating or enlarging the
corpus to improve the result (violates the frozen design); building a general experiment framework (premature — one
question, one regime).
