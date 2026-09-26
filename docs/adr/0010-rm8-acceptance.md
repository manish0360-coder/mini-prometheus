# ADR 0010 — RM8 (Engineering Constraint Reasoning) implementation and acceptance

- **Status:** Accepted (Director design freeze and gate ratification, 2026-09-26)
- **Date:** 2026-09-26
- **Deciders:** Project owner / Research Director (design freeze, Option A ratification); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM8-engineering-constraint-reasoning.md`, `docs/milestones/RM8-completion-report.md`,
  `tests/fixtures/rm8_default_behavior_golden.json`, `tests/unit/test_rm8_default_zero_diff.py`, ADR-0005 (RM1),
  ADR-0004 / CAP-0001 (Situation State withdrawn)

## Context

RM1's manufacturing loop is complete but its manufacturability oracle under-reports its own frozen taxonomy
(`TOLERANCE_UNSUPPORTED` never emitted; `PRECEDENCE_VIOLATION` only structural). RM6 (real Velith) and RM7 (real
Noetica) remain externally blocked. The roadmap's RM8+ slot ("tolerance/precedence models") is the smallest
unblocked step that makes Mini Prometheus's manufacturing verification materially more real. A first increment
(C1) existed only as a local, unpushed commit `ad90856` with no specification or ADR.

## Decisions (as built)

1. **Identity: Engineering Constraint Reasoning (ECR).** Two deterministic oracle checks driven only by the capability
   model's declarative constraint data: declared precedence (C2) and tolerance feasibility (C3); plus the CLI switch
   (C4). No contract, schema, enum member, protocol, dependency, or ownership change.
2. **Situation State: none.** Represented by the existing `DesignInput` + internal `EngineeringSituation`; no MP-owned
   state component (CAP-0001). Noetica owns state, Velith engineering intelligence, Mini Prometheus manufacturing
   intelligence.
3. **C1 adopted after audit.** Original commit `ad90856c2e13ae9922b299c5fca4c71fd01459ad` (2026-09-15, local, never
   pushed) was audited read-only — contracts unchanged, no dependency, import rules clean, default behavior preserved
   (902 serialized outputs identical to `rm5-complete`) — and its implementation is folded unchanged into the single
   RM8 commit. C1 is not a separate milestone.
4. **Precedence → `PLAN_INVALID`** with `PRECEDENCE_VIOLATION`; declared pairs only; RM1's structural check unchanged.
5. **Tolerance → `NOT_MANUFACTURABLE`** with the existing `TOLERANCE_UNSUPPORTED`; strict `<` against the capability
   minimum; equal/looser feasible; absent tolerance or non-tolerance-bearing capability → no check. The requested
   tolerance reaches the oracle through the open `ProcessStep.params` (`required_tolerance_mm`), written by the
   planner only under a model with tolerance data, because the `Verifier` signature is fixed.
6. **All findings reported;** `PLAN_INVALID` dominates `NOT_MANUFACTURABLE`; a tolerance finding is never dropped.
7. **Versioning:** verifier `1.0.0` on the default path, `1.1.0` when constraint data is present; planner rule
   `1.1.0` only when tolerance data is introduced. Capability model: default `1.0.0`, constrained `1.1.0`.
8. **CLI:** `--capability-model {default,constrained}`, default `default` = legacy behavior. The legacy default CLI
   does not read `tolerances` and performs no tolerance reasoning — documented as a known limitation, not fixed,
   because fixing it would change default-mode outputs.
9. **Gate evolution (Option A, ratified).** The CI byte-freeze of the RM1/RM2 core (zero-diff vs `rm2-complete`) is
   replaced **only** for `capability_model.py`, `oracle.py`, `planner.py` and `orchestration/runner.py` by a
   committed behavioral zero-diff gate. The directories remain byte-frozen via pathspec exclusions of exactly those
   files. The golden was generated once from `rm5-complete` (`96eb81f`) and is frozen by digest
   (`f36c5d4be10da83d8669c5036ecf36d607e699b3129e9075f14426ac606ffa02`) along with its generating probe
   (`47a218c63e25060617a43d393163f9aedffafc7d960071dbdda495dd0f38bb4c`); it is never regenerated. No unrelated
   gate is weakened.
10. **Versions:** runtime `0.5.0 → 0.6.0`; contract suite stays `0.4.0`.

## Consequences

- Constrained mode now rejects misordered routings and tolerances tighter than the assigned process can hold, with
  grounded, logged verdicts. Default mode and every RM1–RM5 artifact are unchanged.
- The tolerance model is a coarse demo-domain approximation (one scalar per capability); no real-world tolerance,
  GD&T or DFM claim is made.
- Future edits to the four RM8 files are governed by the behavioral golden, not by byte identity; any default-path
  behavior change fails CI.

## Alternatives rejected

- **Option B (new package, all byte gates untouched):** departs from the frozen design (no "existing CLI", C1
  relocated) and duplicates plan-hashing logic.
- **Changing the Verifier signature or the contract** to carry tolerance: forbidden by the freeze.
- **Fixing the legacy default CLI's tolerance drop:** would change default-mode outputs; out of scope.
