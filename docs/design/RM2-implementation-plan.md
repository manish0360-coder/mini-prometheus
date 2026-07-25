# RM2 Implementation Plan — Experience Read-Back & Idempotent Reuse

- **Status:** ✅ **EXECUTED & COMPLETE (RM2, `rm2-complete`, 2026-07-25)** — all five milestones (M1–M5) delivered
  as written; 50 tests pass. See `docs/milestones/RM2-completion-report.md`.
- **Status (original):** Execution-ready. Derived from the **frozen** RM2 spec (`specs/milestones/RM2-experience-reuse.md`)
  and engineering package (`docs/design/RM2-engineering-package.md`). **No architectural decisions remain open.**
- **Invariants (non-negotiable):** RM1 is frozen (zero diff to any RM1 file); no new published contracts
  (`contracts/VERSION` stays `0.2.0`); no MiniFlyWire import (Law 4); no Noetica store/retention engine (Law 6);
  every milestone leaves the **entire** suite green (RM1 + RM2).
- **This document is documentation only** — it changes no code and no frozen artifact.

---

## 0. Pre-decided engineering choices (nothing is left for implementation time)

Every choice below is **fixed**. An implementer executes them verbatim; no discussion required.

1. **Deserialization** (JSONL → `ManufacturingEpisode`): an **explicit, per-type reconstructor** inside the
   reader (private builders `_episode/_task/_product_intent/_plan/_step/_assignment/_verdict/_provenance/_produced_by/_ref/_timing`).
   No generic reflection, no new dependency. Enum conversions — and **only** these two: episode
   `engineering_verification_status` → `EngineeringVerificationStatus(value)`; each `ProcessStep.op` →
   `ProcessOp(value)`. `verdict.status` stays a plain `str` (it is a `str` in the contract).
2. **Integrity on load:** after reconstruction, recompute `content_hash(episode_identity(episode))` and assert it
   equals the stored `content_hash`; mismatch → raise `EpisodeIntegrityError`. A **missing** store path → return `[]`.
3. **Reuse key (composite):** `ReuseKey = (design_input_identity_hash, capability_model_version)`.
   - from a new request: `( content_hash(design_input_identity(design_input)), model.version )`.
   - from a stored episode: `( episode.design_ref.content_hash, episode.capability_model_version )`.
   These are equal exactly when the intent **and** the capability model match.
4. **Reuse semantics:** on a hit, return the **stored** (reconstructed) `plan` + `verdict`; **write no episode**
   (idempotent). On a miss, delegate to RM1's unchanged `runner.run`, which logs a new episode.
5. **Reproducibility guard:** default **on** (`verify_reuse=True`). On a hit, recompute the plan via
   `planner.plan(design_input, model)` and assert `plan.content_hash == stored episode.plan.content_hash`;
   mismatch → raise `ExperienceConsistencyError`. Verdict determinism follows from `(plan, model_version)`, so the
   plan-hash guard is sufficient — the verdict is **not** separately recomputed.
6. **Placement (RM1 zero-diff):** `run_with_reuse` lives in a **new file** `orchestration/reuse_runner.py`.
   RM1's `runner.py` and every other RM1 module are **byte-unchanged**.
7. **Result type:** `ReuseRunResult` mirrors RM1's `RunResult` fields plus `reused: bool` and
   `source_episode: Ref | None`. Internal, never persisted.
8. **Store path:** default = RM1's `orchestration.episode_store.DEFAULT_STORE` (reuse the same constant; do not
   redefine it).
9. **No contracts change:** reuse frozen `ManufacturingEpisode/ProductionPlan/Verdict/DesignInput/Ref`.
10. **Close-out version:** runtime `0.2.0 → 0.3.0`; `contracts/VERSION` and `constitution/VERSION` unchanged;
    tag `rm2-complete`.

**RM1 file set (must remain zero-diff vs tag `rm1-complete`):**
`src/mini_prometheus/{_contracts.py,_hashing.py,_validate.py,_provenance.py,_verifier.py,intake/,manufacturing_planning/,manufacturing_constraints/,orchestration/__init__.py,orchestration/runner.py,orchestration/episode_store.py}`
and all of `contracts/`.

## 0.1 Verification commands (run at the end of every milestone)

```
python -m pytest -q                                            # entire suite green (RM1 + RM2)
python -m ruff check src tests tools                           # lint clean
python tools/generate_contracts.py && git diff --exit-code contracts/python   # no binding drift
lint-imports                                                   # import-linter (from M4)
git diff --exit-code rm1-complete -- <RM1 file set above> contracts/          # RM1 + contracts zero-diff (from M4)
```

---

## Milestone RM2-M1 — Episode store reader (read side)

**Objective.** Deterministically read RM1's episode JSONL back into verified `ManufacturingEpisode` objects.

