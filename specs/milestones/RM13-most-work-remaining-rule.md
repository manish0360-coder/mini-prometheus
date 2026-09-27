# RM13 Specification — Opt-In Most-Work-Remaining Tie-Break Rule

- **Status:** Frozen (Director approval, 2026-09-27; accepted in ADR-0016). Specification of record.
- **Milestone:** RM13. **Baseline:** RM12 (`rm12-complete`, `23e3b6d`).
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** a bounded, **opt-in** scheduling-rule comparison. One new, separately named rule,
  `earliest_start_v1_most_work_remaining`, that differs from `earliest_start_v1` only in how it breaks **exact**
  earliest-start ties. **Supported for opt-in evaluation on a frozen synthetic corpus — not promoted, not a default,
  not an optimizer, no claim about real-factory performance.**
- **Immovable:** the default rule `earliest_start_v1` (every RM11/RM12 golden and identity byte-identical); RM12
  downtime semantics; RM9 machine assignments; contracts (`0.4.0`); no solver, no Giffler–Thompson, no tuning.

---

## 1. Evidence (Pass 1, read-only)

On the 135 tiny instances of the RM12 adversarial audit, with exhaustive optima: `earliest_start_v1` is optimal in
124/135 (42/53 contended). Root cause of the 11 failures (every tie resolution and every active-schedule choice
enumerated): 8 are **tie-break** failures (some tie resolution reaches the optimum — two operations ready at the same
minute on a shared machine), 3 are **earliest-start commitment** failures (no tie-break reaches the optimum; an
active-schedule method could), 0 lie beyond active schedules. A diagnostic most-work-remaining tie-break repaired
exactly the 8 tie cases. Giffler–Thompson was not justified (3 cases; reachability is not a rule).

## 2. The rule (frozen)

`earliest_start_v1_most_work_remaining` is `earliest_start_v1` (RM11, with RM12 downtime) with step 4 replaced:

```
earliest feasible start S (RM12 earliest fit around the assigned machine's downtime) is computed first;
select the candidate with the smallest S;
ONLY among candidates with exactly that S:
    1. maximum remaining_work;
    2. request_id ascending;
    3. step_index ascending.
```

It **never** selects a later-starting candidate over an earlier-starting one (the decision key is
`(S, -remaining_work, request_id, step_index)`; for `earliest_start_v1` the second term is a constant 0, which is
exactly the RM11 order).

`remaining_work(job, decision point) = duration_min(candidate) + Σ duration_min(every later unscheduled operation of
that job)` — RM10 durations only; **no** downtime, waiting, machine idle, calendar delay, setup or future availability.
It is processing workload, not elapsed time.

Under relevant downtime the rule is recorded as `earliest_start_v1_most_work_remaining_downtime` (RM12 semantics
exactly: downtime shapes S; the tie-break applies only after S; no rerouting, reassignment or gap insertion). Rule
version `1.0.0`. Model assumptions, lower bounds, checker and all-or-nothing refusals are RM11/RM12's unchanged.

## 3. Selection and default (frozen)

- API: `schedule_requests(..., rule="earliest_start_v1_most_work_remaining")` /
  `schedule_job_set(..., rule=...)`; CLI `--rule earliest_start_v1_most_work_remaining`.
- Selectable: `earliest_start_v1` (default) and `earliest_start_v1_most_work_remaining`. Anything else (including
  the `_downtime` provenance ids) raises `UnknownSchedulingRuleError` before planning; CLI exit 2.
- The rule id is part of `schedule_input_identity`, so the opt-in rule has its own identity even when its placements
  equal the default's; the default identities are unchanged.

## 4. RM13_REGRESSION_CORPUS_01 (frozen)

> "This is a synthetic algorithm-regression corpus. It is not representative evidence of factory performance."

`tests/fixtures/rm13_regression_corpus_01.json`: the exact 135 audit instances (case ids 0–134 as in the Pass-1
measurement), each with its jobs (request id, operations with declared durations), its downtime input, its exhaustive
optimum and its contention flag. Pinned: file digest `cdafd164…`, input digest `d0d9927b…`, optimum digest
`734f7718…`. Every optimum is re-derived by an independent exhaustive search in the test (ground truth proven, not
merely pinned). Not a production benchmark.

