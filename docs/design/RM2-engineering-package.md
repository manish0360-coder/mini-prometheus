# RM2 Engineering Package — Experience Read-Back & Idempotent Reuse

- **Status:** ✅ **IMPLEMENTED by RM2** (`rm2-complete`, 2026-07-25); architecture was frozen (Claude + Gemini
  converged). Realized in `src/mini_prometheus/experience/` + `orchestration/reuse_runner.py`; see
  `docs/milestones/RM2-completion-report.md`.
- **Milestone:** RM2. **Layer:** Mini Prometheus (Layer 4). **Constitution:** v1.1.0.
- **Immovable:** RM1 is frozen. RM2 is **purely additive** — it touches no RM1 file, no frozen contract, no schema, no binding.
- **Deliverable contents:** (1) frozen spec, (2) architecture, (3) components, (4) file plan, (5) contracts confirmation, (6) public interfaces, (7) internal interfaces, (8) data flow, (9) verification strategy, (10) test strategy, (11) milestone decomposition, (12) implementation roadmap.
- **No code. No repository changes.**

---

## 1. Frozen RM2 specification (final)

**Objective (frozen).** Make RM1's logged experience useful: given a `ManufacturingRequest`, deterministically
detect whether an **equivalent** request (identical `DesignInput` identity *and* capability-model version) was
already processed, and if so **retrieve and reuse** the prior verified `ProductionPlan` + `Verdict` instead of
recomputing — writing no duplicate episode. This is the first measurable rung of **compounding** at the
manufacturing layer and opens the **read side of the Experience Flow**.

**Scope (frozen, in):** a read-only `experience/` package (episode loader + deterministic index); exact-key
retrieval; an additive reuse composition (`run_with_reuse`) that returns the prior result on a hit and
otherwise delegates to RM1's unchanged `run()`; a reproducibility guard that recomputes the plan and asserts
its `content_hash` matches the stored one; runtime provenance of the reuse (reference to the prior episode).

