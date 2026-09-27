# ADR 0017 — RM14 (Sequence-Dependent Resource Changeover Scheduling) implementation and acceptance

- **Status:** Accepted (Director synthesis and design freeze, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (synthesis and freeze); one independent adversarial review (Gemini,
  input only, not authority); Chief Systems Engineer (audit, implementation).
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM14-sequence-dependent-changeover.md`, `docs/milestones/RM14-completion-report.md`,
  ADR-0013 (RM11), ADR-0015 (RM12), ADR-0016 (RM13)

## Context

After multi-job scheduling (RM11), downtime (RM12) and an opt-in tie-break (RM13), the largest modelled gap between a
schedule and a shop floor was changeover: RM11 froze "no setup/changeover time". The read-only audit found no setup
concept anywhere; RM10's `duration_min` is the declared total operation time (a per-operation setup would double-count);
only `mill01` performs several operation codes in the shipped models; and the schedule digest covers every field of
every scheduled operation. The review showed operation-pair rules alone cannot express a changeover between two jobs
on a single-operation machine, that assuming zero for an undeclared transition would invent a parameter, and that
within-job transitions risk double counting.

## Decisions (as built)

1. **Input:** optional, internal, per-run `SetupRule(machine_id, prev_op, curr_op, duration_min)`; transition rules
   and a per-machine default `(machine, None, None, minutes)` — no wildcard string. Validated before planning
   (`InvalidSetupError`), canonical order, CLI `--setup` / `--setup-default`.
2. **Precedence:** when the rule needs (evaluates) a cross-job transition on a machine with any declared rule:
   transition rule, else machine default, else **refuse** (`UNSPECIFIED_SETUP_TRANSITION`) — never zero. A possible
   transition the rule never evaluates is not required (Director correction before the freeze: the setup table is
   not an exhaustive declaration).
3. **Cross-job only;** none before a machine's first operation; machines without rules have none.
4. **Timing:** changeover + operation are one uninterrupted block `[S, S + setup + duration)` starting no earlier than
   the job's predecessor completion and the machine's available time, fitted as a whole around RM12 downtime;
   `setup_end == processing_start`; selection by the block start.
5. **Unchanged:** RM9 assignments (never rerouted), RM12 downtime semantics, RM13 remaining work (processing only),
   lower bounds (still valid; no setup-aware bound), contracts `0.4.0`.
6. **Artifact and identity:** relevant canonical rules and one recorded changeover interval per applied changeover,
   present only when relevant; they enter `schedule_input_identity` / the digest only then, so every earlier identity
   and digest is byte-identical. Rule ids gain a `_setup` suffix (provenance) under relevant rules.
7. **Checker:** independently re-reads the raw rules and re-derives relevance and every required changeover from each
   machine's sequence; ten new issue codes; import-linter forbids it the setup-rule module.
8. Runtime `0.11.0 → 0.12.0`; contracts `0.4.0`; no CI change; no dependency.

## Consequences

- Multi-job schedules can account for declared sequence-dependent changeover without any machine, tool, fixture or
  material state; an incomplete declaration is refused rather than silently optimistic.
- An incomplete setup table is accepted as long as the schedule never needs a missing transition; when it does, the
  set is refused with the needed transitions named (a default on the machine always suffices).
- Lower bounds ignore changeover, so gaps grow with setup; a tighter bound (a sequencing problem) is deferred.
- Synthetic verification only: no claim about real changeover times or factory performance.

## Review record

The review's accepted substance: the machine default rule, refusal of undeclared transitions, cross-job-only
application, attached (non-anticipatory) setup, the whole block avoiding downtime, RM13 remaining work unchanged,
relevance-filtered identity. Not adopted: an opt-in within-job flag and an initial-setup mapping (deferred). A factual
error in the review — a `drill_press01` machine — does not exist in the shipped models.

## Alternatives rejected

- **Per-operation setup (`params.setup_time_min`):** not sequence-dependent; double-counts `duration_min`.
- **Operation-pair rules only / global pairs / capability pairs:** blind on single-operation machines, across machines,
  or between face_mill and pocket_mill (both `cap.mill`).
- **Zero for undeclared transitions:** invents a physical parameter.
- **Anticipatory setup:** speculative machine reservation before the part arrives.
- **Material/tool/fixture-aware changeover, setup optimization, solvers:** out of scope; no evidence or state for them.
