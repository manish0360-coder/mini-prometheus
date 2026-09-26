# ADR 0011 — RM9 (Resource Availability) implementation and acceptance

- **Status:** Accepted (Director design freeze with the plan-identity refinement, 2026-09-27)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (design freeze); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** `specs/milestones/RM9-resource-availability.md`, `docs/milestones/RM9-completion-report.md`,
  ADR-0010 (RM8, the baseline and the behavioral gate), ADR-0006 (RM2)

## Context

RM8 (`rm8-complete`, `0e2cebb`) is the frozen manufacturing baseline. RM1–RM8 assume every machine is always
available; the frozen reason code `RESOURCE_UNAVAILABLE` has never been emitted. The read-only audit located the
smallest integration point: the capability model and the shared assignment helper, all within the four files RM8
placed under the behavioral zero-diff gate.

## Decisions (as built)

1. **Input:** a defaulted-empty `unavailable_resources` field on `ProcessCapabilityModel`, set only through
   `with_unavailable_resources()`, which rejects unknown resource ids (`UnknownResourceError`) before planning. The
   model `version` is unchanged (the contract's strict `X.Y.Z` cannot carry availability). Availability is an
   immutable per-run snapshot; Mini Prometheus holds no availability state (Noetica owns state).
2. **Material effect:** one shared definition — the RM1-selected provider for a required capability is unavailable.
3. **Planner:** assigns the first available provider (RM1's selection when nothing relevant is down), reroutes to an
   available alternative, leaves the step unassigned when none exists, and records
   `params["unavailable_resources"]` only on materially affected steps; planning rule `1.2.0` only then.
4. **Verifier:** `RESOURCE_UNAVAILABLE` → `NOT_MANUFACTURABLE` when a materially affected capability has no available
   provider or the plan assigns an unavailable resource; responsible resources named in `Verdict.detail`. An absent
   machine stays `CAPABILITY_MISSING`. Findings combine with RM1/RM8 findings; `PLAN_INVALID` still dominates.
   Verifier `1.2.0` only when availability participates; otherwise `1.1.0`/`1.0.0` as before.
5. **Plan identity (Director refinement):** irrelevant unavailability leaves plan and verdict byte-identical;
   relevant unavailability changes the plan. Both are named tests.
6. **RM2 unchanged; availability not in the reuse key.** RM2's re-derivation guard fails closed when availability
   changes the plan; a stale verdict is never served (tests A, B, C).
7. **CLI:** repeatable `--unavailable-resource ID`; default invocation identical to RM8.
8. **No CI change:** the four modified files are already governed by the RM8 behavioral golden (ADR-0010), which
   still passes unchanged. Runtime `0.6.0 → 0.7.0`; contract suite `0.4.0`.

## Consequences

- Mini Prometheus can now answer "can this part be made on the machines that are actually up?" — rerouting when an
  alternative exists, naming the down machines when none does, and flagging stored plans that have gone stale.
- Availability is a time-free snapshot: no time windows, capacity, queues or calendars. That is scheduling — the next,
  separate milestone.

## Alternatives rejected

- **Writing the global unavailable list into every step:** would change plan identity for irrelevant outages
  (rejected by the Director's refinement).
- **Adding availability to the RM2 reuse key:** modifies frozen RM2 code; the existing guard already fails closed.
- **Encoding availability in `capability_model_version`:** impossible under the strict SemVer contract pattern.
- **Detection only (no rerouting):** would report `RESOURCE_UNAVAILABLE` even when an alternative machine could do
  the work.
