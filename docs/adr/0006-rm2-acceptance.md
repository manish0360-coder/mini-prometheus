# ADR 0006 — RM2 implementation and acceptance

- **Status:** Accepted
- **Date:** 2026-07-25
- **Deciders:** Project owner (acceptance); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM2-experience-reuse.md`, `docs/design/RM2-engineering-package.md`, `docs/design/RM2-implementation-plan.md`, `docs/milestones/RM2-completion-report.md`, ADR-0005 (RM1 acceptance)

## Context

RM2 was selected from first principles (candidate comparison in the frozen RM2 spec §B): the Constitution's
spine is compounding (§1.7, Principle 8), and RM1 logged experience but never used it. RM2 delivers the read
side of the Experience Flow — reuse of prior verified experience — with no external dependency. It was built
in five milestones (M1–M5) exactly as the frozen implementation plan specified.

## Decisions (as built)

1. **Additive only.** The reuse composition lives in a **new file** `orchestration/reuse_runner.py`; RM1's
   `runner.py` and every other RM1 module are byte-unchanged, enforced by a CI zero-diff gate vs `rm1-complete`.
2. **No new contracts.** RM2 reuses the frozen `ManufacturingEpisode`/`ProductionPlan`/`Verdict`; `contracts/VERSION`
   stays `0.2.0`, asserted by a CI contract-freeze gate.
3. **Composite reuse key** `(design_input_identity_hash, capability_model_version)` — no stale-model reuse.
4. **Reproducibility guard on by default** — a reused plan is re-derived and its `content_hash` asserted
   (verification-first, Principle 1); mismatch raises `ExperienceConsistencyError`.
5. **Law-6 boundary held.** The read side is a minimal in-memory index over MP's own episodes — no retention/
   compression/pruning/query engine (that is Noetica's lifecycle framework, §11.11; deferred). It is the
   extraction seed for Noetica (Law 8, N.3). Enforced by an AST boundary test + import-linter.
6. **Roadmap reprioritization recorded.** RM2 = experience reuse (this milestone) preceded real-Velith, which
   becomes RM3. Justified by first principles; reflected in `docs/ROADMAP.md`.

## Acceptance

RM2 is **accepted and frozen**: delivered exactly as specified across M1–M5; **50 tests pass** (RM1's 31
unchanged + 19 RM2); ruff clean; contracts frozen; bindings drift-stable; boundary and RM1 zero-diff gates
in CI. Runtime `0.2.0 → 0.3.0`; tag `rm2-complete`. Recorded in `CHANGELOG.md`, `docs/ROADMAP.md`, and
`docs/milestones/RM2-completion-report.md`.

## Consequences

- RM2 modules, spec, engineering package, and implementation plan are frozen; change only on a discovered
  critical defect.
- RM3 (real pinned Velith package) is the next milestone, gated on Velith publishing a consumable release
  (CAP-0001 Field 8) — independent of RM1/RM2.

## Alternatives rejected

Real-Velith-first (externally gated, low present value — RM2 spec §B); DFM depth (premature abstraction);
STEP geometry (too large / research-grade). Full rationale in the frozen RM2 spec.
