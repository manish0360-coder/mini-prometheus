# RM12 Specification — Time-Aware Resource Downtime Scheduling

- **Status:** Frozen (Director final synthesis, 2026-09-27; accepted in ADR-0015). Specification of record.
- **Milestone:** RM12. **Baseline:** RM11 (`rm11-complete`, `40d6066`) + packaging integrity
  (`packaging-integrity-complete`, `a383af1`).
- **Layer:** Mini Prometheus (Layer 4 — Manufacturing Intelligence). Constitution v1.1.0.
- **Identity:** already-assigned machines may have explicit, **finite downtime** during one scheduling run;
  operations on them **wait**. Deterministic, independently checked, with the RM11 lower bound retained and a
  tighter window-aware lower bound added. **Not** positive availability windows, calendars, shifts, maintenance
  policies, MES, live machine state or factory persistence; **not** an optimizer.
- **Immovable:** contracts (suite `0.4.0`); the `Verifier` signature; RM1–RM10; RM2 reuse; **the no-relevant-downtime
  path is byte-identical to RM11** (frozen `rm11-complete` golden); ownership (Handbook §6.8, §6.11).

---

## 1. Audit and review summary

Read-only audit (A–M) and one independent adversarial review (Gemini) were synthesized by the Director. Accepted:
downtime (unavailability) semantics on an unbounded horizon instead of positive availability windows (which make
scheduling a feasibility search and create "impossible" operations); strict canonicalization merging overlapping and
touching intervals; no rerouting (RM9 chooses the machine at planning time); append-only earliest-fit placement; a
relevant-machine identity filter; the RM11 bound retained plus a window-aware machine bound; the independent checker
extended; the RM11 rule id kept when no relevant downtime exists. Everything stays internal (no contract change).

## 2. Downtime model (frozen)

- Per **known** machine: half-open intervals `[start_min, end_min)`, integers, `0 <= start_min < end_min < ∞`,
  relative to schedule origin 0 (no wall-clock time, dates, time zones or calendar objects).
- The machine is **available everywhere else**; the horizon stays unbounded, so every operation with a finite duration
  on a valid assigned machine eventually fits — no "impossible operation" outcome and no new reason code.
- **Invalid input** (negative start, `end <= start` incl. zero length, non-integer incl. `bool`/float/`inf`/`None`/
  strings, malformed pairs, unknown machine ids) raises `InvalidDowntimeError` **before planning** — an invalid
  scheduling input, never a manufacturing verdict or refusal. Unknown machines are rejected, never ignored.
- Downtime is **immutable input to one run**: never saved, updated, polled or read from MES/live state.

## 3. Canonicalization (frozen)

Validate → sort by `start_min` → merge overlapping → merge touching. `[60,120) + [120,180) → [60,180)`;
`[50,100) + [75,130) → [50,130)`. Representation `dict[str, tuple[DowntimeInterval, ...]]`, machines sorted,
intervals sorted, pairwise disjoint and non-touching; machines without intervals omitted.

## 4. RM9 boundary (frozen)

RM9 chooses the machine at planning time. RM12 never reassigns or reroutes: an assigned machine's downtime **delays**
the operation on that machine. (Rerouting would change the `ProductionPlan` and require re-planning/re-verification.)

## 5. Rule `earliest_start_v1_downtime` (frozen)

Recorded **only when relevant downtime exists**; otherwise the rule is `earliest_start_v1` and every output is
byte-identical to RM11. The RM11 rule with one change to step 2:

```
earliest_possible = max(job predecessor completion, assigned machine free time)
S := earliest_possible
for each canonical downtime interval [a, b) of the assigned machine, in order:
    if S + duration <= a: stop                          # fits before it (and every later one)
    if S < b:            S := b                          # [S, S + duration) would intersect: wait
select the smallest S; ties by request_id, then step_index; place [S, S + duration);
set the machine's free time and the job's completion to the end (append-only).
```

Non-preemptive, integer-minute, deterministic, append-only; no gap insertion and no other heuristic. Because the
selection uses the downtime-adjusted start, placements still come in non-decreasing start order, so no idle gap before
a placed operation can later be used by any operation: idle time created by downtime is a property of the baseline.

## 6. Relevance and identity (frozen)

