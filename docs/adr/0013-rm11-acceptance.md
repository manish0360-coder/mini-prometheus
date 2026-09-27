# ADR 0013 — RM11 (Multi-Job Deterministic Scheduling) implementation and acceptance

- **Status:** Accepted (Director approval, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (rulings D1–D6 and the implementation freeze); Chief Systems
  Engineer (author); independent adversarial review (Gemini) considered, not adopted automatically
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM11-multi-job-schedule.md`, `docs/milestones/RM11-completion-report.md`,
  ADR-0012 (RM10, the frozen scheduling baseline), ADR-0011 (RM9), ADR-0010 (the behavioral gate)

## Context

RM10 gave one job a serialized timeline from engineer-declared operation times. Several jobs sharing machines had
no representation at all: no job-set concept, no no-overlap, no cross-job artifact. A cross-job schedule cannot live
in per-job plan `params` without making a job's plan identity (and RM2 reuse key) depend on the jobs it is scheduled
with. With fixed machine assignments, integer durations, intra-job order and no due dates, a feasible schedule
always exists; minimizing makespan is NP-hard in general and no objective has been frozen. The Director required an
audit and an independent adversarial review before any solver or multi-job design, then froze D1–D6.

## Decisions (as built)

1. **Model assumptions (D1)** are frozen and recorded on every schedule as assumptions of the RM11 model: one
   machine processes at most one operation at a time; non-preemptive; every job available at 0; RM10 step order;
   the RM9 machine assignment retained; duration = RM10 `duration_min`; no setup/changeover, transfer time,
   calendars/shifts/maintenance, due/release dates or flexible reassignment; no optimization; no execution/dispatch.
2. **Determinism (D2):** canonical order `request_id` ascending; duplicates refused; operation ties broken by the
   explicit key `(start_time, request_id, step_index)`. The generator is order-independent by construction.
3. **Internal artifact (D3):** `MultiJobSchedule` is an internal dataclass in the new content package
   `manufacturing_scheduling`; the contract suite stays `0.4.0` — no `ProductionSchedule`, no `ScheduleVerdict`.
4. **All-or-nothing (D4):** closed internal refusal reasons (`EMPTY_JOB_SET`, `DUPLICATE_REQUEST_ID`,
   `JOB_NOT_MANUFACTURABLE`, `JOB_OPERATION_UNASSIGNED`, `JOB_TIMELINE_MISSING`), every applicable one reported,
   canonically sorted; no partial or fabricated schedule; no "infeasible" outcome invented.
5. **Pure / read-only (D5):** scheduling plans and verifies every job itself, with the unchanged RM1–RM10 planner and
   oracle, under ONE capability model (alignment to one shop state by construction); it writes nothing.
6. **Dedicated CLI (D6):** `orchestration/schedule_runner.py`; `runner.py` untouched; request files parsed exactly
   as the single-job CLI parses them.
7. **Baseline rule `earliest_start_v1` 1.0.0:** repeatedly place the candidate with the smallest earliest feasible
   start = max(job predecessor completion, machine available time); ties by request_id, then step_index. A one-job
   set reproduces the RM10 timeline exactly. Labelled `optimization_status = NOT_OPTIMIZED`.
8. **Independent checker, trusted before the generator:** re-derives everything from the plans; never imports the
   generator, the bound calculator or the job-set gate (import-linter contract); generator-agnostic. A schedule that
   fails it is never returned (`ScheduleIntegrityError`; CLI exit 1).
9. **Lower-bound certificate:** `LB = max(longest job total duration, busiest machine load)`; `gap = makespan − LB`;
   `PROVABLY_OPTIMAL` (under the RM11 model) only when the gap is 0, otherwise only the gap is stated — never a
   suboptimality claim. Exposed for a future, evidence-gated RM12 comparison.
10. **Identity vs digest:** `schedule_input_identity` = hash of (rule, rule version, capability-model version,
    canonical `(request_id, plan content hash)` pairs) — never a derived output; `schedule_digest` = hash of the
    whole artifact except the digest. Irrelevant RM9 unavailability leaves both unchanged.
11. **Boundaries:** two new import-linter contracts — no RM1–RM10 module imports scheduling (per-job planning never
    sees co-scheduled jobs; RM3/RM4 never read schedules), and the checker is independent of the generator. Runtime
    `0.8.0 → 0.9.0`. No CI change (the new paths are outside both byte-diff sets).

## Consequences

- An engineer can hand Mini Prometheus several verified, timed jobs and get one reproducible schedule on the shared
  machines — every placement, each job's completion, the makespan, and a provable measure of how far the makespan
  can be from a valid lower bound — with the model's assumptions stated on the artifact.
- The schedule is a computation, not a command: nothing is persisted, executed or dispatched.
- The baseline is not an optimizer; improving on it is a separate, measured question (RM12), answerable against the
  exposed lower-bound metrics with the same checker.

## Alternatives rejected

- **Contract suite `0.5.0` with `ProductionSchedule` / `ScheduleVerdict`:** a second verdict type duplicates
  Noetica's `Verdict` (Handbook §6.11); a published schedule representation is Noetica's plan representation
  (§6.8); it would freeze today's simplifications (capacity 1, no setup) into the cross-layer contract.
- **Reusing `PLAN_MALFORMED` or extending the manufacturability taxonomy:** conflates schedule validity with plan
  manufacturability; a taxonomy member change is MAJOR.
- **An `availability_snapshot_id` and a version pre-flight validator:** no such id exists (RM9 deliberately keeps
  the model version and records material availability in the plan); it would make irrelevant unavailability change
  identity, contradicting the accepted RM9 ruling. Alignment by construction replaces it.
- **`task_id` tie-break:** a hash-derived UUID — tie winners would be arbitrary and could flip on any byte change.
- **Job-sequential rule (each job appended in list order):** earlier jobs reserve future machine time and later
  jobs wait behind avoidable idle gaps; dominated by the earliest-start rule.
- **OR-Tools / CP-SAT or any solver or dispatch heuristic:** no objective is frozen; heavy dependency; determinism
  risk; improvements must be measured first (RM12, only if the evidence justifies it).
- **Writing per-job episodes or saving schedules during a scheduling run:** would pollute the experience store and
  drift toward factory state.
