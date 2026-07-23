# ADR 0002 — Architecture refinement pass (external review)

- **Status:** Accepted
- **Date:** 2026-07-16
- **Deciders:** Architecture Board
- **Supersedes:** — (refines, does not supersede, ADR-0001)
- **Constitution version in force:** 1.0.0

## Context

The Phase 1 Repository Foundation (ADR-0001) has been committed and frozen. Before any runtime
implementation begins, an external architecture review requested six documentation clarifications.
None touch the frozen constitutional architecture; all are refinements to make existing rules
explicit. This ADR records the decisions; the normative text lives in
[`docs/architecture/repository-architecture.md`](../architecture/repository-architecture.md) §§12–16.

## Decision

1. **External contracts vs internal implementation APIs are formally distinguished** (arch doc §13).
   `contracts/` is the only cross-boundary surface (versioned, compliance-tested). Everything else a
   package exposes is internal, unguaranteed, and marked (`_`-prefixed or `_internal`); a cross-package
   import of a non-contract symbol fails CI.
2. **The five-layer hierarchy is formalized** (arch doc §2 diagram + §12.1):
   Constitution → Specification → Contract → Implementation → Verification, each derived from and
   constrained by the layer above; no layer may be skipped.
3. **`world_model/` and `constraint_network/` are documented as expandable package namespaces**
   (arch doc §12.2): their internal structure grows submodules over time while their external contract
   stays fixed in `contracts/`. Internal growth is not a "speculative folder."
4. **`integrations/` is adapters-only, no business logic** (arch doc §14): each adapter only translates
   a frozen upstream's types to/from our contract types. Business logic in an adapter is a violation.
5. **Inter-package dependency rules are made explicit** (arch doc §14): owned object packages depend on
   `contracts/` only and are peers (never import each other); `orchestration` is the sole composition
   root permitted to import concrete packages to wire them; integrations depend only on contracts plus
   their one pinned upstream. Enforced via import-linter in CI when implementation lands.
6. **The Constitution is versioned** (arch doc §15): additive `constitution/VERSION` baseline `1.0.0`.
   Amendments bump it and cite an ADR. Downstream artifacts record the constitution version they derive
   from, giving an unbroken trace from any shipped artifact to the frozen theory.

## Consequences

- The rules in points 1, 4, 5 are documentation now and become executable import-linter contracts when
  the first implementation lands — no runtime code is added by this ADR.
- `constitution/VERSION` gives permanent, auditable traceability without changing any frozen content.
- No directory was added or removed; no frozen document was modified. The Phase 1 freeze holds.

## Alternatives considered

- **Encode the dependency rules only in code later** — rejected: teams start implementing before that
  code exists; the rules must be authoritative documentation from day one.
- **Version the Constitution by git SHA only** — rejected: a semantic version communicates the *kind*
  of change (MAJOR/MINOR/PATCH) and is what downstream artifacts can meaningfully pin to.
- **Merge internal APIs into `contracts/` for convenience** — rejected: it would destroy the freedom to
  rewrite implementations that the contract spine exists to protect.