**Files to create.**
- `src/mini_prometheus/experience/__init__.py` — package docstring (opens the read side of the Experience Flow).
- `src/mini_prometheus/experience/episode_store_reader.py` — `load(store_path) -> list[ManufacturingEpisode]`;
  private per-type reconstructors (§0.1); `EpisodeIntegrityError`. *Why:* the read side's foundation; everything
  downstream consumes reconstructed, integrity-checked episodes.
- `tests/unit/test_episode_store_reader.py`. *Why:* proves reconstruction + integrity before anything depends on it.

**Files to modify.** None (no RM1 file, no contract).

**Required tests (exact cases).**
1. Write episodes with RM1's `runner.run` to a `tmp_path` store, then `load` → returns the same count; each
   `content_hash` re-verifies.
2. Round-trip: `to_contract_dict(loaded[i]) == json.loads(line_i)`.
3. Missing store path → `[]`.
4. Tampered line (mutate a hashed field) → raises `EpisodeIntegrityError`.
5. Enum reconstruction: `loaded[0].engineering_verification_status` is `EngineeringVerificationStatus`;
   `loaded[0].plan.steps[0].op` is `ProcessOp`.

**Verification gates.** `pytest tests/unit/test_episode_store_reader.py` green; ruff clean; RM1 suite unchanged;
no RM1/contract file touched.

**Completion criteria.** Reader loads + verifies deterministically; all 5 cases pass; RM1 zero-diff.

**Commit.** `feat(rm2): experience episode store reader (read side)`

---

## Milestone RM2-M2 — Episode index (composite-key retrieval)

**Objective.** Deterministic index and `lookup` by `ReuseKey`.

**Files to create.**
- `src/mini_prometheus/experience/episode_index.py` — `ReuseKey`, `EpisodeIndex.build(episodes)`,
  `EpisodeIndex.lookup(key) -> ManufacturingEpisode | None`. *Why:* retrieval primitive; composite key prevents
  stale-model reuse.
- `tests/unit/test_episode_index.py`. *Why:* proves deterministic hit/miss and key discrimination.

**Files to modify.** None.

**Required tests.**
1. `build` from a list → `lookup(matching key)` returns that episode.
2. `lookup(absent key)` → `None`.
3. Two episodes, same design identity, different `capability_model_version` → distinct keys; each retrievable.
4. Determinism: build twice from the same list → identical lookups.

**Verification gates.** `pytest tests/unit/test_episode_index.py` green; ruff; RM1 unchanged.

**Completion criteria.** Index deterministic; all 4 cases pass.

**Commit.** `feat(rm2): experience episode index (composite-key retrieval)`

---

## Milestone RM2-M3 — Reuse composition + reproducibility guard

**Objective.** `run_with_reuse` composing intake → lookup → (reuse + guard) | RM1 `run`, additively.

**Files to create.**
- `src/mini_prometheus/orchestration/reuse_runner.py` — `ReuseRunResult`, `ExperienceConsistencyError`,
  `run_with_reuse(...)` (exact signature/algorithm in the engineering package §6/§8). *Why:* delivers compounding
  rung-1; new file guarantees RM1 `runner.py` zero-diff.
- `tests/integration/test_experience_reuse.py`. *Why:* proves the end-to-end compounding behavior.

**Files to modify.** None of RM1 (the new file imports RM1 read-only).

**Required tests (exact cases).**
1. **miss → log → hit → reuse:** first `run_with_reuse(req)` → `reused=False`, store has 1 line; second identical
   call → `reused=True`, same `plan.content_hash` and `verdict.status`, store **still 1 line**, `source_episode` set.
2. **different request → miss:** store grows to 2 lines.
3. **guard success:** default `verify_reuse=True` reuse passes on a hit.
4. **guard failure:** load a doctored store (an episode whose `key` matches but whose stored `plan.content_hash`
   is altered) → `run_with_reuse` raises `ExperienceConsistencyError`.
5. **key discrimination:** same request, different `capability_model` (drop a resource) → **miss** (no stale reuse).
6. **INFRA_ERROR on miss:** inject a boom oracle → `status="INFRA_ERROR"`, `reused=False`, **no** episode written.

**Verification gates.** `pytest tests/integration/test_experience_reuse.py` green; **full suite** green; ruff;
import-linter clean; RM1 zero-diff.

**Completion criteria.** All 6 cases pass; RM1 files unchanged; store idempotent on reuse.

**Commit.** `feat(rm2): idempotent reuse composition + reproducibility guard`

---

## Milestone RM2-M4 — Boundary, freeze & regression gates + CI

**Objective.** Make the constitutional boundaries executable and gate them in CI.

**Files to create.**
- `tests/boundary/test_experience_boundaries.py`. *Why:* enforces Law-6 non-goals + import discipline in code.

**Files to modify.**
- `.github/workflows/ci.yml` — add the RM2 tests, the contract-freeze check, and the RM1 zero-diff git-diff gate.
  *Why:* CI is the non-skippable gate; it is not an RM1 runtime module, so editing it is permitted.

