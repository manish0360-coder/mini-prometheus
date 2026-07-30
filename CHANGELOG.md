# Changelog

All notable changes to Mini Prometheus are recorded here. The runtime and the contract suite
(`contracts/VERSION`) are versioned independently; both are noted below.

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: SemVer.

## [Unreleased]

### Changed — RM1 correction: `ManufacturingEpisode` complete engineering memory (ratified impact analysis)
- **`ManufacturingEpisode` gains optional `design_input: DesignInput`** so new episodes embed the full engineering
  input (complete engineering memory for future deterministic precedent reasoning). `manufacturing_episode`
  `schema_version` `1.0.0 → 1.1.0`; contract suite `contracts/VERSION 0.3.0 → 0.4.0`. `DesignInput` unchanged.
- **Backward compatible / migration:** `design_input` is **optional** and **excluded from the content-hash
  identity view** (design identity is already in `design_ref.content_hash`), so existing episode hashes are
  unchanged and legacy `1.0.0` episodes remain valid. Legacy episodes **cannot** be back-filled (their
  `material_code`/`tolerances` live only inside one-way hashes); no migration is performed. **Retrieval policy for
  legacy episodes is intentionally deferred to a later milestone** — legacy episodes are preserved, not classified.
- Updated: episode schema + regenerated `manufacturing_episode` binding; RM1 emission (`orchestration/episode_store.py`)
  now populates `design_input`; RM2 read-side (`experience/episode_store_reader.py`) reconstructs it when present;
  contract-version assertions `0.3.0 → 0.4.0`. No RM3 work; retriever not implemented.

## [0.3.0] — 2026-07-25 — RM2: experience read-back & idempotent reuse (compounding, rung 1)

**RM2 complete and frozen** (tag `rm2-complete`). Mini Prometheus now *reuses* its own verified
experience: a repeated `ManufacturingRequest` retrieves and reuses the prior `ProductionPlan` + `Verdict`
deterministically, writing no duplicate episode — the first measurable rung of compounding. Purely additive:
**RM1 is byte-unchanged and contracts stay frozen at `0.2.0`.** Runtime `0.2.0 → 0.3.0`.
See `docs/milestones/RM2-completion-report.md` and `docs/ROADMAP.md`.

### Added (RM2 — five milestones)
- **M1** — `experience/episode_store_reader.py`: read RM1's episode JSONL back into verified
  `ManufacturingEpisode` objects (explicit per-type reconstruction + content_hash integrity).
- **M2** — `experience/episode_index.py`: deterministic composite-key index
  (`(design_input_identity_hash, capability_model_version)`) with exact-match `lookup`.
- **M3** — `orchestration/reuse_runner.py` (new file): `run_with_reuse` — intake → lookup → reuse (with a
  reproducibility guard that re-derives the plan and asserts the content_hash) or delegate to RM1's `run`;
  `ReuseRunResult`, `ExperienceConsistencyError`. RM1's `runner.py` untouched.
- **M4** — `tests/boundary/test_experience_boundaries.py` + CI gates: Law-6 non-goals (no store/retention
  engine), import discipline, contract-freeze (`VERSION == 0.2.0`), and an RM1 zero-diff gate vs `rm1-complete`.
- **M5** — this governance close-out.
- **Verified:** 50 tests pass (RM1's 31 unchanged + 19 RM2); ruff clean; contracts frozen; bindings drift-stable.
- Planning record: `specs/milestones/RM2-experience-reuse.md` (spec), `docs/design/RM2-engineering-package.md`
  (architecture), `docs/design/RM2-implementation-plan.md` (plan); decision in `docs/adr/0006-rm2-acceptance.md`.

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