## 5. Frozen metrics (both rules; absolute gaps in minutes)

| Metric | `earliest_start_v1` | `earliest_start_v1_most_work_remaining` |
|---|---|---|
| exact-optimal overall | 124/135 | **131/135** |
| exact-optimal under contention | 42/53 | **49/53** |
| median / max absolute gap | 0 / 32 | 0 / 32 |
| median / max relative gap | 0 / 64% (32/50) | 0 / 64% (32/50) |
| misses (case: gap) | 7:20, 23:3, 32:12, 46:9, 56:6, 72:3, 76:8, 91:10, 101:32, 105:18, 115:15 | 72:3, 91:5, 101:32, 130:4 |

New rule vs default: improved 9 (7, 23, 32, 46, 56, 76, 91, 105, 115); equal 125; **regression 1 — case 130: 163 → 167
(the default is optimal there; +4 min, documented)**; newly optimal 8 (7, 23, 32, 46, 56, 76, 105, 115 — the tie-break
failures); partially improved 91 (40 → 35, optimum 30); unchanged 72 and 101 (earliest-start commitment failures).
Remaining misses of the new rule: 72, 91, 101, 130.

## 6. Worked examples (hand-computed; the tests assert exactly these)

| Case | Jobs | New rule | Why |
|---|---|---|---|
| tie on saw01 (test 1) | A saw 10 · B saw 10 → mill 100 | B saw [0,10), A saw [10,20), B mill [10,110) = 110 (default 120) | B has 110 min of work vs A's 10 |
| later start never wins (2) | A mill 10 · B saw 5 → mill 100 | A mill [0,10), B saw [0,5), B mill [10,110) | B's mill op is ready only at 5 |
| candidate counted (3) | A saw 30 · B saw 10 → deburr 15 | A first (30 > 25) | |
| later ops counted (4) | A saw 10 · B saw 5 → deburr 3 → inspect 3 | B first (11 > 10) | |
| downtime not counted (5) | A saw 10 → deburr 1 · B saw 5 → inspect 5, cmm01 down [500,520) | A first (11 > 10) | downtime is not work |
| equal work (6) | A saw 10 · B saw 10, passed as [B, A] | A first | request_id |
| RM12 downtime (10) | three jobs, mill01 down [20,45) | makespan 102 (default 103), window-aware bound 77, gap 25 | |

## 7. File scope

New: this spec, `docs/adr/0016-rm13-acceptance.md`, `docs/milestones/RM13-completion-report.md`,
`tests/fixtures/rm13_regression_corpus_01.json`, `tests/unit/test_rm13_{rule,regression_corpus,mutation}.py`,
`tests/integration/test_rm13_cli.py`.
Modified: `manufacturing_scheduling/{model,earliest_start,job_set}.py`, `orchestration/schedule_runner.py`,
`tools/verify_installed_wheel.py` (installed `--rule` check), `pyproject.toml` (runtime `0.11.0`),
`docs/ROADMAP.md`, `docs/adr/README.md`, `CHANGELOG.md`.
Unchanged: contracts, CI, RM1–RM10, the checker, lower bounds, downtime canonicalizer, every RM8–RM12 golden, probe,
fixture and test.

## 8. Verification gate and stop condition

Docker verifier (Python 3.11): full pytest; RM8, RM9/RM10, RM11/RM12 goldens; mypy; import-linter; contract drift; CI
git gates; installed-wheel check; true-source mutants of the new rule (tie-break → request_id, candidate omitted,
later operations omitted, downtime counted, tie-break before start, comparison reversed, request_id fallback removed,
default changed) plus every RM8–RM12 mutant; protected-file check. One commit; post-commit gate; push; tag
`rm13-complete`; GitHub CI; STOP.

## 9. Out of scope

Changing the default; Giffler–Thompson or any active-schedule generation (a new architectural boundary requiring
independent review); solvers/OR-Tools; tuning; new benchmarks or seeds; changeover, calendars; any real-factory claim.
