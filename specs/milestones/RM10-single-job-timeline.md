# RM10 Specification — Declared Operation Times and Single-Job Timeline

- **Status:** Frozen (Director design freeze, 2026-09-27; accepted in ADR-0012). Specification of record.
- **Milestone:** RM10. **Baseline:** RM9 (`rm9-complete`, `6ca4d22`), the frozen manufacturing baseline.
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** a deterministic **single-job timeline** derived only from engineer-declared operation times. **RM10
  is not a production scheduler**: one job, serialized, no contention, no optimization.
- **Immovable:** contracts byte-identical (suite `0.4.0`); the `Verifier` signature; RM8/RM9 behavior for requests
  that declare no duration; RM2 code; ownership (Noetica owns state and the plan executor — Handbook §6.8; Mini
  Prometheus owns schedule *content*).

---

## 1. Audit summary (read-only, before design)

| Question | Finding |
|---|---|
| Manufacturing durations | none anywhere (the only time fields, `timing.plan_ms/verify_ms`, measure software latency and are excluded from identity) |
| Setup / changeover / capacity / calendars | none |
| Scheduling substrate | none (placeholder docstrings only); no solver dependency (runtime deps: `jsonschema`) |
| Plan representation | ordered `ProcessStep`s (contiguous indices = execution order) + `ResourceAssignment{step_index, resource_id, capability_id}`; all schemas closed except `ProcessStep.params` and `DeclaredOperation.params` |
| Identity path | declared operation `params` flow into `DesignInput` identity → task → plan and the RM2 reuse key |
| RM3/RM4 | relevance compares operation codes only; judgment reads no params — unaffected |
| Multi-job scheduling | needs a multi-job input and a cross-task schedule contract, neither of which exists → later milestone |

## 2. Frozen semantics

**Input (engineer-declared).** `DeclaredOperation.params["duration_min"]` = the engineer-declared total manufacturing
time of that operation for this specific request, in **integer minutes ≥ 1**. No float (not even `18.0`), no `bool`,
no string, no implicit conversion. No quantity × cycle-time, setup, machine-dependent, stochastic or physics model.

**Timing requested** ⇔ at least one declared operation carries a `duration_min` key.

**Prerequisites.** Every operation has a valid `duration_min`, and every step has an assigned machine (RM9). If any
fails, **no timeline value of any kind** is written — no default, estimate, partial timeline or fake start/end — and
`timeline_issues(design_input, plan)` reports each missing prerequisite (`"step i (op): duration_min missing"`,
`"... invalid (<value>); must be an integer >= 1"`, `"... no machine assigned"`). RM9's manufacturability verdict is
untouched (status, reason codes, `detail`, version). The report is derivable from the persisted episode (its design
input and plan) and is printed by the CLI.

**Timeline (derived by Mini Prometheus, serialized).** For step `i` in plan order:
`start_0 = 0`, `start_i = end_(i-1)`, `end_i = start_i + duration_i`, `lead_time = end_last`. Exact integer
arithmetic. Recorded in the open `ProcessStep.params`:

| Key | Kind | Where |
|---|---|---|
| `duration_min` | input (the declared value, copied) | every step |
| `schedule_start_min`, `schedule_end_min` | derived | every step |
| `schedule_lead_time_min` | derived | final step only |

Start/end values supplied in a request are never read (input vs derived separation).

**Verifier (only when the plan carries timeline data).** Inconsistent → `PLAN_MALFORMED`, status `PLAN_INVALID`:
timeline not on every step; non-integer minutes; duration < 1; first start ≠ 0; end ≠ start + duration; next start ≠
previous end; an unassigned step; lead time missing, ≠ final end, or present on a non-final step.

**Versioning.** Planner rule `1.3.0` only when a valid timeline was derived. Verifier `1.3.0` only when it evaluated a
carried timeline (a valid one, or a tampered one it rejects — the rule set that produced the finding is recorded).
Requests without timing data keep `1.0.0` / `1.1.0` / `1.2.0` exactly as before.

**Identity / RM2.** Declared durations participate through the existing parameter identity path: same request + same
durations ⇒ same hashes; a changed duration ⇒ a different design identity, plan and reuse key (a fresh, verified run,
not a reuse). RM2 is unchanged.

**CLI.** The existing CLI already passes declared `params`. When timing was requested it prints either
`lead time: N min (single-job serialized timeline)` or `timeline not derived: <issues>`; otherwise the output is RM9's.

**Out of scope.** Multiple jobs, queues, contention, optimization, makespan minimization across jobs, setup/
changeover, calendars, maintenance, partial availability, stochastic times, OR-Tools or any solver, factory/MES
integration, execution/dispatch, typed timing contract fields.

## 3. Exact file scope

Modified: `src/mini_prometheus/manufacturing_planning/planner.py`,
`src/mini_prometheus/manufacturing_constraints/oracle.py`, `src/mini_prometheus/orchestration/runner.py`,
`pyproject.toml` (runtime `0.8.0`), `docs/ROADMAP.md`, `docs/adr/README.md`, `CHANGELOG.md`.
New: this spec, `docs/adr/0012-rm10-acceptance.md`, `docs/milestones/RM10-completion-report.md`,
`tests/fixtures/engineer_request_with_durations.json` (declared test inputs, not manufacturing data),
`tests/rm10_rm9_baseline_probe.py`, `tests/fixtures/rm10_rm9_baseline_golden.json`,
`tests/unit/test_rm10_timeline.py`, `tests/unit/test_rm10_no_duration_zero_diff.py`,
`tests/unit/test_rm10_mutation.py`, `tests/integration/test_rm10_reuse_and_cli.py`.
Untouched: `contracts/**`, `.github/workflows/ci.yml`, `capability_model.py`, intake, integrations, experience,
`reuse_runner.py` (RM2), precedent, judgment, experiment, the RM8 golden/probe/tests, the RM9 tests.

## 4. Invariants

1. `contracts/` byte-identical; `contracts/VERSION == 0.4.0`; no enum member added; no typed timing field.
2. `Verifier.verify(plan, capability_model) -> Verdict` unchanged.
3. Requests without durations are byte-identical to RM9: the RM8 golden (from `rm5-complete`) and the RM10 golden
   (from `rm9-complete`, covering the ECR and availability paths) both pass unchanged.
4. No duration is ever defaulted, estimated or invented; no partial timeline.
5. Deterministic, exact integer arithmetic; identical inputs ⇒ identical outputs.
6. No executor/dispatch runtime, no MP-owned state, no dependency, no solver, no ML, no multi-job logic.

## 5. Verification gate and stop condition

Docker verifier (Python 3.11): `pytest -q`, the RM8 and RM10 zero-diff goldens, `mypy src`, `lint-imports`,
contract drift, the CI git gates, and true-source mutations — T1 missing duration defaults to zero, T2 start chain
shifted by one, T3 consistency check removed — each failing the gate through named tests (RM8 M1/M2 and RM9 M3–M5
re-run). One commit; the complete gate re-run on the committed tree; clean tree; no push without authorization.
