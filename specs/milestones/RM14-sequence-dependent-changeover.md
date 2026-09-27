# RM14 Specification — Sequence-Dependent Resource Changeover Scheduling

- **Status:** Frozen (Director synthesis after one independent adversarial review, 2026-09-27; accepted in
  ADR-0017). Specification of record.
- **Milestone:** RM14. **Baseline:** RM13 (`rm13-complete`, `7651699`).
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** multi-job scheduling accounts for an **explicitly declared, sequence-dependent, cross-job** machine
  changeover (setup) time that occupies the machine before an operation. Stateless, per-run input; refuse to invent;
  independently checked. **Not an optimizer, not a setup-management system, no claim about real-factory performance.**
- **Immovable:** without relevant setup rules every RM11/RM12/RM13 output, identity and digest is byte-identical;
  RM9 machine assignments; RM12 downtime semantics; RM13 remaining work; lower bounds; contracts (`0.4.0`).

---

## 1. Evidence (Pass 1, read-only audit)

- No setup or changeover concept existed in source or contracts: only the frozen RM11 model assumption
  "no setup/changeover time".
- RM10 defines `duration_min` as the engineer-declared **total** time of an operation for the request, so a
  sequence-independent setup (`params.setup_time_min`) would double-count; RM14 models only what depends on the
  machine's **sequence**.
- In both shipped capability models (1.0.0, 1.1.0) only `mill01` performs more than one operation code (drill,
  face_mill, pocket_mill); saw01, lathe01, bench01 and cmm01 perform one each. Operation-pair rules alone therefore
  cannot express a changeover between two jobs on a single-operation machine — hence the per-machine default rule.
- `schedule_digest` hashes every field of every `ScheduledOperation`, so changeovers are a separate artifact field
  present only when relevant (as RM12 did for downtime).

One independent adversarial review was run on the design space; the Director synthesis froze §2–§8.

## 2. Input model (frozen)

Optional, internal, per-run input `setup_rules`: a collection (list, tuple or set — re-iterable; the independent
checker reads it again) of `SetupRule(machine_id, prev_op, curr_op, duration_min)` or equivalent 4-item sequences.

- **Transition rule** `(machine, prev_op, curr_op, minutes)`: both operation codes.
- **Machine default** `(machine, None, None, minutes)`: every other cross-job transition on that machine. No wildcard
  string ("ANY" is rejected as an unknown operation).
- Validation before planning (`InvalidSetupError`; CLI exit 2): known machine of the capability model; both operations
  None or both operation codes **the machine can perform**; minutes an integer ≥ 0 (no bool, float or string; zero is
  valid); each `(machine, prev_op, curr_op)` at most once; malformed entries and non-collections (text, mappings,
  one-shot iterators) rejected.
- Canonical form: sorted by `(machine_id, default first, prev_op, curr_op)`; insertion order and container type never
  matter.
- CLI: `--setup MACHINE:PREV_OP:CURR_OP:MINUTES` and `--setup-default MACHINE:MINUTES` (repeatable).
- The scheduling rule receives the declared canonical rules (so it knows which machines are active) and records only
  the relevant ones (§6).

## 3. Matching precedence and refusal (frozen)

A machine with **any** declared rule is *active*. When the scheduling rule needs (evaluates or uses) a cross-job
transition `prev_op → curr_op` on an active machine M: (1) the transition rule `(M, prev_op, curr_op)`; (2) otherwise
M's default; (3) otherwise **fail closed** — `UNSPECIFIED_SETUP_TRANSITION` refusal of the whole set (`request_id`
None, detail `"M: cross-job changeover P -> C is not declared and M has no declared default"`), never zero.

A transition is *needed* when, at some decision, an unfinished job's next operation on M is a candidate and M's last
placed operation belongs to another job: the candidate's block (§5) depends on that changeover. At the first decision
with any needed undeclared transition the run stops and every such transition of that decision is reported (sorted,
so independent of input order). A possible transition the rule never evaluates is **not** required — the setup table
is not an exhaustive declaration. The check runs only when every job meets its other prerequisites (otherwise the set
is already refused and nothing is scheduled). A machine without any declared rule has no changeover (the RM11
assumption).

## 4. When a changeover applies (frozen)

- **Cross-job only:** operation X is preceded on its machine, in this run's sequence, by an operation of **another**
  job. Consecutive operations of the same job never get an RM14 changeover (`duration_min` already covers them).
- **First operation** on a machine in the run: no changeover (no machine state is owned; initial setup is deferred).
- A job returning to a machine after another job's operation does get one (the transition is cross-job).
- Machine assignment is RM9's, fixed: a changeover never reroutes, never reconsiders capability.