- **Relevant downtime** = canonical downtime of machines assigned to at least one operation of the job set. Downtime on
  an unused machine changes neither the output, nor `schedule_input_identity`, nor `schedule_digest`.
- `schedule_input_identity` = hash of (rule, rule version, capability-model version, canonical job identities, **and
  relevant canonical downtime only when there is some**) — never irrelevant downtime, never a derived output.
- `schedule_digest` = hash of the artifact; the RM12 fields (`downtime`, `window_aware_lower_bound_min`, its binding
  machines) enter the artifact view only under relevant downtime.
- Recorded model assumptions: the RM11 list plus three RM12 items (downtime exactly as declared and available
  elsewhere; operations never overlap downtime and wait; downtime never reroutes).

## 7. Lower bounds (frozen)

- `lower_bound_min` = **LB_RM11** = max(longest job duration, busiest machine total work) — retained, still valid.
- **LB_RM12** = max(LB_RM11, max over relevant-schedule machines of `T_avail(W_m)`), where `T_avail(W)` is the earliest
  `T >= 0` with `T − downtime_inside[0, T) >= W` (a preemptive relaxation), exact integers.
- Under relevant downtime `gap_to_lower_bound_min = makespan − LB_RM12`; `PROVABLY_OPTIMAL` means provably optimal
  **under the frozen RM12 model** only when the gap is 0; otherwise only the gap is stated. Never "optimal schedule",
  "true optimum" or "distance from optimum".

## 8. Worked examples (hand-computed; the tests assert exactly these)

Machines: cut_stock → saw01; face_mill, drill, pocket_mill → mill01; turn → lathe01; deburr → bench01; inspect →
cmm01. `A < B < C` are the RM11 fixture request ids.

### 8.1 Three jobs, mill01 down on [20, 45)

| # | Candidates (downtime-adjusted start) | Chosen | Placed |
|---|---|---|---|
| 1 | A0 saw 0 · B0 saw 0 · C0 saw 0 | A0 | saw01 [0, 10) |
| 2 | A1 mill 10→**45** · B0 saw 10 · C0 saw 10 | B0 (tie → B) | saw01 [10, 15) |
| 3 | A1 45 · B1 lathe 15 · C0 saw 15 | B1 (tie → B) | lathe01 [15, 35) |
| 4 | A1 45 · B2 mill 35→**45** · C0 saw 15 | C0 | saw01 [15, 23) |
| 5 | A1 45 · B2 45 · C1 mill 23→**45** | A1 (tie → A) | mill01 [45, 75) |
| 6 | A2 cmm 75 · B2 mill 75 · C1 mill 75 | A2 (tie → A) | cmm01 [75, 80) |
| 7 | B2 75 · C1 75 | B2 | mill01 [75, 85) |
| 8 | B3 cmm 85 · C1 mill 85 | B3 | cmm01 [85, 90) |
| 9 | C1 85 | C1 | mill01 [85, 97) |
| 10 | C2 bench 97 | C2 | bench01 [97, 103) |

Completions 80 / 90 / 103; **makespan 103**; LB_RM11 **52** (mill01); T_avail(mill01, 52) = 20 before the downtime +
32 after it = **77** → LB_RM12 **77** (mill01); **gap 26**.

### 8.2 Two jobs sharing saw01, saw01 down on [0, 5)

A: saw 10 · B: saw 10 → mill 100. A0 [5, 15), B0 [15, 25), B1 [25, 125): makespan **125**; LB_RM11 110 (job B);
T_avail(saw01, 20) = 25, mill01 100 → LB_RM12 **110**; **gap 15**.

### 8.3 Two independent jobs, mill01 down on [0, 10) and saw01 on [0, 3)

A: mill 100 · B: saw 5 → deburr 5. B0 [3, 8), B1 [8, 13), A0 [10, 110): makespan **110**; LB_RM11 100;
T_avail(mill01, 100) = 110 → LB_RM12 **110**; gap **0** → provably optimal under the RM12 model.

### 8.4 Boundaries (one mill operation)

