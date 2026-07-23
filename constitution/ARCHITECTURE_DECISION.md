# Ecosystem Architecture — Frozen Boundary (v1.0 proposal)

**Role of this document:** Chief Systems Architect review of the proposed
MiniFlyWire → Noetica → Velith → Mini Prometheus stack, prior to freezing.
**Method:** first-principles software + AI-systems architecture, checked against
repository evidence. Where evidence contradicts assumptions, evidence wins.
**Status:** Proposed for ratification. Once accepted, record as a decision in
`DECISIONS.md` and reconcile `VISION.md` naming lineage.

---

## STEP 1 — What is actually built (evidence, not assumption)

Only one repository is physically reachable this session: **`Noetica-agent-lab`**
(`github.com/manish0360-coder/Noetica-agent-lab`). MiniFlyWire, Velith, and Mini
Prometheus exist here **only as references inside this repo's documents** — I have
not inspected their code, so every statement about them below is about *intended*
responsibility, not verified implementation. This is itself the first finding:
**the architecture is currently documentation-led, not code-led.**

Verified facts about the reachable repo:

- **Code present:** `core/agent.py` (an "Agent Zero" JSON status-loop with a clean
  `terminated_reason` vs `success` split and a `check_fn` verifier seam);
  `phase2_memory/*` (a student-tutor: `knowledge_state`, `forgetting`, `concepts`,
  `verdict`, `judge`, `memory_agent` over a fractions curriculum); `agent_zero/step1–9`
  probe scripts; `tests/` (~58 passing). This is education-domain code.
- **Governing docs are far ahead of the code.** `VISION.md`, `DECISIONS.md` (D1–D21),
  `PROJECT_STATE.md`, and `M0–M2` specs describe a *renamed* flagship (**Velith**),
  a verification-first SWE `propose → verify → log` loop, a deterministic Docker
  verifier, and an episode store — and mark **M0/M1 "complete and certified."**
