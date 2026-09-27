# RM12 Completion Report — Time-Aware Resource Downtime Scheduling

- **Milestone:** RM12. **Identity:** explicit, finite downtime on already-assigned machines for one scheduling run;
  operations wait — never rerouted; deterministic, independently checked; RM11 bound retained plus a window-aware
  lower bound. **Not an optimizer; no calendars, MES, live state or persistence.**
- **Status:** ✅ Complete — 2026-09-27. Runtime `0.10.0`. Tag: pending `rm12-complete`. Baseline: RM11
  (`rm11-complete`) + packaging integrity (`packaging-integrity-complete`, `a383af1`).
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged**; schedule and downtime internal).
- **Record:** spec `specs/milestones/RM12-resource-downtime.md`; ADR-0015; this report.

## 1. What RM12 delivered

Three-job fixture with `--downtime mill01:20:45` (hand-computed, spec §8.1):

| Start | End | Machine | Job | Step |
|---|---|---|---|---|
| 0 | 10 | saw01 | A | 0 cut stock |
| 10 | 15 | saw01 | B | 0 cut stock |
| 15 | 35 | lathe01 | B | 1 turn |
| 15 | 23 | saw01 | C | 0 cut stock |
| **45** | 75 | mill01 | A | 1 face mill (waited for the downtime to end) |
| 75 | 80 | cmm01 | A | 2 inspect |
| 75 | 85 | mill01 | B | 2 drill |
| 85 | 90 | cmm01 | B | 3 inspect |
| 85 | 97 | mill01 | C | 1 pocket mill |
| 97 | 103 | bench01 | C | 2 deburr |

Makespan **103** (68 without downtime) · RM11 lower bound 52 · window-aware lower bound **77** (mill01: 20 minutes of
work before the downtime, 32 after) · gap **26**. Rule `earliest_start_v1_downtime`; nothing written.

| Situation | Result |
|---|---|
| no downtime, or downtime only on machines the jobs do not use | byte-identical to `rm11-complete` (rule, identity, digest, schedule, bounds, refusals, CLI) — frozen golden, 13 scenarios |
| overlapping / touching / unsorted / split downtime | canonicalized (merged, sorted) — same schedule and identity |
| operation ending exactly at a downtime start / starting exactly at its end | allowed (half-open) |
| operation that would cross downtime | starts at the downtime end |
| a second idle capable machine | never used — downtime delays, never reroutes |
| unknown machine, zero-length, negative, non-integer or unbounded interval | rejected before planning (`InvalidDowntimeError`; CLI exit 2) |
| gap 0 under downtime | "PROVABLY OPTIMAL under the RM12 model" (independent jobs example: 110 = 110) |
| a schedule with an operation inside downtime | rejected by the independent checker (`DOWNTIME_CONFLICT`); never returned |
| installed wheel | RM12 CLI works from a regular installation; digest equals the repository source |

## 2. How it connects to RM1–RM11

RM12 reuses RM9's machine assignments (never changed), RM10 durations, the RM11 scheduler architecture, tie-break,
checker, identity/digest model, lower bound, CLI and all-or-nothing refusals, and the packaging-integrity install.
Plans, plan identity, RM2 reuse and RM3/RM4 are untouched. RM11's `IssueCode` set and every RM8–RM11 test and golden
are unchanged and pass.

## 3. Evidence (pre-commit, Docker verifier, Python 3.11)

| Gate | Result |
|---|---|
| `pytest -q` | **481 passed** (389 up to packaging + 92 RM12) |
| Goldens: RM8 (`rm5-complete`), RM9/RM10 (`rm9-complete`), RM11 (`rm11-complete`, new) | **10/10** |
| `mypy src` / import-linter / contract drift | clean (50 files) / **5 of 5 kept** / none |
| CI git gates: RM1/RM2 (ADR-0010), RM3/RM4, contract version `0.4.0` | pass |
| Protected files vs `packaging-integrity-complete` (RM1–RM10 source, contracts, CI, RM8–RM11 tests/goldens/probes, packaging) | **0 changed** |
| `tools/verify_installed_wheel.py` (incl. RM12 installed-CLI checks) | all pass |
| `ruff check` on every RM12 file (the frozen probe excepted) | clean |

## 4. Mutation evidence (real source, full suite of 481 per mutant; named cases in `test_rm12_mutation.py`)

| Mutant | Change | Named gate case | Full suite |
|---|---|---|---|
| D1 | downtime collision check removed | `crossing_op_shifted`, `checker_clean_with_downtime` | 34 failed |
| D2 | canonicalization (merging) skipped | `overlapping_merged` | 9 failed |
| D3 | touching intervals not merged | `touching_merged` | 7 failed |
| D4 | wrong boundary semantics (`<` for `<=`) | `ends_exactly_at_downtime_start` | 4 failed |
| D5 | machine rerouting allowed (downtime machines treated as unavailable at planning) | `no_rerouting` | 33 failed |
| D6 | append-only broken (machine free time not advanced to the end) | `left_justified_append_only`, `checker_clean_with_downtime` | 57 failed |
| D7 | irrelevant downtime included in identity | `irrelevant_downtime_ignored` | 5 failed |
| D8 | relevant downtime excluded from identity | `relevant_downtime_changes_identity` | 2 failed |
| D9 | window-aware bound corrupted | `window_bound_exact` | 34 failed |
| D10 | downtime checker removed | `downtime_tamper_detected` | 4 failed |
| D11 | canonical sorting skipped | `unsorted_input_canonical` | 6 failed |

Historical mutants re-run against the RM12 suite — all still caught: RM11 R1–R10 (58, 67, 68, 42, 70, 70, 11, 23, 11,
46), C1–C3 (7, 58, 4), J1–J3 (8, 6, 4); RM8–RM10 M1–M5 (9, 3, 19, 16, 4), T1–T3 (7, 157, 12). **Zero survivors.**

## 5. Remaining scheduling gap (deliberately out of scope)

- **Baseline, not optimized.** Append-only earliest fit; idle time caused by downtime is visible. Whether a different
  rule is worth adopting is an RM13 question to be answered with measured evidence against the lower bounds.
- **Downtime only.** No positive availability windows, calendars, shifts, maintenance policies, overtime or
  stochastic availability; calendars can later compile into relative downtime outside the core.
- **No rerouting or re-planning** around downtime; **no changeover**, capacity > 1, due dates or priorities.
- **Internal only; nothing executed or persisted** (execution integration remains Noetica-owned).
