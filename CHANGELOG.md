# Changelog

All notable changes to Mini Prometheus are recorded here. The runtime and the contract suite
(`contracts/VERSION`) are versioned independently; both are noted below.

Format: [Keep a Changelog](https://keepachangelog.com/). Versioning: SemVer.

## [0.11.0] — 2026-09-27 — RM13 Opt-In Most-Work-Remaining Tie-Break Rule

Runtime `0.10.0 → 0.11.0`; the contract suite stays **frozen at `0.4.0`**. See
`specs/milestones/RM13-most-work-remaining-rule.md`, ADR-0016, `docs/milestones/RM13-completion-report.md`.
**Opt-in only; the default rule and every RM11/RM12 identity are unchanged.**

### Added — RM13
- Rule `earliest_start_v1_most_work_remaining` 1.0.0 (`..._downtime` under relevant downtime): exact earliest-start
  ties go to the job with the most remaining processing work (candidate + later unscheduled RM10 durations), then
  request_id, then step_index; never a later-starting candidate.
- Selection: `schedule_requests(..., rule=...)`, `schedule_job_set(..., rule=...)`, CLI `--rule`;
  `UnknownSchedulingRuleError` for anything else.
- Frozen synthetic algorithm-regression corpus `tests/fixtures/rm13_regression_corpus_01.json`
  (RM13_REGRESSION_CORPUS_01; digests pinned; optima re-derived in the tests) and pinned metrics for both rules.
- Tests 1–16, true-source mutants, and an installed-wheel `--rule` check.

### Unchanged
- Default rule `earliest_start_v1`; all RM11/RM12 goldens and identities; RM12 downtime semantics; RM9 assignments;
  checker; lower bounds; contracts; CI; dependencies. No Giffler–Thompson, solver, tuning or new benchmark.

## [0.10.0] — 2026-09-27 — RM12 Time-Aware Resource Downtime Scheduling

Runtime `0.9.1 → 0.10.0`; the contract suite stays **frozen at `0.4.0`**. See
`specs/milestones/RM12-resource-downtime.md`, ADR-0015, `docs/milestones/RM12-completion-report.md`.
**Explicit finite downtime on already-assigned machines; operations wait, never rerouted; not an optimizer.**

### Added — RM12
- `manufacturing_scheduling/downtime.py`: validation (`InvalidDowntimeError` before planning: unknown machines,
  zero-length, negative, non-integer, unbounded) and canonicalization (sorted; overlapping and touching merged) of
  per-machine `[start_min, end_min)` downtime; relevance filter (machines the job set uses).
- Rule `earliest_start_v1_downtime` (only under relevant downtime): append-only earliest fit around the assigned
  machine's downtime, half-open, RM11 tie-break.
- Window-aware lower bound `window_aware_lower_bound_min` (LB_RM12 = max(LB_RM11, max T_avail)); the gap is measured
  to it; the RM11 `lower_bound_min` is retained.
- Checker: independent re-derivation of relevant canonical downtime and T_avail; `DowntimeIssueCode`
  (`DOWNTIME_MISMATCH`, `DOWNTIME_CONFLICT`, `WINDOW_LOWER_BOUND_MISMATCH`).
- Identity: relevant canonical downtime in `schedule_input_identity` (only when present).
- CLI `--downtime MACHINE:START:END` (repeatable); `schedule_requests(..., downtime=...)`.
- Frozen golden `tests/fixtures/rm12_rm11_baseline_golden.json` (generated once from `rm11-complete` by
  `tests/rm12_rm11_baseline_probe.py`); RM12 tests A–AD; true-source mutants D1–D11; RM12 installed-CLI checks in
  `tools/verify_installed_wheel.py`.

### Unchanged
- Without relevant downtime every output is byte-identical to `rm11-complete`. Contracts; `Verifier`; RM1–RM10; RM2;
  RM11's `IssueCode` set and tests; CI configuration; dependencies. No calendars, shifts, maintenance policies, MES,
  persistence, execution, rerouting, optimization or solver.

## [0.9.1] — 2026-09-27 — Packaging integrity (maintenance)

Runtime `0.9.0 → 0.9.1`; the contract suite stays **frozen at `0.4.0`**. See ADR-0014.

### Fixed
- The installed wheel lacked the `contracts/` tree, so the RM10 and RM11 CLIs failed from a regular installation
  (`ModuleNotFoundError: contracts`, then `NoSuchResource` for the schemas). The wheel now installs the repository
  layout — `site-packages/mini-prometheus-runtime/{src/mini_prometheus, contracts}` — plus `mini_prometheus.pth`
  (new source file `distribution/mini_prometheus.pth`), so every source-relative path resolves as in the
  repository. No source, contract or CI file changed; editable installs are unchanged.

### Added
- `tools/verify_installed_wheel.py` (build, inspect, clean-venv install, RM10/RM11 CLIs from a neutral directory,
  schema rejection, digest equality with the repository source) and `tests/boundary/test_packaging_integrity.py`.
- The verifier Dockerfile copies `distribution/` before building the wheel.

### Unchanged
- All RM1–RM11 source and behavior; contracts; CI configuration; dependencies.

## [0.9.0] — 2026-09-27 — RM11 Multi-Job Deterministic Scheduling

Runtime `0.8.0 → 0.9.0`; the contract suite stays **frozen at `0.4.0`**. See
`specs/milestones/RM11-multi-job-schedule.md`, ADR-0013, `docs/milestones/RM11-completion-report.md`.
**RM11 is a verified multi-job scheduling substrate with a lower-bound certificate — not an optimizer, not a
dispatcher.**

### Added — RM11
- New content package `manufacturing_scheduling`: the internal `MultiJobSchedule` model with the frozen RM11 model
  assumptions; the baseline rule `earliest_start_v1` (earliest feasible start; ties by `request_id`, then
  `step_index`; `NOT_OPTIMIZED`); an independent checker (never imports the generator) that every schedule must
  pass before it is returned; the lower-bound certificate (`lower_bound_min`, `gap_to_lower_bound_min`,
  `PROVABLY_OPTIMAL` only when the gap is 0); `schedule_input_identity` (the problem) vs `schedule_digest` (the
  artifact); all-or-nothing refusals (`EMPTY_JOB_SET`, `DUPLICATE_REQUEST_ID`, `JOB_NOT_MANUFACTURABLE`,
  `JOB_OPERATION_UNASSIGNED`, `JOB_TIMELINE_MISSING`).
- `orchestration/schedule_runner.py`: `schedule_requests()` and the dedicated CLI
  `python -m mini_prometheus.orchestration.schedule_runner REQUEST.json ...` (`--capability-model`,
  `--unavailable-resource`).
- Import-linter: the new package joins the existing forbidden contracts; new contracts — no RM1–RM10 module imports
  scheduling, and the checker is independent of the generator and the bound calculator.
- Tests (Director list 1–20, every checker tampering class, determinism across permutations and hash seeds) and
  true-source mutation tests; declared test fixtures `tests/fixtures/rm11_jobs/`.

### Unchanged
- Contracts; the `Verifier` signature; all RM1–RM10 code (`planner.py`, `oracle.py`, `capability_model.py`,
  `runner.py`) and behavior (RM8 and RM10 goldens pass); RM2; CI configuration. No dependency, solver, ML,
  persistence, execution, dispatch, FutureScore, MiniFlyWire, Velith or Noetica change.

## [0.8.0] — 2026-09-27 — RM10 Declared Operation Times and Single-Job Timeline

Runtime `0.7.0 → 0.8.0`; the contract suite stays **frozen at `0.4.0`**. See
`specs/milestones/RM10-single-job-timeline.md`, ADR-0012, `docs/milestones/RM10-completion-report.md`.
**RM10 is a single-job deterministic timeline, not a production scheduler.**

### Added — RM10
- Engineer-declared operation time `DeclaredOperation.params.duration_min` (integer minutes ≥ 1; no float, bool,
  string or conversion; no time model).
- Planner: a serialized single-job timeline (`schedule_start_min`, `schedule_end_min` per step,
  `schedule_lead_time_min` on the final step, plus the declared `duration_min` copied) only when every operation has
  a valid duration and every step is assigned; otherwise no timeline value at all. Planning rule `1.3.0` only then.
- `planner.timeline_issues()` / `planner.lead_time_min()`; the CLI prints the lead time or the missing prerequisites.
- Oracle: an inconsistent carried timeline → `PLAN_MALFORMED`, `PLAN_INVALID`; verifier `1.3.0` only when it
  evaluates a timeline.
- Frozen golden `tests/fixtures/rm10_rm9_baseline_golden.json` (generated once from `rm9-complete`) pinning the ECR and
  availability paths for requests without durations; fixture `engineer_request_with_durations.json` (test inputs).
- Tests A–T, the golden, and mutation tests.

### Unchanged
- Requests without durations (RM8 and RM10 goldens pass); RM9's manufacturability verdict for requests that do declare
  durations; contracts; `Verifier` signature; RM2; CI configuration; no dependency, solver, ML, multi-job logic,
  FutureScore, MiniFlyWire, Velith or Noetica change.

## [0.7.0] — 2026-09-27 — RM9 Resource Availability

Runtime `0.6.0 → 0.7.0`; the contract suite stays **frozen at `0.4.0`**. See
`specs/milestones/RM9-resource-availability.md`, ADR-0011, `docs/milestones/RM9-completion-report.md`.

### Added — RM9
- `ProcessCapabilityModel.unavailable_resources` (defaulted empty) and `with_unavailable_resources()` — declare KNOWN
  resources unavailable for one planning snapshot; unknown ids raise `UnknownResourceError` before planning.
- Planner: assigns only available capable machines (reroutes to an alternative when one exists); records
  `params["unavailable_resources"]` only on steps availability materially affects; planning rule `1.2.0` only then.
- Oracle: `RESOURCE_UNAVAILABLE` (status `NOT_MANUFACTURABLE`) when every capable machine for a required operation is
  unavailable, or when a plan assigns a machine that is now unavailable; the machines are named in `Verdict.detail`.
  Verifier `1.2.0` only when availability participates.
- CLI: repeatable `--unavailable-resource ID` on the existing runner CLI.
- Tests: outcomes, plan identity (irrelevant vs relevant unavailability), versioning, validation, CLI, RM2 reuse
  guard interaction (A/B/C), and mutation tests.

### Unchanged
- Default and RM8 behavior (the RM8 behavioral golden passes unchanged); an absent machine is still
  `CAPABILITY_MISSING`; contracts; `Verifier` signature; RM2 code and reuse key; CI configuration; no dependency,
  scheduling, optimization, ML, FutureScore, MiniFlyWire, Velith or Noetica change.

## [0.6.0] — 2026-09-26 — RM8 Engineering Constraint Reasoning (declared precedence + tolerance feasibility)

Runtime `0.5.0 → 0.6.0`; the contract suite stays **frozen at `0.4.0`** (no contract, schema or enum change). See
`specs/milestones/RM8-engineering-constraint-reasoning.md`, ADR-0010, `docs/milestones/RM8-completion-report.md`.

### Added — RM8
- **Declared-precedence check** in the manufacturability oracle: a declared "A before B" pair violated by the routing
  → `PRECEDENCE_VIOLATION`, status `PLAN_INVALID`. Declared pairs only; unconstrained pairs never fail.
- **Tolerance-feasibility check:** a requested tolerance strictly tighter than the assigned tolerance-bearing
  capability's minimum → `TOLERANCE_UNSUPPORTED`, status `NOT_MANUFACTURABLE`; equal/looser feasible; absent
  tolerance or non-bearing operation → no check. All findings reported together; `PLAN_INVALID` dominates.
- **Capability model data (C1, originally local commit `ad90856`, audited and folded in):** defaulted-empty
  `capability_tolerance_mm` / `ordering_constraints`, opt-in `constrained_model()` (`1.1.0`),
  `min_tolerance_for_capability()`.
- **CLI:** `--capability-model {default,constrained}` on the existing runner CLI (default = legacy behavior).
- **Behavioral zero-diff gate:** `tests/fixtures/rm8_default_behavior_golden.json` (902 serialized plans/verdicts/
  episodes + hashes, legacy CLI, contracts digest), generated once from `rm5-complete` and frozen by digest.
- Tests: precedence, tolerance, multiple findings, versioning, determinism, CLI both modes, boundaries, mutation.

### Changed
- Verifier version `1.1.0` and planner rule version `1.1.0` are recorded only on the constrained path (tolerance
  carried); the default path still reports `1.0.0`.
- CI: the RM1/RM2 byte-freeze now excludes exactly `capability_model.py`, `oracle.py`, `planner.py` and
  `orchestration/runner.py`, which are guarded by the new RM8 behavioral zero-diff step (ratified, ADR-0010).

### Known limitation (documented, unchanged)
- The legacy default CLI does not read the request's `tolerances` and performs no tolerance or precedence reasoning.

### Unchanged
- Default-model behavior byte-identical to `rm5-complete`; `contracts/` byte-identical; `Verifier` signature; RM3/RM4
  byte gate; RM5 fixture and reproducibility freeze; no dependency, no ML, no MiniFlyWire, no Velith/Noetica change.

## [0.5.0] — 2026-09-15 — RM5 Compounding Validation Experiment (internal validation of the compounding spine)

**Governance/versioning release.** Runtime `0.4.0 → 0.5.0`; the contract suite stays **frozen at `0.4.0`** (RM5 adds
no public contract/schema). See `docs/milestones/RM5-completion-report.md`, ADR-0009, `docs/releases/rm5-0.5.0.md`.

### Added — RM5: Compounding Validation Experiment (measurement milestone)
- **New leaf package `experiment/`** (`corpus`, `partition`, `protocol`, `arms`, `runner`) — a deterministic,
  read-only harness that measures whether accumulated verified experience improves RM4 judgment against the RM1
  oracle on strictly held-out, analogous-but-non-identical cases within one fixed regime `R* = default_model()`
  minus `lathe01`. Three arms (Cold Start / No Precedent / Full System); primary causal contrast **Arm 3 − Arm 2**;
  validity control **Arm 1 == Arm 2**. Composes RM1/RM3/RM4 read-only; no reasoning re-implemented.
- **Frozen fixture** `tests/fixtures/rm5_corpus/` (checkpoint `sha256:9aec55…`); the committed corpus is the source
  of truth and is not regenerated during evaluation.
- **Reproducibility freeze** `tests/unit/test_rm5_reproducibility.py` pins the report `content_hash`
  (`sha256:2b7c48…`) and every Director-preserved headline value; boundary tests + an import-linter leaf contract
  keep `experiment/` a leaf consumer that never writes the RM2 episode store.

### Result (deterministic oracle-internal world only)
- **Positive finite-corpus precedent effect:** Arm 2 = 76/121, Arm 3 = 118/121, **marginal +42/121 (+0.3471)**,
  concentrated on MANUFACTURABLE (42/45; NOT-class marginal 0/76 — internal-verdict cancels, so no label leakage).
  Coverage 45/45 and 76/76; excluded duplicates 0.
- **NOT demonstrated (valid scientific findings, not bugs):** **H2 cautionary false-alarm ceiling = 0 → NOT MET
  (3/45)**; **strict monotonic compounding → NOT MET** (marginal curve 0 → 0.3223 → 0.3554 → 0.3471, final step
  decreases). The result is a positive learning effect, not strict monotonic compounding.
- **Independent review (Gemini):** `SCIENTIFICALLY SOUND AS A LIMITED INTERNAL VALIDATION` (circularity LOW;
  synthetic-corpus generalization MEDIUM; no mandatory correction). **Claim boundary:** no real-world manufacturing
  correctness, DFM, cost/quality, human-superiority, or deployment-readiness claims.

### Changed
- Runtime version `0.4.0 → 0.5.0` (governance only). `docs/ROADMAP.md` updated to record RM5's reprioritization from
  "wire real Velith" (externally blocked → RM6+) to the Compounding Validation Experiment. CI adds an RM3/RM4
  zero-diff gate vs `rm4-complete` and `include_external_packages = true` (import-linter 2.13 compatibility for the
  existing Law-4 external-forbidden contract; no contract semantics changed).

### Unchanged
- **RM1–RM4 byte-unchanged**; **`contracts/VERSION == 0.4.0`**; no new contract/schema; no ML/embeddings; no Noetica
  store engine (Law 6); no MiniFlyWire (Law 4).

## [0.4.0] — 2026-08-03 — RM3 Engineering Precedent Reasoning + RM4 Engineering Judgment (compounding, rungs 2 & 3)

**Consolidated release.** This cuts the accumulated, previously-unreleased work — RM3, the ratified RM1
correction, and RM4 — into one runtime `0.3.0 → 0.4.0` release. The contract suite is **frozen at `0.4.0`**
throughout (RM3 and RM4 are additive/internal; only the earlier RM1 correction touched contracts). See
`docs/ROADMAP.md`, `docs/milestones/RM3-completion-report.md`, and `docs/milestones/RM4-completion-report.md`.

### Added — RM4: Engineering Judgment (compounding rung 3; tag pending `rm4-complete`)
- **Engineering Judgment** — the deterministic, advisory capability of judging a proposed manufacturing
  solution in the full context of its case. Its first implementation is **Engineering Critique**. New package
  `judgment/` + composition entry `orchestration/judgment_runner.py`, built in six commits:
  - **C1** internal `EngineeringSituation` (the coherent engineering state of one case; strictly internal —
    no contract, no persistence, no external identity); **C2** deterministic versioned `critic_model`
    (closed finding-family taxonomy: intent-coverage, precedent-consistency, internal-verdict; summary
    assessment); **C3** `engineering_critique` (applies the model, orders findings, assembles the advisory
    critique with an in-memory reproducibility `content_hash` + provenance); **C4** `judgment_runner`
    (thin read-only composition (episode, report) → situation → critique); **C5** boundary gates + CI wiring;
    **C6** this close-out.
- **Situated value:** a plan whose own RM1 verdict is `MANUFACTURABLE` yet strongly resembles a
  `NOT_MANUFACTURABLE` precedent yields a **CAUTIONARY** critique — a signal isolated verification cannot produce.
- **Purely additive / internal:** RM1/RM2/RM3 byte-unchanged; **no contract** (suite frozen at `0.4.0`); no
  planning, verification, retrieval, persistence, ML, or external identity. `EngineeringSituation` is consumed
  only within `judgment/` (boundary-test enforced). **Primitive-revelation record:** the observed load-bearing
  constituents are `{design_input, plan, verdict, precedent_report}` (RM4 completion report §Primitive Revelation).
- **Verified:** 131 tests pass (RM3's + 39 RM4: 6 situation, 8 critic-model, 8 critique, 6 pipeline, 7 boundary,
  plus regressions); `mypy src` clean; contracts frozen.

### Added — RM3: Engineering Precedent Reasoning (compounding rung 2; retroactively documented in this release)
- **Engineering Precedent Reasoning** — a deterministic, read-only capability that surfaces the most *relevant
  prior verified* manufacturing cases for a new request and derives a supporting/cautionary/none signal. New
  package `precedent/` (`precedent_model`, `retriever`, `reasoner`) + `orchestration/precedent_runner.py`, built
  across RM3-M2…M5. Additive `PrecedentReport`/`PrecedentEntry`/`PrecedentSignal` contracts (part of the `0.4.0`
  suite). Retriever = extraction seed / mechanism; reasoner = domain identity (seed/identity separation, Law 3/8).
- **Boundaries:** deterministic structural relevance only — no ML/embeddings/vector DB, no store/retention engine
  (Law 6), no MiniFlyWire (Law 4); read-only. Architectural debt recorded: the O(N) retriever is an intentional
  local extraction seed (`docs/governance/RM3-architectural-debt.md`).

### Changed — RM1 correction: `ManufacturingEpisode` complete engineering memory (ratified impact analysis)
- **`ManufacturingEpisode` gains optional `design_input: DesignInput`** so new episodes embed the full engineering
  input (complete engineering memory for future deterministic precedent reasoning). `manufacturing_episode`
  `schema_version` `1.0.0 → 1.1.0`; contract suite `contracts/VERSION 0.3.0 → 0.4.0`. `DesignInput` unchanged.
- **Backward compatible / migration:** `design_input` is **optional** and **excluded from the content-hash
  identity view** (design identity is already in `design_ref.content_hash`), so existing episode hashes are
  unchanged and legacy `1.0.0` episodes remain valid. Legacy episodes **cannot** be back-filled (their
  `material_code`/`tolerances` live only inside one-way hashes); no migration is performed. **Retrieval policy for
  legacy episodes is intentionally deferred to a later milestone** — legacy episodes are preserved, not classified.
- Updated: episode schema + regenerated `manufacturing_episode` binding; RM1 emission (`orchestration/episode_store.py`)
  now populates `design_input`; RM2 read-side (`experience/episode_store_reader.py`) reconstructs it when present;
  contract-version assertions `0.3.0 → 0.4.0`. No RM3 work; retriever not implemented.

## [0.3.0] — 2026-07-25 — RM2: experience read-back & idempotent reuse (compounding, rung 1)

**RM2 complete and frozen** (tag `rm2-complete`). Mini Prometheus now *reuses* its own verified
experience: a repeated `ManufacturingRequest` retrieves and reuses the prior `ProductionPlan` + `Verdict`
deterministically, writing no duplicate episode — the first measurable rung of compounding. Purely additive:
**RM1 is byte-unchanged and contracts stay frozen at `0.2.0`.** Runtime `0.2.0 → 0.3.0`.
See `docs/milestones/RM2-completion-report.md` and `docs/ROADMAP.md`.

### Added (RM2 — five milestones)
- **M1** — `experience/episode_store_reader.py`: read RM1's episode JSONL back into verified
  `ManufacturingEpisode` objects (explicit per-type reconstruction + content_hash integrity).
- **M2** — `experience/episode_index.py`: deterministic composite-key index
  (`(design_input_identity_hash, capability_model_version)`) with exact-match `lookup`.
- **M3** — `orchestration/reuse_runner.py` (new file): `run_with_reuse` — intake → lookup → reuse (with a
  reproducibility guard that re-derives the plan and asserts the content_hash) or delegate to RM1's `run`;
  `ReuseRunResult`, `ExperienceConsistencyError`. RM1's `runner.py` untouched.
- **M4** — `tests/boundary/test_experience_boundaries.py` + CI gates: Law-6 non-goals (no store/retention
  engine), import discipline, contract-freeze (`VERSION == 0.2.0`), and an RM1 zero-diff gate vs `rm1-complete`.
- **M5** — this governance close-out.
- **Verified:** 50 tests pass (RM1's 31 unchanged + 19 RM2); ruff clean; contracts frozen; bindings drift-stable.
- Planning record: `specs/milestones/RM2-experience-reuse.md` (spec), `docs/design/RM2-engineering-package.md`
  (architecture), `docs/design/RM2-implementation-plan.md` (plan); decision in `docs/adr/0006-rm2-acceptance.md`.

## [0.2.0] — 2026-07-23 — RM1: "plan → verify → log" (first manufacturing capability)

**RM1 complete and frozen** (tag `rm1-complete`). Mini Prometheus turns a real engineer
`ManufacturingRequest` into a verified, provenance-complete `ProductionPlan` + `ManufacturingEpisode`.
First tagged release; runtime `0.1.0` → `0.2.0` (contracts `0.2.0`, constitution `1.1.0`).
See `docs/milestones/RM1-completion-report.md` and `docs/ROADMAP.md`.

### RM1 — Implementation milestone (complete)
- Implemented the plan → verify → log manufacturing loop strictly against the frozen contracts:
  intake (`intake/`), Velith adapter (`integrations/velith/`), deterministic planner
  (`manufacturing_planning/`), manufacturability oracle implementing the Noetica `Verifier` protocol
  (`manufacturing_constraints/`), episode emission + composition root (`orchestration/`), and internal
  mechanisms (`_hashing`, `_validate`, `_provenance`, `_verifier`, `_contracts`).
- Produces a tangible **ProductionPlan** for a real engineer `ManufacturingRequest` (machined part) and a
  content-hashed, provenance-complete **ManufacturingEpisode**; INFRA_ERROR writes no episode.
- Verified: **31 tests pass** (contract-compliance, unit, integration [determinism, negative, both intake
  paths, honesty chain, INFRA_ERROR], boundary [Law 4/6/9/15]); ruff clean; bindings regeneration-stable.
  Real CI pipeline in `.github/workflows/ci.yml` (drift → build → unit → contract → integration → boundary).
- One fixed defect found during implementation: episode identity used `plan.content_hash` (not the embedded
  plan) per contract package §3.6, restoring hash determinism. No spec/contract/schema change.

### RM1 — Contract stage (frozen)
- Froze the RM1 Contract Package (`contracts/RM1-contract-package.md`): demonstration domain = Machined Part;
  `ManufacturingRequest` primary input; STEP opaque-only; permanent `NS_MP = 4f5b56ae-3c77-4135-9f5c-1eef0ab1b252`.
- Authored 10 JSON Schema files (Draft 2020-12) under `contracts/schemas/` — MP-owned manufacturing set +
  consumed Velith/Noetica stubs; all meta-validated and ref-resolved.
- Generated Python bindings (`contracts/python/`, typed dataclasses + StrEnum, no logic) via
  `tools/generate_contracts.py` (datamodel-code-generator). Suite `contracts/VERSION` 0.1.0 → **0.2.0**.

### Governance — constitutional archaeology + conformance (CAP-0001, ADR-0004)
- Reconstructed the project's evolution across 5 repositories (`docs/governance/constitutional-evolution-report.md`);
  verdict: **repository ownership correction required** (HANDBOOK_v1.1 governs, on evidence).
- **Ratified CAP-0001** (project owner) and conformed the repository:
  - Constitution: transcribed HANDBOOK_v1.1 + ARCHITECTURE_DECISION into `constitution/`; `VERSION` → **1.1.0**.
  - Ownership: `src/` packages renamed to manufacturing content
    (`situation_state→manufacturing_state`, `world_model→manufacturing_twin`,
    `constraint_network→manufacturing_constraints`); README/CODEOWNERS/architecture doc corrected.
  - Dependencies: removed `integrations/miniflywire/` (Law 4); `integrations/` now Velith + Noetica only.
  - Withdrawn: engineering cognition/reasoning packages (Velith content); `specs/interfaces/situation-state.md`; RM1 substrate framing (to be re-scoped to manufacturing content).
  - Recorded in `docs/adr/0004-conform-repository-to-handbook.md`. No runtime code.

### Earlier work included in this first release
- Phase 1 repository architecture: governance, contract spine, runtime substrate skeleton
  (`docs/adr/0001-adopt-repository-architecture.md`).
- Constitution versioning: additive `constitution/VERSION` (baseline `1.0.0`, now `1.1.0`).
- Architecture refinement pass (documentation only): five-layer hierarchy, external-vs-internal
  contracts, expandable namespaces, dependency rules (`docs/adr/0002-architecture-refinement-external-review.md`).
- RM1 planning + runtime implementation order (`docs/adr/0003-runtime-implementation-order.md`); the
  original Situation State RM1 spec was withdrawn by ADR-0004 and re-scoped to manufacturing content.
