# Changelog

All notable changes to Mini Prometheus are recorded here. The runtime and the contract suite
(`contracts/VERSION`) are versioned independently; both are noted below.

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: SemVer.

## [Unreleased]

_RM2 in planning (wire the real pinned Velith/Noetica packages). No changes yet._

## [0.2.0] — 2026-07-23 — RM1: "plan → verify → log" (first manufacturing capability)

**RM1 complete and frozen** (tag `rm1-complete`). Mini Prometheus turns a real engineer
`ManufacturingRequest` into a verified, provenance-complete `ProductionPlan` + `ManufacturingEpisode`.
First tagged release; runtime `0.1.0` → `0.2.0` (contracts `0.2.0`, constitution `1.1.0`).
See `docs/milestones/RM1-completion-report.md` and `docs/ROADMAP.md`.

### RM1 — Implementation milestone (complete)
- Implemented the plan → verify → log manufacturing loop strictly against the frozen contracts:
  intake (`intake/`), Velith adapter (`integrations/velith/`), deterministic planner
  (`manufacturing_planning/`), manufacturability oracle implementing the Noetica `Verifier` protocol
  (`manufacturing_constraints/`), episode emission + composition root (`orchestration/`), and internal
  mechanisms (`_hashing`, `_validate`, `_provenance`, `_verifier`, `_contracts`).
- Produces a tangible **ProductionPlan** for a real engineer `ManufacturingRequest` (machined part) and a
  content-hashed, provenance-complete **ManufacturingEpisode**; INFRA_ERROR writes no episode.
- Verified: **31 tests pass** (contract-compliance, unit, integration [determinism, negative, both intake
  paths, honesty chain, INFRA_ERROR], boundary [Law 4/6/9/15]); ruff clean; bindings regeneration-stable.
  Real CI pipeline in `.github/workflows/ci.yml` (drift → build → unit → contract → integration → boundary).
- One fixed defect found during implementation: episode identity used `plan.content_hash` (not the embedded
  plan) per contract package §3.6, restoring hash determinism. No spec/contract/schema change.

### RM1 — Contract stage (frozen)
- Froze the RM1 Contract Package (`contracts/RM1-contract-package.md`): demonstration domain = Machined Part;
  `ManufacturingRequest` primary input; STEP opaque-only; permanent `NS_MP = 4f5b56ae-3c77-4135-9f5c-1eef0ab1b252`.
- Authored 10 JSON Schema files (Draft 2020-12) under `contracts/schemas/` — MP-owned manufacturing set +
  consumed Velith/Noetica stubs; all meta-validated and ref-resolved.
- Generated Python bindings (`contracts/python/`, typed dataclasses + StrEnum, no logic) via
  `tools/generate_contracts.py` (datamodel-code-generator). Suite `contracts/VERSION` 0.1.0 → **0.2.0**.

### Governance — constitutional archaeology + conformance (CAP-0001, ADR-0004)
- Reconstructed the project's evolution across 5 repositories (`docs/governance/constitutional-evolution-report.md`);
  verdict: **repository ownership correction required** (HANDBOOK_v1.1 governs, on evidence).
- **Ratified CAP-0001** (project owner) and conformed the repository:
  - Constitution: transcribed HANDBOOK_v1.1 + ARCHITECTURE_DECISION into `constitution/`; `VERSION` → **1.1.0**.
  - Ownership: `src/` packages renamed to manufacturing content
    (`situation_state→manufacturing_state`, `world_model→manufacturing_twin`,
    `constraint_network→manufacturing_constraints`); README/CODEOWNERS/architecture doc corrected.
  - Dependencies: removed `integrations/miniflywire/` (Law 4); `integrations/` now Velith + Noetica only.
  - Withdrawn: engineering cognition/reasoning packages (Velith content); `specs/interfaces/situation-state.md`; RM1 substrate framing (to be re-scoped to manufacturing content).
  - Recorded in `docs/adr/0004-conform-repository-to-handbook.md`. No runtime code.

### Earlier work included in this first release
- Phase 1 repository architecture: governance, contract spine, runtime substrate skeleton
  (`docs/adr/0001-adopt-repository-architecture.md`).
- Constitution versioning: additive `constitution/VERSION` (baseline `1.0.0`, now `1.1.0`).
- Architecture refinement pass (documentation only): five-layer hierarchy, external-vs-internal
  contracts, expandable namespaces, dependency rules (`docs/adr/0002-architecture-refinement-external-review.md`).
- RM1 planning + runtime implementation order (`docs/adr/0003-runtime-implementation-order.md`); the
  original Situation State RM1 spec was withdrawn by ADR-0004 and re-scoped to manufacturing content.
