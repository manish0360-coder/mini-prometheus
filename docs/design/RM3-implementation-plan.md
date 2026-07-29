# RM3 Implementation Plan — Engineering Precedent Reasoning

- **Status:** Execution-ready. Derived from the **frozen** RM3 spec (`specs/milestones/RM3-engineering-precedent-reasoning.md`),
  contract package (`contracts/RM3-contract-package.md`), and engineering package (`docs/design/RM3-engineering-package.md`).
- **This document is the plan only** — no code, no pseudocode, no JSON Schema, no bindings.
- **Invariants (non-negotiable):** RM1 and RM2 are frozen (zero diff); RM3 contracts are **additive** exactly per the
  frozen RM3 contract package; determinism; **read-only**; RM1/RM2 compatibility. The only authorized contract change
  is the additive RM3 set (`contracts/VERSION 0.2.0 → 0.3.0`) — RM1/RM2 schemas and bindings stay byte-identical.

---

## 0. Fixed inputs (nothing re-decided here)

Every engineering choice is already fixed in the frozen documents and is executed verbatim:
- **Contracts** (shapes, enums, identity views, per-mille relevance, provenance sentinel `"0.0.0"`, deterministic
  `report_id`) — `contracts/RM3-contract-package.md`.
- **Modules, responsibilities, dependency graph, data flow, build order** — `docs/design/RM3-engineering-package.md`.
- **Reused conventions** (canonical JSON, `content_hash`, `uuid5(NS_MP,…)`, `Ref`/`Provenance`) — RM1 contract package.
- **Runtime shim / test harness** — reuse RM2's (`tests/conftest.py`, `pythonpath = ["src",".","tests"]`, StrEnum 3.11 shim); unchanged.

**Frozen file set that MUST remain zero-diff vs tag `rm2-complete`** (RM1 + RM2 code + RM1/RM2 contract files):
`src/mini_prometheus/{_contracts,_hashing,_validate,_provenance,_verifier}.py`, `intake/`, `manufacturing_planning/`,
`manufacturing_constraints/`, `manufacturing_state/`, `manufacturing_twin/`, `orchestration/{__init__,runner,episode_store,reuse_runner}.py`,
`experience/`, and the existing `contracts/schemas/**` + `contracts/python/**` files that predate RM3. The gate diffs
**explicit existing files** (not directories) so new RM3 files are additions, not diffs.

### 0.1 Verification commands (run at each milestone gate)
```
python -m pytest -q                                            # entire suite green (RM1 + RM2 + RM3 so far)
python -m ruff check src tests tools                           # lint clean
python tools/generate_contracts.py && git diff --exit-code contracts/python   # bindings match schemas (no drift)
lint-imports                                                   # import-linter (CI; 3.11)
git diff --exit-code rm2-complete -- <frozen RM1/RM2 file set §0>             # RM1/RM2 zero-diff (from M5)
```

---

## Milestone RM3-M0 — Contract artifacts (realize the frozen RM3 contract package)

**Objective.** Materialize the additive RM3 contracts (no design decisions — mechanical realization of the frozen
contract package). This is the *only* milestone that touches `contracts/`.

