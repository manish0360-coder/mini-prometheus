# Mini Prometheus — Runtime Roadmap

Tracks the **runtime-implementation milestones** (RM track), distinct from the directory-creation
milestones (M1–M3) in `docs/architecture/repository-architecture.md` §7. Each RM is one logically
complete engineering milestone under the frozen workflow (Specification → Contract → Implementation →
Testing → Verification → Commit → Review). Governed by the frozen Constitution (`constitution/`,
v1.1.0); all ownership traces to Handbook §2.4.

| Milestone | Capability | Status | Tag | Notes |
|---|---|---|---|---|
| **RM1** | `plan → verify → log` — engineer `ManufacturingRequest` → verified `ProductionPlan` + `ManufacturingEpisode` | ✅ **Complete** (2026-07-23) | `rm1-complete` | runtime `0.2.0`; deterministic planner + manufacturability oracle; fixtures/contract-only upstreams |
| **RM2** | Wire the **real pinned Velith package** behind `integrations/velith` (verified-design path) | ⏭ Planned (next) | — | Hard prerequisite: Velith publishes a consumable release (CAP-0001 Field 8). Velith is at M0–M1. |
| **RM3** | Consume real **Noetica** platform mechanisms (substrate/provenance/Verifier) via pinned package | ⏳ Planned | — | Replaces RM1's contract-only stubs with the published Noetica contracts |
| **RM4+** | Deepen manufacturing content (scheduling across resources, tolerance/precedence models, model-based planner seam), emit the Experience Flow to Noetica's lifecycle framework | ⏳ Future | — | Model-based planner relocates determinism to the oracle (spec §9); no premature abstraction |

## RM1 — what shipped (2026-07-23)

- Owned manufacturing **content** only (Handbook §2.4): intake, deterministic planner, manufacturability
  oracle (implements the Noetica `Verifier` protocol, Law 15), episode emission.
- Tangible artifact: a content-hashed, provenance-complete `ProductionPlan` for a machined-part request.
- Consumes Velith/Noetica by **contract** (fixtures), never re-implements them; never imports MiniFlyWire.
- Verified by 31 tests; ruff clean; bindings regeneration-stable; real CI gate.
- Full record: `docs/milestones/RM1-completion-report.md`, ADR-0005, contract package `contracts/RM1-contract-package.md`.

## Standing prerequisite for RM2/RM3

RM1 deliberately depends on the Velith/Noetica **contracts**, not their published **packages** (mirrors
Velith D16.3). RM2 cannot leave Specification until **Velith publishes a pinned, consumable package**;
RM3 likewise for **Noetica**. This gate is independent of RM1 and is tracked here.

## Governance

Milestone acceptance is recorded by an ADR and reflected here + in `CHANGELOG.md`. Constitutional or
ownership changes require a CAP (Law 22/23) — not a routine roadmap edit.
