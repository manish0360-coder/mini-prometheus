# RM15 Completion Report — Enriched-Oracle Compounding Re-Measurement (retrospective)

- **Milestone:** RM15. **Identity:** a deterministic, read-only re-run of the frozen RM5 compounding protocol on a
  new synthetic corpus whose verdicts come from the RM8 `constrained_model()` (declared precedence and scalar
  tolerance minimums) instead of RM5's `R*` regime. **This is a measurement milestone. It is not the real-Velith
  integration, which remains RM6 (ADR-0009).**
- **Status:** ✅ Measured and reproduced. The pre-registered result is **mixed**: H1 and H3 met; **H2 and H4 not met**.
  This report records that result. It does not present the experiment as a success.
- **Record type:** retrospective, written 2026-11-06 in Stage 0 record reconciliation (ADR-0019, ADR-0021). The
  implementation commits carry no message body. The RM15 specification and "RM15 governance" / "§B audit" notes that
  the source docstrings cite are **not in the repository**. This report is built only from source, tests, the tag and
  the measurement output.
- **Constitution in force:** v1.1.0. Contract suite `0.4.0` (unchanged). Runtime `0.12.0` (unchanged).
- **Evidence:** `docs/milestones/evidence/rm15_report.json` (the original measurement output, byte-identical copy).

## 1. Implementation history (from Git)

| Step | Commit | Date (IST) | Content |
|---|---|---|---|
| EC1 | `30d8785` | 2026-10-16 15:35 | `experiment/enriched_corpus.py` generator; frozen fixture `tests/fixtures/rm15_corpus/` (960 episodes, partition, checkpoint); `test_enriched_corpus.py` (6 tests). Tag `rm15-corpus-frozen` points here. |
| EC2 | `11a8c59` | 2026-10-16 18:10 | `test_rm15_protocol_compat.py` (5 tests): the frozen RM5 protocol maps enriched verdicts |
| EC3 | `f2892ba` | 2026-10-16 21:23 | `test_rm15_harness_binding.py` (5 tests): AST-verified harness wiring before measurement |
| EC4 | `6571d84` | 2026-10-16 23:19 | `experiment/enriched_runner.py`; `test_rm15_enriched_runner.py` (22 tests). Composes frozen RM5 modules by import; modifies none. |
| Run | — | 2026-10-17 00:58 (`produced_at` 2026-10-16T19:28:45Z) | Measurement executed locally; output written to the gitignored `artifacts/evaluation/rm15_report.json` |

No RM1–RM14 source, contract, schema, CI or dependency changed. `experiment/` remains a leaf (import-linter contract
"RM5 experiment is a leaf consumer" kept).

## 2. Reproduction (Stage 0, 2026-11-06)

The measurement was re-run once in the authoritative Docker verifier against an exact export of HEAD:

```
git archive ab8cc44 | tar -x -C <scratch>/head
docker run --rm --network none -v <scratch>/head:/work:ro -v <scratch>/out:/out \
  mini-prometheus-verifier:rm4  python -c "... enriched_runner.run(); write_report(rep, '/out')"
Python 3.11.18; imports resolved to /work/src; run time 9.1 s
content_hash = sha256:e00acabaaa69f4bd69a5d159a56ffb29d8f201dcebe32aa909ed841ddedf5085   validity_passed = True
```

A field-by-field comparison with the original report found **one difference only:** `provenance.produced_at`
(2026-10-16T19:28:45.411592Z → 2026-11-06T05:12:10.359887Z). That field is excluded from the report's identity by
design. The identity `content_hash` is equal, so the measurement is **reproducible**. The original file is preserved
unchanged (sha256 `f4f61166aff87709e93bc315aecac08152fe13955ae2c8775927193416725a61`) and is the copy committed as
evidence.

The original run happened after EC4 and before RDAI-1. RDAI-1 (`abbc1b8`, `ab8cc44`) touches only
`artifact_intake/` and tests, which the experiment does not import. This is consistent with the identical hash.

## 3. Regime and corpus

- Capability regime: `constrained_model()` v1.1.0 (default resources plus 11 declared ordering pairs plus tolerance
  minimums lathe 0.01, mill 0.02, drill 0.05 mm).
- Corpus: 960 synthetic episodes → 731 experience / 229 held-out (checkpoint
  `sha256:11c039a9…cb4d6`, matches the committed checkpoint). 229 held-out cases are analogous; 0 exact duplicates
  excluded. Held-out classes: 70 MANUFACTURABLE controls, 159 not-manufacturable.
- Versions: critic model 1.0.0, precedent model 1.0.0, evaluation protocol 1.0.0, enriched generator 1.0.0, RM15
  runner 1.0.0.

## 4. Pre-registered hypotheses

| Hypothesis | Criterion | Value | Met |
|---|---|---|---|
| H1 | primary (b−c)/n > 0 on held-out analogous MANUFACTURABLE | 67/70 | **Yes**, with the caveat in §5 |
| H2 | zero cautionary false alarms on MANUFACTURABLE controls (origin: RM4 H1) | 3/70 | **No** |
| H3 | precedent coverage > 0 for both verdict classes | 70/70 and 159/159 | Yes |
| H4 | marginal non-decreasing in experience size | 0 → 65 → 63 → 67 (of 229) | **No** |

Validity gates (all passed): Arm 1 = Arm 2 exactly (0 mismatches); both verdict classes present; no cross-partition
exact duplicates; checkpoint matches committed; analogous set non-empty; partition disjoint and covering; primary
subset has Arm 2 abstaining with c = 0.

Other metrics: status-class agreement Arm 1 159/229, Arm 2 159/229, Arm 3 226/229; aggregate marginal 67/229. The
per-axis marginals on the not-manufacturable axes are all zero: material 0/38, precedence 0/35, tolerance 0/21. The
first two of these are flagged as similarity-confounded.

Reason-aligned agreement was **not measured**. The runner records it as `measured: false` because no defensible
mapping from frozen RM4 findings to oracle reason codes exists.

## 5. What this result does and does not show

- **H1 is weaker than "met" suggests.** On the MANUFACTURABLE subset the Arm 2 baseline structurally abstains, so
  c = 0 by construction and 67/70 is Arm 3's one-sample agreement rate against an abstaining baseline. It is not a
  paired-classifier improvement. The runner and the report's `statement_of_claims` say this explicitly.
- **The precedent effect is confined to the MANUFACTURABLE class**, as in RM5. On every not-manufacturable axis the
  marginal is zero, because the oracle verdict is already correct in all arms there.
- **H2 fails again** (3/70; RM5 had 3/45). Judgment still raises cautionary findings on cases the oracle accepts.
  The three cases have not been analysed. That analysis is the obvious next scientific step before any change to
  judgment.
- **H4 fails.** The curve dips at half the experience (65 → 63) before recovering (67). Compounding is not monotone
  in this corpus.
- **Scope.** The enriched oracle rules are synthetic, declared-model rules. Nothing here validates real-world
  manufacturing performance or generalises beyond this fixed regime and corpus.

## 6. Verification evidence

- RM15 tests: 38 test functions across the four files above. All pass in the full gate.
- Full gate at HEAD in the Docker verifier (Stage 0 audit, 2026-11-06): pytest 696 passed; mypy `src` clean
  (55 files); import-linter 5 kept, 0 broken.
- Independent review of RM15: **none recorded.**

## 7. Not done

No completion ADR existed before this retrospective, and the RM15 specification is not in the repository. No
analysis of the three H2 false alarms exists. No independent review exists.
