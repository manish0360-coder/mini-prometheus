# RM5 Completion Report — Compounding Validation Experiment

- **Milestone:** RM5 (fifth runtime implementation milestone). **Identity:** *Compounding Validation Experiment*.
- **Status:** ✅ Complete and frozen — 2026-09-15. Runtime `0.5.0`. Tag: `rm5-complete`.
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (**unchanged** — RM5 adds no contract/schema).
- **Frozen artifacts:** the executable protocol is `src/mini_prometheus/experiment/` (corpus, partition, protocol,
  arms, runner) + the committed fixture `tests/fixtures/rm5_corpus/`; the measured result is frozen by the
  reproducibility test `tests/unit/test_rm5_reproducibility.py` (report `content_hash` pinned). This report and
  ADR-0009 are the governance record.

## 1. Reprioritization note

The roadmap slot originally labelled "RM5 = wire the real pinned Velith package" was **externally blocked**: Velith
is at `m8-complete` (version `0.0.0`), publishes no consumable release/dist, and exposes no
`EngineeringTask`/`EngineeringResult` API (manufacturing is its decade-scale destination, not its current SWE
vertical). Real-Velith integration therefore moves to **RM6+**. RM5 was reprioritized to the highest-value work
unblocked *today*: a rigorous internal validation of the compounding spine (Constitution §1.7) built entirely from
the frozen RM1–RM4 mechanisms. See the roadmap and ADR-0009.

## 2. What RM5 delivered

A deterministic, read-only **measurement harness** (`experiment/`) that answers one frozen scientific question:

> *Does accumulated verified engineering experience produce measurable improvement in engineering judgment against
> the deterministic RM1 oracle on strictly held-out, analogous-but-non-identical cases within one fixed capability
> regime R*?*

RM5 is a **measurement milestone**, not a new capability: it introduces no cognitive primitive, no public contract,
and no change to RM1–RM4. It composes them read-only:

```
frozen corpus (R* = default_model() minus lathe01), content-addressed held-out partition
  → Arm 1 Cold Start   (empty experience → NONE precedent report → RM4 judgment)
  → Arm 2 No Precedent  (full corpus available, but RM4 receives NONE)      → validity control
  → Arm 3 Full System  (full corpus + the ACTUAL RM3 PrecedentReport → RM4 judgment)
primary causal contrast: Arm 3 − Arm 2   (arms differ ONLY in the precedent input)
```

Assessment↔oracle mapping (frozen): SUPPORTIVE↔MANUFACTURABLE; CAUTIONARY↔NOT_MANUFACTURABLE|PLAN_INVALID;
NEUTRAL = abstention (excluded from agreement, counted in coverage).

## 3. Delivered across the commits

| Commit | Deliverable | Landed |
|---|---|---|
| **C0+C1** | Deterministic corpus generator + content-addressed held-out partition + frozen fixture | `10fca38` |
| **C2–C4** | Frozen evaluation protocol + three arms + compounding runner + **first real measurement** | `2e1118f` |
| **C5** | Experiment-package boundary tests + reproducibility freeze + CI/import-linter gates | `a4d11eb` |
| **C6** | This governance close-out + ADR-0009 + release notes + CHANGELOG + roadmap + `0.5.0` bump | this commit |

## 4. Successful controls (validity established)

- **Arm 1 == Arm 2 exactly: 121/121** analogous held-out cases, **0 mismatches** (critique `content_hash`-level
  equality) — judgment depends solely on the precedent-report input, not latent corpus state.
- **Cross-partition exact duplicates: 0** — content-addressed split by `design_ref.content_hash` with design-level
  integrity; a design never spans the boundary; exact identity is excluded from the analogous measure.
- **Deterministic checkpoint/fixture:** `checkpoint_id = sha256:9aec551ee2f7eecc161fce08728e288151ad7a78a1ed03d4e127a298e4f64ed2`;
  the committed fixture reproduces it (AC8).
- **RM1–RM4 byte integrity:** zero real content change vs `rm4-complete`.
- **Reproducible measurement:** report `content_hash = sha256:2b7c487294e7cd792155a832e2e5f2e73591721e71c2f2314bcf5534ef2b3574`,
  pinned in CI.

## 5. Primary result (exact, frozen)

On the **121** strictly held-out, analogous-but-non-identical cases under R*:

| Quantity | Value |
|---|---|
| Arm 2 (No Precedent) oracle agreement | **76/121** = 0.6281 |
| Arm 3 (Full System) oracle agreement | **118/121** = 0.9752 |
| **Precedent marginal agreement (Arm 3 − Arm 2)** | **+42/121 = +0.3471** |
| NOT-class marginal | **0/76** |
| MANUFACTURABLE-class marginal | **42/45** |

**Decoupling (why the result is non-tautological):** RM4's internal-verdict finding fires CAUTIONARY on adverse
verdicts in *all* arms, so the NOT-class marginal cancels to **0**. The precedent's entire measurable effect
concentrates on **MANUFACTURABLE** held-out cases — exactly where the internal critic is silent and cannot leak the
oracle label. This is a successful diagnostic, not a confounder (Gemini §2, §4: circularity risk **LOW**).

