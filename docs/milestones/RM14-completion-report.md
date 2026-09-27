# RM14 Completion Report — Sequence-Dependent Resource Changeover Scheduling

- **Milestone:** RM14. **Identity:** multi-job scheduling accounts for an explicitly declared, sequence-dependent,
  cross-job machine changeover that occupies the machine before an operation. **Stateless per-run input; refuses to
  invent a changeover time; independently checked; not an optimizer; no claim about real-factory performance.**
- **Status:** ✅ Complete — 2026-09-27. Runtime `0.12.0`. Tag: pending `rm14-complete`. Baseline: RM13
  (`rm13-complete`, `7651699`).
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged**).
- **Record:** spec `specs/milestones/RM14-sequence-dependent-changeover.md`; ADR-0017; this report.

## 1. What RM14 delivered

```
--setup-default saw01:2 --setup-default mill01:6 --setup mill01:face_mill:drill:3
```

On the three-job fixture this records four changeovers — two on saw01 between different jobs' cuts (the machine
default), mill01 face_mill → drill (the transition rule, 3 min) and drill → pocket_mill (the default, 6 min) — and a
makespan of **77** (68 without changeover), lower bound 52, gap 25. A job's own consecutive operations never get a
changeover; neither does a machine's first operation. Declaring only `mill01:face_mill:drill:3` refuses the set
because the schedule needs C's pocket_mill after A's face_mill on mill01 (undeclared, no default) — never zero; a
transition the schedule never evaluates needs no declaration. Without relevant setup rules every output is exactly
RM13's.

## 2. Frozen semantics verified

| Item | Evidence |
|---|---|
| transition rule + machine default; explicit beats default | tests B, C, S, T; mutants S4, S5 |
| needed undeclared transition refused (`UNSPECIFIED_SETUP_TRANSITION`), never zero; unused theoretical gaps not refused | tests D (unused gap schedules; needed gap refuses; all-irrelevant machine still refuses; order-independent report); property test; mutants S2, S3 |
| cross-job only; none within a job; none before a machine's first operation | tests F, G; property invariants 7, 8; mutant S6 |
| setup starts no earlier than the predecessor completes (no anticipation) | test J; checker `SETUP_BEFORE_PREDECESSOR`; mutant S7 |
| setup consumes machine capacity; `setup_end == processing_start`; one non-preemptive block | tests H, I; mutants S1, S9 |
| block never crosses downtime (one or several windows, half-open boundary) | tests K, L, V; mutant S8 |
| RM9 assignment unchanged; RM13 remaining work processing-only; lower bounds unchanged | reroute test, MWKR test, test K bounds |
| identity: relevant rules only, canonical, relevant change changes it | tests M, N, O; mutants S10–S14 |
| no RM14 relevance ⇒ byte-identical RM11/RM12/RM13 | zero-diff gate (frozen rm11-complete golden, RM12 downtime, RM13 corpus both rules) |
| independent checker catches every corruption class | `test_rm14_checker.py`; mutants K1–K9 |

## 3. Evidence (pre-commit, Docker verifier, Python 3.11)

| Gate | Result |
|---|---|
| `pytest -q` | **641 passed** (517 up to RM13 + 124 RM14) |
| RM14 zero-diff: frozen `rm11-complete` golden with no / empty / unshared-machine rules; RM12 downtime cases; all 135 RM13 corpus instances × 2 rules with unshared-machine rules; zero-minute changeovers everywhere leave every corpus placement unchanged (106 contended runs carry changeovers) | pass |
| Property test: 400 seeded instances (365 scheduled, 35 refused): production schedule = independent reference placement for placement and changeover for changeover; 14 invariants asserted without the production checker; refusals = exactly the undeclared transitions the reference rule needs; 4 scheduled sets have an undeclared but never-needed possible transition | pass |
| `mypy src` / import-linter / contract drift | clean (51 files) / **5 of 5 kept** (checker also forbidden the setup-rule module) / none |
| `tools/verify_installed_wheel.py` (incl. installed RM14 run, digest equal to source, invalid-rule usage error) | 18/18 pass |
| `ruff format` / `ruff check` on every RM14-touched file | clean |

## 4. Mutation evidence (real source, full suite of 641 per mutant; named cases in `test_rm14_mutation.py`)

| Mutant | Change | Named gate case | Full suite |
|---|---|---|---|
| S1 | setup consumes no time (processing not shifted) | `setup_occupies_the_machine_before_its_operation` | 32 failed |
| S2 | needed undeclared transition not refused (skipped) | `undeclared_transition_refused` | 8 failed |
| S3 | generator treats an undeclared transition as zero | `generator_never_invents_a_changeover` | 8 failed |
| S4 | default used instead of the explicit rule | `explicit_rule_beats_default` | 17 failed |
| S5 | precedence reversed (default wins) | `explicit_rule_beats_default` | 14 failed |
| S6 | within-job setup allowed | `no_changeover_inside_a_job` | 12 failed |
| S7 | setup may start before the predecessor completes | `no_anticipatory_changeover` | 8 failed |
| S8 | setup may cross downtime (only processing fitted) | `block_avoids_downtime` | 8 failed |
| S9 | one-minute gap between setup and processing | `setup_occupies_the_machine_before_its_operation` | 32 failed |
| S10 | setup identity drops the minutes | `identity_covers_relevant_minutes` | 3 failed |
| S11 | irrelevant transition rules in identity | `only_relevant_rules` | 10 failed |
| S12 | relevant rules excluded from identity | `identity_covers_relevant_minutes` | 4 failed |
| S13 | canonical sort skipped | `canonical_order` | 16 failed |
| S14 | machine default never relevant | `only_relevant_rules` | 30 failed |
| K1 | checker: adjacency check removed | `checker_adjacency` | 3 failed |
| K2 | checker: missing-setup check removed | `checker_missing` | 5 failed |
| K3 | checker: expects setup inside a job | `checker_accepts_valid` | 12 failed |
| K4 | checker: setup-downtime check removed | `checker_setup_downtime` | 3 failed |
| K5 | checker: predecessor check removed | `checker_predecessor` | 3 failed |
| K6 | checker: block-overlap check removed | `checker_overlap` | 3 failed |
| K7 | checker: minutes/transition not compared | `checker_minutes` | 5 failed |
| K8 | checker: interval arithmetic unchecked | `checker_interval_arithmetic` | 4 failed |
| K9 | checker: recorded rules unchecked | `checker_recorded_rules` | 4 failed |

Historical mutants re-run against the RM14 suite — all still caught: RM13 W1–W8 (13, 8, 11, 5, 7, 17,
41, 48); RM12 D1–D11 (53, 15, 13, 7, 53, 116, 10, 2, 52, 4, 11); RM11 R1–R10 (119, 104, 129, 79, 130, 156, 21, 64,
28, 95), C1–C3 (7, 95, 4), J1–J3 (10, 8, 4); RM8–RM10 M1–M5 (9, 3, 21, 18, 4), T1–T3 (7, 264, 12). **Zero survivors
across 66 mutants.**

## 5. Limitations (what RM14 does not settle)

- **Synthetic verification only** — no real changeover times, no factory evidence, no optimality claim.
- The lower bounds ignore changeover (still valid, weaker); a setup-aware bound is a sequencing problem, deferred.
- "Needed" means evaluated as a candidate at a decision (§3 of the spec): an undeclared transition of a candidate that
  is then not chosen still refuses the run; a machine default always suffices.
- Deferred: a declared initial machine state (first-operation setup), opt-in within-job setup, material/tool/fixture-
  aware changeover, setup-aware RM13 remaining work, any setup sequencing optimization.
