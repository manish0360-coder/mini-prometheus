# MP-S1 Completion Report — Declared Shop Capability Model

- **Milestone:** MP-S1. **Identity:** an engineer declares a shop in a validated, versioned file, and every plan
  made under it is bound to the shop's content and evidence basis. A changed shop or evidence basis can never reuse
  an incompatible verdict.
- **Status:** ✅ Complete — 2026-11-06. Runtime `0.13.0`. Contract suite `0.5.0` (additive). Baseline `ee46767`.
  Spec of record: `specs/milestones/MP-S1-declared-shop-capability-model.md` (revision 3.1, frozen).
  Decision: ADR-0022.
- **Evidence class of everything here:** **synthetic**.
  - MP-S1 proves software correctness on synthetic declarations only. It is **not** real-shop validation.
  - MP-E1 (real-world evaluation) stays **blocked** until a participating shop and historical jobs with known
    outcomes exist (ADR-0021 Q5).

## 1. Owner conditions

| # | Condition | Result |
|---|---|---|
| 1 | The reproduced stale-verdict bug is the primary acceptance requirement | **Met.** `test_the_reproduced_stale_verdict_bug_is_fixed` reproduces §1.3 verbatim (same label 1.0.0, aluminium removed). Run 2 is `NOT_MANUFACTURABLE [MATERIAL_UNSUPPORTED]`, `reused=False`. All 10 AC4 variants match a fresh run. |
| 2 | Historical protection | **Met.** No tag, golden, probe, frozen fixture or milestone record was modified. RM1–RM15 goldens and corpora pass. The RM8 902-row golden is reproduced row by row by the declared mirrors. |
| 3 | Scope control | **Met.** Frozen spec only. The pre-authorised reduction (deferring §3.7 guarantee 2) was not used. Six recorded deviations (ADR-0022) are placements and corrections, not features. |
| 4 | Full Docker gate on the exact committed tree | **Met.** See §5 and the commit's verification record. |
| 5 | One milestone commit, with docs | **Met.** Implementation, tests, ADR-0022, this report, the roadmap and the changelog are in one commit. |

## 2. What shipped

- **Contract 0.5.0.** `contracts/schemas/manufacturing/shop_capability_model.schema.json` (new). Optional
  `ProductionPlan.capability_model_ref`, which comes with plan `schema_version` 1.1.0 only when present. Bindings
  are regenerated, and every other 0.4.0 file is byte-identical.
- **Loader** `src/mini_prometheus/shop_declaration/shop_model.py`:
  - schema validation through the frozen registry;
  - 15 closed issue codes, reported as complete, sorted lists;
  - the declared-intent rules;
  - cycle refusal;
  - the two hashes;
  - G2 `require_plan_shop_identity`;
  - the §3.4 presentation line, which never says "verified".

  `orchestration/shop_model_file.py` handles strict JSON file reading.
- **Model:** `ProcessCapabilityModel.source: ShopModelSource | None`. Code models leave it `None`.
- **Guards:**
  - G1 in the planner;
  - G2 in `runner.run` and in `job_set`, per job;
  - G3 in `episode_store_reader`;
  - G4: a 3-part `ReuseKey`;
  - G5: schedule `shop_model_ref` plus the independent checker.
- **Traceability:** `orchestration/verdict_trace.py` (`VerdictTrace`, `trace_run`, `trace_job`). A runner CLI
  trace line; declared-shop scheduling refusals name plan, shop and "no episode".
- **Cross-shop precedent:**
  - a 6th import-linter contract (guarantee 1);
  - `orchestration/precedent_basis.py` with five bases, of which only `SAME_DECLARATION` counts as evidence
    (guarantee 2).
- **CLIs:** `--capability-model-file` on `runner` and `schedule_runner`. The installed-wheel verifier gained three
  MP-S1 checks.
- **Fixtures** (`tests/fixtures/shop_models/`, all synthetic):
  - mirrors of `default_model()`, `constrained_model()` and R*;
  - `three_cell_synthetic`;
  - 10 single-field variants;
  - 15 invalid files, one per issue code.

## 3. Acceptance criteria