**Non-goals (frozen):** no retention/compression/pruning/archival framework (Noetica's, §11.11); no general
memory/knowledge engine, query DSL, or cross-domain store (Noetica's, Law 6) — RM2 is the minimal MP-owned
read index over MP's own episodes, the *extraction seed* for Noetica (Law 8); no similarity/near-duplicate
retrieval (exact key only; distance-based deferred — Velith D25); no adaptive learning/policy/plan
optimization; **no change to any RM1 module, frozen contract, schema, or binding**; no real Velith/Noetica
package integration (RM3+); no geometry; no execution.

**Definition of Done (frozen):** `experience/` read side + additive reuse composition implemented; all
verification gates (§9) green; **RM1's 31 tests pass unchanged with zero RM1 diff**; no frozen contract/schema/
binding modified; compounding rung-1 demonstrated (a repeated request deterministically reuses prior verified
experience, writes no duplicate, passes the reproducibility guard); governance close-out complete (spec frozen
in `specs/milestones/`, completion report, `docs/ROADMAP.md` update, RM2 acceptance ADR, `CHANGELOG` release,
runtime version bump, tag `rm2-complete`).

*(Full rationale, candidate comparison, and rejections are in the approved RM2 specification; unchanged here.)*

---

## 2. Architecture document

### 2.1 Where RM2 sits

RM2 adds the **consume/read side** of the Experience Flow that RM1 only produced (write side). It is
Mini Prometheus manufacturing **content** (Handbook §2.4 "emit the Experience Flow"), realized as a small,
stateless read index over MP's own `ManufacturingEpisode` records.

```
        RM1 (frozen)                              RM2 (additive)
  request → intake → DesignInput → plan → verify → log ─┐
                                                        ▼  append-only JSONL episode store (RM1 artifact)
  request → intake → DesignInput ──▶ experience.lookup(key) ──┬─ hit → reuse (no recompute of compute path; guard recomputes plan)
                                                              └─ miss → RM1 run()  (unchanged)
```

### 2.2 Constitutional boundary (the load-bearing line)

- **What RM2 owns (MP content):** reading its own episodes, a deterministic in-memory index, and the reuse
  decision. Legitimate domain behavior (Handbook §2.4; §11.11 "domains produce/configure").
- **What RM2 must not become (Noetica mechanism, Law 6):** a persistent store engine, a retention/compression/
  pruning framework, a general query/memory API, or a cross-domain store. These are **non-goals** and are the
  Noetica lifecycle framework, deferred (§11.11). RM2 is the **extraction seed** (Law 8, N.3 — the Velith
  episode store → Noetica precedent).
- **Enforcement:** the index is rebuilt from the file each call (no persistent index engine state); non-goals
  are asserted by boundary tests + import-linter (§9).

### 2.3 Dependency direction

`experience/` and the reuse composition depend on: `contracts/` (frozen `ManufacturingEpisode`, `ProductionPlan`,
`Verdict`, `Ref`), the internal `_hashing` mechanisms, and RM1 modules **read-only** (`intake`, `runner.run`,
`manufacturing_planning.planner`). Nothing depends on `experience/` except the new reuse composition. No
MiniFlyWire import (Law 4). No sibling-content coupling beyond contracts + the RM1 read-only reuse (arch §14).

### 2.4 Why additive (RM1 immutability)

The reuse composition lives in a **new file** (`orchestration/reuse_runner.py`); RM1's `runner.py` and all
other RM1 modules are **byte-unchanged**. This guarantees the DoD's "zero RM1 diff" structurally rather than
by discipline.

---

## 3. Component decomposition

| # | Component | New/Reused | Responsibility | Depends on |
|---|---|---|---|---|
| 1 | **Episode store reader** | New (`experience/`) | Read the JSONL store → `list[ManufacturingEpisode]`; verify each `content_hash` on load (reject tampered/corrupt lines). | contracts (`ManufacturingEpisode`), `_hashing`, `_validate` |
| 2 | **Episode index** | New (`experience/`) | Build a deterministic map `key → episode` where `key = (design_input_identity_hash, capability_model_version)`; `lookup(key)`. Last-writer-wins on duplicate keys is impossible (idempotent store), so a key maps to exactly one episode. | component 1 |
| 3 | **Reuse composition** | New (`orchestration/reuse_runner.py`) | `run_with_reuse`: intake → compute key → lookup → (reuse + guard) or (delegate to RM1 `run`). Owns `ReuseRunResult`. | intake (RM1), `runner.run` (RM1), planner (RM1, for the guard), components 1–2, `_hashing` |
| 4 | **Reproducibility guard** | New (within component 3) | On a hit, recompute the plan (`planner.plan`) and assert `plan.content_hash == stored episode.plan.content_hash`; raise `ExperienceConsistencyError` on mismatch. | planner (RM1), `_hashing` |
| 5 | **Tests** | New | Unit, integration, boundary (§10). | all |
| 6 | **CI extension** | Edit `.github/workflows/ci.yml` | Add the new tests to the existing gate (CI is not an RM1 runtime module). | — |

RM1 runtime modules are **imported unchanged**; none is edited.

---

## 4. Directory / file plan (to be created at implementation time — not now)

```
src/mini_prometheus/
├── experience/                         # NEW package (read side of the Experience Flow)
│   ├── __init__.py
│   ├── episode_store_reader.py         # load(store_path) -> list[ManufacturingEpisode]; verify content_hash
│   └── episode_index.py                # ReuseKey, EpisodeIndex(build, lookup)
└── orchestration/
    └── reuse_runner.py                 # NEW file: ReuseRunResult, run_with_reuse, ExperienceConsistencyError
                                        #   (runner.py is NOT edited)

tests/
├── unit/
│   ├── test_episode_store_reader.py    # NEW
│   └── test_episode_index.py           # NEW
├── integration/
│   └── test_experience_reuse.py        # NEW (compounding demonstration)
└── boundary/
    └── test_experience_boundaries.py   # NEW (Law 6 non-goals; no RM1 edits; import discipline)

.github/workflows/ci.yml                # EDIT: add new tests (non-RM1 file)
```

Everything under `src/mini_prometheus/` that is RM1 (intake, manufacturing_planning, manufacturing_constraints,
orchestration/runner.py, orchestration/episode_store.py, the internal `_*` modules) is **untouched**.

---

## 5. Required contracts — confirmation

**No new published contracts are required.** RM2 reuses the frozen `ManufacturingEpisode`, `ProductionPlan`,
`Verdict`, `DesignInput`, `Ref`. Therefore:

- `contracts/schemas/**` — **unchanged**. `contracts/python/**` — **unchanged**. `contracts/VERSION` — **stays 0.2.0**.
- The Contract stage of the workflow for RM2 is a **confirmed no-op**, recorded (not skipped): a boundary test
  asserts the contract suite is byte-unchanged and bindings remain drift-stable.
- **Internal, non-contract types** introduced by RM2 (repo-arch §13; never published, never persisted):
  `ReuseKey` (tuple of `design_input_identity_hash: str`, `capability_model_version: str`), `EpisodeIndex`,
  `ReuseRunResult`, `ExperienceConsistencyError`.
- **Why no episode change:** on reuse, RM2 returns the *existing* episode and writes nothing new; the "reused"
  indication is a runtime field on `ReuseRunResult`, so the append-only store and its schema remain frozen.

---

## 6. Public interfaces (RM2's MP-level API)

```
# orchestration/reuse_runner.py
@dataclass
class ReuseRunResult:
    status: str                     # verdict status (MANUFACTURABLE / NOT_MANUFACTURABLE / PLAN_INVALID / INFRA_ERROR)
    verdict: Verdict
    task: ManufacturingTask | None
    plan: ProductionPlan | None
    episode: ManufacturingEpisode | None
    reused: bool                    # True iff served from a prior episode
    source_episode: Ref | None      # Ref(prior episode_id, content_hash) when reused, else None
    episode_path: str | None        # store path (unchanged on reuse)

def run_with_reuse(
    request: ManufacturingRequest,
    *,
    capability_model: ProcessCapabilityModel | None = None,
    oracle: Verifier | None = None,
    produced_at: str | None = None,
    store_path: str | None = None,
    verify_reuse: bool = True,      # run the reproducibility guard on a hit (default on: verification-first)
) -> ReuseRunResult: ...
```

Signature intentionally mirrors RM1's `run_from_request` (same optional injection points) so callers can adopt
reuse without relearning the API. `run_with_reuse` is the RM2 public entry; RM1's `run`/`run_from_request`
remain available and unchanged.

## 7. Internal interfaces

```
# experience/episode_store_reader.py
def load(store_path: str | Path) -> list[ManufacturingEpisode]:
    """Read JSONL; parse each line to ManufacturingEpisode; verify content_hash; raise on mismatch/corruption.
       A missing store returns []."""

# experience/episode_index.py
ReuseKey = tuple[str, str]          # (design_input_identity_hash, capability_model_version)

class EpisodeIndex:
    @classmethod
    def build(cls, episodes: list[ManufacturingEpisode]) -> "EpisodeIndex": ...
    def lookup(self, key: ReuseKey) -> ManufacturingEpisode | None: ...

# key derivation (reused RM1 mechanism, no new hashing rule)
#   design_input_identity_hash = _hashing.content_hash(_hashing.design_input_identity(design_input))
#   which equals episode.design_ref.content_hash for a matching design
#   capability_model_version    = model.version   (== episode.capability_model_version)
```

Consumed unchanged from RM1: `intake.intake`, `runner.run`, `manufacturing_planning.planner.plan`,
`_hashing.{design_input_identity, content_hash}`, `manufacturing_constraints.capability_model.default_model`.

## 8. Data flow

```
run_with_reuse(request)
  1. design_input      = intake(request)                                  # RM1, unchanged
  2. model             = capability_model or default_model()
  3. key               = ( content_hash(design_input_identity(design_input)), model.version )
  4. episodes          = episode_store_reader.load(store_path)            # read side
     index             = EpisodeIndex.build(episodes)
  5. hit = index.lookup(key)
     ├─ hit is not None  →  REUSE
     │     if verify_reuse:                                              # reproducibility guard (verification-first)
     │         _task, plan = planner.plan(design_input, model)          # deterministic recompute
     │         assert plan.content_hash == hit.plan.content_hash        # else raise ExperienceConsistencyError
     │     return ReuseRunResult(reused=True, plan=hit.plan, verdict=hit.verdict,
     │                           episode=hit, source_episode=Ref(hit.episode_id, hit.content_hash),
     │                           status=hit.verdict.status, episode_path=store_path)   # writes NOTHING
     └─ hit is None      →  MISS
           r = runner.run(design_input, capability_model=model, oracle=oracle,
                          produced_at=produced_at, store_path=store_path)  # RM1, unchanged (plan→verify→log)
           return ReuseRunResult(reused=False, plan=r.plan, verdict=r.verdict, episode=r.episode,
                                 source_episode=None, status=r.status, episode_path=r.episode_path)
```

Notes: (a) verdict determinism follows from `(plan, model_version)`, so a matching plan hash + matching model
version implies a matching verdict — the plan-hash guard is sufficient. (b) INFRA_ERROR only arises on a miss
via RM1's runner (unchanged: no episode written). (c) the store read is the only I/O added; the index is
transient.

## 9. Verification strategy (gates; all must pass in CI)

| Gate | Assertion |
|---|---|
| **Reader integrity** | `load` parses valid JSONL, verifies `content_hash`, raises on a tampered line, returns `[]` for a missing store. |
| **Index determinism** | `build` + `lookup` are deterministic; correct episode on key match; `None` on miss. |
| **Compounding (integration)** | 1st run = miss → logs 1 episode; 2nd identical run = **hit**, `reused=True`, same `plan.content_hash`/`verdict`, **store still 1 line**; different request = miss → store grows. |
| **Reproducibility guard** | on reuse, recomputed `plan.content_hash` == stored; a forced mismatch raises `ExperienceConsistencyError`. |
| **Reuse key correctness** | same intent but different `capability_model_version` ⇒ **miss** (no stale reuse). |
| **RM1 immutability (regression)** | RM1's 31 tests pass unchanged; a check asserts no RM1 source file differs from `rm1-complete`. |
| **Boundary (Law)** | `experience/`/`reuse_runner` import contracts + RM1 read-only; **no** retention/pruning code; **no** Noetica memory/store-engine import; no MiniFlyWire import (Law 4); import-linter clean. |
| **Contract freeze** | `contracts/VERSION` == 0.2.0; `contracts/schemas` + `contracts/python` byte-unchanged; bindings drift-stable. |

## 10. Test strategy (files → cases)

- `tests/unit/test_episode_store_reader.py`: valid load; content-hash verification; tampered-line rejection; missing-store → `[]`.
- `tests/unit/test_episode_index.py`: deterministic build; hit/miss; composite-key (model-version) discrimination.
- `tests/integration/test_experience_reuse.py`: miss→log→hit→reuse (no duplicate); different-request growth; guard success; guard failure raises; INFRA_ERROR path (miss) writes nothing.
- `tests/boundary/test_experience_boundaries.py`: source-scan that `experience/` has no retention/pruning/Noetica-memory imports and no MiniFlyWire; RM1 files unchanged vs tag; import-linter contract.
- Reuse RM1's `tests/conftest.py` fixtures (`engineer_request`, `store_path`) and `support` helpers — unchanged.

## 11. Milestone decomposition (build order)

1. **Contract confirmation (no-op, recorded):** assert no new contracts; freeze check.
2. **Episode store reader** (`experience/episode_store_reader.py`) + unit tests.
3. **Episode index** (`experience/episode_index.py`, composite key) + unit tests.
4. **Reuse composition + guard** (`orchestration/reuse_runner.py`, `ReuseRunResult`, `run_with_reuse`, `ExperienceConsistencyError`) + integration tests.
5. **Boundary tests** (Law 6 non-goals; RM1-unchanged; import discipline).
6. **CI extension** (add tests to `ci.yml`).
7. **Verification** (all gates §9 green; RM1 regression zero-diff).
8. **Close-out** (freeze spec in `specs/milestones/`, completion report, roadmap update, RM2 ADR, CHANGELOG release, runtime version bump, tag `rm2-complete`).

Each step follows the frozen workflow (Specification → Contract → Implementation → Testing → Verification →
Commit → Review). Steps 2–5 are individually atomic commits; 8 is the close-out commit + tag.

## 12. Implementation roadmap

| Phase | Deliverable | Gate before proceeding | Est. size |
|---|---|---|---|
| P0 | Contract confirmation recorded (no new contracts) | freeze check green | XS |
| P1 | Reader + index (read side) | unit gates (reader integrity, index determinism) | S |
| P2 | Reuse composition + guard | compounding + guard + key-correctness gates | S–M |
| P3 | Boundary + regression | Law gates + RM1 zero-diff | S |
| P4 | CI + full green | entire suite (RM1 + RM2) green; bindings drift-stable | XS |
| P5 | Governance close-out + tag `rm2-complete` | version bump; docs; ADR | S |

**Dependency gates outside RM2 (none block it):** RM2 depends on nothing unpublished. Real Velith (RM3) and
real Noetica (RM4) remain gated on those upstreams; RM2 is independent of both.

**Version plan (at close-out):** runtime `0.2.0 → 0.3.0` (additive feature); `contracts/VERSION` unchanged
(0.2.0); `constitution/VERSION` unchanged (1.1.0); tag `rm2-complete`.

---

## Appendix — engineering-package decisions confirmed against the frozen spec (not a redesign)

These are implementation-level confirmations consistent with the approved architecture:

- **Composite reuse key** `(design_input_identity_hash, capability_model_version)` — prevents reusing a plan
  computed under a different capability model. (Refines "identity match" in the spec; same intent.)
- **Reuse composition placed in a NEW file** (`orchestration/reuse_runner.py`), not an edit to `runner.py` —
  guarantees the spec's "does not modify RM1's `run()`" at the file level (zero RM1 diff).
- **Guard default on** (`verify_reuse=True`) — verification-first (Principle 1): stored experience is
  re-derived and checked, never trusted blindly.

*Engineering package for RM2. Frozen architecture; implementation-ready. No code; no repository changes.*
