# RM11 Specification — Multi-Job Deterministic Scheduling

- **Status:** Frozen (Director approval, 2026-09-27; accepted in ADR-0013). Specification of record.
- **Milestone:** RM11. **Baseline:** RM10 (`rm10-complete`, `f58d8f6`), the frozen scheduling baseline.
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** a **verified multi-job scheduling substrate** — several verified jobs sharing machines → one
  deterministic, independently checked schedule → total makespan with a **lower-bound certificate**. The baseline
  rule is **not an optimizer**; Mini Prometheus computes the schedule and never executes, dispatches, persists or
  tracks it (it is not an executor, dispatcher, robot controller, factory-state owner or MES).
- **Immovable:** contracts byte-identical (suite `0.4.0`); the `Verifier` signature; all RM1–RM10 code and
  behavior (`planner.py`, `oracle.py`, `capability_model.py`, `runner.py` byte-identical to `rm10-complete`); RM2
  reuse; ownership (Handbook §6.8: Noetica owns the plan representation and executor; Mini Prometheus owns
  schedule *content*; §6.11: Noetica owns the verification protocol and `Verdict` type).

---

## 1. Audit and review summary

Read-only audit (before design):

| Question | Finding |
|---|---|
| What is one job | one `ManufacturingRequest` → one `DesignInput` / `ManufacturingTask` → one `ProductionPlan` → one verdict → one episode |
| Multi-job input | none: no batch / job-set concept anywhere — a new internal concept |
| Operation key across jobs | `(request_id, step_index)`; the request id is part of design identity, so the same part ordered twice under different request ids is two jobs |
| Machines | one assigned machine per step (RM9 first available); no capacity field, no no-overlap anywhere |
| Durations | RM10 `duration_min`, per-operation totals in integer minutes; they compose unchanged across jobs |
| Precedence | intra-job only (plan order, which contains RM8 declared pairs); nothing expresses cross-job precedence |
| Where a cross-job schedule can live | **not** in per-job plan `params` (a job's plan identity / RM2 key would depend on its co-scheduled jobs) → a separate artifact |
| Feasibility | with fixed machines, integer durations, intra-job order and no due dates or calendars, a feasible schedule **always exists** |
| Solver | none needed for feasibility; makespan minimization is NP-hard in general and no objective is frozen |
| Dependencies | runtime `jsonschema` only |

An independent adversarial review (Gemini) was evaluated against the repository and synthesized by the Director:
adopted — no solver, explicit non-optimized labelling, explicit assumptions, identity must bind the inputs,
pure/stateless offsets-only computation, MANUFACTURABLE + RM10 prerequisites, unique jobs, canonical ordering,
dropping the job-sequential rule; rejected — contract `0.5.0` with `ProductionSchedule` / `ScheduleVerdict` (a
second verdict type duplicates Noetica's `Verdict`, §6.11; a published schedule representation is Noetica's, §6.8;
it would freeze immature simplifications), an `availability_snapshot_id` (no such id exists; it would break the RM9
ruling that irrelevant unavailability does not change identity), a `task_id` tie-break (hash-derived, arbitrary).

## 2. Director rulings

| ID | Ruling |
|---|---|
| D1 | The RM11 model assumptions (§3) are frozen as assumptions of this model, not universal manufacturing claims. |
| D2 | Canonical job order is `request_id` ascending; duplicate `request_id`s are rejected; nothing depends on argument order, filesystem order, set/hash iteration, randomness, clock time or thread scheduling; operation ties use the explicit key `(start_time, request_id, step_index)`. |
| D3 | The schedule is INTERNAL: no contract change, no `ProductionSchedule` / `ScheduleVerdict` schema, suite stays `0.4.0`. |
| D4 | All-or-nothing: any failing prerequisite → `NOT_SCHEDULED` with every applicable refusal; never a partial or fabricated schedule. |
| D5 | Pure / read-only: no episode, schedule, memory, repository or manufacturing state is written; no Noetica execution; no dispatch. |
| D6 | A dedicated entry point; `runner.py` is not modified. |

## 3. RM11 model assumptions (frozen, recorded on every schedule)

1. one machine processes at most one operation at a time;
2. operations are non-preemptive;
3. each job is available at time 0;
4. each job preserves its RM10 step order;
5. each operation retains the machine assignment produced by RM9;
6. duration is the RM10 `duration_min`;
7. no setup/changeover time;
8. no transfer time;
9. no calendars/shifts/maintenance;
10. no due dates/release dates;
11. no flexible machine reassignment during RM11;
12. no optimization;
13. no execution/dispatch.

## 4. Semantic model

- **Job set:** N ≥ 1 engineer requests with pairwise-distinct `request_id`s. **Shop:** ONE
  `ProcessCapabilityModel` instance, including its RM9 availability snapshot, shared by every job of the run.
- **Per job (unchanged RM1–RM10 code):** `intake` → `planner.plan(design_input, model)` →
  `ManufacturabilityOracle().verify(plan, model)`. Scheduling plans every job itself under the one model, so all
  jobs are aligned to the same shop state **by construction** (no snapshot id is needed or invented).
- **Schedulable job:** verdict `MANUFACTURABLE`, every step has an assigned machine, and the plan carries a valid
  RM10 timeline (`planner.lead_time_min(plan)` is not `None`).
- **Operation** `o = (request_id, step_index)`: machine `m(o)` = the plan's `ResourceAssignment`; duration `p(o)` =
  the step's `duration_min`.
- **Schedule:** integer start `s(o) ≥ 0`, end `e(o) = s(o) + p(o)` (minutes from schedule origin 0). Constraints:
  every operation exactly once; the planned machine; non-preemptive; `s(j,k) ≥ e(j,k−1)`; operations on one machine
  have disjoint half-open intervals `[s, e)` (touching is allowed); integer minutes.
- **Outputs:** per operation machine/start/end; per job its completion (end of its final step); **makespan** =
  max `e(o)`; the lower-bound certificate (§7). **No objective is optimized.**

## 5. The baseline rule `earliest_start_v1` (exact)

```
state:  per job, its next unscheduled operation (its first step) and its predecessor completion (0);
        per machine, its available time (0).
repeat until every operation is placed:
  1. identify the next unscheduled operation (plan step order) of each unfinished job;
  2. earliest feasible start = max(job predecessor completion, assigned machine available time);
  3. select the candidate with the smallest earliest feasible start;
  4. break exact ties by request_id (ascending, code-point order), then step_index;
  5. schedule it: start = earliest feasible start, end = start + duration_min;
  6. set the job's predecessor completion and the machine's available time to end;
  7. repeat.
```

- The decision key `(start_time, request_id, step_index)` is total (request ids are unique), so the result never
  depends on the order in which jobs are passed. The generator itself is order-independent (tested with reversed
  inputs); the job-set layer additionally sorts refusals canonically.
- **Placement order = canonical order.** When a candidate is placed at `t`, every other candidate has start ≥ `t`,
  and every operation that becomes a candidate later starts after its predecessor ends (> `t`, durations ≥ 1). So
  starts never decrease in placement order, appending at a machine's available time never leaves a gap a later
  operation could use, and the placed sequence is exactly the `(start, request_id, step_index)` order in which the
  artifact lists operations. Every operation starts at max(its job predecessor's end, the previous end on its
  machine) ("left-justified").
- **A one-job set reproduces the RM10 serial timeline exactly** (its own machines are never busy when it is ready).

## 6. Independent validity checker (built before the generator is trusted)

`checker.schedule_issues(schedule, jobs, capability_model_version)` re-derives everything from the jobs' plans and
never imports the generator, the bound calculator or the job-set gate (import-linter contract + boundary test). It
is generator-agnostic. Closed internal issue codes:

| Proves | Issue code |
|---|---|
| every scheduled operation belongs to exactly one input job | `UNKNOWN_OPERATION`, `DUPLICATE_OPERATION` |
| every required operation is scheduled exactly once | `MISSING_OPERATION` |
| all times are integer minutes, start ≥ 0 | `INVALID_TIME` |
| the machine is the plan's fixed assignment | `MACHINE_MISMATCH` |
| duration equals the RM10 duration | `DURATION_MISMATCH` |
| start/end arithmetic is exact (`end = start + duration`) | `ARITHMETIC_MISMATCH` |
| operation order preserved; start ≥ predecessor end | `JOB_ORDER_VIOLATION` |
| no two operations overlap on one machine (`[s, e)`) | `MACHINE_OVERLAP` |
| canonical `(start, request_id, step_index)` ordering | `NON_CANONICAL_ORDER` |
| job completions, makespan = max end | `COMPLETION_MISMATCH`, `MAKESPAN_MISMATCH` |
| lower bound, gap and bound status exact | `LOWER_BOUND_MISMATCH`, `GAP_MISMATCH`, `BOUND_STATUS_MISMATCH` |
| metadata, job set, input identity, digest | `METADATA_MISMATCH`, `JOB_SET_MISMATCH`, `DIGEST_MISMATCH` |

**A generated schedule that fails the checker is never returned:** `job_set` raises `ScheduleIntegrityError` and
the CLI prints `SCHEDULE_INTEGRITY_ERROR (no schedule returned)` with exit code 1.

## 7. Lower-bound certificate (not an optimizer)

`LB = max(longest job total duration, busiest machine total assigned duration)`;
`lower_bound_min = LB`; `gap_to_lower_bound_min = makespan − LB`.

Why it is a bound under the RM11 assumptions: a job's operations are non-preemptive and totally ordered, so any
feasible schedule has makespan ≥ the job's total duration; a machine runs one operation at a time inside
`[0, makespan)`, so makespan ≥ its total assigned duration.

- `makespan == LB` → `bound_status = PROVABLY_OPTIMAL`: the schedule is provably optimal **under the RM11 model**.
- `makespan > LB` → `bound_status = GAP_ABOVE_LOWER_BOUND`: nothing is claimed except the gap `makespan − LB` (the
  bound need not be attainable). **No suboptimality claim is ever made.**

The binding terms (the jobs and machines that attain LB) are recorded in sorted order.

## 8. Identity vs digest

| | `schedule_input_identity` | `schedule_digest` |
|---|---|---|
| Question | what scheduling problem and rule are being evaluated? | what exact schedule artifact was produced? |
| Content | scheduling rule + version, capability-model version, every job's `(request_id, plan content hash)` in canonical `request_id` order | every artifact field except the digest: metadata, input identity, completions, placements, makespan, lower bound + binding terms, gap, bound status |
| Never contains | any derived output (placements, makespan, bound) | timestamps, paths, compute timings |

Both are `sha256(canonical_json(view))` with the existing `_hashing`. A job's plan hash already covers its machines,
declared durations and any RM9 availability that materially affected it, so irrelevant unavailability leaves both
unchanged (consistent with RM9) and relevant unavailability changes both. Identical job sets in any argument order,
the same model (including availability) and the same rule version give byte-identical artifacts across processes and
`PYTHONHASHSEED` values.

## 9. Worked examples (hand-computed; the tests assert exactly these)

Declared test inputs, not manufacturing data. `ID_A = aaaaaaaa-…-001 < ID_B = bbbbbbbb-…-002 < ID_C = cccccccc-…-003`.
Machines: cut_stock → saw01; face_mill, drill, pocket_mill → mill01; turn → lathe01; deburr → bench01;
inspect → cmm01.

### 9.1 Three jobs (fixtures `tests/fixtures/rm11_jobs/`)

A: saw 10, face mill 30, inspect 5 · B: saw 5, turn 20, drill 10, inspect 5 · C: saw 8, pocket mill 12, deburr 6.

| # | Candidates (earliest feasible start) | Chosen | Placed |
|---|---|---|---|
| 1 | A0 saw 0 · B0 saw 0 · C0 saw 0 | A0 (tie → A) | saw01 [0, 10) |
| 2 | A1 mill 10 · B0 saw 10 · C0 saw 10 | A1 (tie → A) | mill01 [10, 40) |
| 3 | A2 cmm 40 · B0 saw 10 · C0 saw 10 | B0 (tie → B) | saw01 [10, 15) |
| 4 | A2 40 · B1 lathe 15 · C0 saw 15 | B1 (tie → B) | lathe01 [15, 35) |
| 5 | A2 40 · B2 mill 40 · C0 saw 15 | C0 | saw01 [15, 23) |
| 6 | A2 40 · B2 40 · C1 mill 40 | A2 (tie → A) | cmm01 [40, 45) |
| 7 | B2 40 · C1 40 | B2 (tie → B) | mill01 [40, 50) |
| 8 | B3 cmm 50 · C1 mill 50 | B3 (tie → B) | cmm01 [50, 55) |
| 9 | C1 50 | C1 | mill01 [50, 62) |
| 10 | C2 bench 62 | C2 | bench01 [62, 68) |

Completions A 45, B 55, C 68; **makespan 68**. Job totals 45 / 40 / 26; machine loads saw01 23, mill01 52,
lathe01 20, cmm01 10, bench01 6 → **LB 52** (busiest machine mill01); **gap 16** (`GAP_ABOVE_LOWER_BOUND`).

### 9.2 Two jobs sharing one machine (tie at t = 0)

A: saw 10 · B: saw 10 → face mill 100. A0 saw01 [0, 10), B0 saw01 [10, 20), B1 mill01 [20, 120): **makespan 120**;
LB = max(10, 110, saw01 20, mill01 100) = **110** (longest job B); **gap 10**. With the ids swapped (the long job is
A) the tie goes to it: A0 [0, 10), A1 [10, 110), B0 [10, 20): makespan 110 = LB → `PROVABLY_OPTIMAL`. RM11 states
only the gap; the checker test also builds a valid alternative schedule of the first instance with makespan 110 —
the comparison hook a future RM12 would use (§12).

### 9.3 Two independent jobs (disjoint machines)

A: face mill 100 · B: saw 5 → deburr 5. A0 mill01 [0, 100), B0 saw01 [0, 5), B1 bench01 [5, 10): **makespan 100**
(the last-placed operation ends at 10 — makespan is the maximum end, not the last one); LB 100 (job A and mill01);
gap 0 → `PROVABLY_OPTIMAL`.

### 9.4 One job ≡ RM10

The RM10 engineer fixture: [0, 12) saw01, [12, 47), [47, 65), [65, 83) mill01, [83, 93) bench01, [93, 108) cmm01 —
exactly its RM10 timeline; makespan 108 = RM10 lead time = LB (the job) → `PROVABLY_OPTIMAL`.

## 10. Refusals (all-or-nothing; closed internal reasons, every applicable one reported)

| Reason | When | Detail |
|---|---|---|
| `EMPTY_JOB_SET` | no job | `no job was given` |
| `DUPLICATE_REQUEST_ID` | a request id repeats | `request_id appears N times; each job must be unique` |
| `JOB_NOT_MANUFACTURABLE` | verdict ≠ MANUFACTURABLE | `<status> [<reason codes>]` (+ `(<verdict detail>)`) — the job's unchanged RM1–RM10 verdict |
| `JOB_OPERATION_UNASSIGNED` | a step has no machine | `no machine assigned: step i (op), …` |
| `JOB_TIMELINE_MISSING` | no valid RM10 timeline | `timeline_issues(...)`, or `no operation declares duration_min (RM10 timing not requested)` |

Refusals are sorted by `(request_id, reason declaration order, detail)` — identical for every input order. Nothing
enters the Noetica `Verdict` or the manufacturability taxonomy; per-job verdicts are unchanged. There is no
"infeasible" outcome: under the model every schedulable set is feasible, and none is invented.

## 11. Metadata and CLI

Every schedule records `scheduling_rule = "earliest_start_v1"`, `scheduling_rule_version = "1.0.0"`,
`optimization_status = "NOT_OPTIMIZED"`, the §3 assumptions and the capability-model version.

`python -m mini_prometheus.orchestration.schedule_runner REQUEST.json [REQUEST.json ...]
[--capability-model default|constrained] [--unavailable-resource ID ...]` — request files parsed exactly as the
single-job CLI parses them (a job's plan is byte-identical to its standalone plan); file order is irrelevant. It
prints the placements table, completions, `makespan`, `lower bound` (with binding terms), `gap to lower bound`
(with `PROVABLY OPTIMAL under the RM11 model` only when the gap is 0), the assumptions, and both identities; or
`NOT_SCHEDULED` with each refusal. Exit 0 for `SCHEDULED` / `NOT_SCHEDULED`, 1 for an integrity error, 2 for usage
errors (e.g. an unknown resource).

## 12. Future comparison hook (RM12 not implemented)

`makespan_min`, `lower_bound_min` and `gap_to_lower_bound_min` are exposed on every schedule, and the checker
accepts any schedule satisfying the model whatever rule produced it. A future RM12 may compare the baseline with an
alternative rule on these metrics **if the evidence justifies it**. RM11 introduces no other heuristic and runs no
optimization research.

## 13. Exact file scope

New: `src/mini_prometheus/manufacturing_scheduling/{__init__,model,lower_bound,earliest_start,checker,job_set}.py`,
`src/mini_prometheus/orchestration/schedule_runner.py`, this spec, `docs/adr/0013-rm11-acceptance.md`,
`docs/milestones/RM11-completion-report.md`, `tests/rm11_support.py`, `tests/fixtures/rm11_jobs/job_{a,b,c}.json`,
`tests/unit/test_rm11_schedule.py`, `tests/unit/test_rm11_checker.py`, `tests/unit/test_rm11_mutation.py`,
`tests/integration/test_rm11_schedule_runner.py`, `tests/boundary/test_rm11_boundaries.py`.
Modified: `pyproject.toml` (runtime `0.9.0`; import-linter: the new package joins the two existing forbidden
contracts, plus "no RM1–RM10 module imports scheduling" and "the checker is independent of the generator"),
`docs/ROADMAP.md`, `docs/adr/README.md`, `CHANGELOG.md`.
Byte-unchanged: `contracts/**`, `.github/workflows/ci.yml`, `planner.py`, `oracle.py`, `capability_model.py`,
`runner.py`, `reuse_runner.py`, intake, integrations, experience, precedent, judgment, experiment, every RM8–RM10
golden, probe and test. The new paths lie outside both CI byte-diff sets, so no CI change is needed.

## 14. Invariants

1. Contracts byte-identical; suite `0.4.0`; no schedule schema; no taxonomy member added.
2. RM1–RM10 byte-identical and behaviorally unchanged (RM8 + RM10 goldens pass); RM2 unchanged; a job's plan inside
   a schedule is its standalone plan.
3. No schedule is returned unless the independent checker accepts it; never a partial or fabricated schedule.
4. Deterministic: independent of argument order, filesystem order, set/hash iteration, randomness, clock and threads.
5. No invented durations, setup, calendars, capacities or maintenance; no solver, dependency, ML, persistence,
   execution or dispatch; no FutureScore or MiniFlyWire.

## 15. Verification gate and stop condition

Docker verifier (Python 3.11): `pytest -q`; the RM8 golden, the RM9/RM10 baseline golden; `mypy src`;
`lint-imports`; contract drift; the CI git gates; every true-source RM11 mutation (R1–R10, C1–C3, J1–J3) failing
the suite and caught by named cases in `test_rm11_mutation.py`; the RM8–RM10 mutants (M1–M5, T1–T3) still caught.
One commit; the complete gate re-run on the committed tree; no push without authorization; RM12 is not begun.

## 16. Out of scope

Optimization of any objective; OR-Tools, CP-SAT or any solver; dispatch heuristics; flexible machine choice or
re-planning; setup/changeover/transfer times; calendars, shifts, maintenance, wall-clock time; release/due dates,
priorities, tardiness; capacity > 1, batching, preemption, lot splitting; cross-job precedence; persistence or
reuse of schedules; contracts `0.5.0`; mapping to Noetica plans; execution, dispatch, progress tracking,
event-driven rescheduling; RM3/RM4 consuming schedules; Velith-originated jobs; RM12.