**Required tests / gates (exact).**
1. **Boundary source-scan:** every file under `experience/` and `orchestration/reuse_runner.py` imports only
   `mini_prometheus._*`, `mini_prometheus.contracts`-bound names, RM1 modules (read-only), and stdlib; contains
   **no** token in {`retention`, `prune`, `compress`, `evict`, `archival`} and **no** `noetica` memory/store import;
   **no** `miniflywire` (Law 4).
2. **import-linter:** existing contracts pass; `experience` and `reuse_runner` depend on `contracts` + RM1 only.
3. **Contract freeze:** assert `contracts/VERSION` text == `0.2.0`; `python tools/generate_contracts.py` then
   `git diff --exit-code contracts/python` (no drift); no `contracts/schemas` change.
4. **RM1 zero-diff (CI step):** `git diff --exit-code rm1-complete -- <RM1 file set> contracts/`.

**Verification gates.** Entire suite green including `tests/boundary`; all four gates pass locally.

**Completion criteria.** Boundaries enforced in code + CI; RM1 + contracts provably unchanged.

**Commit.** `test(rm2): boundary, contract-freeze, and RM1 zero-diff gates + CI`

---

## Milestone RM2-M5 — Close-out & freeze

**Objective.** Freeze and govern RM2 (mirrors the RM1 close-out).

**Files to modify / create.**
- `pyproject.toml` — runtime `0.2.0 → 0.3.0`. *Why:* additive feature release.
- `CHANGELOG.md` — cut `## [0.3.0] — RM2` release. *Why:* release record.
- `README.md` — status line → RM2 complete. *Why:* front-page status.
- `docs/ROADMAP.md` — mark RM2 ✓; record that RM2 (compounding) preceded real-Velith (RM3). *Why:* tracking.
- `docs/milestones/RM2-completion-report.md` *(new)* — close-out report. *Why:* milestone record.
- `docs/adr/0006-rm2-acceptance.md` *(new)* + `docs/adr/README.md` index row. *Why:* governance acceptance.
- `docs/releases/rm2-0.3.0.md` *(new)* — release notes. *Why:* user-facing notes.
- `specs/milestones/RM2-experience-reuse.md` — status → ✅ Implemented & Complete. *Why:* freeze the spec of record.
- `docs/design/RM2-engineering-package.md` — add an "Implemented by RM2" stamp. *Why:* traceability.

**Files to modify.** None of RM1; no contract.

**Verification gates.** Full suite green; docs internally consistent; version bumped; drift-stable.

**Completion criteria.** RM2 frozen; runtime `0.3.0`; ready to tag `rm2-complete`.

**Commit.** `docs(rm2): close out RM2 — 0.3.0 release, completion report, ADR-0006, roadmap`
**Then tag:** annotated `rm2-complete` on the close-out commit; push commit then tag.

---

## Complete implementation roadmap (first commit → RM2 complete)

| Order | Milestone | Deliverable | Green gate before next | Commit |
|---|---|---|---|---|
| 1 | **RM2-M1** | `experience/` reader (+integrity) | reader unit tests; RM1 zero-diff | `feat(rm2): experience episode store reader (read side)` |
| 2 | **RM2-M2** | `experience/` index (composite key) | index unit tests | `feat(rm2): experience episode index (composite-key retrieval)` |
| 3 | **RM2-M3** | `orchestration/reuse_runner.py` + guard | integration (6 cases) + full suite | `feat(rm2): idempotent reuse composition + reproducibility guard` |
| 4 | **RM2-M4** | boundary/freeze/zero-diff tests + CI | boundary + freeze + zero-diff gates | `test(rm2): boundary, contract-freeze, and RM1 zero-diff gates + CI` |
| 5 | **RM2-M5** | close-out docs + version + ADR-0006 | full suite; docs consistent | `docs(rm2): close out RM2 — 0.3.0 release, completion report, ADR-0006, roadmap` |
| — | **Tag** | `rm2-complete` | all gates green | `git tag -a rm2-complete …` |

**Properties of this decomposition.**
- **Minimum risk:** M1/M2 are pure, independently-tested read-side utilities; M3 is the only composition and is a
  new file (no RM1 edit); M4 turns the invariants into automated gates; M5 is docs-only.
- **Maximum reviewability:** five small, single-purpose commits, each leaving the whole suite green.
- **RM1 preserved:** no RM1 file or contract is edited in any milestone; a CI zero-diff gate proves it.
- **No open decisions:** §0 fixes every engineering choice; each milestone is executable without further discussion.

**Git flow per milestone** (beginner-safe, whole-file staging only — no `git add -p`):
```
git add <the exact files listed for that milestone>
git status
git commit -m "<the milestone's commit message>"
git push
```
At M5, after the close-out commit + push:
```
git tag -a rm2-complete -m "RM2 complete — experience read-back & idempotent reuse (compounding rung 1). Runtime 0.3.0."
git push origin rm2-complete
```

*Implementation plan only. No code produced; no repository code or frozen artifact modified.*
