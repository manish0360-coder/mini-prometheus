# ADR 0008 — RM4 (Engineering Judgment) implementation and acceptance

- **Status:** Accepted
- **Date:** 2026-08-03
- **Deciders:** Project owner (acceptance); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM4-engineering-judgment.md`, `docs/design/RM4-engineering-package.md`,
  `docs/milestones/RM4-completion-report.md`, ADR-0007 (RM3)

## Context

RM4 is **compounding rung 3**: the first capability that reasons over the *whole case* (design + plan + verdict +
precedent) rather than a single artifact. Its architectural identity is **Engineering Judgment**; the first
implementation delivered is **Engineering Critique**. RM4 is also the first real consumer of the internal
`EngineeringSituation` primitive, tasked with revealing its stable shape (independent architectural review).

## Decisions (as built)

1. **Identity = Engineering Judgment; first implementation = Engineering Critique.** Future forms (comparison,
   ranking, evaluation, optimization advice) fit beneath this identity without change. Package named `judgment/`.
2. **`EngineeringSituation` is strictly internal.** The coherent single-case engineering state — no contract, no
   schema, no persistence, **no external identity** — consumed only within `judgment/` (boundary-test enforced).
   Its content-hash-free status is deliberate; the *critique* carries an in-memory reproducibility `content_hash`
   only (not persisted, not published, not a contract).
3. **No re-derivation.** RM4 receives already-produced RM1/RM3 **output types** and never re-plans, re-verifies, or
   re-retrieves; it never touches the RM2 read side. Enforced by an AST boundary test.
4. **No contract.** `contracts/VERSION` stays `0.4.0`; the advisory critique is a runtime object, not a contract.
5. **Deterministic, read-only, additive.** RM1/RM2/RM3 byte-unchanged; no ML/embeddings; no store/retention engine
   (Law 6); no MiniFlyWire (Law 4). Versioned `critic_model`; total-order findings; reproducible critique hash.
6. **Primitive revelation delivered.** Observed load-bearing constituents: `{design_input, plan, verdict,
   precedent_report}`; stable across the finding families. Extraction to a contract remains **deferred** (spec §12
   Extraction Review Gate) — no second consumer yet.

## Acceptance

RM4 is **accepted and frozen**: delivered across six commits (C1–C6) exactly as specified; **131 tests pass** (39
RM4 + regressions); `mypy src` clean; contracts frozen at `0.4.0`; boundary + import-linter gates green. **Situated
value proven**: a `MANUFACTURABLE` plan resembling a `NOT_MANUFACTURABLE` precedent yields a `CAUTIONARY` critique.
Runtime `0.3.0 → 0.4.0`; tag pending `rm4-complete`.

## Consequences

- RM4 modules, spec, and engineering package are frozen; change only on a discovered critical defect.
- Next: RM5 (real pinned Velith package), externally gated on a Velith consumable release. `EngineeringSituation`
  extraction is revisited only when a second consumer or cross-boundary coherence need appears.

## Alternatives rejected

Publishing `EngineeringSituation` as a contract now (premature — one consumer; repeats the withdrawn-Situation-State
error); giving the critique a persisted/published identity (over-reach — advisory only); a learned/ML critic (Law 6).
