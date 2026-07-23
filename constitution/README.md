# constitution/ — FROZEN theory

These documents are the frozen inputs to Mini Prometheus (Ontology, Computational Objects,
Operators, Runtime Architecture, Repository Responsibilities, Promotion Workflow, Responsibility
Matrix). They are amendment-gated: edits require a proven contradiction and Architecture Board
sign-off, never a routine PR. See `docs/architecture/repository-architecture.md`.

## Version

The frozen theory is versioned in `VERSION` for long-term traceability (baseline **1.0.0**). This is
additive metadata and does not alter any frozen document's content. Every amendment bumps the version
and is recorded by an ADR that cites the contradiction and the affected clause. Semantics: MAJOR = a
frozen clause changed/removed; MINOR = clarified/added without invalidating implementations; PATCH =
editorial/transcription fix. Downstream artifacts (`contracts/VERSION`, releases) reference the
constitution version they were derived under. See §15 of the repository-architecture document.
