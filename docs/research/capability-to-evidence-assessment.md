# Mini Prometheus — Bounded Capability-to-Evidence Assessment

**Type:** Read-only, bounded assessment. No code, contract, schema, test, dependency, frozen-spec, ADR, or
Git change. No milestone proposed. Ends in one **investigation** recommendation + the exact evidence needed
to authorize any implementation.
**Repo state:** `main` @ `ab8cc44`; working tree CRLF-only vs HEAD; untracked `research/`, `uv.lock`
preserved. **Not reopened:** capability-model drift hypothesis (closed/deferred) and the RM4
verification-provenance wording decision (Decision A).
**Scope guard:** compares exactly the three named directions, using the current repo + existing reports +
general prior-art knowledge (no new web sweep).

---

## 0. One fact that frames all three: there is no real design artifact on hand

Neither repository contains a **real or independently-validated CAD part**. MP's only STEP fixture is
`tests/fixtures/step/valid_minimal.step` — a 196-byte *synthetic* ISO-10303-21 container (structurally
valid, geometrically trivial; `step_intake.py` validates the container only). The Velith repo's `designs/`
holds only `episodes`, no `.step/.stp/.brep/.iges`. **Every acceptance test below therefore requires first
sourcing one real, ground-truthed part** — that is the single most binding dependency across all three
directions, and the cheapest gap to close.

---

## 1. Direction 1 — Real STEP geometry interpretation via an existing CAD kernel

**Exact code/contracts it would touch.**
- `src/mini_prometheus/artifact_intake/step_intake.py` — today reads bytes and does a *container*
  structural check only (`_structural_container_check`); it extracts **no** geometry. Geometry parsing
  would extend/parallel this leaf.
- `contracts/schemas/manufacturing/design_input.schema.json` `$defs/DesignArtifactRef` — "OPAQUE … **Never
  parsed by RM1**." Interpreting geometry contradicts this contract's stated semantics.
- `specs/milestones/RM1-plan-verify-log.md` §3 — "**STEP geometry interpretation / feature recognition …
  Out of scope (deferred)**." Direction 1 reopens a **frozen** scope boundary (constitutional change,
  Laws 22/23) — explicitly, not incidentally.

**Already implemented vs genuinely missing.**
- *Implemented:* byte ingest, structural container validation, byte-identity + provenance traceability
  (RDAI-1 C1/C2).
- *Missing:* any B-rep parse (solids/faces/edges), volume/bounding-box/topology extraction — i.e., turning
  the opaque artifact into geometric facts.

**Prior art (general knowledge, not a fresh sweep).** Open CASCADE Technology (OCCT) is the de-facto
open-source STEP/B-rep kernel; `pythonocc-core`, CadQuery, build123d, and FreeCAD all wrap it and already
do robust STEP→B-rep parsing, volume/bbox/topology, and healing. **Building our own parser would duplicate
OCCT**; "Direction 1" realistically means *adopting* OCCT.

**Minimal falsifiable acceptance test.** On one real STEP part with independently-known geometry: parse via
OCCT and assert extracted solid volume and bounding box match the reference values within tolerance, and
the solid count/closedness matches.

**Proves / does not prove.** *Proves:* MP can deterministically turn a real STEP file into correct nominal
geometric facts. *Does NOT prove:* anything about manufacturability, DFM, tolerance achievability, or that
any MP reasoning consumer *uses* those facts — it is geometry extraction, not manufacturing reasoning.

**Complexity (qualitative).** High. OCCT is a heavy native dependency (build/packaging, determinism across
platforms, version pinning, the Python-3.10-sandbox/3.11 reality from prior milestones). Verification
non-trivial (geometric tolerance, healing edge cases).

**Blockers/dependencies.** A real ground-truthed STEP part (§0); a heavy native dependency; **and a frozen
constitutional boundary** that must be reopened. No in-repo consumer for the extracted geometry yet.

**Human problem / missing value evidence.** Problem: today MP cannot see the part at all. *Missing
evidence:* that extracting geometry, **by itself**, changes any MP decision — without a consumer
(Direction 2), geometry facts are inert. Risk: a large dependency and a boundary breach that buys nothing
decision-relevant on its own.

---

## 2. Direction 2 — A narrowly scoped geometry-based manufacturability check

**Exact code/contracts it would touch.**
- Everything in Direction 1 (it **requires** some geometry extraction), **plus**
- `src/mini_prometheus/manufacturing_constraints/oracle.py` — the verdict is currently *plan+model
  derivable only*; a geometry check adds a new evidence class to (or beside) `verify`.