**Files to create/modify.**
- create `contracts/schemas/manufacturing/precedent_report.schema.json` — `PrecedentReport` with `PrecedentEntry`
  and `PrecedentSignal` as `$defs` (mirroring RM1's `production_plan`/`manufacturability` layout). *Why:* the
  source-of-truth schema for the one new output.
- modify `contracts/schemas/manufacturing/README.md` — add the new schema to the manifest.
- modify `contracts/VERSION` — `0.2.0 → 0.3.0` (additive MINOR). *Why:* suite version per the contract package §7.
- (generated) `contracts/python/manufacturing/precedent_report_schema.py` + `contracts/python/README.md` — produced
  by `tools/generate_contracts.py`; **not hand-written**.

**Verification gate.**
- all schemas meta-validate; every `$ref` resolves; regeneration is drift-stable;
- **RM1/RM2 schemas + bindings are byte-unchanged** (`git diff rm2-complete -- <existing contract files>` empty);
- new RM3 bindings import; full suite still green.

**Completion criteria.** RM3 contracts exist and validate; `contracts/VERSION == 0.3.0`; RM1/RM2 contract files unchanged.

---

## Milestone RM3-M1 — Precedent model (deterministic relevance)

**Objective.** The deterministic, versioned engineering relevance model (domain content).

**Files to create.**
- `src/mini_prometheus/precedent/__init__.py` — package + Law-6 boundary docstring.
- `src/mini_prometheus/precedent/precedent_model.py` — deterministic relevance over the frozen features; owns
  `precedent_model_version` + default. *Why:* engineering-package module #1; the content that defines relevance.
- `tests/unit/test_precedent_model.py`.

**Verification gate.** Model unit tests green (determinism; identical designs ⇒ relevance `1000`; version-carried;
relevance in `0..1000`); ruff; RM1/RM2 zero-diff; contracts unchanged.

**Completion criteria.** Deterministic relevance model, independently tested.

---

## Milestone RM3-M2 — Retriever (extraction-seed mechanism)

**Objective.** Rank the verified-episode corpus by the model — the isolated retrieval mechanism (extraction seed).

**Files to create.**
- `src/mini_prometheus/precedent/retriever.py` — consumes RM2 `experience` reader + index (read-only); ranks by
  `precedent_model`; deterministic total order (relevance desc, tie-break by episode `content_hash` asc); top-K.
- `tests/unit/test_precedent_retriever.py`.

**Verification gate.** Retriever unit tests green (total-order ranking, tie-break, top-K, read-only, determinism);
depends only on model + RM2 read side; ruff; RM1/RM2 zero-diff; contracts unchanged.

**Completion criteria.** Deterministic ranked candidate retrieval; the seed is isolated (no report semantics inside it).

---

## Milestone RM3-M3 — Reasoner (RM3 identity: signal + PrecedentReport)

**Objective.** Engineering Precedent Reasoning — derive the signal, assemble the `PrecedentReport`, compute
identity/hash/provenance.

**Files to create.**
- `src/mini_prometheus/precedent/reasoner.py` — from ranked candidates + verdicts: `PrecedentSignal` (+
  `signal_source_rank`), `PrecedentEntry[]`, `PrecedentReport`, `content_hash`, `report_id`, provenance (sentinel
  `capability_model_version = "0.0.0"`). Read-only. *Why:* engineering-package module #3 (identity).
- `tests/unit/test_precedent_reasoner.py`.

**Verification gate.** Reasoner unit tests green (deterministic signal derivation; report/entry fields exactly per
contract; `content_hash`/`report_id`; **structural honesty** — no query-verdict field; contract validation of the
report); ruff; RM1/RM2 zero-diff; contracts unchanged.

**Completion criteria.** A schema-valid, content-hashed `PrecedentReport` is produced deterministically from ranked candidates.

---

## Milestone RM3-M4 — Composition entry (end-to-end) — INTEGRATION CHECKPOINT

**Objective.** Compose intake → retriever → reasoner into a single read-only entry returning a `PrecedentReport`.

**Files to create.**
- `src/mini_prometheus/orchestration/precedent_runner.py` — **new file**; RM1 `runner.py` and RM2 `reuse_runner.py`
  untouched. *Why:* engineering-package composition module.
- `tests/integration/test_precedent_reasoning.py`.

**Verification gate (integration checkpoint).** End-to-end tests green: deterministic report; **generalization** (a
similar-but-not-identical prior request surfaced; identical ⇒ relevance `1000`); **cautionary signal** from a
`NOT_MANUFACTURABLE` precedent with its reason codes; empty corpus ⇒ `NONE`; **read-only** (corpus + RM1 plan/verdict
unchanged); full suite green; ruff; RM1/RM2 zero-diff.

**Completion criteria.** RM3 works end-to-end, read-only, deterministically, with RM1/RM2 untouched.

---

## Milestone RM3-M5 — Boundary, freeze & regression gates + CI

**Objective.** Make the constitutional invariants executable and wire them into CI.

**Files to create/modify.**
- create `tests/boundary/test_precedent_boundaries.py` — AST-based: `precedent/` + `precedent_runner` import only
  contracts + RM1/RM2 read-only + stdlib; **no** ML/embeddings/vector-DB imports; **no** store/retention/prune engine;
  **no** MiniFlyWire (Law 4); retriever is the sole RM2-read-side consumer (seed/identity separation).
- modify `.github/workflows/ci.yml` — extend the zero-diff gate to diff vs **`rm2-complete`** over the §0 frozen file
  set; update the contract-freeze gate to `contracts/VERSION == 0.3.0`; ensure the new tests run.

**Verification gate.** Boundary tests green; full suite green; import-linter clean (CI); zero-diff vs `rm2-complete`;
contract-freeze at `0.3.0`; bindings drift-stable.

**Completion criteria.** All constitutional gates enforced in code + CI.

---

## Milestone RM3-M6 — Governance close-out

**Objective.** Freeze and govern RM3 (mirrors RM1/RM2 close-outs).

**Files to modify/create.**
- `pyproject.toml` — runtime `0.3.0 → 0.4.0`.
- `CHANGELOG.md` — cut `## [0.4.0] — RM3`.
- `README.md` — status → RM3 complete.
- `docs/ROADMAP.md` — mark RM3 ✅; RM4 = real Velith (gated).
- create `docs/milestones/RM3-completion-report.md`; create `docs/adr/0007-rm3-acceptance.md` + index row in `docs/adr/README.md`;
  create `docs/releases/rm3-0.4.0.md`.
- status-stamp `specs/milestones/RM3-engineering-precedent-reasoning.md`, `contracts/RM3-contract-package.md`,
  `docs/design/RM3-engineering-package.md`, `docs/design/RM3-implementation-plan.md` → Implemented/Executed.

**Verification gate.** Full suite green; docs consistent; version bumped; drift-stable.

**Completion criteria.** RM3 frozen; runtime `0.4.0`; ready to tag `rm3-complete`.

---

## Exact file creation order (consolidated, linear)

1. `contracts/schemas/manufacturing/precedent_report.schema.json` → regen `contracts/python/manufacturing/precedent_report_schema.py`; update `contracts/schemas/manufacturing/README.md`, `contracts/python/README.md`, `contracts/VERSION` (M0)
2. `src/mini_prometheus/precedent/__init__.py` (M1)
3. `src/mini_prometheus/precedent/precedent_model.py` → `tests/unit/test_precedent_model.py` (M1)
4. `src/mini_prometheus/precedent/retriever.py` → `tests/unit/test_precedent_retriever.py` (M2)
5. `src/mini_prometheus/precedent/reasoner.py` → `tests/unit/test_precedent_reasoner.py` (M3)
6. `src/mini_prometheus/orchestration/precedent_runner.py` → `tests/integration/test_precedent_reasoning.py` (M4)
7. `tests/boundary/test_precedent_boundaries.py` → `.github/workflows/ci.yml` (M5)
8. close-out docs + `pyproject.toml` + `CHANGELOG.md` + `README.md` + `docs/ROADMAP.md` + `docs/milestones/…` + `docs/adr/…` + `docs/releases/…` (M6)

No existing RM1/RM2 source file is edited at any step. Only additive files + (M5) `ci.yml` + (M6) governance/version docs.

## Integration checkpoints

- **CP-A (after M3):** contract-level integration — a `PrecedentReport` assembled from ranked candidates validates
  against the RM3 schema and re-hashes stably.
- **CP-B (after M4):** system integration — full `request → PrecedentReport` path proven end-to-end (generalization,
  cautionary signal, empty corpus, read-only).
- **CP-C (after M5):** constitutional integration — boundary + zero-diff + contract-freeze + import-linter all green in CI.

## Rollback / stable checkpoints

- **Stable checkpoint = each milestone that ends with its gate green** (full suite green + RM1/RM2 zero-diff +
  contracts as expected). Each milestone is one atomic commit; a green milestone commit is a safe rollback target.
- **Rollback rule:** if a milestone's gate fails, do **not** advance; revert the working changes for that milestone
  (`git restore` / discard) or `git reset --soft` the milestone commit, returning to the previous green checkpoint.
- **Ultimate safety anchors:** tags `rm1-complete` and `rm2-complete`. Because RM3 never edits RM1/RM2 files, RM1 and
  RM2 remain independently intact and buildable at all times; RM3 can be abandoned entirely by removing only the
  additive RM3 files and reverting `contracts/VERSION`/`ci.yml`, with RM1/RM2 unaffected.
- **Contract rollback:** only M0 changed `contracts/`; reverting M0 (delete the RM3 schema/bindings, restore
  `contracts/VERSION` to `0.2.0`) fully undoes RM3's contract footprint.

## Final acceptance checklist (proves RM3 complete)

- [ ] **Determinism:** identical query + identical corpus + identical `precedent_model_version` ⇒ identical
      `PrecedentReport` `content_hash` and `report_id` (timestamps/provenance excluded).
- [ ] **Generalization:** a similar-but-not-identical prior request is surfaced as a precedent; an identical one at relevance `1000`.
- [ ] **Cautionary/supporting/none signal:** derived deterministically with a valid `signal_source_rank`; a
      `NOT_MANUFACTURABLE` precedent yields `CAUTIONARY` with reason codes; empty corpus ⇒ `NONE`.
- [ ] **Read-only:** a precedent query leaves the episode store unchanged and RM1's plan/verdict for the query unchanged.
- [ ] **Structural honesty:** the report has no query-verdict field; precedents are labeled with relevance (analogous).
- [ ] **Ownership / boundaries:** reasoner = domain identity; retriever = isolated extraction-seed mechanism; no store
      engine, no ML/embeddings, no MiniFlyWire import; never bypasses Velith.
- [ ] **Contract additivity:** only `PrecedentReport`/`PrecedentEntry`/`PrecedentSignal` added; `contracts/VERSION == 0.3.0`;
      RM1/RM2 schemas + bindings byte-unchanged.
- [ ] **RM1/RM2 compatibility:** RM1's and RM2's test suites pass unchanged; `git diff --exit-code rm2-complete` over the
      frozen file set is empty.
- [ ] **Full verification green:** entire suite (RM1 + RM2 + RM3) + ruff + import-linter + drift + boundary + zero-diff all pass in CI.
- [ ] **Governance:** RM3 spec/contract/package/plan status-stamped; completion report, ADR-0007, release notes, roadmap
      updated; runtime `0.4.0`; tag `rm3-complete`.

## Roadmap (first commit → RM3 complete)

| Order | Milestone | Green gate before next | Stable checkpoint |
|---|---|---|---|
| 1 | RM3-M0 contracts | schemas valid + drift-stable + RM1/RM2 contracts unchanged | ✓ |
| 2 | RM3-M1 model | model unit gate | ✓ |
| 3 | RM3-M2 retriever | retriever unit gate | ✓ |
| 4 | RM3-M3 reasoner | reasoner unit gate + CP-A | ✓ |
| 5 | RM3-M4 runner | end-to-end gate + CP-B | ✓ |
| 6 | RM3-M5 gates+CI | boundary + zero-diff + freeze + CP-C | ✓ |
| 7 | RM3-M6 close-out | full suite + docs consistent | tag `rm3-complete` |

*Implementation plan only. No code, pseudocode, JSON Schema, or bindings produced. Each milestone is an atomic,
independently-verifiable commit; RM1/RM2 stay byte-unchanged throughout.*
