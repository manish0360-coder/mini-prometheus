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
>
> **Reprioritization note (2026-09-15).** Real-Velith integration (then RM5) was **externally blocked**
> — Velith is `m8-complete`, version `0.0.0`, with no consumable release and no `EngineeringTask`/
> `EngineeringResult` API (manufacturing is its decade-scale destination). RM5 was reprioritized to the
> fully-unblocked **Compounding Validation Experiment** (the held-out compounding measurement formerly
> parked at RM7+). Real Velith moved to **RM6**, real Noetica to **RM7**. See ADR-0009.

| Milestone | Capability | Status | Tag | Notes |
|---|---|---|---|---|
| **RM1** | `plan → verify → log` — engineer `ManufacturingRequest` → verified `ProductionPlan` + `ManufacturingEpisode` | ✅ **Complete** (2026-07-23) | `rm1-complete` | runtime `0.2.0`; deterministic planner + manufacturability oracle |
| **RM2** | **Experience read-back & idempotent reuse** — reuse a prior verified plan+verdict for a repeated request (compounding, rung 1) | ✅ **Complete** (2026-07-25) | `rm2-complete` | runtime `0.3.0`; additive read side; RM1 byte-unchanged |
| **RM1 correction** | `ManufacturingEpisode` embeds the full `DesignInput` (complete engineering memory) | ✅ Ratified | — | contract suite `0.2.0 → 0.4.0`; backward-compatible; enables RM3/RM4 |
| **RM3** | **Engineering Precedent Reasoning** — surface relevant prior verified cases and derive a supporting/cautionary/none signal (compounding, rung 2) | ✅ **Complete** (2026-08-03) | in `0.4.0` | runtime `0.4.0`; additive `PrecedentReport` contracts; deterministic structural relevance (no ML); read-only |
| **RM4** | **Engineering Judgment** — situated advisory critique of a proposed plan against its whole case; first consumer of the internal `EngineeringSituation` primitive (compounding, rung 3) | ✅ **Complete** (2026-08-03) | pending `rm4-complete` | runtime `0.4.0`; additive, **no contract**; `EngineeringSituation` internal; RM1–RM3 byte-unchanged |
| **RM5** | **Compounding Validation Experiment** — deterministic, read-only measurement of whether accumulated verified experience improves RM4 judgment vs the RM1 oracle on held-out analogous cases within one fixed regime R* | ✅ **Complete** (2026-09-15) | `rm5-complete` | runtime `0.5.0`; measurement milestone, **no contract**; leaf `experiment/` package; RM1–RM4 byte-unchanged |
| **RM6** | Wire the **real pinned Velith package** behind `integrations/velith` (verified-design path) | ⏳ Planned | — | Hard prerequisite: Velith publishes a consumable release (CAP-0001 Field 8) |
| **RM7** | Consume real **Noetica** platform mechanisms (substrate/provenance/Verifier) via pinned package; evaluate `EngineeringSituation` extraction per the RM4 §12 gate | ⏳ Planned | — | Noetica is grown by extraction (N.3); publish availability gates this |
| **RM8** | **Engineering Constraint Reasoning (ECR)** — the manufacturability oracle enforces declared operation precedence and tolerance feasibility (opt-in `constrained_model()`, CLI `--capability-model constrained`) | ✅ **Complete** (2026-09-26) | `rm8-complete` | runtime `0.6.0`; **no contract** (suite `0.4.0`); default model byte-identical to `rm5-complete` (behavioral golden); ADR-0010; the current manufacturing baseline |
| **RM9** | **Resource Availability** — declare known machines unavailable for a planning snapshot; the planner reroutes to an available capable machine or the oracle reports `RESOURCE_UNAVAILABLE` (CLI `--unavailable-resource ID`) | ✅ **Complete** (2026-09-27) | `rm9-complete` | runtime `0.7.0`; **no contract** (suite `0.4.0`); RM8 golden unchanged; RM2 unchanged; ADR-0011 |
| **RM10** | **Declared Operation Times and Single-Job Timeline** — engineer-declared `duration_min` per operation (integer minutes) → a serialized job timeline and lead time; missing prerequisites reported, nothing invented. **Not a production scheduler.** | ✅ **Complete** (2026-09-27) | `rm10-complete` | runtime `0.8.0`; **no contract** (suite `0.4.0`); RM8 + RM10 goldens pass; RM2 unchanged; ADR-0012 |
| **RM11** | **Multi-Job Deterministic Scheduling** — several verified, timed jobs sharing machines → one deterministic, independently checked schedule (`earliest_start_v1`, `NOT_OPTIMIZED`) → makespan with a lower-bound certificate; all-or-nothing refusals; pure/read-only; dedicated CLI | ✅ **Complete** (2026-09-27) | pending `rm11-complete` | runtime `0.9.0`; **no contract** (suite `0.4.0`, schedule internal); RM1–RM10 byte-unchanged; ADR-0013 |
| **RM12+** | A measured comparison of scheduling rules against the RM11 lower bound (only if the evidence justifies it); then setup, calendars, capacity; model-based planner seam; revisit the RM5 caveat on organic data | ⏳ Future | — | No premature abstraction |