| AC | Evidence (tests) | Result |
|---|---|---|
| AC1 history | Full existing suite (696 tests), the RM8 golden library and CLI pins, the RM10–RM14 goldens and corpora | Pass |
| AC2 equivalence | `test_mp_s1_equivalence.py`: **902/902** golden rows (451 × `default`, 451 × `r_star`), read-only, with verdict dict, stripped plan hash and digest, episode hash and digest all equal; constrained mirror live on 451 requests | Pass |
| AC3 identities | `test_mp_s1_shop_model.py`: 14 truth-table rows, tolerance spellings, label-only key behaviour, 50 random permutations, single-field implication property | Pass |
| AC4 no stale reuse | `test_mp_s1_reuse.py`: 10 variants plus the §1.3 bug plus the legacy pin | Pass |
| AC5 typed fail-closed | 15 issue-code fixtures; strict JSON; CLI exit 2 with no store and no `default_model()` call (spy), for both CLIs | Pass |
| AC6 evidence and precedent | AST check that the loader is the only writer; no `shop_declared` fixture; wording checks; five precedent bases; mixed report; frozen report untouched; verdict unaffected by cross-shop precedent | Pass |
| AC7 identity cannot be lost or mismatched | Positive cases for plan, episode, verdict and schedule. Negatives: ref deleted or edited, schema mismatch (G3), injected mismatch (G2), checker missing/different/mixed (G5), mixed-declaration store (G4). Traces for fresh, reuse, infra-error and scheduling, plus four inconsistency refusals | Pass |
| AC8 contract compatibility | `test_mp_s1_gates.py` manifest check; the five evolved boundary tests; drift check (regeneration is idempotent) | Pass |
| AC9 gate | §5 | Pass |

- **New tests:** 116 (shop model 48, mutation 11, equivalence 2, reuse 13, identity 29, precedent basis 8, gates 5).
- **Total:** 812.
- **Mutants:** 11 true-source mutants (T10.1), each caught by a named gate that passes on the real code:
  1. plan loses its ref;
  2. key drops the declaration hash;
  3. key uses the content hash;
  4. G2 skipped;
  5. G3 skipped;
  6. checker ignores the ref;
  7. cycle check skipped;
  8. CLI falls back to the default model;
  9. annotation counts `OTHER_SHOP` as evidence;
  10. trace skips its consistency check;
  11. `display_name` leaks into the hash.

## 4. Deviations from the frozen spec

These are recorded in full in ADR-0022:
1. The loader lives in the new `shop_declaration/` package, to keep the RM2 byte gate exactly as ratified.
2. The AC4 tolerance example values are corrected, because the spec's values were feasible.
3. The `reuse_runner.py` change is two lines.
4. Presentation-only fields are added to `ShopModelSource`.
5. Scheduling imports the ref type through `mini_prometheus`.
6. `contracts/schemas/manufacturing/README.md` is not updated, because it is a frozen 0.4.0 file.

## 5. Verification

The Docker verifier (`mini-prometheus-verifier:rm4`, Python 3.11.18) ran on an exact export of the committed
tree:
- pytest: 812 passed;
- mypy `src`: clean (60 files);
- import-linter: 6 kept, 0 broken;
- installed-wheel verifier: 21/21 PASS, including 3 MP-S1 checks;
- contract drift: none;
- CI byte-freeze diffs against `rm2-complete` (as evolved) and `rm4-complete`: empty;
- the RM8 zero-diff: passed.

Ruff stays advisory. The new source files have zero findings; the new test files have only E501 findings, in
comments and docstrings.

## 6. Known limitations (unchanged by MP-S1, stated plainly)

- **Shop-wide materials.** A machine that cannot process a listed material is not expressible (spec §4.1).
- **Code models keep label-only reuse identity.** The stale hit is still possible between two in-code models with
  equal labels (T4.9). Declared shops are the supported path.
- **Precedent retrieval is unfiltered.** Only the annotation path (`run_precedent_for_shop`) labels it. Callers
  that use the frozen `run_precedent` directly get no label. `PrecedentReport.signal_source_rank` already
  identifies the entry that drove the signal, so a later milestone could use it for exact attribution. MP-S1 keeps
  the frozen conservative any-entry rule.
- **A bare `Verdict` is not traceable on its own.** `VerdictTrace` is the supported form. Scheduling verdicts have
  no episode by RM11 design.
- **No forgery protection.** Hashes detect loss and mismatch, not a consistent forgery. Signing would be Noetica's.
- **No real-shop evidence.** MP-E1 is blocked.
