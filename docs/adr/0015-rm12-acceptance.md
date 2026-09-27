# ADR 0015 — RM12 (Time-Aware Resource Downtime Scheduling) implementation and acceptance

- **Status:** Accepted (Director final synthesis, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (final synthesis and frozen scope); Chief Systems Engineer
  (author); one independent adversarial review (Gemini) considered and checked against the repository
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM12-resource-downtime.md`, `docs/milestones/RM12-completion-report.md`, ADR-0013
  (RM11), ADR-0014 (packaging integrity), ADR-0011 (RM9)

## Context

RM11 assumes every machine is free on `[0, ∞)`. RM9 availability is a time-free planning snapshot that reroutes. Real
shops schedule around known downtime. The audit and the review exposed the key choice: positive availability windows
truncate the horizon (operations can become unplaceable, and a greedy rule can refuse a set another order would
fit), whereas explicit finite downtime keeps the horizon unbounded and RM11's "every schedulable set has a schedule".

## Decisions (as built)

1. **Downtime, not availability windows:** per known machine, finite integer `[start_min, end_min)` intervals from
   origin 0; available everywhere else. Invalid input (incl. unknown machines, zero length, negative, non-integer,
   unbounded) raises `InvalidDowntimeError` before planning — never a verdict or refusal.
2. **Canonicalization:** validate, sort, merge overlapping and touching intervals; deterministic
   `dict[str, tuple[DowntimeInterval, ...]]` (new module `downtime.py`).
3. **No rerouting:** downtime delays operations on the RM9-assigned machine; plans are untouched.
4. **Rule `earliest_start_v1_downtime` 1.0.0**, recorded only under relevant downtime: earliest start that fits around
   the assigned machine's downtime (`S := downtime end` while intersecting; half-open), append-only, selection by the
   adjusted start, RM11 tie-break. Without relevant downtime the rule stays `earliest_start_v1` and the output is
   byte-identical to RM11 (frozen golden generated once from `rm11-complete`, also with downtime on unused machines).
5. **Relevance:** only machines used by the job set; irrelevant downtime changes nothing.
6. **Identity:** `schedule_input_identity` includes relevant canonical downtime (only when present); the digest covers
   the new artifact fields (only when present).
7. **Bounds:** LB_RM11 retained as `lower_bound_min`; LB_RM12 = max(LB_RM11, max `T_avail(W_m)`) added as
   `window_aware_lower_bound_min` with binding machines; under downtime the gap is measured to LB_RM12;
   `PROVABLY_OPTIMAL` only under the frozen RM12 model.
8. **Checker:** re-derives relevant canonical downtime and `T_avail` with its own code; proves no downtime conflict,
   recorded downtime, window bound, gap, assumptions and identity; separate `DowntimeIssueCode` enum (RM11's
   `IssueCode` unchanged); independence from the canonicalizer added to the import-linter contract.
9. **CLI:** `--downtime MACHINE:START:END` (repeatable); usage error on invalid input; RM11 report unchanged without
   relevant downtime.
10. **Internal only:** contracts `0.4.0`; no public scheduling schema or `Verdict` code. Runtime `0.9.1 → 0.10.0`.

## Consequences

- Engineers can schedule several verified jobs around known machine downtime and see how far the result is from a
  valid downtime-aware lower bound — reproducibly, with nothing stored or executed.
- Calendars, shifts and maintenance systems can later compile into relative downtime outside the core.
- Placement is append-only earliest-fit: idle time caused by downtime is visible, not optimized away.

## Alternatives rejected

- **Positive availability windows:** finite horizon, unplaceable operations, greedy false refusals.
- **Rerouting around downtime:** changes plans without re-planning/re-verification (violates RM9/RM11 boundaries).
- **Gap insertion or other heuristics:** not needed for correctness; any improvement must be measured first.
- **Reusing `RESOURCE_UNAVAILABLE` or adding a `Verdict` code:** conflates manufacturability with schedule-time input.
- **Hashing all declared downtime:** would make irrelevant downtime change identity (contradicts RM9's principle).
- **Extending RM11's `IssueCode`:** kept separate so the RM11 checker taxonomy and its tests stay untouched.
