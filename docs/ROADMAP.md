# Mini Prometheus — Runtime Roadmap

Tracks the **runtime-implementation milestones** (RM track), distinct from the directory-creation
milestones (M1–M3) in `docs/architecture/repository-architecture.md` §7. Each RM is one logically
complete engineering milestone under the frozen workflow (Specification → Contract → Implementation →
Testing → Verification → Commit → Review). Governed by the frozen Constitution (`constitution/`,
v1.1.0); all ownership traces to Handbook §2.4.

| Milestone | Capability | Status | Tag | Notes |
|---|---|---|---|---|
| **RM1** | `plan → verify → log` — engineer `ManufacturingRequest` → verified `ProductionPlan` + `ManufacturingEpisode` | ✅ **Complete** (2026-07-23) | `rm1-complete` | runtime `0.2.0`; deterministic planner + manufacturability oracle; fixtures/contract-only upstreams |
| **RM2** | **Experience read-back & idempotent reuse** — reuse a prior verified `ProductionPlan` + `Verdict` for a repeated request (compounding, rung 1) | ✅ **Complete** (2026-07-25) | `rm2-complete` | runtime `0.3.0`; additive read side; RM1 byte-unchanged; contracts frozen `0.2.0`. *(First-principles review reprioritized this over real-Velith — compounding is the Constitution's spine and has no external gate.)* |
| **RM3** | Wire the **real pinned Velith package** behind `integrations/velith` (verified-design path) | ⏭ Planned (next) | — | Hard prerequisite: Velith publishes a consumable release (CAP-0001 Field 8). Velith is at M0–M1. |
| **RM4** | Consume real **Noetica** platform mechanisms (substrate/provenance/Verifier) via pinned package | ⏳ Planned | — | Replaces RM1's contract-only stubs; Noetica is grown by extraction (N.3), so publish availability gates this. |
| **RM5+** | Deepen manufacturing content (scheduling across resources, tolerance/precedence models, model-based planner seam); extract the experience read side up into Noetica's lifecycle framework (Law 8) | ⏳ Future | — | Model-based planner relocates determinism to the oracle (spec §9); no premature abstraction |

## RM1 — what shipped (2026-07-23)

- Owned manufacturing **content** only (Handbook §2.4): intake, deterministic planner, manufacturability
  oracle (implements the Noetica `Verifier` protocol, Law 15), episode emission.
- Tangible artifact: a content-hashed, provenance-complete `ProductionPlan` for a machined-part request.
- Consumes Velith/Noetica by **contract** (fixtures), never re-implements them; never imports MiniFlyWire.
- Verified by 31 tests; ruff clean; bindings regeneration-stable; real CI gate.
- Full record: `docs/milestones/RM1-completion-report.md`, ADR-0005, contract package `contracts/RM1-contract-package.md`.

## RM2 — what shipped (2026-07-25)

- Owned manufacturing **content** only: the read side of the Experience Flow — an episode reader, a
  deterministic composite-key index, and an additive `run_with_reuse` composition with a reproducibility guard.
- Delivers **compounding rung 1**: a repeated request reuses prior verified experience deterministically and
  writes no duplicate episode.
- Purely additive — **RM1 is byte-unchanged** (CI zero-diff gate vs `rm1-complete`); **no new contracts**
  (`contracts/VERSION` frozen at `0.2.0`); no Noetica store/retention engine (Law 6 — deferred).
- Verified by 19 RM2 tests (50 total); ruff clean; bindings drift-stable.
- Full record: `docs/milestones/RM2-completion-report.md`, ADR-0006, spec `specs/milestones/RM2-experience-reuse.md`,
  engineering package `docs/design/RM2-engineering-package.md`, implementation plan `docs/design/RM2-implementation-plan.md`.

## Standing prerequisite for RM3/RM4

RM1 and RM2 deliberately depend on the Velith/Noetica **contracts**, not their published **packages**
(mirrors Velith D16.3), and had no external gate. **RM3** cannot leave Specification until **Velith
publishes a pinned, consumable package**; **RM4** likewise for **Noetica** (which is grown by extraction,
N.3). These gates are independent of RM1/RM2 and are tracked here.

## Governance

Milestone acceptance is recorded by an ADR and reflected here + in `CHANGELOG.md`. Constitutional or
ownership changes require a CAP (Law 22/23) — not a routine roadmap edit.
