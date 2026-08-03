# ADR 0007 — RM3 (Engineering Precedent Reasoning) implementation and acceptance

- **Status:** Accepted
- **Date:** 2026-08-03 (documented in the consolidated `0.4.0` release)
- **Deciders:** Project owner (acceptance); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM3-engineering-precedent-reasoning.md`, `contracts/RM3-contract-package.md`,
  `docs/design/RM3-engineering-package.md`, `docs/milestones/RM3-completion-report.md`, ADR-0006 (RM2), ADR-0008 (RM4)

## Context

A first-principles review advanced the **compounding spine** (Constitution §1.7) ahead of external package
integration. RM3 became **Engineering Precedent Reasoning** (compounding rung 2), reprioritized above the
real-Velith integration (now RM5). RM3 generalizes RM2's exact reuse to *analogous* verified cases.

## Decisions (as built)

1. **Seed/identity separation (Law 3/8).** The **retriever** is the isolated extraction-seed *mechanism* (a
   deterministic O(N) ranker); the **reasoner** is the domain *identity* that derives the signal and assembles the
   `PrecedentReport`. Keeping them apart lets a future Noetica retrieval mechanism replace the seed without touching
   the reasoner or the contract.
2. **Additive contracts.** `PrecedentReport`/`PrecedentEntry`/`PrecedentSignal` only; part of the `0.4.0` suite.
3. **Deterministic structural relevance** — no ML/embeddings/vector DB; integer per-mille relevance; total-order
   ranking with a `content_hash` tie-break.
4. **Read-only; Law-6 boundary held** — no store/retention engine; the retriever is the sole RM2-read-side consumer.
   Enforced by an AST boundary test + import-linter.
5. **Architectural debt recorded** (`docs/governance/RM3-architectural-debt.md`): the O(N) retriever is an intentional
   MP-local extraction seed; scalable indexed retrieval is future Noetica extraction.

## Acceptance

RM3 is **accepted and frozen** as part of the consolidated `0.4.0` release. Delivered exactly as specified (M2–M5);
verified deterministic, read-only, additive; RM1/RM2 behavioral core byte-unchanged. Runtime `0.4.0`. Its runtime
close-out was deferred at the time; this ADR records acceptance retroactively. RM3's code has been frozen since it
was committed.

## Consequences

- RM3 modules, spec, contract package, and engineering package are frozen; change only on a discovered critical defect.
- RM4 (Engineering Judgment) consumes RM3's `PrecedentReport` output read-only.
