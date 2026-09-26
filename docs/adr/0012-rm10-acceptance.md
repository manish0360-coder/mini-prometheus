# ADR 0012 — RM10 (Declared Operation Times and Single-Job Timeline) implementation and acceptance

- **Status:** Accepted (Director design freeze, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (design freeze); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM10-single-job-timeline.md`, `docs/milestones/RM10-completion-report.md`,
  ADR-0011 (RM9, the baseline), ADR-0010 (the behavioral gate)

## Context

The read-only scheduling audit found no manufacturing durations, setup, capacity or scheduling substrate anywhere in
Mini Prometheus. A real scheduler built now would have to invent times. The smallest honest capability is to accept
engineer-declared operation times and derive a single-job timeline from them — nothing invented.

## Decisions (as built)

1. **Input:** `DeclaredOperation.params["duration_min"]`, the engineer-declared total time of an operation for this
   request, integer minutes ≥ 1; no float/bool/string, no conversion, no time model of any kind.
2. **Timeline:** serialized in plan order — `start_0 = 0`, `start_i = end_(i-1)`, `end_i = start_i + duration_i`,
   lead time = final end — exact integers, recorded in the open `ProcessStep.params` (`duration_min` input copy;
   `schedule_start_min`, `schedule_end_min` derived; `schedule_lead_time_min` on the final step only). Request-side
   start/end values are never read.
3. **No partial or invented schedule:** any missing/invalid duration or unassigned step → no timeline value at all;
   `timeline_issues()` reports each prerequisite, derivable from the persisted episode; the CLI prints them. RM9's
   verdict is untouched (chosen over writing into `Verdict.detail`, which would alter the manufacturability verdict).
4. **Verifier:** a carried timeline that is inconsistent → `PLAN_MALFORMED`, `PLAN_INVALID` (existing taxonomy).
5. **Versioning:** planner `1.3.0` only when a valid timeline is derived; verifier `1.3.0` only when it evaluates a
   carried timeline (including a tampered one it rejects — honest provenance for the rule that produced the finding).
   Everything else keeps its RM8/RM9 version.
6. **Identity / RM2:** durations enter identity through the existing parameter path; RM2 unchanged.
7. **Zero-diff evidence:** a second frozen golden, generated once from `rm9-complete`, pins the ECR and availability
   paths for requests without durations (the RM8 golden pins the default model and R*).
8. **Contracts unchanged** (`0.4.0`); no CI change (the modified files stay under the RM8 behavioral gate). Runtime
   `0.7.0 → 0.8.0`.

## Consequences

- An engineer who declares operation times gets a verified routing with a machine-by-machine timeline and a lead time.
- This is a single-job serialized timeline, **not** a production scheduler: no machine contention, queues, setup,
  calendars or optimization.
- Cross-task scheduling (several jobs sharing machines) needs a multi-job input and a typed schedule contract; per the
  Director, an independent adversarial architecture review precedes any solver or multi-job design (RM11).

## Alternatives rejected

- **quantity × cycle time / setup models:** would assert manufacturing physics the repository does not represent.
- **Float or string durations with conversion:** non-exact and ambiguous.
- **Typed contract fields now:** deferred to the cross-task schedule contract.
- **Reporting prerequisites in `Verdict.detail`:** would change RM9's manufacturability verdict.