- `contracts/schemas/manufacturing/manufacturability.schema.json` — the closed `ManufacturabilityReasonCode`
  enum (member change = MAJOR) would likely need a geometry-derived reason code.
- Same frozen RM1 §3 boundary + `DesignArtifactRef` "never parsed" semantics as Direction 1.

**Already implemented vs genuinely missing.**
- *Implemented:* declared-only checks (capability existence, material, declared precedence, declared
  tolerance-vs-capability-minimum). The oracle **assumes** declared intent faithfully describes the part.
- *Missing:* any check that reads the actual geometry to **confirm or contradict** the declared intent —
  e.g., "the declared operation set cannot produce a feature the solid actually contains," or "a declared
  tolerance is finer than the geometry's as-modeled feature permits."

**Prior art.** Palmetto (feature recognition + rule DFM; **accuracy/coverage unestablished** per the
Director) and commercial DFM (DFMPro, aPriori) cover *generic* DFM checks. A single, narrowly-scoped check
tied to **MP's declared-intent reasoning** (geometry vs the engineer's declaration) is a *different framing*
from generic DFM — but the underlying geometric primitive (e.g., min wall thickness, hole depth/diameter,
tool accessibility) is itself well-trodden. Differentiation is in the *declared-intent-contradiction*
reasoning, not the geometric primitive.

**Minimal falsifiable acceptance test.** On one real part with a **known** declared-intent/geometry
contradiction (e.g., a solid containing a feature the declared operation set cannot produce), a single
geometry-derived check flags the contradiction; and on a matched control part (declaration consistent with
geometry) it does **not** flag. Measured: true-positive on the known bad case, no false-positive on the
control.

**Proves / does not prove.** *Proves:* geometry-grounded reasoning can catch a declared-intent error the
current declared-only pipeline accepts as MANUFACTURABLE — i.e., it attacks MP's deepest assumption.
*Does NOT prove:* general DFM correctness, coverage across feature types, tolerance/quality on real
machines, or that such contradictions occur often enough to matter (frequency unestablished).

**Complexity (qualitative).** High (Direction-1 machinery) + Medium (one check + reason-code + oracle
wiring) + a frozen-scope reopening. Verification needs a ground-truthed contradiction pair.

**Blockers/dependencies.** All of Direction 1's, **plus** a real part with an independently-validated
*contradiction* (harder to source than a plain part), **plus** a MAJOR contract touch (reason-code enum)
and the frozen boundary.

**Human problem / missing value evidence.** Problem (the strongest of the three): an engineer's declared
operations/tolerances can silently mis-describe the real part, and MP would still return MANUFACTURABLE.
*Missing evidence:* that this class of error is real and non-rare in practice, and that a *narrow* check
catches a useful fraction without false alarms.

---

## 3. Direction 3 — Integration with a consumable, genuinely verified Velith release

**Exact code/contracts it would touch.**
- `src/mini_prometheus/integrations/velith/adapter.py` (`from_engineering_result`) and
  `src/mini_prometheus/orchestration/runner.py::run_from_velith` — the verified-design path.
- `contracts/schemas/consumed/velith/engineering_result.schema.json` — explicitly a **"CONSUMED STUB —
  owned by Velith … Pinned until the real Velith contract publishes."**

**Already implemented vs genuinely missing.**
- *Implemented:* the full adapter + runner path against the **stub** `EngineeringResult`; it already
  produces `velith_verified` DesignInputs (fixture-exercised). MP's side is **done**.
- *Missing:* a **real Velith release** that produces a real `EngineeringResult`. This is entirely external.

**Prior art.** N/A — internal cross-repo dependency, not an open-source alternative.

**Minimal falsifiable acceptance test.** Given a pinned, consumable Velith package, map one real Velith
`EngineeringResult` → `DesignInput` (`velith_verified`) and run `plan→verify→log`, asserting the opaque
artifact + verification provenance survive into the episode. **This test cannot be constructed today.**

**Proves / does not prove.** *Would prove:* MP consumes a genuinely reality-verified design end-to-end.
*Would not prove:* any geometry reasoning (the artifact stays opaque — Law 9).

**Complexity (qualitative).** MP-side: Low (adapter exists). Overall: **Unbounded/blocked** — gated on an
external release that does not exist.

**Blockers/dependencies — confirmed at the source, not inferred from MP's roadmap.**
- Velith `pyproject.toml`: `version = "0.0.0"`; README confirms `0.0.0`.
- Velith is at **M8**, a held-out *evaluation* program (roadmap M0–M10); it is a computational-neuroscience
  measurement system, **not** an engineering-design producer.
