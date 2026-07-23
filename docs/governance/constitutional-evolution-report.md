# Constitutional Evolution Report — Architectural Archaeology of the AI Manufacturing Ecosystem

- **Status:** Findings for project-owner ruling. **AI-authored analysis — recommendation only, never a ratification** (Handbook Law 22).
- **Method:** Reconstruction of the *legal history* from primary sources — repository structures, commit/release metadata, founding VISION, the DECISIONS ledger, the boundary-review architecture decision, and the frozen Handbook. Evidence governs; nothing is invented, optimized, or modernized.
- **Question:** How did the architecture evolve, which document has authority when two disagree, what should Mini Prometheus own, and which of four verdicts applies.
- **Date:** 2026-07-23.

---

## 0. Sources inspected (primary evidence)

| # | Repository / document | Nature | Key metadata |
|---|---|---|---|
| R1 | `AI-intereactive-Brain-inspired-from-Mini-Flywire-` (**MiniFlyWire**) | Research lab, JavaScript/Three.js | 37 commits; repo-id 1219302525 (oldest); `render/`, `research/`, `experiments/exec_influence`, `benchmarks/harness`, `LAB_NOTES`, `PROJECT_MEMORY` |
| R2 | `Noetica-agent-lab` (**"Noetica"/MiniNoetica**) | Education cognitive lab, Python | repo-id 1265903809; 58 tests; `agent_zero/`, `core/`, `phase2_memory/`, `docs/`; Phase 1–2 complete |
| R3 | `Velith` | Engineering flagship, Python + Docker | repo-id 1275383336; 26 commits; **M0 released `m0-complete` 2026-06-21**; `docs/VISION.md`, `docs/DECISIONS.md`, `src/velith`, `docker/` |
| R4 | `pcos-samantha` | Personal cognitive OS ("Samantha") | repo-id 1286952364; 31 commits; own `PROJECT_CONSTITUTION.md`, "12 Immutable Principles"; **separate domain** |
| R5 | `mini-prometheus` | Manufacturing runtime (this repo) | repo-id 1302382636 (newest); 2 commits; `constitution/`, `contracts/`, `src/mini_prometheus/` |
| D1 | `Velith/docs/VISION.md` | Founding vision | Program **PrometheusLite**, System **Noetica**; 10 principles; manufacturing = decade north-star |
| D2 | `Velith/docs/DECISIONS.md` | Decision ledger | **D1–D25**, last updated 2026-07-06; explicit **naming lineage**; D9 state-centric; D11 MiniNoetica separate |
| D3 | `ARCHITECTURE_DECISION.md` (uploaded) | Boundary review, "v1.0 proposal prior to freezing" | Proposes the four-layer mechanism/content split; responsibility matrix; STEP 6 dependency DAG |
| D4 | `HANDBOOK_v1.1.md` (uploaded) | Frozen Constitution | Canonical four-layer taxonomy (N.1); 23 Laws; N.2/N.3 naming reconciliation; Law 22/23 |

Repo-ids are monotonic with creation time, giving an objective creation order: **R1 → R2 → R3 → R4 → R5**.

---

## Part 1 — Evolution: how the architecture evolved

The program is one continuous line, not four independent projects. Five phases, each with primary evidence.

**Phase 0 — Cognitive research (MiniFlyWire, R1).** A brain-inspired, JavaScript cognitive architecture: reinforcement learning, episodic + semantic memory, embedding learning, attention, executive control, planning, motivation, long-term consolidation, all inside a 3D neural visualization. Its own README frames it as "a research platform" whose intelligence "emerges from the cooperation of multiple specialized cognitive systems." *Deliverable: validated cognitive primitives — knowledge, not production code.*

**Phase 1 — Education cognitive lab (Noetica-agent-lab / "MiniNoetica", R2).** A Python, test-driven **student-tutor** system: an agent loop (`agent_zero/`), a provider-agnostic LLM interface and JSON/`Verdict` contracts (`core/`), and a Memory Agent with `KnowledgeState` and a forgetting model (`phase2_memory/`). Its README is explicitly education-domain ("How do we know whether someone has actually learned?"). This is where the founding **VISION.md** and **DECISIONS.md** were authored. Per **D2/D11** it is designated **MiniNoetica** — "a completed learning project and read-only reference repository … not a dependency," whose value was "the engineering experience and reusable implementation patterns it produced, not its educational domain."

