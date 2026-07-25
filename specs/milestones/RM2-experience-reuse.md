# RM2 Specification — Experience Read-Back & Idempotent Reuse (the read side of the Experience Flow)

- **Status:** ✅ **IMPLEMENTED & COMPLETE (RM2, `rm2-complete`, 2026-07-25).** Delivered exactly as specified;
  verified by 19 RM2 tests (50 total). See `docs/milestones/RM2-completion-report.md` and ADR-0006. Frozen
  specification of record.
- **Milestone:** RM2 (second runtime implementation milestone).
- **Layer:** Mini Prometheus (Layer 4). Constitution v1.1.0.
- **Governing:** HANDBOOK_v1.1 (§1.7, Principle 8, §2.4, §11.11, Laws 6/8/12/14/18/21), ADR-0004/0005, frozen RM1 spec + contracts.
- **Immovable constraint:** RM1 is frozen. RM2 adds a read layer; it changes no RM1 module, contract, schema, or binding.

---

## Part A — First-principles derivation

### A.1 What capability is missing after RM1?

RM1 delivers `plan → verify → log`: a real engineer `ManufacturingRequest` becomes a verified,
content-hashed `ManufacturingEpisode`. But **RM1 emits experience and never uses it.** Every request is
planned and verified from scratch; the logged episodes are write-only. Measured against the North Star
("assist engineers in creating real manufacturable products") and, decisively, against the **Constitution's
own spine**:

- **Principle 8 (Compounding is the test):** "A system that accumulates experience without improving at the
  task has failed, however impressive any single output appears."
- **§1.7 (the falsifiable commitment):** competence must *compound* over grounded episodes.
- **Law 21 (Experience Flow):** experience is a first-class, versioned data contract.

By the program's own definition, **RM1 is currently a "toy": it logs but does not compound.** The single
most important missing capability is therefore not a new input source or a richer model — it is the **read
side of the Experience Flow**: making logged experience *count*. Everything compounding-related (memory,
retrieval, learning, calibration) is downstream of this.

### A.2 Why is RM2 the highest-priority next milestone?

Three first-principles reasons:

1. **It closes the Constitution's central gap.** Compounding is the falsifiable spine; RM1 fails it. No
   other candidate remedies a *constitutional* failure.
2. **It is on the critical path and unblocks the future.** The read side (an episode index + retrieval +
   reuse) is the foundation every later capability (memory policies, calibrated models, adaptive planning)
   builds on. It is also the **extraction seed** for Noetica's memory framework (Law 8, N.3 — exactly how
   Velith's episode store seeded Noetica).
3. **It is buildable now, self-contained, with no external gate.** Unlike wiring real Velith/Noetica
   packages, it depends on nothing unpublished. It uses only MP's own already-emitted episodes.

---

## Part B — Candidate directions, comparison, selection

### B.1 Candidates

- **C1 — Real Velith integration.** Replace RM1's fixture with the pinned Velith package's `EngineeringResult`.
- **C2 — Manufacturability depth (richer DFM).** Deepen the capability model + oracle (tolerances, process
  constraints, material-process compatibility, real precedence).
- **C3 — Experience read-back & idempotent reuse (compounding, rung 1).** Read RM1's episodes back; retrieve
  a prior verified plan for an equivalent request and reuse it deterministically. *(This spec.)*
- **C4 — STEP geometry / feature recognition.** Wrap a CAD kernel to derive manufacturing features from the
  opaque STEP, so plans come from real geometry.

### B.2 Objective comparison

| Axis | C1 Real Velith | C2 DFM depth | **C3 Experience reuse** | C4 STEP geometry |
|---|---|---|---|---|
| **Engineering value** | Low *now* — Velith's vertical is software (D4/D5 rung 1); no manufacturable design to plan | Med — but blind without geometry | **High — makes experience count; the North-Star spine** | High — real geometry drives plans |
| **Architectural value** | Med — proves adapter-only change | Med — more content, no new seam | **High — opens the Experience Flow read side + episode index (load-bearing)** | Med-High — big new subsystem |
| **Future scalability** | Med — needed eventually | Med — grows anyway | **High — everything compounding builds on it** | High — foundational, but heavy |
| **Implementation effort** | Low-Med *if published* | Med-High | **Med — read index + retrieval + reuse** | **Very High — feature recognition is research-grade** |
| **Dependency risk** | **High — Velith unpublished + not manufacturable** | Low | **Low — MP's own episodes only** | Med — CAD kernel |

### B.3 Rejections (with justification)

- **Reject C1 (Real Velith):** doubly blocked by externals — Velith is not published as a consumable package
  *and* its current output is a verified SWE patch, not a manufacturable design (D5 rung 1). Planning a
  machining routing for a software patch is meaningless. High dependency risk, low present value. It becomes
  RM3/RM4 once Velith reaches a manufacturable rung. *(This revises the tentative ordering in `docs/ROADMAP.md`,
  which listed real-Velith next; a first-principles review supersedes the indicative roadmap — see §E risks.)*
