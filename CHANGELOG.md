# Changelog

All notable changes to Mini Prometheus are recorded here. The runtime and the contract suite
(`contracts/VERSION`) are versioned independently; both are noted below.

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: SemVer.

## [Unreleased]

### Added
- Phase 1 repository architecture: governance, contract spine, and runtime substrate skeleton.
  Runtime `0.1.0`, contracts `0.1.0`. See `docs/adr/0001-adopt-repository-architecture.md`.
- Constitution versioning: additive `constitution/VERSION` baseline `1.0.0` for long-term traceability.

### Changed
- Architecture refinement pass (documentation only, external review): formalized the five-layer
  hierarchy, distinguished external contracts from internal APIs, documented expandable namespaces,
  the integrations adapters-only rule, and inter-package dependency rules. No frozen content, no
  directories, no runtime code changed. See `docs/adr/0002-architecture-refinement-external-review.md`.

### Planning
- RM1 selected as the first runtime implementation milestone (Situation State vertical slice + contract
  pipeline). Specification drafted at `specs/interfaces/situation-state.md` (blocked on constitutional
  transcription). Decision recorded in `docs/adr/0003-runtime-implementation-order.md`. No runtime code.

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
