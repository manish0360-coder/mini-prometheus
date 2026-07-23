# ADR 0003 — Runtime implementation order: Situation State first (RM1)

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Architecture Board (proposed by Chief Systems Engineer)
- **Supersedes:** —
- **Constitution version in force:** 1.0.0
- **Related:** ADR-0001 (repository architecture), ADR-0002 (refinement pass), `specs/interfaces/situation-state.md`

## Context

The repository architecture is frozen. Runtime implementation now begins. We must implement one
logically complete subsystem at a time (no simultaneous subsystems) and choose the first milestone by
dependency order derived from the frozen architecture.

## Decision

The first runtime milestone is **RM1 — Situation State vertical slice + contract pipeline**. RM1
implements the Situation State object end-to-end (Specification → Contract → Implementation → Testing →
Verification) and, in the same milestone, stands up the reusable contract machinery (`tools/`
schema→bindings codegen, `tests/contracts/` compliance harness, real CI gate replacing placeholders).

We introduce a **runtime milestone track (RM1, RM2, …)** distinct from the directory-creation
milestones (M1–M3) in ADR-0001/§7, which denote when future directories are created.

## Rationale (dependency order)

1. **Contract-first is frozen (§12–§14).** No implementation may exist without a contract, generated
   bindings, and a compliance suite. That pipeline is built once and reused; RM1 builds it on the
   simplest real object rather than a throwaway.
2. **Situation State is the substrate — the root of the derivation.** The Engineering World Model is a
   view over Situation State; the Constraint Network reasons over the World Model. The three are
   import-peers (§14) but form a strict build order. Situation State has no conceptual dependency on
   sibling objects and everything else depends on it.
3. **Orchestration and integrations cannot precede it.** `orchestration` is the composition root with
   nothing to compose until an object exists; `integrations/` adapters need a contract to translate
   upstream types into. Native acceleration is benchmark-justified (M2).

Therefore Situation State is the only object implementable without depending on unbuilt work, and it
unblocks the rest. RM1 is logically complete: a trustworthy state substrate plus a proven pipeline.

## Alternatives considered

- **World Model first** — rejected: defined over Situation State; inverts the derivation.
- **Integration-first to de-risk the frozen upstreams** — strongest counter (upstreams are external),
  but they passed independent readiness reviews and an adapter needs a contract target. Integration
  de-risking is slotted after the first contract exists (RM2/RM3), not RM1.
- **Tracer-bullet on a throwaway dummy object** — rejected: proving the pipeline on the real Situation
  State avoids discardable work.

## Consequences

- RM1 has a **precondition**: the frozen Situation State definition must be transcribed into
  `constitution/` (currently placeholders) before the Specification can be finalized. Tracked in
  `specs/interfaces/situation-state.md` §2. This is transcription of frozen theory, not redesign.
- RM1 deliberately spans three ownership domains (World-Model team; Infra for `tools/`/CI; Board+Staff
  for `contracts/` and `tests/contracts/`). It is sequenced as separate atomic per-owner PRs so
  change-atomicity and CODEOWNERS review authority are both preserved.
- Subsequent order (indicative, re-derived per milestone): RM2 World Model, RM3 Constraint Network,
  with orchestration wiring and integration/provenance slices introduced once their contract targets
  exist.