**Phase 2 — Verification-first engineering flagship (Velith, R3).** The ratified system. **VISION.md** (D1) names Program *PrometheusLite*, System *Noetica*, with manufacturing as the Level-3 decade north-star. **DECISIONS.md** (D2) ratifies verification-first (D2), deterministic zero-model-gap verification (D3), software-first vertical (D4), the migration ladder software→PCB→HDL→mechanical/FEA→manufacturing (D5), the compounding experiment (D6–D8), and the **state-centric substrate** (D9). The code delivers M0 (containerized skeleton, released 2026-06-21) and M1 (`propose → verify → log`: a local model proposes a patch, a deterministic Docker verifier disposes of it, the outcome is a content-hashed **episode** that survives container exit). At this stage **"Velith" is the name of the whole system.**

**Phase 3 — The four-layer freeze (ARCHITECTURE_DECISION → HANDBOOK, D3→D4).** A first-principles boundary review (D3) found the system was outgrowing one layer and proposed splitting it by **mechanism vs. content**: a reusable platform (Noetica) beneath domain applications (engineering = Velith; manufacturing = Mini Prometheus), with MiniFlyWire as a feeder, never a dependency. The **Handbook v1.1** (D4) froze this as the canonical four-layer taxonomy (N.1), added 23 Laws, and — crucially — **re-attributed every prior name** rather than discarding it (N.2/N.3).

**Phase 4 — Manufacturing runtime (mini-prometheus, R5).** The newest repo, Layer 4. Its machinery (contract spine, five-layer doc hierarchy, ADR governance) is sound, but its stated *ownership* was written from a pre-Handbook charter summary and diverged from the line above (Part 5).

**Parallel, not in the stack — pcos-samantha (R4).** A local-first, node-based **personal** cognitive OS ("Observe → Remember → Retrieve → Reason → Speak") for a voice assistant persona. Its domain (personal productivity, spatial perception, TTS) has **no** manufacturing or engineering-verification content and **no** dependency on the stack. It contributes to the *AI-manufacturing architecture* **nothing in ownership**; it contributes **methodological evidence only** — its `PROJECT_CONSTITUTION.md`, "12 Immutable Principles," module-boundary style ("Perception observes but does not think… Infrastructure orchestrates but contains no business logic"), Architecture-Freeze, and ADR/DECISION_LOG show the author's governance methodology maturing in parallel — the same style later formalized as the Handbook's Laws.

---

## Part 2 — Authority: which document governs when two disagree

**Instruction honored:** the Handbook is *not* treated as authoritative merely because it declares itself so (P.2). Authority is established from the evolutionary record.

### The evidence chain

1. **Each founding document names its own supersession path — upward.**
   - VISION.md §9: "Superseded only by explicit, justified amendment recorded in `DECISIONS.md`." → VISION yields to the DECISIONS ledger.
   - DECISIONS.md: "changed only by a new dated entry that explicitly supersedes the prior one." It is the ratification ledger VISION defers to.
   - So the founding docs themselves establish a chain of authority terminating in a ratified ledger — not a frozen-in-time equality.

2. **DECISIONS.md contains an explicit, dated naming lineage that pre-authorizes the split.** Verbatim: *"This program was discussed during its review phase under the working names PrometheusLite / Mini Prometheus (program) and Noetica (system). The ratified flagship name is Velith. Where earlier internal documents use the older names, they refer to this same project."* This is primary evidence that **"Mini Prometheus" and "Noetica" were working names for one evolving system**, expected to be re-attributed — exactly what the Handbook later does.

3. **The Handbook is chronologically last and continuous, not contradictory.** Its ten "design principles" (§1.11) are the **verbatim** VISION.md §5 principles; its state-centric core is DECISIONS D9; its verification-first law is D2/D3; its "grow by extraction" is the boundary review's build rule. The Handbook **preserves the theory** and adds only (a) the four-layer packaging and (b) 23 Laws. Nothing substantive was reversed.

