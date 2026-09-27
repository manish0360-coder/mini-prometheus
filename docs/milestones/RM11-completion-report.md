# RM11 Completion Report — Multi-Job Deterministic Scheduling

- **Milestone:** RM11. **Identity:** a verified multi-job scheduling substrate with deterministic behavior and a
  measurable distance from a valid lower bound. **Not an optimizer; not an executor, dispatcher or MES.**
- **Status:** ✅ Complete — 2026-09-27. Runtime `0.9.0`. Tag: pending `rm11-complete`. Baseline: RM10
  (`rm10-complete`, `f58d8f6`).
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged**; the schedule is internal).
- **Record:** spec `specs/milestones/RM11-multi-job-schedule.md`; ADR-0013; this report.

## 1. What RM11 delivered

An engineer hands Mini Prometheus several requests with declared operation times. Mini Prometheus plans and verifies
each one (unchanged RM1–RM10) under one capability model and — only if every job is schedulable — returns one
deterministic schedule on the shared machines, proven by an independent checker, with each job's completion, the
makespan and a lower-bound certificate. The model's assumptions are recorded on the artifact.

Three-job fixture (declared test inputs; hand-computed in spec §9.1):

| Start | End | Machine | Job | Step |
|---|---|---|---|---|
| 0 | 10 | saw01 | A | 0 cut stock |
| 10 | 40 | mill01 | A | 1 face mill |
| 10 | 15 | saw01 | B | 0 cut stock |
| 15 | 35 | lathe01 | B | 1 turn |
| 15 | 23 | saw01 | C | 0 cut stock |
| 40 | 45 | cmm01 | A | 2 inspect |
| 40 | 50 | mill01 | B | 2 drill |
| 50 | 55 | cmm01 | B | 3 inspect |
| 50 | 62 | mill01 | C | 1 pocket mill |
| 62 | 68 | bench01 | C | 2 deburr |

Completions A 45, B 55, C 68 · **makespan 68** · **lower bound 52** (busiest machine mill01) · **gap 16** — reported
as a gap only; no suboptimality claim.

| Situation | Result |
|---|---|
| one job | exactly its RM10 timeline; makespan = RM10 lead time = lower bound → provably optimal under the RM11 model |
| two jobs on disjoint machines | run in parallel; makespan = lower bound → provably optimal under the RM11 model |
| two jobs tied for one machine at t = 0 | the lower `request_id` goes first — whatever the argument order |
| any permutation of the input / another hash seed / another clock time | byte-identical schedule, input identity and digest |
| a job not MANUFACTURABLE, with an unassigned operation, or without a valid RM10 timeline | `NOT_SCHEDULED`, every applicable refusal listed, no schedule at all |
| a duplicate `request_id` / an empty set | `NOT_SCHEDULED` (`DUPLICATE_REQUEST_ID` / `EMPTY_JOB_SET`) |
| RM9 unavailability irrelevant to every job | identical input identity and digest |
| RM9 unavailability forcing a reroute | different plans → different input identity and digest |
| a second mill that sits idle | not used — no machine reassignment during RM11 |
| a generated schedule failing the checker | never returned (`ScheduleIntegrityError`; CLI exit 1) |

CLI: `python -m mini_prometheus.orchestration.schedule_runner job_a.json job_b.json job_c.json` prints the
placements, completions, `makespan: 68 min`, `lower bound: 52 min (busiest machine mill01)`,
`gap to lower bound: 16 min`, the assumptions, and both identities. Nothing is written.

## 2. How it connects to RM1–RM10

RM11 reuses, unchanged: intake, the planner (RM1 step order, RM8 precedence, RM9 routing, RM10 durations and
timeline), the manufacturability oracle and its verdicts, `timeline_issues` / `lead_time_min`, the capability model
and `with_unavailable_resources`, the existing canonical hashing, and the single-job CLI's request parsing. A job's
plan inside a schedule is byte-identical to its standalone plan, so RM2 reuse, RM3 precedent and RM4 judgment are
untouched; import-linter now forbids any RM1–RM10 module from importing the scheduling code.

## 3. Evidence (pre-commit, Docker verifier, Python 3.11)

