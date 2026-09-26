# RM9 Completion Report — Resource Availability

- **Milestone:** RM9. **Identity:** declarative, opt-in resource availability for one planning snapshot.
- **Status:** ✅ Complete — 2026-09-27. Runtime `0.7.0`. Tag: pending `rm9-complete`. Baseline: RM8 (`rm8-complete`).
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged**).
- **Record:** spec `specs/milestones/RM9-resource-availability.md`; ADR-0011; this report.

## 1. What RM9 delivered

An engineer (or a future factory adapter) can declare which known machines are down for a planning snapshot
(`with_unavailable_resources()`, CLI `--unavailable-resource ID`). Mini Prometheus then plans on the machines that
are actually up.

| Situation (engineer fixture: saw → face mill → drill ×2 → deburr → inspect) | Result |
|---|---|
| `mill01` down, no other mill | `NOT_MANUFACTURABLE` [`RESOURCE_UNAVAILABLE`], detail `RESOURCE_UNAVAILABLE: mill01`; milling/drilling steps unassigned and marked |
| `mill01` down, a second centre `mill02` exists | `MANUFACTURABLE`, milling and drilling rerouted to `mill02` |
| `lathe01` down (not needed by this part) | plan and verdict byte-identical to the normal run |
| `mill01` and `cmm01` down | `RESOURCE_UNAVAILABLE`, detail names both |
| lathe absent from the model, turning requested | `CAPABILITY_MISSING` (not `RESOURCE_UNAVAILABLE`) |
| stored plan assigned to `mill01`, `mill01` now down | re-verification → `RESOURCE_UNAVAILABLE` (stale plan) |
| ECR model + `mill01` down + inspection first + 0.001 mm | `PLAN_INVALID` [`PRECEDENCE_VIOLATION`, `RESOURCE_UNAVAILABLE`, `TOLERANCE_UNSUPPORTED`] |
| unknown id `mill99` | rejected before planning (CLI exit 2, nothing written) |

The verifier reports `1.2.0` and the planner rule `1.2.0` only when availability participates; every other run
reports exactly what RM8 reported.

## 2. How it connects to RM1–RM8

It reuses the capability model's machine map, the RM1 assignment order, `ResourceAssignment`, the frozen
`RESOURCE_UNAVAILABLE` code, the Noetica `Verdict` envelope (`detail`), the `ManufacturingEpisode`, the RM8 opt-in
pattern and behavioral gate, and RM2's re-derivation guard. Findings flow into episodes and on to RM2/RM3/RM4
unchanged (RM3/RM4 treat reason codes generically).

## 3. Evidence (pre-commit, Docker verifier, Python 3.11)

| Gate | Result |
|---|---|
| `pytest -q` | **244 passed** (214 up to RM8 + 30 RM9) |
| RM8 behavioral zero-diff (golden from `rm5-complete`, unchanged) | **3/3** |
| `mypy src` / import-linter / contract drift | clean / 3 of 3 kept / none |
| CI git gates: RM1/RM2 (as amended by ADR-0010), RM3/RM4, contract version `0.4.0` | pass |
| Named identity tests | "irrelevant unavailable resource does not change plan identity" and "relevant unavailable resource changes plan identity" pass |
| RM2 interaction | A reuse succeeds (irrelevant); B fails closed (reroute); C fails closed and the stale plan re-verifies as `RESOURCE_UNAVAILABLE` |
| Mutation M3 — remove the availability finding (real source) | gate fails (12 named tests) |
| Mutation M4 — planner ignores availability (real source) | gate fails (5 named tests) |
| Mutation M5 — absent machine classified as unavailable (real source) | gate fails (3 named tests) |
| RM8 mutations M1/M2 re-run | still caught (8 and 3 named tests) |

## 4. Limitations and the remaining manufacturing gap

- Availability is a binary, time-free snapshot per machine: no time windows, capacity, queues, setup times,
  maintenance calendars or partial availability.
- Assignment is deterministic first-available; no load balancing or optimization.
- The snapshot is supplied per run; no MES/factory adapter feeds it yet, and Mini Prometheus stores none of it.
- The next gap is **scheduling**: when each step runs on which machine, given time and capacity — a separate
  milestone.
