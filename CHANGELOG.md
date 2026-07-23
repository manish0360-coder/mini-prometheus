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