## RM11 — what shipped (2026-09-27)

- Owned manufacturing **content**: a verified **multi-job scheduling substrate**. Mini Prometheus plans and verifies
  every job under one capability model (unchanged RM1–RM10), refuses the whole set if any job is not MANUFACTURABLE,
  has an unassigned operation or lacks a valid RM10 timeline, and otherwise schedules all operations on their RM9
  machines with the deterministic baseline `earliest_start_v1` (ties by `request_id`, then `step_index`). A one-job
  set reproduces the RM10 timeline exactly.
- An independent checker (it never imports the generator) proves every schedule before it is returned: every
  operation exactly once, fixed machines, exact durations and arithmetic, step order, per-machine no-overlap,
  canonical order, completions, makespan, lower bound, gap, metadata, identity and digest.
- **Lower-bound certificate:** `LB = max(longest job, busiest machine)`; makespan = LB → provably optimal under the
  RM11 model; otherwise only the gap is stated. `schedule_input_identity` (the problem) is separate from
  `schedule_digest` (the artifact); both are stable across input order, hash seeds and the clock.
- Internal artifact only (contracts stay `0.4.0`); pure and read-only; no solver, dependency, persistence,
  execution or dispatch. Frozen model assumptions are recorded on every schedule.
- Full record: `docs/milestones/RM11-completion-report.md`, ADR-0013, spec `specs/milestones/RM11-multi-job-schedule.md`.

## RM10 — what shipped (2026-09-27)

- Owned manufacturing **content**: an engineer may declare, per operation, `params.duration_min` — the total
  manufacturing time of that operation for the request, in integer minutes ≥ 1. With every duration valid and every
  step assigned, the planner derives a serialized single-job timeline (start/end per step, lead time on the final
  step); otherwise it writes no timeline value at all and reports the missing prerequisites. The verifier rejects an
  inconsistent carried timeline (`PLAN_MALFORMED`, `PLAN_INVALID`). The CLI prints the lead time.
- Requests without durations are byte-identical to RM9 (RM8 golden + a new golden generated from `rm9-complete`).
- No contract change, no CI change, no solver, no multi-job logic, no invented times. **Not a production scheduler.**
- Full record: `docs/milestones/RM10-completion-report.md`, ADR-0012, spec `specs/milestones/RM10-single-job-timeline.md`.

## RM9 — what shipped (2026-09-27)

- Owned manufacturing **content**: **Resource Availability** — known resources can be declared unavailable for one
  planning snapshot (`with_unavailable_resources()`, unknown ids rejected before planning). The planner uses only
  available capable machines, rerouting to an alternative when one exists; otherwise the oracle reports
  `RESOURCE_UNAVAILABLE` (`NOT_MANUFACTURABLE`) and names the down machines. A machine absent from the model remains
  `CAPABILITY_MISSING`. Stored plans assigned to a machine that is now down are flagged as stale.
