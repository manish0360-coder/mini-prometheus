# RM8 Completion Report — Engineering Constraint Reasoning (ECR)

- **Milestone:** RM8. **Identity:** Engineering Constraint Reasoning — declared operation precedence and tolerance
  feasibility in the manufacturability oracle.
- **Status:** ✅ Complete — 2026-09-26. Runtime `0.6.0`. Tag: pending `rm8-complete`.
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged** — no contract, schema or enum change).
- **Record:** spec `specs/milestones/RM8-engineering-constraint-reasoning.md`; ADR-0010; this report.

## 1. What RM8 delivered

The manufacturability oracle now checks two things it previously could not, for the machined-part domain, when run
with the constrained capability model (`constrained_model()`, capability model `1.1.0`; CLI
`--capability-model constrained`):

| Check | Rule | Outcome |
|---|---|---|
| Declared precedence | a declared "A before B" pair (stock-cut before every operation; every operation before inspection) is violated by the routing | `PLAN_INVALID` + `PRECEDENCE_VIOLATION` |
| Tolerance feasibility | the requested general tolerance is strictly tighter than the minimum of the process capability assigned to a tolerance-bearing step (lathe 0.01, mill 0.02, drill 0.05 mm) | `NOT_MANUFACTURABLE` + `TOLERANCE_UNSUPPORTED` |

All findings are reported together (with the existing capability/material findings); `PLAN_INVALID` dominates.
Worked examples on the engineer fixture (cut stock → face mill → drill ×2 → deburr → inspect, aluminum):

| Request | Constrained verdict |
|---|---|
| tolerance 0.1 mm | `MANUFACTURABLE` |
| tolerance 0.05 mm (= drill minimum) | `MANUFACTURABLE` |
| tolerance 0.03 mm | `NOT_MANUFACTURABLE` [`TOLERANCE_UNSUPPORTED`] |
| inspection first, tolerance 0.001 mm | `PLAN_INVALID` [`PRECEDENCE_VIOLATION`, `TOLERANCE_UNSUPPORTED`] |
| same request, **default** CLI | `MANUFACTURABLE` — legacy behavior, no tolerance/precedence reasoning (documented limitation) |

Every verdict is grounded and logged as a `ManufacturingEpisode`; the verifier records version `1.1.0` and the
planner rule version `1.1.0` when a tolerance is carried.

## 2. What did not change

- **Default-model behavior** is byte-identical to `rm5-complete`: 902 fully serialized plans/verdicts/episodes and
  their hashes (451 requests × {default model, RM5 regime R*}), the legacy CLI on two request JSONs, and the whole
  `contracts/` tree, against a golden generated once from `rm5-complete` and frozen by digest.
- Contracts, the `Verifier` signature, the closed taxonomies, intake, integrations, precedent (RM3), judgment (RM4),
  experience (RM2), the RM5 experiment and its fixture. No dependency, no ML, no MiniFlyWire/FutureScore, no
  Velith/Noetica change. No Situation State component (CAP-0001).

## 3. Provenance

| Item | Value |
|---|---|
| C1 (adopted after read-only audit, folded in) | `ad90856c2e13ae9922b299c5fca4c71fd01459ad` (local, never pushed) |
| Baseline | `rm5-complete` = `96eb81f25c8a89d6a33a064c3c1e18c48b9d260f` |
| Behavioral golden | `tests/fixtures/rm8_default_behavior_golden.json`, sha256 (LF) `f36c5d4be10da83d8669c5036ecf36d607e699b3129e9075f14426ac606ffa02` |
| Generating probe | `tests/rm8_behavior_probe.py`, sha256 (LF) `47a218c63e25060617a43d393163f9aedffafc7d960071dbdda495dd0f38bb4c` |
| Toolchain | project Docker verifier (`docker/verifier.Dockerfile`, `python:3.11-slim-bookworm`) |

## 4. Verification (pre-commit, Docker verifier, Python 3.11)

| Gate | Baseline `rm5-complete` | C1 | RM8 |
|---|---|---|---|
| `pytest -q` | 166 passed | 171 passed | **214 passed** (166 legacy + 5 C1 + 43 RM8) |
| RM8 behavioral zero-diff | — | golden reproduced | **3/3 passed** |
| `mypy src` | clean | clean | **clean** |
| import-linter | 3/3 kept | 3/3 kept | **3/3 kept** |
| contract drift | none | none | **none** |
| RM1/RM2 byte gate (as amended, ADR-0010) | pass | — | **pass**; control: a change to another file in the directory is still caught |
| RM3/RM4 byte gate | pass | pass | **pass** |
| Mutation M1 — remove the declared-precedence check (real source) | — | — | **gate fails** (7 named tests) |
| Mutation M2 — tolerance `<` → `<=` (real source) | — | — | **gate fails** (3 named tests) |

Advisory ruff: the RM8 production lines are within the 100-column standard; pre-existing findings are unchanged.

## 5. Limitations (stated, not hidden)

- The legacy default CLI does not read `tolerances` and does no tolerance or precedence reasoning.
- The tolerance model is one coarse scalar per capability and one general tolerance per request — no feature-level
  tolerances, GD&T, geometry, fixturing or empirical process capability; no real-world tolerance claim.
- The declared precedence set is minimal (stock-cut first, inspection last); inter-machining order is not modelled.
- `RESOURCE_UNAVAILABLE`, scheduling and resource allocation remain out of scope.
