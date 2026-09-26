# RM9 Specification — Resource Availability

- **Status:** Frozen (Director design freeze, 2026-09-27; accepted in ADR-0011). Specification of record.
- **Milestone:** RM9 (ninth runtime milestone). **Baseline:** RM8 (`rm8-complete`, `0e2cebb`), frozen as the
  current Mini Prometheus manufacturing baseline.
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** declarative, opt-in resource availability. The planner uses only available capable machines and
  reroutes to an available alternative when one exists; when every capable machine is unavailable the verdict is
  `RESOURCE_UNAVAILABLE` (the last never-emitted member of the frozen reason-code taxonomy).
- **Immovable:** contracts byte-identical (suite `0.4.0`); the `Verifier` signature; the RM8 behavioral golden and
  every RM8 outcome; RM2 code; ownership (Noetica owns state, Velith engineering intelligence, Mini Prometheus
  manufacturing intelligence). No scheduling, optimization, ML, dependency, FutureScore, MiniFlyWire, Velith or
  Noetica change.

---

## 1. Audit summary (read-only, before design)

| Question | Finding |
|---|---|
| Representation of machines | `ProcessCapabilityModel.resources: dict[resource_id -> frozenset[capability]]` (internal content, not a contract); default shop `mill01{mill,drill}`, `lathe01`, `saw01`, `bench01`, `cmm01` |
| Assignment | `resource_for_capability` = first provider in sorted order; no provider → step unassigned; `ResourceAssignment` in the plan contract |
| Verifier input | `verify(plan, capability_model)`; RM1 checks only that some provider exists (`CAPABILITY_MISSING`) and never read the plan's assignments |
| `RESOURCE_UNAVAILABLE` | frozen, closed taxonomy member; never emitted before RM9; no further contract semantics |
| Existing availability code | none |
| Assumption | RM1–RM8 assume every machine is available; tests model a "down" machine by deleting it (→ `CAPABILITY_MISSING`), which is unchanged |
| Integration point | the capability model + the shared assignment helper, used by both planner and oracle — all within the four files RM8 already placed under the behavioral gate, so **no CI change** |
| RM2 | reuse key `(design identity, capability_model_version)` cannot see availability; RM2 re-derives the plan on a hit and raises on mismatch — the protection RM9 relies on (RM2 unchanged) |
| Versioning | `capability_model_version` is strict `X.Y.Z` (no build metadata), so availability cannot live in it |

## 2. Frozen semantics

**Input.** `with_unavailable_resources(model, ids)` returns the same model (same `version`) with
`unavailable_resources = ids`. Every id must be a resource of that model; an unknown id raises
`UnknownResourceError` **before planning**. The value is an immutable per-run snapshot: Mini Prometheus never
stores, updates or tracks availability (no MP-owned state substrate). Empty set ⇒ RM1–RM8 behavior exactly.

**Material effect (one shared definition).** Availability materially affects a capability iff the resource RM1
would select for it (first provider in sorted order) exists and is unavailable.

**Planner.**
- Assigns the first *available* provider in the deterministic order (identical to RM1 when nothing relevant is down).
- Reroutes to an available alternative capable machine when the selected one is unavailable.
- Leaves the step unassigned when every capable machine is unavailable.
- Writes `params["unavailable_resources"]` (that capability's unavailable providers only) **only on materially
  affected steps** — never the global list, never on unaffected steps.
- Planning rule version `1.2.0` only when that evidence was written; otherwise `1.1.0`/`1.0.0` as before.

**Verifier.**
- `RESOURCE_UNAVAILABLE` when a required capability is materially affected and no provider is available, or when
  the plan assigns a resource that is unavailable (a stale plan); status `NOT_MANUFACTURABLE`; the responsible
  resources are named in the verdict `detail` (`"RESOURCE_UNAVAILABLE: <ids>"`).
- A capability with no provider in the model stays `CAPABILITY_MISSING` (never `RESOURCE_UNAVAILABLE`).
- All findings are reported together with RM1/RM8 findings; `PLAN_INVALID` still dominates.
- Verifier version `1.2.0` only when availability participates in the plan (a materially affected step or a stale
  assignment); otherwise `1.1.0` (ECR data) or `1.0.0` exactly as before.

**Plan-identity rule (Director).** Availability affects plan identity ONLY when it materially affects the requested
plan. An irrelevant unavailable machine (not selected for any required capability) leaves the plan and the verdict
byte-identical; a reroute or an unassignable step changes the plan.

**RM2.** Availability is not added to the reuse key; RM2 is not modified. (A) irrelevant availability → identical
plan → reuse succeeds; (B) changed selection → different plan → reuse fails closed (`ExperienceConsistencyError`);
(C) a stored plan whose machine is now down → the re-derived plan differs and verifying the stored plan yields
`RESOURCE_UNAVAILABLE` → a stale result is never served.

**CLI.** Repeatable `--unavailable-resource ID` on the existing runner CLI, combinable with
`--capability-model {default,constrained}`; unknown ids → usage error (exit 2) before planning, nothing written.
Without the flag the invocation is RM8's exactly (the legacy default still does not read `tolerances`).

**Out of scope.** Scheduling, time windows, capacity, queueing, optimization, partial availability, maintenance
calendars, MES/factory adapters, and any availability persistence or lifecycle.

## 3. Exact file scope

Modified: `src/mini_prometheus/manufacturing_constraints/capability_model.py`, `.../oracle.py`,
`src/mini_prometheus/manufacturing_planning/planner.py`, `src/mini_prometheus/orchestration/runner.py`,
`pyproject.toml` (runtime `0.7.0`), `docs/ROADMAP.md`, `docs/adr/README.md`, `CHANGELOG.md`.
New: this spec, `docs/adr/0011-rm9-acceptance.md`, `docs/milestones/RM9-completion-report.md`,
`tests/unit/test_rm9_availability.py`, `tests/unit/test_rm9_mutation.py`, `tests/integration/test_rm9_cli.py`,
`tests/integration/test_rm9_reuse_guard.py`.
Untouched: `contracts/**`, `.github/workflows/ci.yml`, `_verifier.py`, `_hashing.py`, intake, integrations,
experience, `orchestration/reuse_runner.py` (RM2), precedent, judgment, experiment, the RM5 fixture, the RM8 golden,
probe and tests.

## 4. Invariants

1. `contracts/` byte-identical; `contracts/VERSION == 0.4.0`; no enum member added.
2. `Verifier.verify(plan, capability_model) -> Verdict` unchanged.
3. The RM8 behavioral golden (generated from `rm5-complete`) still passes unchanged; every RM8 outcome and version is
   unchanged.
4. Irrelevant unavailability changes neither plan nor verdict; relevant unavailability changes the plan.
5. Identical availability (in any order) ⇒ identical plan, verdict and hashes; timestamps never matter.
6. RM2 never serves a stale verdict: identical plan or its existing fail-closed error.
7. No MP-owned availability state; no new dependency, scheduling, optimization, ML, FutureScore, MiniFlyWire,
   Velith or Noetica change.

## 5. Verification gate and stop condition

Docker verifier (Python 3.11): `pytest -q` (all legacy + RM8 + RM9), the RM8 behavioral zero-diff test, `mypy src`,
`lint-imports`, contract drift, the CI git gates (RM1/RM2 as amended by ADR-0010, RM3/RM4, contract version), and
true-source mutation runs — M3 remove the availability finding, M4 planner ignores availability, M5 absent machine
classified as unavailable — each of which must make the gate fail through named tests. One commit; the complete gate
re-run on the committed tree; clean tree; no push without separate authorization.