- **That M0/M1 code is not in this repo.** There is no `src/velith/`, no Docker files,
  no verifier, no episode store. The git log ("Restore Noetica repository", "Remove
  accidentally nested project directory") indicates the Velith and Noetica working
  trees were tangled and the Velith code lives elsewhere.
- **`DECISIONS.md` D11** explicitly declares the education code ("MiniNoetica") a
  completed, read-only reference — *not a dependency, not to be extended* — and
  reuses only *patterns* (LLM-call shape, episode→JSONL, test discipline) by
  re-implementation, never import.

**Implication for the freeze:** the boundary you ratify must be honest about two
different arrow types — *research→platform* (ideas re-implemented) and
*platform→application* (code imported). The current diagram draws them the same, and
that is the root of most problems below.

---

## STEP 2 — Per-layer review

### MiniFlyWire — *mostly correct, but mislabelled as a stack layer*

- **Purpose (research cognition): correct.** Keep it as a sandbox whose deliverable
  is validated mechanisms and negative results, not software.
- **Misplacement:** it is drawn as the top of a *dependency* stack, but nothing may
  import it (D11; it carries research-grade code and the LLM-as-judge anti-pattern).
  Its output is *knowledge*, consumed by re-implementation. **Fix:** redraw
  MiniFlyWire as a **feeder lab beside the stack**, connected by a dashed
  "validated-mechanism transfer" arrow — a different arrow type from the solid
  import arrows below it.
- **Add:** an explicit **promotion gate** — the criteria a mechanism must meet
  (falsified, ablated, domain-agnostic, dependency-light) before Noetica is allowed
  to re-implement it. `forgetting.py` and the `KnowledgeState` update rule already
  pass this bar; `judge.py` explicitly does not.

### Noetica — *right ambition, but the list omits the core and over-claims cognition*

- **Purpose (agent platform, not an assistant): correct and worth protecting.**
- **The single biggest omission:** the **shared state substrate**. `DECISIONS.md` D9
  says the architecture is *state-centric* — "a persistent, typed, provenance-tracked
  representation is the substrate; generators, planners, verifiers, learners are
  transformations over it." Your 17-item list is *all transformations and services and
  zero substrate*. Without the substrate named as Noetica's core, the platform will
  drift into a control-flow-centric "bag of agents," which D9 explicitly rejects.
  **Add:** `State Substrate / Blackboard`, `Provenance & Lineage`, `Model-Abstraction
  & Routing` (LLMs swappable — D16.4), and `Cost / Budget / Meta-control` (bounded
  rationality — VISION §5). These are currently missing and are load-bearing.
- **Over-claim risk (homunculus):** listing a bare **"Reasoner"** and **"Planner"** as
  platform components implies Noetica *knows how to reason about the world*. VISION
  forbids a homunculus. **Fix by renaming to mechanism, not mind:** Noetica owns the
  **form** of reasoning/planning — a reasoning *runtime/loop*, a *plan representation*
  and *plan executor*, a *reflection loop*, verification *seams* — never domain
  reasoning **content**. Velith supplies the content.
- **Duplicated-responsibility risk:** `Memory Framework`, `Knowledge Engine`, and
  `Context Engine` overlap. They are three legitimate things *only if* defined
  crisply: **Memory** = persistence of episodes/experience over time; **Knowledge** =
  the typed, provenance-tracked semantic/graph *store engine* (schema-agnostic);
  **Context** = working-set assembly and context-window budgeting for a single
  inference. Write those definitions down or they will collide.
- **Ownership hazard — verification:** "Evaluation" is listed, but the boundary that
  the current repo already got wrong must be stated: **Noetica owns the verification
  *protocol/harness* (how arms run, the held-out lock, metrics, the `Verdict`
  interface); the concrete *verifier/oracle* is domain-owned** (SWE test-runner in
  Velith; SPICE/FEA later; manufacturing checks in Mini Prometheus). A domain verifier
  inside the core is a boundary breach.
- **Remove/relabel:** `Developer APIs` and `Plugin SDK` are *surfaces over* the core,
  not peers of Memory/Planner. Group them as a "developer surface" tier. `Guardrails`,
  `Logging`, `Observability`, `Evaluation` are **cross-cutting platform services**, not
  cognitive primitives — put them in their own tier so the abstraction levels stop
  mixing.

### Velith — *correct direction; split its two sub-layers and bind to interfaces*

- **Purpose (engineering intelligence consuming Noetica): correct.** The three
  "Never reimplement memory/planning/runtime" rules are exactly right — keep verbatim.
- **Mixed abstraction inside Velith:** the list blends *engineering cognition*
  (engineering planner, scientific/physics reasoning, material selection) with
  *tool integration* (CAD orchestration, simulation, optimization, verification).
  **Split conceptually:** `Velith-Core` (engineering knowledge + reasoning content
  expressed as Noetica plans/skills) and `Velith-Adapters` (wrapped external kernels,
  solvers, and the **engineering verifier**, each implementing a Noetica interface).
  This honours VISION §9 "wrap, don't rebuild."
- **Ownership clarity:** the *engineering verifier* lives here but **implements
  Noetica's `Verifier` interface**; the *engineering ontology* lives here but
  **populates Noetica's knowledge store** — interface owned above, content owned here.

### Mini Prometheus — *correct, but larger than one layer, and Digital Twin needs a split*

- **Purpose (manufacturing intelligence consuming Velith): correct.**
- **Scalability risk:** its scope (manufacturing planning, factory automation, supply
  chain, robotics, scheduling, digital twin) is broad enough to become its *own*
  internal stack. Allow a layer to itself be layered (the architecture should be
  **recursive**), rather than forcing all of manufacturing into one flat module.
- **Mechanism/content split again:** a **Digital Twin** is a *stateful, provenance-
  tracked world model synced to a physical system* — that is a **Noetica substrate
  capability** *instantiated* with manufacturing content. The **twin engine** (state
  sync, provenance, versioning) belongs to Noetica; the **manufacturing twin content**
  belongs to Mini Prometheus.

### "AI Manufacturing Intelligence" — *not a 5th project*

The diagram shows five boxes but defines four. "AI Manufacturing Intelligence" is the
**mission/outcome the stack delivers**, i.e. Mini Prometheus's north star — not a
separate repository. **Remove it as a layer**; keep it as the stated goal, or it will
invite a phantom codebase and duplicated ownership.

---

## STEP 3 — Architectural violations found

1. **Mixed dependency types.** MiniFlyWire→Noetica (knowledge transfer, no import) is
   drawn identically to Noetica→Velith→Mini Prometheus (code import). Different arrows.
2. **Mechanism/content conflation at every seam.** "Reasoner", "Knowledge", "Verifier",
   "Digital Twin" each appear where a *mechanism* and its *domain content* are fused.
   This is the recurring defect; §4 gives the single fix.
3. **Missing shared-state substrate.** The declared state-centric core (D9) is absent
   from Noetica's responsibilities → risk of a control-flow-centric bag-of-agents.
4. **Undefined verification ownership.** Protocol-vs-oracle split unstated; the repo has
   already leaked a domain (SWE) verifier toward the core.
5. **Mixed abstraction levels inside Noetica and Velith.** Cognitive primitives,
   cross-cutting services, and developer surfaces listed as peers.
6. **Hidden coupling via shared schemas.** If layers share episode/state types by
   convention, a Noetica schema change silently breaks Velith. Needs versioned,
   typed public contracts (the existing `Verdict` dataclass with construction-time
   validation is the right seed pattern).
7. **Documentation/code divergence & tangled repos** (STEP 1) — a provenance violation
   by the program's own Principle 7 ("if we can't say *why it did that*, it's a toy").
8. **Speculative generality risk.** Building a full 17-capability platform before it has
   two real consumers is the classic "framework with no users" trap; interfaces guessed
   in the abstract are usually wrong. (Addressed in §4 and STEP 8.)

*No circular dependency exists in the strict linear model — that part is healthy.* The
risk is latent: Noetica's eval harness must test itself against a **reference/fake**
verifier, never import Velith's real one. Enforce with a test.

---

## STEP 4 — The best boundary: one invariant that resolves the rest

> **Noetica owns *mechanisms and interfaces and the shared state substrate*.
> Domain layers own *content and the concrete implementations* of those interfaces.
> Research (MiniFlyWire) owns *discovery*; it is a feeder, never a dependency.**

Two axes make this unambiguous:

- **Mechanism vs. Content.** *How* to remember / plan / verify / reason (Noetica) vs.
  *what* is remembered / planned / verified / reasoned about (Velith, Mini Prometheus).
- **Interface vs. Implementation.** Noetica publishes typed interfaces
  (`Verifier`, `MemoryStore`, `Skill`, `Tool`, `Plan`, `WorldModel`); domains ship the
  concrete classes (`SweVerifier`, `FeaVerifier`, `EngineeringOntology`, `CadTool`).

**Build rule that prevents speculative generality (adopt this — it reconciles the
vision with the repo's pragmatism, D11/D12):** *a capability is promoted into Noetica
only when it has at least one real consumer and a credible second on the horizon.*
Grow the platform by **extraction from Velith**, not by up-front design. Harvest, don't
speculate. This keeps the four boundaries as **architectural intent** while letting the
code mature bottom-up.

---

## STEP 5 — Responsibility matrix

One owner per capability. `impl` = implements an interface owned above. `—` = must not
touch. `(feeds)` = contributes ideas via re-implementation, not code.

| Capability | MiniFlyWire | Noetica | Velith | Mini Prometheus |
|---|---|---|---|---|
| Cognitive research / hypothesis testing | **Owner** | — | — | — |
| Validated-mechanism discovery | **Owner** | (consumes as ideas) | — | — |
| Shared **state substrate / blackboard** | (feeds) | **Owner** | consumes | consumes |
| **Provenance & lineage** | (feeds) | **Owner** | consumes | consumes |
| **Memory** (episodic/semantic persistence) | (feeds) | **Owner (framework)** | uses | uses |
| **Knowledge store engine** (typed graph, retrieval) | (feeds) | **Owner (engine)** | populates w/ eng. content | populates w/ mfg. content |
| **Context** assembly / window budgeting | (feeds) | **Owner** | uses | uses |
| Reasoning **runtime/loop** (form) | (feeds) | **Owner** | uses | uses |
| Reasoning **content** (domain reasoning) | — | — | **Owner (engineering)** | **Owner (manufacturing)** |
| Planning **representation + executor** (form) | (feeds) | **Owner** | uses | uses |
| Planning **content** (engineering/mfg plans) | — | — | **Owner** | **Owner** |
| Reflection / self-critique loop | (feeds) | **Owner** | uses | uses |
| Tool system + **Tool** interface | — | **Owner** | impl (CAD, solvers) | impl (MES, PLC, robots) |
| Skill system + **Skill** interface | — | **Owner** | impl (eng. skills) | impl (mfg. skills) |
| Agent runtime & lifecycle | — | **Owner** | uses | uses |
| Multi-agent coordination | (feeds) | **Owner** | uses | uses |
| Model abstraction / routing / cost | — | **Owner** | uses | uses |
| Meta-control / budget (bounded rationality) | (feeds) | **Owner** | uses | uses |
| **Verification protocol / harness** | (feeds) | **Owner** | uses | uses |
| **Verifier / oracle** (concrete) | — | interface only | **Owner** (SWE, FEA, SPICE) | **Owner** (mfg checks) |
| Evaluation / experiment arms / held-out lock | (feeds) | **Owner** | configures | configures |
| Guardrails / safety policy engine | (feeds) | **Owner (engine)** | domain policy | domain policy |
| Logging / observability | — | **Owner** | emits | emits |
| Developer SDK / plugin / public APIs | — | **Owner** | consumes | consumes |
| Engineering ontology & physics/material knowledge | — | — | **Owner** | consumes |
| CAD / simulation / optimization orchestration | — | — | **Owner** | consumes |
| **Digital-twin engine** (state sync mechanism) | (feeds) | **Owner** | uses | uses |
| Digital-twin **content** (factory/product twin) | — | — | (eng. models) | **Owner** |
| Manufacturing planning / scheduling / MES | — | — | — | **Owner** |
| Factory automation / robotics / supply chain | — | — | — | **Owner** |

---

## STEP 6 — Dependency rules

Import graph is a strict DAG, one direction only:

```
Mini Prometheus  ──imports──▶  Velith  ──imports──▶  Noetica
        MiniFlyWire  ┄┄feeds ideas (re-implementation, never import)┄┄▶  Noetica
```

Rules:

1. **Noetica imports nothing upward and nothing domain-specific.** It never imports
   Velith, Mini Prometheus, or MiniFlyWire.
2. **Velith imports Noetica only.** Never Mini Prometheus (no upward import), never
   MiniFlyWire.
3. **Mini Prometheus imports Velith (and transitively Noetica) only.** It never reaches
   past Velith to re-implement engineering, and never imports agent infra directly in a
   way that bypasses Velith's engineering layer for engineering concerns.
4. **MiniFlyWire is imported by no one.** It is a source of validated ideas; transfer is
   by reading + re-implementing behind the promotion gate (STEP 2).
5. **All cross-layer contact is through Noetica-published, versioned, typed interfaces.**
   No sharing of concrete internal types across a repo boundary.
6. **Sibling verticals** (if Mini Prometheus fractals into robotics/supply-chain
   modules) coordinate through Velith/Noetica contracts, never sibling-to-sibling imports.
7. **Test-enforced:** Noetica's self-tests use a reference/fake verifier; a CI check
   fails the build if Noetica acquires a domain import or if a domain layer imports a
   sibling.

---

## STEP 7 — Public interfaces per project

### MiniFlyWire
- **Inputs:** research questions, cognitive hypotheses, datasets.
- **Outputs:** validated (or falsified) mechanisms + written specs; reference
  implementations marked research-grade.
- **Public API:** none (no importable surface).
- **Internal:** simulations, RL, neural activation, replay — free to be messy.
- **Others consume:** *documents and validated mechanism specs*, by re-implementation.

### Noetica
- **Inputs:** a task/goal, a configured model+budget, tool/skill/verifier
  registrations, memory handles.
- **Outputs:** grounded agent runs with provenance, updated memory/knowledge state,
  evaluation results.
- **Public API (stable, versioned):** `Agent`/`Runtime`, `MemoryStore`, `KnowledgeStore`,
  `Context`, `Plan` + `Planner`/`Executor`, `ReasoningLoop`, `Reflector`,
  `Tool`, `Skill`, `Verifier` (protocol), `EvalHarness`, `ModelRouter`, `BudgetMeter`,
  `Provenance`, `Guardrail`. Everything a domain needs is an interface + a default.
- **Internal:** substrate storage, routing internals, harness plumbing.
- **Others consume:** the interfaces above — *never* Noetica's internal types.

### Velith
- **Inputs:** engineering intent + constraints; Noetica runtime + interfaces.
- **Outputs:** verified engineering artifacts (designs, analyses) with provenance and
  calibrated uncertainty; concrete `Verifier`/`Tool`/`Skill` implementations.
- **Public API:** `EngineeringTask`, `EngineeringResult`, `DesignArtifact`,
  domain verifier/tool implementations, engineering ontology accessors.
- **Internal:** CAD/solver adapters, physics/material knowledge, engineering planners
  expressed as Noetica plans.
- **Others consume (Mini Prometheus):** engineering results + the engineering-task API —
  not Noetica directly for engineering concerns.

### Mini Prometheus
- **Inputs:** product intent; Velith engineering intelligence.
- **Outputs:** manufacturable plans, factory/robotics/supply-chain workflows, digital-
  twin state, production schedules.
- **Public API:** `ManufacturingTask`, `ProductionPlan`, twin content accessors.
- **Internal:** MES/PLC/robotics adapters, scheduling, supply-chain logic.
- **Others consume:** end users / factory systems (top of the stack).

---

## STEP 8 — Challenge to my own architecture

A hostile review board would raise three serious objections.

**Objection A — "This is speculative generality. You have one real consumer; build
Velith, not a platform."** This is the strongest critique and is exactly what this
repo's own `DECISIONS.md` did when it collapsed Noetica into Velith. **Partially
conceded.** A platform designed before two consumers guesses its interfaces wrong.
**Resolution (already folded into §4):** keep the four boundaries as *logical* layers,
but grow Noetica by **extraction from Velith** — promote a capability only when it has a
real use and a second on the horizon. This keeps decade-scale reusability without paying
for imaginary generality now. I did *not* keep the naive "design the whole platform
first" reading of the proposal.

**Objection B — "Four repos is coordination overhead; use a monorepo with internal
packages."** **Largely conceded.** Separate repos impose cross-repo CI, version skew,
and contract churn that a small team will feel every week. **Resolution:** treat the four
layers as **packages inside one (or few) repos with an enforced package-level DAG**,
not necessarily four Git repos. The *boundary* is architectural; the *packaging* should
start consolidated and split only when a layer needs independent release cadence or an
independent team. MiniFlyWire stays separate (different license/quality bar); Noetica +
Velith (+ later Mini Prometheus) can begin as one repo, many packages.

**Objection C — "A single cognitive substrate won't generalize from software to physical
domains without leaking assumptions."** **Acknowledged as an open research risk**, not a
design error. The migration ladder (D4/D5: SWE → PCB → HDL → mechanical/FEA) is the
correct mitigation — it widens the verification model-gap gradually, and each rung tests
whether the substrate held. The architecture must therefore keep the `Verifier`
abstraction *general enough to represent an approximate oracle with calibrated
uncertainty*, not just a boolean pass/fail. I have specified the verifier as
protocol-owned-above / oracle-owned-below precisely so this can evolve.

**Why the revised architecture still wins:** it preserves the linear, cycle-free
dependency DAG (easy to reason about for a decade), it gives every capability exactly one
owner via the mechanism/content invariant, it names the state substrate as the true core
(honouring D9), it fixes the two things the repo got wrong (verifier ownership and the
MiniFlyWire arrow type), and it defuses the speculative-generality trap by building
platform-by-extraction. It is evolutionary: nothing above requires a rewrite — it
requires renaming a few responsibilities, adding the substrate + provenance + routing +
budget to Noetica's charter, and reconciling the repo/naming bookkeeping.

---

## Final question — what five top labs would agree, challenge, and converge on

Reasoning from first principles, not house style:

**Broad agreement.**
- **Verification-first grounding** and a **falsifiable compounding hypothesis** — treated
  as the correct, rare discipline; the A0/A1/A2/A3 differential design (D6–D8) is
  textbook-clean.
- **LLMs as swappable components, not the architecture**; **provenance and observability
  as first-class**; **a strict acyclic dependency DAG**; **separation of a domain-agnostic
  core from domain applications**.
- **State-centric substrate** over control-flow orchestration — increasingly the
  consensus for durable agent systems.

**Likely challenges.**
- **Speculative platform-before-consumers** — near-universal pushback; the consensus
  instruction would be *extract the platform from a working application*, which is exactly
  Objection A.
- **A monolithic general "Reasoner/Planner"** — challenged as homunculus-shaped; the field
  favours **compositional, typed, tool-using loops with external verification** over a
  central reasoning engine.
- **Four separate repositories** — challenged as premature process overhead; **monorepo +
  enforced internal boundaries** is the more common recommendation until scale demands
  splitting.
- **Strict single-chain linearity** — real systems need **cross-cutting platform services**
  (provenance, eval, budget, safety) that every layer uses, plus room for **sibling
  verticals**; reviewers would want those drawn explicitly rather than forced into a pure
  line.
- **One substrate generalizing across software→physical** — flagged as the central
  empirical risk; they would endorse the migration ladder as the honest test.

**Strongest consensus architecture (what they would converge on).**
A **few-repo / monorepo** system with a **strictly enforced internal package DAG**; a
**domain-agnostic core** = a *typed, provenance-tracked state substrate* + *swappable
model layer* + *memory / context / eval / verification **interfaces*** + cross-cutting
services (budget, safety, observability); **domain layers implement those interfaces and
own all content**; the **verification protocol is core-owned while concrete oracles are
domain-owned** and are allowed to be approximate with calibrated uncertainty; and — most
importantly — **the platform is grown by extraction from real consumers, not designed up
front.** In one line: *keep your four boundaries as logical layers, be pragmatic about
packaging, name the state substrate as the core, and let the platform crystallize out of
Velith rather than being built ahead of it.*

That is the architecture that survives the decade.