## 6. Coverage, false alarms, duplicates (exact, frozen)

- Precedent coverage — **MANUFACTURABLE 45/45**, **NOT 76/76** (both denominators reported; nonzero both classes).
- **Cautionary false alarms on MANUFACTURABLE controls: 3/45 = 0.0667.**
- Excluded exact duplicates: **0**.

## 7. Experience / "compounding" measurements (marginal gain vs Arm 2)

Deterministic experience subsamples (content-hash prefix), marginal agreement **(Arm 3(N) − Arm 2)** over the same
121 analogous cases:

| N | experience size | Arm 3 agreement | marginal vs Arm 2 |
|---|---|---|---|
| 0 | 0 | 76/121 | **0/121 = 0.0000** |
| 1/4 | 82 | 115/121 | **39/121 = 0.3223** |
| 2/4 | 164 | 119/121 | **43/121 = 0.3554** |
| full | 329 | 118/121 | **42/121 = 0.3471** |

The marginal rises steeply (0 → 0.3223 → 0.3554) then **decreases** at the final step (0.3554 → **0.3471**).
**Because the final step decreases, strict monotonic compounding was NOT demonstrated.** The observed effect is a
**positive finite-corpus precedent effect** (a positive learning effect), not strict monotonic compounding.

## 8. Hypothesis criteria — outcomes as measured

| Criterion | Outcome |
|---|---|
| Arm 1 == Arm 2 exactly | **MET** (121/121) |
| Arm 3 − Arm 2 > 0 (primary precedent-marginal effect) | **MET** (+42/121) |
| Coverage nonzero, both classes, denominators reported | **MET** (45/45, 76/76) |
| **H2 — cautionary false-alarm ceiling = 0 on MANUFACTURABLE controls** (origin: RM4 H1) | **NOT MET** (3/45) |
| **Strict monotonic compounding** | **NOT MET** (final step decreases) |

**H2 and strict monotonicity are VALID SCIENTIFIC FINDINGS, not implementation failures.** The 3 false alarms are
genuine precedent-driven misfires — near-miss designs (differing by one verdict-determining op) whose nearest
strongly-relevant precedent was NOT_MANUFACTURABLE while the query is MANUFACTURABLE. This is a real, measurable
precision/safety trade-off of the deterministic relevance model, and its discovery is a *successful* outcome of the
experiment. The non-monotone tail is a genuine property of the model's learning curve on this corpus. Neither was
"fixed", tuned, or suppressed; the frozen protocol, corpus, and criteria were preserved exactly.

## 9. Statement of Claims (mandatory; frozen from the RM5 specification)

**Supported (within the deterministic oracle-internal experimental world only):**
- A large, causal precedent effect: within R*, adding RM3 precedent information *causes* a substantial improvement
  in RM4's agreement with the RM1 oracle on held-out analogous cases (Arm 3 − Arm 2 ablation).
- Successful decoupling from trivial label leakage (NOT-class marginal 0; effect concentrated on MANUFACTURABLE).
- A measurable precision/safety trade-off (3/45 false alarms).
- A positive finite-corpus precedent effect (positive learning effect) — **not** strict monotonic compounding.

**NOT supported / explicitly out of scope (RM5 claims none of these):**
- real-world manufacturing correctness; true DFM correctness or expertise;
- manufacturing cost or quality improvement;
- superiority to human engineers; deployment readiness;
- that the deterministic oracle equals real manufacturability;
- generalization beyond the fixed regime R* or beyond this synthetic, learnable corpus.

## 10. Independent scientific review (Gemini)

**Verdict:** `SCIENTIFICALLY SOUND AS A LIMITED INTERNAL VALIDATION` (confidence: HIGH). Findings incorporated:
oracle–model circularity **LOW**; near-miss / synthetic-corpus generalization caveat **MEDIUM** (the corpus was
built to be learnable — RM5 proves the system *can* learn under controlled conditions, not how it would perform on
organic real-world data); C2–C4 should remain frozen; **no mandatory correction** before C5/C6; the 3/45 false
alarms and the non-monotone curve are legitimate findings, not bugs; final governance must include the Statement of
Claims and explicitly report unmet H2 / strict-monotonicity — done here (§8, §9). Per Gemini §3, the term
"compounding" is retained only as the **milestone identity**; the *result* is described as a positive
finite-corpus precedent effect.

## 11. Boundaries held (see ADR-0009)

`experiment/` is a **leaf consumer**: no RM1–RM4 module imports it (import-linter + AST test). It composes RM1/RM3/RM4
read-only, adds no contract, and never writes the RM2 episode store — its only sinks are the committed fixture dir and
the gitignored `artifacts/evaluation/`. `partition` and `protocol` are pure. No MiniFlyWire (Law 4), no Noetica store
engine (Law 6), no ML/embeddings. All metrics are exact integer rationals; the report `content_hash` excludes volatile
provenance.

*RM5 is closed. Do not modify unless a critical defect is discovered. Do not re-run or tune to change the result.*