- **No `EngineeringResult`/`EngineeringTask` exists anywhere in Velith's Python** (grep: none).
- MP roadmap/ADR-0009 independently state RM6 "cannot leave Specification until Velith publishes a pinned,
  consumable package."
→ The precondition is **absent at the source**. Direction 3 is externally blocked today.

**Human problem / missing value evidence.** Problem: a real verified-design path is the eventual point of
the architecture. *Missing evidence:* a consumable Velith release producing `EngineeringResult` — the whole
dependency.

---

## 4. Comparison matrix

| Criterion | **1 — STEP interpretation (OCCT)** | **2 — Narrow geometry check** | **3 — Real Velith integration** |
|---|---|---|---|
| Touches frozen scope (RM1 §3 / `DesignArtifactRef`) | Yes (reopen) | Yes (reopen) + MAJOR enum | No (adapter exists) |
| Already implemented | Byte ingest/identity only | Declared-only checks | **MP side complete (stub)** |
| Genuinely missing | B-rep extraction | Extraction **+** a declared-vs-geometry check | **A real Velith release (external)** |
| Prior art | OCCT (mature) — adopting, not inventing | Palmetto/commercial DFM (generic) | N/A (internal dep) |
| Strengthens *reasoning*? | No (inert facts alone) | **Yes (attacks declared-intent assumption)** | Indirect (provenance, not geometry) |
| Acceptance test constructible now? | Only after sourcing a real part | After sourcing a real *contradiction* pair | **No (blocked)** |
| Complexity | High (native dep) | High + Medium | MP-low / overall blocked |
| Decisive blocker | Real part + boundary | Real contradiction + boundary + MAJOR enum | External release absent at source |

---

## 5. Ranking

1. **Direction 2 — narrow geometry check** — the only one that could *materially strengthen reasoning about
   a real design* (it tests MP's deepest assumption: declared intent = real part). But it is **not the
   smallest** — it presupposes Direction 1's extraction.
2. **Direction 1 — STEP interpretation** — necessary *enabling machinery* for 2, but inert on its own and a
   large dependency + boundary reopening; not justified **until** 2's value is shown.
3. **Direction 3 — real Velith** — highest architectural payoff eventually, but **externally blocked today**
   (confirmed at the Velith source). Not a current choice; remains parked on the external gate.

---

## 6. Recommendation — one investigation (NOT an implementation milestone)

**Run a single, disposable value-probe for Direction 2 on one real, ground-truthed part — using OCCT as a
throwaway research tool, not as an adopted dependency — to test whether a narrowly-scoped geometry-derived
check would catch a declared-intent/geometry contradiction that the current declared-only pipeline accepts
as MANUFACTURABLE.**

Why this and not an implementation of any direction:
- It tests the **value hypothesis** behind the only reasoning-relevant direction (2) **before** paying for
  the enabling machinery (1) or touching any frozen scope.
- It treats OCCT as a **probe in a scratch space** (outside the repo), so it needs **no** code, contract,
  schema, dependency, or boundary change to MP — consistent with all constraints here.
- It keeps Direction 3 correctly parked (blocked at source) and does not reopen the deferred hypotheses.

**Shape of the probe (research only, outside the repo):** take one real STEP part with an independently
established declared-intent/geometry relationship (one genuine contradiction case + one matched control),
extract the minimal geometric property with an off-the-shelf OCCT read, and check by hand whether a single
rule would have flagged the contradiction while leaving the control clean. Record true/false positives. No
MP integration.

---

## 7. Exact evidence needed to authorize ANY implementation

1. **A real or independently-validated design artifact** (at minimum one contradiction case + one control)
   with **known ground truth** for both declared intent and geometric manufacturability. *This is the
   universal blocker — nothing below can be validated without it, and it is the cheapest to obtain.*
2. **A demonstrated catch:** the probe (§6) shows a geometry-derived check flags a real declared-intent
   error the current pipeline accepts, **with no false positive** on the control.
3. **A frequency/importance signal:** at least weak evidence that such contradictions occur often enough to
   matter (not invented demand; a handful of real cases or a practitioner statement suffices to move it off
   "latent").
4. **For Direction 3 only:** a pinned, consumable Velith release that actually produces `EngineeringResult`
   (version > `0.0.0`, API present) — none exists today.

Absent #1–#3, no geometry direction (1 or 2) is authorized; absent #4, Direction 3 cannot leave
specification. If #1–#3 land, the smallest implementation path is **2 built on the minimum of 1**, delivered
as an additive, boundary-ratified check — never generic DFM, never a geometry comparator.

*No application code, schema, test, dependency, frozen spec, ADR, or Git state was changed. This note is the
only artifact produced.*