| Gate | Result |
|---|---|
| `pytest -q` | **384 passed** (284 up to RM10 + 100 RM11) |
| RM8 golden (from `rm5-complete`) + RM9/RM10 baseline golden (from `rm9-complete`) | **6/6**, unchanged |
| RM8–RM10 tests | 102/102 |
| `mypy src` / import-linter / contract drift | clean (49 files) / **5 of 5 kept** (3 existing + 2 RM11) / none |
| CI git gates: RM1/RM2 (ADR-0010), RM3/RM4, contract version `0.4.0` | pass |
| `ruff check` + `ruff format --check` on every RM11 file | clean |
| True-source RM11 mutants R1–R10, C1–C3, J1–J3 (full suite each; named cases in `test_rm11_mutation.py`) | **16/16 caught** (§4) |
| RM8–RM10 mutants re-run (M1–M5, T1–T3) | **8/8 still caught** (§4) |
| CLI end to end (repository source, files passed C, A, B) | hand-computed schedule reproduced exactly |

## 4. Mutation evidence (real source, full suite per mutant)

Each mutant is one exact substitution in the real source, applied inside the verifier container, followed by the
full suite (384 tests). Every mutant is also caught by its named gate case in `tests/unit/test_rm11_mutation.py`.

| Mutant | Change (real source) | Named gate case that fails | Full suite |
|---|---|---|---|
| R1 | generator ignores machine availability (no-overlap removed) | `shared_machine_exact`, `checker_clean` | 32 failed |
| R2 | generator ignores job predecessor completion (precedence violated) | `checker_clean` | 38 failed |
| R3 | operation duration altered (+1) | `checker_clean` | 34 failed |
| R4 | operation start shifted (+1) | `one_job_equals_rm10` | 22 failed |
| R5 | an operation duplicated | `checker_clean` | 36 failed |
| R6 | an operation omitted | `checker_clean` | 36 failed |
| R7 | makespan = end of the last-placed operation | `independent_makespan` | 9 failed |
| R8 | tie-break changed (higher request_id wins) | `tie_to_lower_request_id` | 12 failed |
| R9 | scheduler depends on input argument order | `argument_order_irrelevant` | 7 failed |
| R10 | lower bound ignores machine loads | `lower_bound_exact` | 22 failed |
| C1 | checker's machine no-overlap check removed | `overlap_tamper_detected` | 6 failed |
| C2 | checker treats touching intervals as overlap | `touching_intervals_accepted` | 32 failed |
| C3 | checker's missing-operation check removed | `omission_tamper_detected` | 4 failed |
| J1 | MANUFACTURABLE prerequisite removed | `non_manufacturable_refused` | 6 failed |
| J2 | duplicate request_id check removed | `duplicate_refused` | 4 failed |
| J3 | check-before-return gate removed | `integrity_gate_raises` | 4 failed |

RM8–RM10 mutants re-run against the RM11 suite — all still caught: M1 9, M2 3, M3 17, M4 12, M5 4, T1 7, T2 102,
T3 12 failures (higher than at RM10 where RM11 tests also exercise the planner and oracle).

## 5. Remaining scheduling gap (deliberately out of scope)

- **Not optimized.** The baseline is a deterministic earliest-start rule; the lower-bound gap measures, it does not
  close. A measured comparison of rules (RM12) is warranted only if the evidence justifies it.
- **Model simplifications (frozen assumptions):** one operation per machine at a time, no setup/changeover or
  transfer time, no calendars/shifts/maintenance, no release or due dates, no priorities, no machine reassignment,
  no preemption or lot splitting, no cross-job precedence.
- **Internal artifact only.** Publishing a schedule representation is a future platform question (Noetica's plan
  representation, Handbook §6.8), not a Mini Prometheus contract.
- **No execution.** Nothing is dispatched, executed, persisted or tracked; real factory execution integration
  remains a later, Noetica-owned step.
- **Pre-existing packaging limitation (not introduced by RM11):** the built wheel does not ship `contracts/`, so
  running either CLI from a non-editable install fails schema validation (`NoSuchResource`); both CLIs work from
  the repository (editable install, as in CI, or `PYTHONPATH=src:.`). Left unchanged — outside RM11 scope.