- **Reject C2 (DFM depth):** premature abstraction (D12/D15, Law 8 "grow by extraction, not speculation").
  Real DFM feasibility needs geometry (deferred), and building a rich rule set before a real design or
  consumer drives its requirements risks guessing the wrong model. Deepen it when a real driver demands it.
- **Reject C4 (STEP geometry):** too large and partly research-grade for one milestone. Robust B-rep feature
  recognition is a milestone-cluster, not a single logically-complete milestone; pursuing it now risks the
  "not a research project" boundary (Handbook §1.9). It follows once compounding infrastructure exists.

### B.4 Selection

**RM2 = C3 — Experience read-back & idempotent reuse.** It is the only candidate that remedies a
*constitutional* failure (compounding), is architecturally load-bearing, is buildable now with no external
gate, and is the legitimate extraction seed for Noetica's memory framework (Law 8).

---

## Part C — The frozen RM2 specification

### C.1 Objective

Make RM1's logged experience useful: given a `ManufacturingRequest`, deterministically detect whether an
**equivalent** request (identical `DesignInput` identity) has already been processed, and if so **retrieve
and reuse** the prior verified `ProductionPlan` + `Verdict` instead of recomputing. This delivers the first,
minimal, measurable rung of *compounding* at the manufacturing layer, and opens the **read side of the
Experience Flow** (a deterministic episode index over MP's own episodes).

### C.2 Scope (in)

1. A new **`experience/`** package (read side only): load RM1-emitted `ManufacturingEpisode` records from the
   append-only JSONL store; build a **deterministic index** keyed by `DesignInput` identity hash (and episode
   `content_hash`).
2. **Retrieval:** exact-identity lookup — given a new request's `DesignInput` identity, return the prior
   episode if one exists, else `None`.
3. **Idempotent reuse** in orchestration: a new `run_with_reuse(...)` composition that returns the retrieved
   plan/verdict (marked reused) on a hit, and otherwise runs the **unchanged** RM1 `plan → verify → log` path.
   On reuse, **no duplicate episode is written** (idempotent).
4. **Consistency / reproducibility guard:** on reuse, recompute the plan and assert its `content_hash`
   matches the stored one (detects drift; proves determinism across time).
5. **Provenance:** the reused result references the prior episode (`source_episode` = its `Ref`), recorded at
   runtime (not by mutating the stored episode).

### C.3 Non-goals (explicit)

- **No retention / compression / archival / pruning framework** — that is Noetica's lifecycle framework
  (§11.11); deferred. RM2's store is read as-is.
- **No general memory / knowledge engine, no cross-domain store, no query DSL** — those are Noetica mechanisms
  (Law 6). RM2 is a **minimal MP-owned read index over MP's own episodes**, explicitly the *extraction seed*
  for Noetica (Law 8), not a platform memory system.
- **No similarity / near-duplicate retrieval** — exact identity match only. Distance-based retrieval is future
  (mirrors Velith D25).
- **No adaptive learning / policy / plan optimization** — reuse is exact, not adaptive. No plan is changed by
  experience in RM2.
- **No change to any RM1 module, frozen contract, schema, or binding.** No real Velith/Noetica package
  integration (RM3+). No geometry, no execution.

### C.4 Architecture

```
ManufacturingRequest
   │ intake (RM1, unchanged)
   ▼
DesignInput ──▶ experience.lookup(DesignInput identity)
                     │ hit ─────────────▶ reuse: return prior episode's plan+verdict (reused=True), write nothing
                     │ miss ────────────▶ RM1 runner.run() [plan→verify→log, unchanged] ─▶ index the new episode
```

- **New package** `src/mini_prometheus/experience/` (read side). Depends on `contracts/` (the frozen
  `ManufacturingEpisode`) and reads the RM1 store path. It is MP manufacturing **content** (Handbook §2.4
  "emit the Experience Flow" — RM2 adds the *consume* side).
- **Orchestration** gains a new `run_with_reuse()` function that *composes* intake + lookup + RM1 `run()`. It
  does **not** modify RM1's `run()`.
- The **episode store** (append-only JSONL) is RM1's artifact; RM2 reads it. The index is rebuilt
  deterministically from the file each run (no persistent index state in RM2 — that would edge toward a store
  engine).

### C.5 Required contracts

- **No new published contracts.** RM2 reuses the frozen `ManufacturingEpisode`, `ProductionPlan`, `Verdict`,
  `DesignInput`. The frozen contract suite (`contracts/VERSION 0.2.0`) is **unchanged**.
- **Internal (not contracts):** `EpisodeIndex` (in-memory), and a `ReuseResult` runtime type (`reused: bool`,
  `source_episode: Ref | None`) — internal MP types under `experience/` (repo-arch §13); never published,
  never persisted into the episode.
- **Rationale for no contract change:** reuse returns an existing episode and writes nothing new; the
  "reused" indication is a runtime concern, so the append-only store and its schema stay frozen.

### C.6 Components

| Component | Location (proposed) | Responsibility |
|---|---|---|
| Episode loader | `experience/episode_store_reader.py` | Read the JSONL store → `list[ManufacturingEpisode]`; verify each `content_hash`. |
| Episode index | `experience/episode_index.py` | Deterministic map: `DesignInput` identity hash → episode; `lookup()`. |
| Reuse composition | `orchestration/runner.py` (new `run_with_reuse`, additive) | intake → lookup → reuse | RM1 `run()`. |
| Consistency guard | within reuse | recompute plan; assert `content_hash` equals stored. |
| Tests | `tests/unit`, `tests/integration`, `tests/boundary` | see C.8. |

RM1 modules (`intake`, `manufacturing_planning`, `manufacturing_constraints`, RM1 `run`, episode emission)
are **imported and reused unchanged**.

### C.7 Interfaces

- `EpisodeIndex.lookup(design_input_identity_hash: str) -> ManufacturingEpisode | None` (internal).
- `run_with_reuse(request: ManufacturingRequest, *, store_path=None, ...) -> RunResultV2` where `RunResultV2`
  extends RM1's result with `reused: bool` and `source_episode: Ref | None` (internal runtime type; RM1's
  `RunResult` is unchanged).
