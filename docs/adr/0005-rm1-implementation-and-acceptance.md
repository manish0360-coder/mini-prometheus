# ADR 0005 — RM1 implementation decisions and acceptance

- **Status:** Accepted
- **Date:** 2026-07-23
- **Deciders:** Project owner (acceptance); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM1-plan-verify-log.md`, `contracts/RM1-contract-package.md`, ADR-0003 (order), ADR-0004 (re-scope), `docs/milestones/RM1-completion-report.md`

## Context

RM1 (`plan → verify → log`) was implemented strictly against the frozen spec and contracts. Two
implementation-time decisions and one defect fix warrant a durable record, and the milestone is accepted.

## Decisions

1. **Deterministic ids end-to-end.** `design_input_id` and `task_id` are derived `uuid5(NS_MP, hash(identity))`,
   like the contract-mandated `plan_id`/`episode_id`. The contract only *required* determinism for
   plan/episode ids, but reproducibility (spec §5.5) requires it upstream too, since refs carry ids into
   downstream hashes. Output remains valid UUID form; **no schema/contract change**. Stricter, compatible.

2. **Defect fixed during implementation (contract was right, code was wrong).** The first cut hashed the
   embedded plan into the episode identity, leaking the plan's volatile `produced_at` and breaking
   determinism. Corrected to use `plan.content_hash` per contract package §3.6. No frozen artifact changed.

3. **Python 3.11 `StrEnum` bindings.** The generated bindings use stdlib `StrEnum` (matches
   `requires-python >= 3.11`). A guarded test shim (`tests/conftest.py`) lets the suite also run on 3.10
   runners; it is a no-op on 3.11+. CI pins 3.11.

4. **Runtime validation at boundaries.** `jsonschema` validates the `ManufacturingRequest` on intake and
   the `ManufacturingEpisode` before emission (verification-first). Added as a runtime dependency.

## Acceptance

RM1 is **accepted and frozen**: delivered exactly as specified; 31 tests pass; ruff clean; bindings
drift-stable; ownership boundaries enforced (Law 4/6/9/15). Runtime version `0.1.0 → 0.2.0`; tagged
`rm1-complete`. Recorded in `CHANGELOG.md`, `docs/ROADMAP.md`, and `docs/milestones/RM1-completion-report.md`.

## Consequences

- RM1 modules, spec, and contracts are frozen; change only on a discovered critical defect.
- RM2 (real pinned Velith package) and RM3 (real Noetica package) are gated on those upstreams publishing
  consumable releases (CAP-0001 Field 8) — independent of RM1.

## Alternatives rejected

- Random `design_input_id`/`task_id` (breaks reproducibility from a fixed request). 
- Changing the contract to add episode `plan.content_hash` explicitly (unnecessary — §3.6 already specifies it).
- Lowering the binding target below 3.11 (contradicts `requires-python`).
