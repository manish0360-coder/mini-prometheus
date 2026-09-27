# ADR 0016 — RM13 (Opt-In Most-Work-Remaining Tie-Break Rule) implementation and acceptance

- **Status:** Accepted (Director approval, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (decision from exact-optimum evidence); Chief Systems Engineer
  (author). No external review (bounded change; a future active-schedule method would require one).
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM13-most-work-remaining-rule.md`, `docs/milestones/RM13-completion-report.md`,
  ADR-0013 (RM11), ADR-0015 (RM12)

## Context

A read-only measurement on the 135 tiny RM12-audit instances (exhaustive optima) found the default rule optimal in
124/135 but only 42/53 under machine contention, with material gaps (median 26.5% among the misses). Root-cause
enumeration showed 8 of the 11 misses are tie-break failures and 3 are earliest-start commitment failures. A
most-work-remaining tie-break repaired exactly the 8, with one small regression elsewhere.

## Decisions (as built)

1. **New, separately named rule** `earliest_start_v1_most_work_remaining` 1.0.0 (`..._downtime` under relevant
   downtime): identical to `earliest_start_v1` except that exact earliest-start ties go to maximum remaining work, then
   request_id, then step_index. The decision key puts the earliest feasible start first, so a later-starting candidate
   can never be chosen.
2. **Remaining work** = candidate duration + later unscheduled durations of the job (RM10 only; no downtime, waiting,
   idle, calendar or setup time).
3. **Opt-in only:** API `rule=` and CLI `--rule`; `earliest_start_v1` stays the default, so all RM11/RM12 goldens and
   default identities are byte-identical. Unknown rules are rejected before planning.
4. **Shared placement core:** both rules use the same earliest-fit, append-only placement (RM12), machines, checker,
   lower bounds and refusals; only the tie-break key term differs (constant for the default).
5. **RM13_REGRESSION_CORPUS_01** frozen (the exact 135 instances + exhaustive optima; digests pinned; optima re-derived
   by an independent exhaustive search in the tests). Explicitly a synthetic algorithm-regression corpus, not
   evidence of factory performance.
6. **Frozen metrics** pinned for both rules (124 → 131 optimal; 42 → 49 contended; regression case 130 163 → 167
   documented; remaining misses 72, 91, 101, 130).
7. Runtime `0.10.0 → 0.11.0`; contracts `0.4.0`; no CI change; no dependency.

## Consequences

- Engineers can opt into a rule that is better on this corpus's contended cases and whose behavior is exactly defined;
  the default and all existing identities are untouched.
- The rule is **supported for opt-in evaluation only**: 131 > 124 on a synthetic corpus is not a promotion argument.
  Promotion to default requires a separate decision on broader evidence.
- The 3 earliest-start commitment failures (and the case-130 regression) remain; addressing them would need an
  active-schedule method — a new architectural boundary requiring independent adversarial review first.

## Alternatives rejected

- **Changing the default:** unproven beyond a synthetic corpus; would change every RM11/RM12 identity.
- **Giffler–Thompson / active-schedule generation now:** only 3 cases; reachability is not a rule; bigger boundary.
- **Solver / OR-Tools, tuning, new benchmarks:** out of scope; no evidence requires them.
- **Remaining work including downtime or waiting:** would turn a processing-workload priority into an elapsed-time one
  and couple the tie-break to the shop calendar.