4. **The split is independently corroborated.** The boundary review (D3) — an independent, first-principles analysis explicitly "checked against repository evidence" — reached the **same** conclusions the Handbook froze: mechanism/content invariant, state substrate as the platform core, verifier *protocol* owned above / *oracle* owned below, MiniFlyWire as a feeder never imported, platform-by-extraction. Two independent documents converging is evidence of correctness, not circular self-assertion.

### Adjudication (per the four categories requested)

| When these disagree… | Verdict | Evidence |
|---|---|---|
| VISION "Noetica = the System" vs. Handbook "Noetica = Layer-2 mechanisms only" | **Newer intentionally specializes older** (not conflict) | VISION §9 defers upward; DECISIONS lineage pre-authorizes; Handbook N.2 maps it |
| DECISIONS "Velith = whole system, owns the substrate (D9)" vs. Handbook "substrate = Noetica; Velith = engineering content" | **Different abstraction levels, reconciled by extraction** (not conflict) | Handbook N.3: the substrate/loop machinery is *extracted up* from the Velith spike into Noetica; the engineering content stays Velith |
| "Mini Prometheus = program" (old) vs. "Mini Prometheus = Layer-4 manufacturing" (new) | **Newer intentionally supersedes** (documented re-scoping) | DECISIONS lineage + Handbook N.1/N.2 |
| Handbook + boundary-review + DECISIONS + VISION **vs. the `mini-prometheus` repo's ownership claims** | **Genuine conflict — the repo is the outlier** | Part 5 |

**Conclusion of Part 2:** the founding documents and the Handbook form one internally consistent, self-superseding lineage. The Handbook governs — established by evolutionary evidence (continuity of principle + explicit lineage + independent corroboration), *not* by its supremacy clause. The only genuine conflict is between the newest **implementation repo** and that otherwise-consistent line.

---

## Part 3 — What Mini Prometheus should legitimately own

Derived from the whole evolution (VISION §3/§8 Level-3, DECISIONS D5 migration ladder, boundary-review STEP 5 matrix, Handbook §2.4 + §9). Six categories, kept strictly separate:

