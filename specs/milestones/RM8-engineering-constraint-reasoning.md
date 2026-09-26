# RM8 Specification — Engineering Constraint Reasoning (ECR)

- **Status:** Frozen (Director design freeze, 2026-09-26; accepted in ADR-0010). Specification of record.
- **Milestone:** RM8 (eighth runtime milestone; RM6 real-Velith and RM7 real-Noetica remain externally blocked).
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** make the existing manufacturability verification materially more real by enforcing **declared
  operation precedence** and **tolerance feasibility**, using reason codes the frozen contract already defines.
- **Immovable:** contracts byte-identical (suite `0.4.0`); the Noetica `Verifier` signature; RM1–RM5 default-model
  behavior byte-identical; ownership (Noetica owns state, Velith owns engineering intelligence, Mini Prometheus owns
  manufacturing intelligence). No new dependency, no ML, no FutureScore, no MiniFlyWire, no Velith/Noetica change.

---

## 1. Why this milestone

RM1 already delivers the manufacturing vertical slice `ManufacturingRequest → DesignInput → ProductionPlan →
manufacturability Verdict → ManufacturingEpisode`. Its oracle, however, under-reports its own frozen taxonomy: the
contract defines `TOLERANCE_UNSUPPORTED`, but RM1 never emits it, and RM1's `PRECEDENCE_VIOLATION` only detects
non-contiguous step numbering — not a real operation-order error. RM8 closes that gap for the machined-part domain.

**Situation State (frozen decision).** No Mini Prometheus-owned Situation State component is created (withdrawn by
CAP-0001 / ADR-0004; the state substrate is a Noetica mechanism). The "situation" of a case is represented by the
existing `DesignInput` plus the existing internal `EngineeringSituation` (RM4). RM8 adds no state object.

## 2. C1 adoption audit (read/verify only; accepted)

C1 was a local, unpushed commit `ad90856` ("declarative precedence + tolerance capability-model fields"). Audit:

| Question | Finding |
|---|---|
| API/behavior changes | `ProcessCapabilityModel` gains two defaulted, empty-by-default fields (`capability_tolerance_mm`, `ordering_constraints`); new `MODEL_VERSION_CONSTRAINED = "1.1.0"`, `constrained_model()`, `min_tolerance_for_capability()`; private `_seed_ordering_constraints()`. |
| Schema/contract changes | None (`contracts/` diff vs `rm5-complete` empty; no drift). |
| Dependencies | None (stdlib `dataclasses.field` only). |
| Boundaries | Imports unchanged; import-linter 3/3 contracts kept. |
| Default-model behavior | Unchanged: the model is never serialized (only its `version` string enters identity); RM5's R* sets only the four original fields. Empirically, 902 fully serialized plan/verdict/episode outputs (451 requests × {default, R*}) are byte-identical to `rm5-complete`. |
| Tests / types | `rm5-complete` 166 passed → C1 171 passed; `mypy src` clean on both. |
| Governance | C1 alone breaks the CI byte-freeze of the RM1/RM2 core (it edits `manufacturing_constraints/`). Resolved by the ratified gate evolution in §6. |

C1's implementation is adopted unchanged and folded into the single RM8 commit; its SHA is recorded in ADR-0010.

## 3. Frozen contract of the checks

Both checks are driven **only** by the capability model's declarative constraint data. `default_model()` carries
none, so on the default path both checks are inert and the verifier reports version `1.0.0` exactly as before.
`constrained_model()` (capability model `1.1.0`) carries: `cut_stock` before every other operation, every other
operation before `inspect` (nothing else — deburr vs machining and inter-machining order are free), and minimum
tolerances `cap.lathe 0.01`, `cap.mill 0.02`, `cap.drill 0.05` mm (coarse demo-domain data, not manufacturing law).

**C2 — declared precedence.** For each declared pair (A, B) meaning "A before B": if both operations are present in
the plan and some A step occurs after some B step → `PRECEDENCE_VIOLATION`, status `PLAN_INVALID`. Pairwise only;
unconstrained pairs never fail; self-pairs are ignored. RM1's structural step-numbering check is unchanged.

**C3 — tolerance feasibility (constrained mode only).** The verifier signature `verify(plan, capability_model)` cannot
carry the request, so the planner carries it: when the model has tolerance data and the request states
`tolerances.general_tolerance_mm`, each step whose capability is tolerance-bearing gets
`params["required_tolerance_mm"]` (the step `params` object is already open in the frozen schema). The verifier then:
- requested `<` capability minimum → `TOLERANCE_UNSUPPORTED`, status `NOT_MANUFACTURABLE` (existing member);
- requested `==` or `>` minimum → feasible;
- no requested tolerance → no finding; capability not tolerance-bearing (saw, bench, cmm) → no check.

**Multiple findings.** All applicable findings are reported (sorted reason codes). Status: `PLAN_INVALID` if a
precedence violation exists; otherwise `NOT_MANUFACTURABLE` if any feasibility finding exists (capability, material,
tolerance); otherwise `MANUFACTURABLE`. A tolerance finding is never discarded because precedence also failed.