| Duration | mill01 downtime | Placed | Why |
|---|---|---|---|
| 20 | [20, 30) | [0, 20) | ends exactly at the downtime start (F) |
| 20 | [0, 10) | [10, 30) | starts exactly at the downtime end (G) |
| 20 | [10, 30) | [30, 50) | would cross → shifted to the end (H) |
| 20 | [5, 10), [25, 30) | [30, 50) | shifted twice (I) |
| 10 | [5, 10), [25, 30) | [10, 20) | fits between two intervals (C) |

Three jobs with mill01 down on [40, 45): A1 [10, 40) ends at 40 and B2 [45, 55) starts at 45 — no conflict.

## 9. Checker (extended, still independent)

Given the RAW downtime input, the checker re-derives the relevant canonical downtime itself (event sweep; touching
spans join), and proves in addition to every RM11 property: the recorded downtime equals it (`DOWNTIME_MISMATCH`), no
operation intersects downtime of its machine, half-open (`DOWNTIME_CONFLICT`), and the window-aware bound is exact
(`WINDOW_LOWER_BOUND_MISMATCH`; `T_avail` recomputed as the least fixed point of `T = W + downtime_inside[0, T)`);
the gap is checked against LB_RM12; model assumptions and identity against the downtime in force. The codes form a
separate closed internal enum (`DowntimeIssueCode`), so RM11's `IssueCode` set is unchanged. The checker never imports
the generator, the bound calculator, the job-set gate or the downtime canonicalizer (import-linter). A schedule is
returned only after it passes.

## 10. CLI

`python -m mini_prometheus.orchestration.schedule_runner REQUEST.json ... [--downtime MACHINE:START:END ...]`
(repeatable; integers). Invalid downtime is a usage error (exit 2) before planning. With relevant downtime the report
adds `downtime: …` and `window-aware lower bound: N min (binding: …)`, and the gap line says `PROVABLY OPTIMAL under
the RM12 model` only when the gap is 0; without relevant downtime the report is RM11's, byte for byte.

## 11. File scope

New: `src/mini_prometheus/manufacturing_scheduling/downtime.py`, this spec, `docs/adr/0015-rm12-acceptance.md`,
`docs/milestones/RM12-completion-report.md`, `tests/rm12_rm11_baseline_probe.py`,
`tests/fixtures/rm12_rm11_baseline_golden.json` (generated once from `rm11-complete`),
`tests/unit/test_rm12_{no_downtime_zero_diff,downtime,checker,mutation}.py`, `tests/integration/test_rm12_cli.py`,
`tests/boundary/test_rm12_boundaries.py`.
Modified (extension points): `manufacturing_scheduling/{model,earliest_start,lower_bound,checker,job_set}.py`,
`orchestration/schedule_runner.py`, `tools/verify_installed_wheel.py` (RM12 installed-CLI checks), `pyproject.toml`
(runtime `0.10.0`; the checker-independence contract also forbids the canonicalizer), `docs/ROADMAP.md`,
`docs/adr/README.md`, `CHANGELOG.md`.
Unchanged: `contracts/**`, CI, RM1–RM10 source, every RM8–RM11 golden, probe and test file.

## 12. Invariants

1. No relevant downtime ⇒ byte-identical to `rm11-complete` (rule id/version, identity, digest, schedule, makespan,
   bounds, refusals, CLI) — frozen golden, including downtime on unused machines.
2. Downtime never reroutes; plans and plan identity are untouched; RM2 unchanged.
3. Every schedule returned passes the independent checker; no operation intersects downtime.
4. Deterministic: independent of job order, downtime mapping/interval order, hash seed and clock.
5. Contracts `0.4.0`; no new public schema, `Verdict` code or dependency; nothing persisted or executed.

## 13. Verification gate and stop condition

Docker verifier (Python 3.11): full pytest, every golden (RM8, RM9/RM10, RM11), mypy, import-linter, contract drift,
CI git gates, the installed-wheel check (incl. RM12), true-source mutants D1–D11 (zero survivors), RM8–RM11 mutants
re-run. One commit; full post-commit gate; push; tag `rm12-complete`; GitHub CI. Then STOP — RM13 is chosen from
RM12 evidence.

## 14. Out of scope

Positive availability windows, calendars, shifts, maintenance policies, overtime, stochastic availability, rerouting
or re-planning, gap insertion or any other heuristic, optimization, OR-Tools/CP-SAT, changeover times, MES, live
machine state, persistence, execution, contracts `0.5.0`, RM13.