- Consumes (read-only): frozen `ManufacturingEpisode`; RM1 `intake`, `runner.run`; `_hashing.design_input_identity`.

### C.8 Verification gates (all must pass; non-skippable in CI)

1. **Unit:** index build is deterministic; `lookup` returns the correct episode on identity match and `None`
   on miss; loader rejects a tampered episode (`content_hash` mismatch).
2. **Integration — compounding demonstration:**
   - First run of a request → **miss** → RM1 path plans/verifies/logs; store has 1 episode.
   - Second run of the **same** request → **hit** → `reused=True`, returns the **same** plan + verdict (same
     `content_hash`), and the store still has **1 episode** (no duplicate).
   - A **different** request → miss → new episode; store grows to 2.
3. **Consistency/reproducibility guard:** reused plan `content_hash` == freshly recomputed plan `content_hash`.
4. **RM1 immutability (regression):** RM1's existing 31 tests pass **unchanged**; no RM1 module diff.
5. **Boundary (Law-enforced):** `experience/` imports `contracts/` + RM1 modules read-only; it does **not**
   implement retention/pruning; it does **not** import or re-implement any Noetica memory/store engine (Law 6);
   no MiniFlyWire import (Law 4); import-linter clean.
6. **Contract freeze:** `contracts/VERSION` unchanged; bindings regeneration-stable; no schema diff.
7. **Determinism:** identical store + request ⇒ identical lookup + reuse result.

### C.9 Risks and mitigations

| Risk | Mitigation |
|---|---|
| **Law 6** — a memory/store engine belongs to Noetica | Scope to a minimal, stateless read index over MP's *own* episodes; explicit non-goals (no retention/query engine); flagged as the extraction seed for Noetica (Law 8). |
| **Premature abstraction** | Exact-identity retrieval only; no similarity, policy, or learning. |
| **Unbounded store growth** (no retention) | Acknowledged; retention is Noetica's framework (§11.11), deferred. RM2's store is bounded only by usage — acceptable for the demonstration; recorded as an RM3+ item. |
| **RM1 immutability** | RM2 is purely additive (new package + new orchestration function); regression gate (C.8.4) enforces zero RM1 diff. |
| **Roadmap deviation** | RM2 = compounding, not the roadmap's tentative real-Velith; justified by first principles (§B). `docs/ROADMAP.md` should be updated on acceptance (a follow-up doc edit, not part of this frozen spec). |

### C.10 Definition of Done

- `experience/` read side implemented; `run_with_reuse` composes RM1 **unchanged**.
- All verification gates (C.8) green; **RM1's 31 tests pass unchanged**; no RM1 module, frozen contract,
  schema, or binding modified.
- Demonstrates **compounding rung 1**: a repeated request deterministically reuses prior verified experience,
  writes no duplicate, and passes the consistency guard.
- Governance close-out (as for RM1): frozen RM2 spec committed to `specs/milestones/`, completion report,
  `docs/ROADMAP.md` update, an RM2 acceptance ADR, `CHANGELOG` release, runtime version bump, tag
  `rm2-complete`.

---

## Part D — Traceability

| RM2 element | Constitution / precedent |
|---|---|
| Compounding as the milestone driver | §1.7, Principle 8 |
| Experience Flow read side; episode as data contract | Law 21, §2.4 |
| Minimal store, no lifecycle framework | §11.11 (Noetica owns the framework; domains produce) |
| Extraction seed for Noetica memory | Law 8, N.3 (Velith episode store → Noetica precedent) |
| Exact-identity retrieval; distance-based deferred | Velith D25 |
| No re-implementation of Noetica mechanisms | Law 6 |
| Owns manufacturing content; consumes contracts only | Handbook §2.4; ADR-0004 |

---

*Formal RM2 specification, ready for architectural review. No implementation code. No repository changes.
On approval: freeze into `specs/milestones/`, then proceed Contract → Implementation → Testing →
Verification → Commit → Review.*
