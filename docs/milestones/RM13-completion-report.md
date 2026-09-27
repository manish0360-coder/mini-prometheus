# RM13 Completion Report — Opt-In Most-Work-Remaining Tie-Break Rule

- **Milestone:** RM13. **Identity:** a bounded, opt-in scheduling-rule comparison — `earliest_start_v1_most_work_remaining`
  breaks exact earliest-start ties by remaining processing work. **Supported for opt-in evaluation on a frozen
  synthetic corpus; not the default; not an optimizer; no claim about real-factory performance.**
- **Status:** ✅ Complete — 2026-09-27. Runtime `0.11.0`. Tag: pending `rm13-complete`. Baseline: RM12
  (`rm12-complete`, `23e3b6d`).
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged**).
- **Record:** spec `specs/milestones/RM13-most-work-remaining-rule.md`; ADR-0016; this report.

## 1. What RM13 delivered

`--rule earliest_start_v1_most_work_remaining` (or `rule=` in the API). On the RM11 worked example (A: saw 10; B: saw
10 → mill 100) the tie at t = 0 on saw01 goes to B, which has 110 minutes of work left: makespan **110** (the optimum)
instead of 120. On the three-job fixture: 67 instead of 68 (102 instead of 103 with mill01 down on [20, 45)). Without
`--rule` every output is exactly RM11/RM12's.

## 2. Evidence on RM13_REGRESSION_CORPUS_01

> "This is a synthetic algorithm-regression corpus. It is not representative evidence of factory performance."

| Metric (135 cases, exhaustive optima) | `earliest_start_v1` | `earliest_start_v1_most_work_remaining` |
|---|---|---|
| exact-optimal overall | 124 | **131** |
| exact-optimal under contention (53) | 42 | **49** |
| median / max absolute gap (min) | 0 / 32 | 0 / 32 |
| median / max relative gap | 0 / 64% | 0 / 64% |

- Original baseline failures: 7, 23, 32, 46, 56, 72, 76, 91, 101, 105, 115.
- Repaired (newly optimal): 7, 23, 32, 46, 56, 76, 105, 115 — the 8 tie-break failures.
- Partially improved: 91 (40 → 35; optimum 30). Unchanged: 72, 101 (earliest-start commitment failures).
- **Regression: case 130, 163 → 167** (the default is optimal there).
- Improved 9 · equal 125 · regressions 1. Remaining misses of the new rule: 72, 91, 101, 130.

## 3. Evidence (pre-commit, Docker verifier, Python 3.11)

| Gate | Result |
|---|---|
| `pytest -q` | **517 passed** (481 up to RM12 + 36 RM13) |
| Goldens: RM8, RM9/RM10, RM11/RM12 (no-downtime `rm11-complete` golden) + RM13 corpus (digests, re-derived optima, metrics) | **13/13** |
| `mypy src` / import-linter / contract drift | clean (50 files) / **5 of 5 kept** / none |
| CI git gates: RM1/RM2 (ADR-0010), RM3/RM4, contract version `0.4.0` | pass |
| Protected files vs `rm12-complete` (RM1–RM10 source, checker, lower bounds, downtime canonicalizer, contracts, CI, every RM8–RM12 test/golden/probe/fixture, packaging) | **0 changed** |
| `tools/verify_installed_wheel.py` (incl. the installed `--rule` check) | all pass |
| `ruff check` on every RM13 file | clean |

## 4. Mutation evidence (real source, full suite of 517 per mutant; named cases in `test_rm13_mutation.py`)

| Mutant | Change | Named gate case | Full suite |
|---|---|---|---|
| W1 | tie-break replaced by request_id | `tie_uses_remaining_work` | 12 failed |
| W2 | candidate duration omitted from remaining work | `remaining_work_includes_candidate` | 7 failed |
| W3 | later operations omitted from remaining work | `remaining_work_includes_later_ops` | 9 failed |
| W4 | downtime included in remaining work | `remaining_work_excludes_downtime` | 4 failed |
| W5 | tie-break applied before the earliest-start comparison | `later_start_never_preferred` | 6 failed |
| W6 | remaining-work comparison reversed | `tie_uses_remaining_work` | 15 failed |
| W7 | request_id fallback removed | `equal_work_falls_back_to_request_id` | 31 failed |
| W8 | default rule changed to the new rule | `default_rule_is_earliest_start_v1` | 29 failed |

Historical mutants re-run against the RM13 suite — all still caught: RM12 D1–D11 (41, 10, 8, 5, 40, 77, 6, 2, 41, 4, 7);
RM11 R1–R10 (79, 84, 86, 54, 89, 92, 15, 36, 23, 62), C1–C3 (7, 76, 4), J1–J3 (8, 6, 4); RM8–RM10 M1–M5 (9, 3, 19, 16, 4),
T1–T3 (7, 174, 12). **Zero survivors across 43 mutants.**

## 5. What RM13 does not settle

- **Not a promotion.** 131 > 124 on a synthetic corpus supports opt-in evaluation only; changing the default needs a
  separate decision on broader evidence.
- **Remaining misses:** 72, 91, 101 (earliest-start commitment — reachable only by an active-schedule method, a new
  architectural boundary that needs independent review) and the case-130 regression.
- No Giffler–Thompson, solver, tuning, changeover or calendars; no real-factory performance claim.