**Versioning / provenance.** Verifier `produced_by.version`: `1.0.0` on the default path; `1.1.0` whenever the model
carries constraint data. Planner `rule_version`: `1.1.0` only when tolerance data is actually introduced into the
plan, else `1.0.0`. Episode identity is unchanged in construction (it never included the verifier version).

**Out of scope:** `RESOURCE_UNAVAILABLE`, scheduling/resource allocation, geometry or STEP parsing, GD&T,
feature-level tolerance attribution, real-world tolerance claims, external Velith/Noetica integration.

## 4. C4 — CLI

The existing CLI (`python -m mini_prometheus.orchestration.runner <request.json>`) gains
`--capability-model {default,constrained}` (default `default`).
- `default` is the legacy behavior, byte-identical to RM1–RM5. **Known limitation, stated explicitly:** default mode
  performs no tolerance or declared-precedence reasoning, and the legacy CLI does not read the request's
  `tolerances` field at all. Default mode must never be described as doing tolerance reasoning.
- `constrained` uses `constrained_model()` and passes `tolerances.general_tolerance_mm` through to planning and
  verification. No other CLI change.

## 5. Exact file scope

Modified: `src/mini_prometheus/manufacturing_constraints/capability_model.py` (C1, as audited),
`src/mini_prometheus/manufacturing_constraints/oracle.py` (C2, C3, versioning),
`src/mini_prometheus/manufacturing_planning/planner.py` (C3 carriage, rule version),
`src/mini_prometheus/orchestration/runner.py` (C4), `.github/workflows/ci.yml` (§6), `pyproject.toml` (runtime
`0.6.0`), `docs/ROADMAP.md`, `docs/adr/README.md`, `CHANGELOG.md`.
New: this spec, `docs/adr/0010-rm8-acceptance.md`, `docs/milestones/RM8-completion-report.md`,
`tests/rm8_behavior_probe.py`, `tests/fixtures/rm8_default_behavior_golden.json`,
`tests/unit/test_capability_model_ecr.py` (C1), `tests/unit/test_rm8_ecr.py`,
`tests/unit/test_rm8_default_zero_diff.py`, `tests/unit/test_rm8_mutation.py`, `tests/integration/test_rm8_cli.py`,
`tests/boundary/test_rm8_boundaries.py`.
Untouched: `contracts/**`, `_verifier.py`, `_hashing.py`, intake, integrations, precedent, judgment, experience,
experiment, the RM5 fixture.

## 6. Verification gate (ratified gate evolution — Option A)

The CI byte-freeze of the RM1/RM2 core is replaced **only for the four files RM8 modifies** by a committed behavioral
zero-diff gate. The directories stay byte-frozen (pathspec exclusions for exactly those files; any other change or
new file there still fails). All other gates are unchanged. The protected property is that RM1–RM5 default-model
behavior stays byte-identical — not that the source files can never evolve.

The behavioral golden `tests/fixtures/rm8_default_behavior_golden.json`:
- was generated ONCE from `rm5-complete` (`96eb81f`) by `tests/rm8_behavior_probe.py`, inside the project verifier
  image, from a `core.autocrlf=false` export; it records 902 fully serialized plans/verdicts/episodes and their
  hashes (default model and R*), the legacy CLI on two request JSONs, and a digest of the whole `contracts/` tree;
- is frozen by digest (`f36c5d4b…`) in `tests/unit/test_rm8_default_zero_diff.py`, together with the digest of the
  probe that produced it (`47a218c6…`); nothing regenerates it from the current implementation.

Gate: `pytest -q` (all legacy + C1 + RM8 tests), `mypy src`, `lint-imports`, contract drift, contract version
`0.4.0`, the RM1/RM2 byte gate (as amended), the RM3/RM4 byte gate, the RM8 behavioral gate — run in the project
Docker verifier (Python 3.11). Mutation: removing the declared-precedence check and changing `<` to `<=` in the
tolerance comparison must each make the gate fail through named tests (in-suite, and on the real source).

## 7. Stop condition

RM8 is complete when every gate in §6 is green in the Docker verifier, the single RM8 commit is made (C1 folded in),
the complete gate is re-run on the committed tree and passes, and the working tree is clean. Then stop; no push
without separate authorization.

## 8. Invariants (checked)

1. `contracts/` byte-identical; `contracts/VERSION == 0.4.0`; no enum member added.
2. `Verifier.verify(plan, capability_model) -> Verdict` unchanged; the oracle still satisfies the protocol.
3. Default model: every RM1–RM5 plan/verdict/episode and hash byte-identical to `rm5-complete` (golden); RM5
   reproducibility freeze passes.
4. Constrained model: deterministic; plan and episode hashes independent of timestamps.
5. ECR findings are grounded outcomes; an episode is written.
6. Precedence is pairwise over declared pairs only; unconstrained pairs never fail.
7. Tolerance: strict `<` is infeasible; equal/looser feasible; absent or non-bearing → no check.
8. No new dependency, no ML, no FutureScore/MiniFlyWire import, no Velith/Noetica change.
