# docs/adr/

Architecture Decision Records. **Append-only**; superseded, never deleted. Format: `NNNN-title.md`.
See `docs/architecture/repository-architecture.md` for the full rationale and constitutional trace.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-adopt-repository-architecture.md) | Adopt the repository architecture | Accepted |
| [0002](0002-architecture-refinement-external-review.md) | Architecture refinement pass (external review) | Accepted |
| [0003](0003-runtime-implementation-order.md) | Runtime implementation order: Situation State first | Accepted (RM1 scope superseded by 0004) |
| [0004](0004-conform-repository-to-handbook.md) | Conform repository to HANDBOOK_v1.1 (ratified CAP-0001) | Accepted |
| [0005](0005-rm1-implementation-and-acceptance.md) | RM1 implementation decisions and acceptance | Accepted |
| [0006](0006-rm2-acceptance.md) | RM2 implementation and acceptance | Accepted |
| [0007](0007-rm3-acceptance.md) | RM3 (Engineering Precedent Reasoning) implementation and acceptance | Accepted |
| [0008](0008-rm4-acceptance.md) | RM4 (Engineering Judgment) implementation and acceptance | Accepted |
| [0009](0009-rm5-acceptance.md) | RM5 (Compounding Validation Experiment) implementation and acceptance | Accepted |
| [0010](0010-rm8-acceptance.md) | RM8 (Engineering Constraint Reasoning) implementation and acceptance; RM1/RM2 byte-gate evolution for four files | Accepted |
| [0011](0011-rm9-acceptance.md) | RM9 (Resource Availability) implementation and acceptance | Accepted |
| [0012](0012-rm10-acceptance.md) | RM10 (Declared Operation Times and Single-Job Timeline) implementation and acceptance | Accepted |
| [0013](0013-rm11-acceptance.md) | RM11 (Multi-Job Deterministic Scheduling) implementation and acceptance | Accepted |
| [0014](0014-packaging-integrity.md) | Packaging integrity: the installed wheel carries the contracts tree (maintenance) | Accepted |
| [0015](0015-rm12-acceptance.md) | RM12 (Time-Aware Resource Downtime Scheduling) implementation and acceptance | Accepted |
| [0016](0016-rm13-acceptance.md) | RM13 (Opt-In Most-Work-Remaining Tie-Break Rule) implementation and acceptance | Accepted |
| [0017](0017-rm14-acceptance.md) | RM14 (Sequence-Dependent Resource Changeover Scheduling) implementation and acceptance | Accepted |

Governance instruments live in `docs/governance/` (CAP-0001, constitutional evolution report).
Milestone reports live in `docs/milestones/`; the roadmap is `docs/ROADMAP.md`.