- Plan identity changes only when availability materially affects the request; irrelevant outages leave plan and
  verdict byte-identical. RM2 is unchanged: its re-derivation guard fails closed when availability changes the plan.
- No contract change; `Verifier` signature unchanged; no CI change (the four files stay under the RM8 behavioral gate,
  which still passes). No scheduling, optimization or ML; no availability state held by Mini Prometheus.
- Full record: `docs/milestones/RM9-completion-report.md`, ADR-0011, spec `specs/milestones/RM9-resource-availability.md`.

## RM8 — what shipped (2026-09-26)

- Owned manufacturing **content**: **Engineering Constraint Reasoning** — two deterministic oracle checks driven only by
  the capability model's declarative constraint data. **Declared precedence:** a declared "A before B" pair violated
  in the routing → `PRECEDENCE_VIOLATION`, `PLAN_INVALID`. **Tolerance feasibility:** a requested tolerance strictly
  tighter than the assigned process capability's minimum → `TOLERANCE_UNSUPPORTED`, `NOT_MANUFACTURABLE`.
- Opt-in through `constrained_model()` (capability model `1.1.0`, verifier `1.1.0`) and the existing CLI
  `--capability-model constrained`. `default_model()` behavior is byte-identical to `rm5-complete`, pinned by a
  behavioral golden generated once from `rm5-complete`. The legacy default CLI does not read `tolerances`
  (documented limitation).
- No contract/schema/enum change; `Verifier` signature unchanged; no dependency; no Velith/Noetica change.
- CI: the RM1/RM2 byte-freeze is replaced by the behavioral gate for exactly the four RM8 files (ratified, ADR-0010).
- Full record: `docs/milestones/RM8-completion-report.md`, ADR-0010, spec `specs/milestones/RM8-engineering-constraint-reasoning.md`.

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

## RM5 — what shipped (2026-09-15)

- A deterministic, read-only **Compounding Validation Experiment** (leaf package `experiment/`): does accumulated
  verified experience measurably improve RM4 judgment against the RM1 oracle on strictly held-out,
  analogous-but-non-identical cases within one fixed regime `R* = default_model()` minus `lathe01`? Three arms
  (Cold Start / No Precedent / Full System); primary contrast **Arm 3 − Arm 2**; validity control **Arm 1 == Arm 2**.
- **Result (oracle-internal world only):** a **positive finite-corpus precedent effect** — marginal **+42/121
  (+0.3471)**, concentrated on MANUFACTURABLE (42/45; NOT-class marginal 0/76, so no oracle-label leakage). Controls
  passed (Arm 1 == Arm 2 121/121; duplicates 0; deterministic checkpoint; reproducible report hash).
- **Explicitly NOT demonstrated (valid findings):** the H2 false-alarm ceiling (3/45) and strict monotonic
  compounding (curve 0 → 0.3223 → 0.3554 → 0.3471, final step decreases). Independent review (Gemini):
  `SCIENTIFICALLY SOUND AS A LIMITED INTERNAL VALIDATION`. Measurement milestone — **no contract** (suite frozen
  `0.4.0`); RM1–RM4 byte-unchanged.
- Full record: `docs/milestones/RM5-completion-report.md`, ADR-0009, release `docs/releases/rm5-0.5.0.md`.

## Standing prerequisite for RM6/RM7

RM1–RM5 deliberately depend on the Velith/Noetica **contracts**, not their published **packages** (mirrors
Velith D16.3). **RM6** cannot leave Specification until **Velith publishes a pinned, consumable package**;
**RM7** likewise for **Noetica** (grown by extraction, N.3). These external gates are independent of RM1–RM5.

## Governance

Milestone acceptance is recorded by an ADR and reflected here + in `CHANGELOG.md`. Constitutional or
ownership changes require a CAP (Law 22/23) — not a routine roadmap edit.
