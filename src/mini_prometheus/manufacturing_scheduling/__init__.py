"""Manufacturing multi-job scheduling (MP-owned CONTENT; RM11).

Computes one deterministic, independently checked schedule for several verified jobs that share
machines (specs/milestones/RM11-multi-job-schedule.md). The schedule is INTERNAL — not a contract
(suite 0.4.0) — and is a computation only: Mini Prometheus never executes, dispatches, persists or
tracks it (Handbook §6.8: the plan executor is Noetica's). The baseline rule is NOT an optimizer;
a lower-bound certificate measures the schedule's distance from a valid bound.

Modules: ``model`` (types, frozen assumptions, identity/digest), ``lower_bound`` (the
certificate), ``earliest_start`` (the baseline generator), ``checker`` (independent validity
checker — never imports the generator or the bound calculator), ``job_set`` (prerequisites,
refusals and the check-before-return gate), ``downtime`` (RM12 downtime input) and ``changeover``
(RM14 setup-rule input: declared sequence-dependent cross-job changeovers).
"""
