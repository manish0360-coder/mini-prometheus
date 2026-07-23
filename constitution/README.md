# constitution/ — FROZEN theory

The **governing Constitution is `HANDBOOK_v1.1.md`** (transcribed here verbatim), supported by
`ARCHITECTURE_DECISION.md` (the ratified boundary review). By the Handbook's own terms it is the single
source of truth at the top of the authority hierarchy (P.1–P.2) and changes only by a ratified
Constitution Amendment Proposal (CAP, Law 23), ratified by the project owner (Law 22).

The seven topic files (Ontology, Computational Objects, Operators, Runtime Architecture, Repository
Responsibilities, Promotion Workflow, Responsibility Matrix) are **cited extractions** from the Handbook
for navigation. On any discrepancy, the Handbook governs. They are amendment-gated, not routine edits.

That the Handbook governs — over the earlier "Mini Prometheus" charter summary — was established on
evidence, not self-declaration, in `docs/governance/constitutional-evolution-report.md` and ratified via
`docs/governance/CAP-0001-adopt-handbook-and-conform-repository.md`.

## Version

`VERSION` = **1.1.0**, adopted from Handbook v1.1 (CAP-0001, ADR-0004). Every amendment bumps the version
and is recorded by an ADR citing the CAP. Semantics: MAJOR = a frozen clause changed/removed; MINOR =
clarified/added without invalidating implementations; PATCH = editorial/transcription fix. Downstream
artifacts (`contracts/VERSION`, releases) reference the constitution version they were derived under.
