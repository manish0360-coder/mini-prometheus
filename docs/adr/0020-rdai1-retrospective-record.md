# ADR 0020 — RDAI-1 (Real STEP Design-Artifact Intake) retrospective record

- **Status:** Accepted as a **retrospective record**. Recorded 2026-11-06 under Stage 0 record reconciliation (ADR-0021).
- **Date of the work:** 2026-10-17 (C1) and 2026-10-23 (C2). **Date of this record:** 2026-11-06.
- **Deciders:** Project owner (Stage 0 ruling Q3: record the actual history and do not claim independent verification);
  Chief Systems Engineer (record).
- **Constitution in force:** v1.1.0
- **Related:** ADR-0005 (RM1: opaque `DesignArtifactRef`), `specs/milestones/RM1-plan-verify-log.md` §3 (geometry out
  of scope), `docs/research/verification-contract-gap-audit.md`, `docs/research/capability-to-evidence-assessment.md`

## Context

RM1 froze an opaque STEP seam (`ManufacturingRequest.step_artifact_ref` → `DesignArtifactRef`) with no code that read a
real file. RDAI-1 grounded that seam in real bytes on disk. The work was committed as `abbc1b8` and `ab8cc44`. Neither
commit has a message body. The package docstring cites an "RDAI-1 spec §A/§D" that is **not in the repository**, and
until this record no ADR, roadmap or changelog entry described the work.

## What was built (from source and Git)

1. **C1, `abbc1b8` (2026-10-17):**
   - New leaf package `src/mini_prometheus/artifact_intake/` with `step_intake.ingest(path) -> StepArtifactRef`.
   - It reads raw bytes and fails closed (`UnsupportedArtifactError`) on unreadable, empty, non-UTF-8 or
     control-character input, or on a malformed ISO-10303-21 container. A container is well formed when its six
     markers appear in strict order.
   - Identity: `content_hash = sha256(raw bytes)`, `id = uuid5(NS_MP, content_hash)`, `media_type = "model/step"`.
   - No geometry, entity grammar, schema, topology or manufacturability is examined.
   - Seven fixtures under `tests/fixtures/step/`, including the 196-byte synthetic `valid_minimal.step`.
   - `tests/unit/test_step_intake.py`: 6 test functions, several of them parametrised.
2. **C2, `ab8cc44` (2026-10-23):** `tests/integration/test_rdai_step_traceability.py` (4 tests). It shows that:
   - the STEP byte hash survives verbatim into the serialised episode;
   - the hash is committed in both the design identity and the episode identity;
   - a request without an artifact omits the reference;
   - malformed STEP fails before the pipeline.
3. **No contract, schema, CI or dependency change.** The suite stays at `0.4.0`. `StepArtifactRef` is an existing RM1
   contract type.

## Verification actually performed

- The tests above pass in the full gate. Stage 0 audit, 2026-11-06, Docker verifier, Python 3.11.18: 696 passed;
  mypy `src` clean; import-linter 5 kept.
- **No independent review is recorded for RDAI-1.** Its only real input is a synthetic file, so it has **not** been
  validated against a real engineering part.
- Not covered by any import-linter contract: `artifact_intake` is not listed in the forbidden-import contracts.
  It is a leaf by convention and by its docstring, not by enforcement.
- Known limitation: `ingest` reads the whole file into memory with no size cap.

## Decision

Record RDAI-1 as implemented and tested **byte-identity intake and traceability only**. It does not interpret geometry,
which belongs to Velith (Handbook §2.3). It is not a real-evidence milestone.

## Consequences

- The record now matches the code (Law 18).
- The missing RDAI-1 specification is not reconstructed here.
- A size cap and an import-linter leaf contract are candidate hardening items for the next change that touches intake.
  Neither is authorised by this record.
