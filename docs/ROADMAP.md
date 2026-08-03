# Mini Prometheus — Runtime Roadmap

Tracks the **runtime-implementation milestones** (RM track), distinct from the directory-creation
milestones (M1–M3) in `docs/architecture/repository-architecture.md` §7. Each RM is one logically
complete engineering milestone under the frozen workflow (Specification → Contract → Implementation →
Testing → Verification → Commit → Review). Governed by the frozen Constitution (`constitution/`,
v1.1.0); all ownership traces to Handbook §2.4.

> **Reprioritization note (2026-08-03).** A first-principles review advanced the **compounding spine**
> (Constitution §1.7) ahead of external package integration: RM3 became **Engineering Precedent
> Reasoning** and RM4 became **Engineering Judgment**. The real-Velith and real-Noetica integrations
> (formerly labelled RM3/RM4) moved out to **RM5/RM6**. This table reflects what was built.

| Milestone | Capability | Status | Tag | Notes |
|---|---|---|---|---|
| **RM1** | `plan → verify → log` — engineer `ManufacturingRequest` → verified `ProductionPlan` + `ManufacturingEpisode` | ✅ **Complete** (2026-07-23) | `rm1-complete` | runtime `0.2.0`; deterministic planner + manufacturability oracle |
| **RM2** | **Experience read-back & idempotent reuse** — reuse a prior verified plan+verdict for a repeated request (compounding, rung 1) | ✅ **Complete** (2026-07-25) | `rm2-complete` | runtime `0.3.0`; additive read side; RM1 byte-unchanged |
| **RM1 correction** | `ManufacturingEpisode` embeds the full `DesignInput` (complete engineering memory) | ✅ Ratified | — | contract suite `0.2.0 → 0.4.0`; backward-compatible; enables RM3/RM4 |
| **RM3** | **Engineering Precedent Reasoning** — surface relevant prior verified cases and derive a supporting/cautionary/none signal (compounding, rung 2) | ✅ **Complete** (2026-08-03) | in `0.4.0` | runtime `0.4.0`; additive `PrecedentReport` contracts; deterministic structural relevance (no ML); read-only |
| **RM4** | **Engineering Judgment** — situated advisory critique of a proposed plan against its whole case; first consumer of the internal `EngineeringSituation` primitive (compounding, rung 3) | ✅ **Complete** (2026-08-03) | pending `rm4-complete` | runtime `0.4.0`; additive, **no contract**; `EngineeringSituation` internal; RM1–RM3 byte-unchanged |
| **RM5** | Wire the **real pinned Velith package** behind `integrations/velith` (verified-design path) | ⏳ Planned | — | Hard prerequisite: Velith publishes a consumable release (CAP-0001 Field 8) |
| **RM6** | Consume real **Noetica** platform mechanisms (substrate/provenance/Verifier) via pinned package; evaluate `EngineeringSituation` extraction per the RM4 §12 gate | ⏳ Planned | — | Noetica is grown by extraction (N.3); publish availability gates this |
| **RM7+** | Deepen manufacturing content (scheduling, tolerance/precedence models, model-based planner seam); held-out compounding experiment (D7/D8) | ⏳ Future | — | No premature abstraction |

## RM3 — what shipped (2026-08-03)

- Owned manufacturing **content**: a deterministic, read-only **precedent reasoning** capability — a versioned
  relevance model, an extraction-seed retriever (mechanism), and a reasoner (domain identity) that assembles a
  `PrecedentReport` with a supporting/cautionary/none signal from verified prior verdicts.
- **Compounding rung 2:** generalizes RM2's exact reuse to *analogous* cases (`D = 0` ⇔ the RM2 exact case).
- Additive `PrecedentReport`/`PrecedentEntry`/`PrecedentSignal` contracts (in the `0.4.0` suite). Deterministic
  structural relevance only — no ML/embeddings/vector DB, no store/retention engine (Law 6), read-only.
- Architectural debt recorded (`docs/governance/RM3-architectural-debt.md`): the O(N) retriever is an intentional
  MP-local extraction seed; scalable indexed retrieval is future Noetica extraction.
- Full record: `docs/milestones/RM3-completion-report.md`, ADR-0007.

## RM4 — what shipped (2026-08-03)

- Owned manufacturing **content**: **Engineering Judgment** — the advisory, situated critique of a proposed plan
  against its whole case. First implementation: **Engineering Critique**. Package `judgment/` + composition
  `orchestration/judgment_runner.py`.
- **Compounding rung 3:** the first capability that reasons over the *whole case* (design + plan + verdict +
  precedent) rather than a single artifact. Situated value proven: a `MANUFACTURABLE` plan that resembles a
  `NOT_MANUFACTURABLE` precedent yields a **CAUTIONARY** critique.
- First real consumer of the internal **`EngineeringSituation`** primitive (kept strictly internal — no contract,
  no persistence, no external identity). **Primitive-revelation record:** load-bearing constituents observed to
  be `{design_input, plan, verdict, precedent_report}`.
- Purely additive — RM1/RM2/RM3 byte-unchanged; **no contract** (suite frozen `0.4.0`); no planning, verification,
  retrieval, persistence, ML, or external identity.
- Full record: `docs/milestones/RM4-completion-report.md`, ADR-0008, spec `specs/milestones/RM4-engineering-judgment.md`,
  engineering package `docs/design/RM4-engineering-package.md`.

## Standing prerequisite for RM5/RM6

RM1–RM4 deliberately depend on the Velith/Noetica **contracts**, not their published **packages** (mirrors
Velith D16.3). **RM5** cannot leave Specification until **Velith publishes a pinned, consumable package**;
**RM6** likewise for **Noetica** (grown by extraction, N.3). These external gates are independent of RM1–RM4.

## Governance

Milestone acceptance is recorded by an ADR and reflected here + in `CHANGELOG.md`. Constitutional or
ownership changes require a CAP (Law 22/23) — not a routine roadmap edit.
