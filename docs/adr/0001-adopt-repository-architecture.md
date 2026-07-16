# ADR 0001 — Adopt the Mini Prometheus repository architecture

- **Status:** Accepted
- **Date:** 2026-07-16
- **Deciders:** Architecture Board
- **Supersedes:** —

## Context

Phase 1 of Mini Prometheus is starting. MiniFlyWire, Noetica, and Velith have passed independent
readiness reviews and their constitutional responsibilities are frozen. Mini Prometheus is now the
runtime orchestration platform integrating all three. We need a permanent repository architecture
derived from the frozen Constitution — not a runtime redesign.

## Decision

Adopt the structure specified in
[`docs/architecture/repository-architecture.md`](../architecture/repository-architecture.md).

Key decisions:

1. **Contracts are the spine.** A dedicated `contracts/` layer (language-neutral schemas + generated
   Python/native bindings) is the only permitted cross-boundary dependency. Implementations
   (`src/`, `native/`) depend on contracts, never on each other. This realizes "separate stable
   contracts from implementation" and "preserve architectural contracts."
2. **Frozen theory is segregated and amendment-gated** in `constitution/`, distinct from evolving
   `docs/`.
3. **Upstreams are pinned versioned package dependencies**, touched only through
   `src/mini_prometheus/integrations/`. No vendoring, no monorepo, no submodules.
4. **Python + Rust/C++**, with a single shared contract layer so the two languages cannot diverge.
5. **Ownership via `CODEOWNERS`**, with review scrutiny scaling toward the spine, enabling
   independent parallel teams.
6. **No speculative folders.** Future-milestone directories are documented but not created until
   their milestone opens.

Every top-level directory traces to a frozen constitutional clause (traceability matrix, §5 of the
architecture doc).

## Consequences

- The first commit establishes governance and the contract spine only — zero business logic.
- Contract changes are high-ceremony (SemVer bump + compliance-suite update + senior review); this
  is intentional and is the price of safe independent development.
- Two-language build complexity is deferred: `native/` crates open only when benchmark-justified.

## Alternatives considered

- **Monorepo including the three upstreams** — rejected: contradicts independent readiness reviews
  and clean repository boundaries.
- **Git submodules for upstreams** — rejected: heavier, source-coupled; pinned packages give a
  cleaner freeze boundary.
- **Co-locating contracts inside each implementation package** — rejected: reintroduces the
  impl-to-impl coupling this architecture exists to prevent.