## 5. Timing model and rule (frozen)

For both RM13 rules, on the assigned machine M of candidate X with changeover s (0 if none):

```
S = the earliest block start >= max(job predecessor completion, machine available time)
    such that the whole block [S, S + s + duration_min) intersects no canonical downtime interval of M
    (RM12 half-open earliest fit, applied to the block; S := the downtime's end while it intersects)
changeover  = [S, S + s)            (recorded only when a changeover applies; s may be 0)
operation   = [S + s, S + s + duration_min)
select the candidate by (S, rule priority, request_id, step_index)   # S is the BLOCK start
```

- `setup_end == processing_start` strictly; changeover and operation form **one uninterrupted, non-preemptive
  block**; neither crosses downtime; the changeover never starts before the job's predecessor completes (no
  anticipatory setup) and never before the machine is free; the machine's available time advances to the operation's
  end (append-only).
- Blocks are placed in non-decreasing block-start order (a placement on M only raises M's available time; other
  machines' candidates are unchanged), so no idle gap before a placed block can later be used.
- RM13's remaining work stays **processing time only** (candidate + later unscheduled `duration_min`); it never
  includes a changeover (a future operation's machine predecessor is unknown).
- Rule ids gain a `_setup` suffix only under relevant setup rules: `earliest_start_v1_setup`,
  `earliest_start_v1_downtime_setup`, `earliest_start_v1_most_work_remaining_setup`,
  `earliest_start_v1_most_work_remaining_downtime_setup` (provenance; not selectable). Rule version `1.0.0`.

## 6. Artifact, relevance, identity (frozen)

- **Relevant rules:** a transition rule whose transition is possible (§3); a machine default when some possible
  transition on its machine has no transition rule. Rules for unused machines, machines used by one job, transitions
  that cannot occur, or a default that covers nothing are irrelevant.
- With relevant rules the artifact records `setup_rules` (relevant canonical rules) and `setups` — one
  `ScheduledSetup(request_id, step_index, resource_id, prev_request_id, prev_op, curr_op, matched, duration_min,
  start_min, end_min)` per applied changeover (including zero-minute ones), `matched` ∈ {`transition`,
  `machine_default`}, canonical `(start_min, request_id, step_index)` order. Operations keep their fields
  (`start_min`/`end_min` = processing interval).
- `schedule_input_identity` includes the relevant canonical rules; `schedule_digest` covers `setup_rules` and
  `setups`. Without relevant rules neither field appears and every identity and digest is exactly RM13's.
- Model assumptions under relevant rules: RM11's (or RM12's) list with "no setup/changeover time" withdrawn and four
  RM14 statements added (`MODEL_ASSUMPTIONS_SETUP`, `MODEL_ASSUMPTIONS_DOWNTIME_SETUP`).

## 7. Independent checker (frozen)

Given the RAW setup input, the checker (never importing the generator, bound calculator, downtime or setup-rule
modules) re-reads the rules, re-derives the relevant ones and every required changeover from each machine's sequence
in the schedule, and proves: recorded rules = relevant canonical input (`SETUP_RULES_MISMATCH`); every used cross-job
transition on an active machine is declared (`UNSPECIFIED_SETUP_TRANSITION`); every required changeover recorded
(`SETUP_MISSING`), none fabricated — first operation, same job, undeclared machine (`SETUP_UNEXPECTED`); machine,
predecessor job, transition, matched rule and minutes correct (`SETUP_MISMATCH`); integer, non-negative, end = start +
minutes (`SETUP_INVALID_TIME`); end = operation start (`SETUP_NOT_ADJACENT`); start ≥ job predecessor end
(`SETUP_BEFORE_PREDECESSOR`); no downtime intersection (`SETUP_DOWNTIME_CONFLICT`); blocks never overlap on a machine
(`SETUP_OVERLAP`); canonical order; metadata, identity and digest.

## 8. Unchanged boundaries

Lower bounds (RM11; RM12 window-aware) unchanged — still valid because changeovers only add machine time; no
setup-aware bound, no new optimality claim (`PROVABLY_OPTIMAL` keeps its meaning: makespan equals a valid lower bound).
RM1 planning, RM2 reuse, RM3/RM4 precedent and critique never see setup rules (they are schedule-level, per run).
Contracts `0.4.0`; no schema, `ProductionPlan`, `ManufacturingRequest` or episode change; no state.

## 9. Worked examples (hand-computed; the tests assert exactly these)

A, B, C = request ids in ascending order. Default model.

| Case | Jobs | Rules / downtime | Schedule |
|---|---|---|---|
| explicit beats default | A face_mill 10 · B pocket_mill 20 | mill01 face_mill→pocket_mill 3, default 9 | A [0,10); B changeover [10,13) transition + [13,33) |
| default | same | mill01 drill→pocket_mill 3 (irrelevant), default 9 | B changeover [10,19) default + [19,39) |
| unused gap, no refusal | same | mill01 face_mill→pocket_mill 3 only | B [10,13) transition + [13,33) (pocket_mill → face_mill never evaluated) |
| needed gap, refusal | same | mill01 pocket_mill→face_mill 3 only | NOT_SCHEDULED: face_mill → pocket_mill needed, undeclared |
| within job | A face_mill 10 → drill 5 · B pocket_mill 20 | mill01 default 7 | A [0,10), [10,15) (no changeover); B [15,22) + [22,42) |
| first op, saw default | A saw 10 → face_mill 10 · B saw 5 → drill 5 | saw01 default 2, mill01 default 4 | A saw [0,10), A mill [10,20) (first on mill01); B [10,12)+[12,17); B [20,24)+[24,29) |
| occupancy | A, B, C saw 10 | saw01 default 5 | A [0,10); B [10,15)+[15,25); C [25,30)+[30,40) |
| no anticipatory setup | A face_mill 10 · B saw 30 → pocket_mill 10 | mill01 default 8 | B changeover [30,38) (not [22,30)) + [38,48) |
| block vs downtime | A saw 10 · B saw 10 | saw01 default 5; saw01 down [16,20) | B [20,25)+[25,35) |
| multiple windows | same | down [12,20), [30,33), [40,60) | B [60,65)+[65,75) |
| long changeover | same | default 30; down [50,55) / [49,55) | B [10,40)+[40,50) / [55,85)+[85,95) |
| three-job fixture (CLI) | job_a/b/c | saw01 default 2, mill01 default 6, mill01 face_mill→drill 3 | makespan 77, lower bound 52, gap 25 |

## 10. Implementation choices where the frozen design was silent

1. Selection uses the **block start** (the changeover's start), which keeps placements non-decreasing and ties exact.
2. The `_setup` rule-id suffix follows the RM12 `_downtime` provenance precedent.
3. "Needed" (§3) is the candidate evaluation: every candidate's changeover is computed at each decision (its block
   start depends on it around downtime), so an undeclared transition of an evaluated candidate refuses the run even
   if another candidate is then chosen; all such transitions of that decision are reported in sorted order.
4. Operation codes in a rule must be ones the machine can perform (catches typos the way unknown machines are).
5. Zero-minute changeovers are recorded (they show which declared rule applied).
6. `setup_rules` must be a re-iterable collection (the checker reads the raw input a second time).

## 11. File scope

New: this spec, ADR-0017, `docs/milestones/RM14-completion-report.md`, `manufacturing_scheduling/changeover.py`,
`tests/rm14_support.py`, `tests/unit/test_rm14_{setup,checker,properties,mutation,no_setup_zero_diff}.py`,
`tests/integration/test_rm14_cli.py`, `tests/boundary/test_rm14_boundaries.py`.
Modified: `manufacturing_scheduling/{model,earliest_start,job_set,checker,__init__}.py`,
`orchestration/schedule_runner.py`, `tools/verify_installed_wheel.py`, `pyproject.toml` (runtime `0.12.0`; checker
independence contract also forbids the setup-rule module), `docs/ROADMAP.md`, `docs/adr/README.md`, `CHANGELOG.md`.
Unchanged: contracts, CI, RM1–RM10, lower bounds, downtime canonicalizer, every RM8–RM13 golden, probe, fixture and
test.

## 12. Verification gate and stop condition

Docker verifier (Python 3.11): full pytest; RM8, RM9/RM10, RM11/RM12 goldens, RM13 corpus and the RM14 zero-diff gate;
mypy; import-linter; contract drift; CI git gates; installed-wheel check (incl. RM14); true-source mutants S1–S14,
K1–K9 plus every RM8–RM13 mutant; protected-file check. One commit; post-commit gate; push; tag `rm14-complete`;
GitHub CI.

## 13. Out of scope / deferred

Initial machine setup (a declared per-run initial state); opt-in within-job setup; material-, tool-, fixture- or
job-identity-aware changeovers; tool inventory, jaws, coolant, G-code; automatic setup discovery; setup-aware lower
bound; setup-aware remaining work; setup sequencing optimization, Giffler–Thompson, solvers; calendars, shifts, MES,
live or persistent machine state; any contract change; any real-factory claim.