| Category | Owner | For Mini Prometheus |
|---|---|---|
| **Platform mechanisms** | **Noetica** | **Consumed, never owned:** state substrate, provenance/lineage, memory/knowledge/context engines, reasoning & planning *form*, reflection, model routing, budget/meta-control, eval & verification *protocol/harness*, **digital-twin/state-sync engine**, data-lifecycle framework. |
| **Engineering mechanisms & content** | **Velith** | **Consumed via Velith's API, never owned:** engineering ontology, physics/material knowledge, CAD/simulation/optimization orchestration, the concrete engineering *verifier/oracle*, engineering reasoning *content*, engineering planners-as-plans. |
| **Manufacturing "mechanisms"** | **Mini Prometheus (as content/adapters)** | Manufacturing-specific planning/scheduling logic and MES/PLC/robotics *adapters*. These are domain content + wrapped integrations, **not** reusable platform mechanisms; any domain-agnostic mechanism discovered here is **extracted up into Noetica** (Law 8), never kept as a private platform. |
| **Manufacturing content** | **Mini Prometheus (owned)** | **Owned:** manufacturing planning & scheduling ("its heart"), factory/robotics/supply-chain workflows, MES/production execution, the **manufacturing digital-twin content** (on Noetica's twin engine), Sim2Real divergence tracking, experience collection. |
| **Shared contracts** | **Noetica publishes; all consume** | Noetica interfaces (`WorldModel`, `MemoryStore`, `Verifier`/`Verdict`, `Plan`, `Tool`, `Skill`, state-substrate schema) + Velith's `EngineeringTask`/`EngineeringResult`/`DesignArtifact` + upward **Experience data contracts** (Law 21). MP *publishes* `ManufacturingTask`, `ProductionPlan`, twin-content accessors. |
| **Consumed interfaces** | — | Velith engineering API as the **engineering entry point**; Noetica platform mechanisms (substrate, provenance, twin engine) **through interfaces**. **Never imports MiniFlyWire** (Law 4); **never bypasses Velith** for engineering (Law 9). |

---

## Part 4 — Concept lineage: experimental → platform → engineering → manufacturing

| Concept | Originated (experimental) | Became a platform mechanism (Noetica) | Became engineering (Velith) | Became manufacturing (Mini Prometheus) |
|---|---|---|---|---|
| Episodic memory / episode store | MiniFlyWire `episodic.js`; MiniNoetica episode→JSONL | **Yes** — memory framework + episode store, extracted from Velith's content-hashed episode store | Velith episode store instance (SWE) | Manufacturing experience records |
| Forgetting / consolidation | MiniFlyWire `longTermConsolidation.js`; MiniNoetica forgetting model | **Yes** — data-lifecycle/forgetting framework (Handbook §11.11) | consumes | configures retention |
| Verdict / verification | MiniNoetica `Verdict` JSON contract; Velith verdict taxonomy | **Yes** — `Verifier` *protocol* + `Verdict` type | concrete SWE **oracle** (owned) | manufacturing checks (owned) |
| State substrate | VISION §5.2 / DECISIONS **D9** | **Yes** — the platform core | consumes | consumes (twin content on it) |
| Provenance / content-hash | Velith M1 content-hash | **Yes** — provenance mechanism | consumes | consumes |
| LLM adapter / routing | MiniNoetica LLM-call shape; Velith `llm/client.py` (D16.4) | **Yes** — model routing/abstraction | consumes | consumes |
| Reasoning / planning | MiniFlyWire planning/executive; MiniNoetica agent loop | **Yes** — reasoning/planning *form* | reasoning/planning **content** | manufacturing plans (content) |
| Digital twin | (implied by state substrate) | **Yes** — twin/state-sync *engine* | engineering models | twin **content** (owned) |

Note the governing rule visible across the record: **research primitives transfer by re-implementation (never import)** (D11, Law 4/7); **application mechanisms transfer up by extraction** (D3 build rule, Law 8). Two arrow types, consistently applied.

---

## Part 5 — Terminology reconciliation vs. genuine conflicts

### Terminology changed, meaning preserved (reconcilable — not conflicts)

| Term | Where | Canonical meaning | Ruling |
|---|---|---|---|
| PrometheusLite | VISION | The whole program/ecosystem | Renamed; = the ecosystem, not a layer |
| "Noetica" as *the System* | VISION | Split → Layer-2 mechanisms + Layer-3 engineering content | Specialized (N.2) |
| "Velith" as *whole system* | DECISIONS | Layer-3 engineering content; loop machinery extracted up to Noetica | Specialized (N.3) |
| "Mini Prometheus" as *program name* | DECISIONS lineage | Layer-4 manufacturing | Superseded/re-scoped (documented) |
| MiniNoetica | DECISIONS D11 | Completed education reference (= Noetica-agent-lab), not a layer | Consistent |
| MP repo "Situation State" | mini-prometheus | Manufacturing situation/twin **content** on Noetica's substrate (no canonical object by this name) | Reconcile terminology |
| MP repo "Constraint Network" | mini-prometheus | Manufacturing **constraint content** in Noetica's knowledge store (no canonical object) | Reconcile terminology |

### Genuine constitutional conflicts (all in one place)

**Conflict C1 (the only live one) — `mini-prometheus` ownership vs. the entire governing line.** The repo's README/architecture claims MP **owns** *Engineering cognition, Situation State, Engineering World Model, Constraint Network, Engineering reasoning* and integrates **all three** upstreams (including a `integrations/miniflywire/` adapter). This contradicts, simultaneously:
- Handbook §1.10/§2.4 + Laws 3, 4, 6, 9 (state substrate/`WorldModel` = Noetica; engineering content = Velith; MP = manufacturing content; MiniFlyWire imported by no one);
- the boundary review's STEP 5 matrix and STEP 6 DAG;
- DECISIONS **D9** (substrate is the platform core) and **D11** (research/education code is never a dependency);
- VISION §5.2.

This is **more than terminology**: "MP owns Engineering cognition/reasoning" and the MiniFlyWire adapter are genuine **ownership and dependency-graph** errors (Law 4/6/9), not naming. It traces to the pre-Handbook charter summary, **not** to any founding document. *(Already documented in `constitution-source-audit.md` and `CAP-0001`; this report supplies the full evolutionary evidence behind them.)*

**Non-conflicts confirmed:** D9 "Velith owns substrate" vs. Handbook "Noetica owns substrate" is resolved by extraction (N.3), not a contradiction. Four separate repos vs. Handbook §11.9 "packaging is pragmatic" is **permitted** (a layer may be its own repo for independent cadence), so it is not a violation.

---

## Ownership map (authoritative, post-reconciliation)

```
MiniFlyWire  → cognitive primitives (research). Owned by no one downstream. Transfer = re-implementation.
Noetica      → mechanisms + interfaces + state substrate + provenance + twin engine + verification PROTOCOL
                + memory/knowledge/context/routing/budget/eval/data-lifecycle FRAMEWORKS.
Velith       → engineering CONTENT: ontology, physics, CAD/sim orchestration, concrete engineering ORACLE,
                engineering reasoning/planning content. Implements Noetica interfaces.
MiniPrometheus → manufacturing CONTENT: planning/scheduling, factory/robotics/supply-chain/MES adapters,
                manufacturing twin CONTENT, Sim2Real, experience collection. Implements interfaces; consumes Velith.
pcos-samantha → OUTSIDE the stack. Owns nothing here. Methodological evidence only.
```

## Dependency map (strict acyclic — DECISIONS/Handbook/boundary-review all agree)

```
MiniPrometheus ──imports──▶ Velith ──imports──▶ Noetica
        MiniFlyWire ┄┄feeds ideas (re-implementation, never import)┄┄▶ Noetica
Rules: no upward/cyclic imports (Law 9); MiniFlyWire imported by no one (Law 4);
       no sibling-to-sibling imports (Law 19); cross-layer only via versioned typed interfaces (Law 14);
       experience flows up as DATA, never code (Law 12/21).
```

---

## Final recommendation

> ### Verdict: **(3) Repository ownership correction required.**

**Why not (1) Already correct:** the `mini-prometheus` repo claims ownership of the state substrate, engineering world model, engineering cognition/reasoning, and a constraint-network object, and carries a MiniFlyWire adapter — each contradicted by the founding DECISIONS (D9/D11), the boundary review, and the Handbook (Laws 3/4/6/9). (Conflict C1.)

**Why not (2) Terminology reconciliation only:** renaming "Situation State" etc. is necessary but **insufficient** — "MP owns Engineering cognition/reasoning" and the `integrations/miniflywire/` dependency are real ownership/DAG violations, not naming. Terminology reconciliation is a *component* of the fix, not the whole of it.

**Why not (4) Fundamental redesign:** a redesign is warranted only if the prior evolution is **internally inconsistent**. The evidence shows the opposite: VISION, DECISIONS (D1–D25), the boundary review, and the Handbook share identical principles, a documented naming lineage, and an independently corroborated mechanism/content split. The lineage is coherent end-to-end. The defect is **localized to one repository's charter**, and the repository's *machinery* (contract spine, hierarchy, ADR/CAP governance) is already Handbook-aligned. Nothing in the theory or the runtime architecture needs redesigning.

**The correction (bounded, evolutionary):** re-scope `src/mini_prometheus/` and `integrations/` to manufacturing content that **consumes** Velith→Noetica; drop the MiniFlyWire adapter (Law 4); reconcile the object names per Part 5; transcribe the Handbook into `constitution/`. This is exactly the change already drafted in **`CAP-0001`**, now backed by the full evolutionary record. Per Laws 22/23 it requires project-owner ratification; this report ratifies nothing.

---

*Reconstruction of the project's legal history from primary sources. Changes no frozen content and ratifies nothing. The project owner rules (Laws 22, 23).*
