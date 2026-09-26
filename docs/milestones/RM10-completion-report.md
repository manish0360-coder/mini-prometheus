# RM10 Completion Report — Declared Operation Times and Single-Job Timeline

- **Milestone:** RM10. **Identity:** a deterministic single-job timeline from engineer-declared operation times.
  **Not a production scheduler.**
- **Status:** ✅ Complete — 2026-09-27. Runtime `0.8.0`. Tag: pending `rm10-complete`. Baseline: RM9 (`rm9-complete`).
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged**).
- **Record:** spec `specs/milestones/RM10-single-job-timeline.md`; ADR-0012; this report.

## 1. What RM10 delivered

An engineer declares how long each operation takes (`params.duration_min`, integer minutes). Mini Prometheus returns
the verified routing with a machine-by-machine timeline and the job's lead time — derived only from those declared
values.

Engineer fixture (declared test inputs: saw 12, face mill 35, drill 18, drill 18, deburr 10, inspect 15 min):

| Step | Machine | Start | End |
|---|---|---|---|
| 0 cut stock | saw01 | 0 | 12 |
| 1 face mill | mill01 | 12 | 47 |
| 2 drill | mill01 | 47 | 65 |
| 3 drill | mill01 | 65 | 83 |
| 4 deburr | bench01 | 83 | 93 |
| 5 inspect | cmm01 | 93 | 108 |

CLI: `MANUFACTURABLE episode -> …` then `lead time: 108 min (single-job serialized timeline)`.

| Situation | Result |
|---|---|
| a duration missing, zero, negative, fractional (incl. `18.0`), text or boolean | no timeline value at all; `timeline not derived: step 2 (drill): …`; manufacturability verdict unchanged |
| `mill01` down (RM9) with valid durations | no timeline (`no machine assigned` for steps 1–3); RM9 verdict `RESOURCE_UNAVAILABLE` unchanged |
| `lathe01` down (irrelevant) | plan and verdict identical to the normal timed run |
| a stored plan with a tampered start, end or lead time | `PLAN_INVALID` [`PLAN_MALFORMED`] |
| same request, same durations | identical hashes; RM2 reuses |
| one duration changed | new identity; RM2 does not reuse (a fresh verified run); lead time recomputed |
| no durations declared | byte-identical to RM9 |

## 2. How it connects to RM1–RM9

RM10 reuses the plan's step order (RM1), the machine assignments (RM1/RM9), the open `params` fields and the existing
identity path (declared params → design input → plan → RM2 reuse key), the verifier and its existing taxonomy
(`PLAN_MALFORMED`), and the RM8 opt-in / behavioral-gate pattern. RM3/RM4 are unaffected (they do not read params).

## 3. Evidence (pre-commit, Docker verifier, Python 3.11)

| Gate | Result |
|---|---|
| `pytest -q` | **284 passed** (244 up to RM9 + 40 RM10) |
| RM8 golden (from `rm5-complete`) + RM10 golden (from `rm9-complete`, 11 ECR/availability scenarios) | **6/6**, unchanged |
| RM9 tests | 30/30 |
| `mypy src` / import-linter / contract drift | clean / 3 of 3 kept / none |
| CI git gates: RM1/RM2 (as amended by ADR-0010), RM3/RM4, contract version `0.4.0` | pass |
| Mutation T1 — missing duration defaults to zero (real source) | gate fails (5 named tests) |
| Mutation T2 — start chain shifted by one (real source) | gate fails (12 named tests) |
| Mutation T3 — timeline consistency check removed (real source) | gate fails (12 named tests) |
| RM8 M1/M2 and RM9 M3–M5 re-run | still caught (9, 3, 15, 9, 4) |

## 4. Remaining scheduling gap

- **One job only, serialized.** No machine contention between jobs, no queues, no no-overlap across jobs, no makespan
  across jobs — this needs a multi-job input and a typed cross-task schedule contract.
- **Durations are declared totals.** No setup/changeover, per-unit cycle time, quantity scaling, machine-dependent or
  stochastic times.
- **No calendars, shifts, maintenance windows or partial availability** (RM9 availability is a time-free snapshot).
- **No optimization and no solver**; no execution, dispatch or MES integration (the plan executor is Noetica's).
- Per the Director, RM11 (cross-task scheduling) starts with an independent adversarial architecture review before
  any solver or multi-job design is chosen.
