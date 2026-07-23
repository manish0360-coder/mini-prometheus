# THE ENGINEERING CONSTITUTION AND ARCHITECTURE HANDBOOK

### The Permanent Operating Manual of the AI Manufacturing Intelligence Ecosystem

**Ecosystem:** MiniFlyWire → Noetica → Velith → Mini Prometheus
**Document class:** Constitution. Highest-priority artifact in the ecosystem.
**Version:** 1.1
**Status:** RATIFIED (Handbook v1.1, derived from and superseding the scope of *Architecture Constitution v1.0*)
**Amendments in this version:** integrates the five approved constitutional amendments ratified at the final review stage — Data Contract Law (Law 21), AI Contributor Oversight (Law 22), Architectural Stability + CAP (Law 23), Infrastructure Ownership (§6.21, matrix), and Data Lifecycle Governance (§11.11). No architecture, boundary, or numbering was redesigned. See Appendix E.
**Governs:** every roadmap, repository, milestone, module, API, pull request, model, and contributor — human or AI.
**Supersession:** amended only by the Constitution Amendment Proposal (CAP) procedure in Part XI. Never changed silently.

---

> **How to read this document.** This handbook is written to be read alone. A contributor — human or AI — who joins the ecosystem five years from now should be able to read only this document and correctly decide *where a module belongs*, *whether it violates the architecture*, *how it interacts with other layers*, and *what it must never do*, without asking the original authors. Where that test fails, the section is defective and must be amended, not worked around.
>
> This is a **standard**, not a tutorial and not an implementation. It defines architecture, philosophy, responsibilities, boundaries, workflows, laws, governance, and decision process. It does not contain application code, and it does not authorize any. Code is written *downstream* of this handbook and must conform to it.

---

## MASTER TABLE OF CONTENTS

**Front Matter**
- Preamble — Authority, Scope, and Precedence
- Canonical Naming and the Reconciliation of Prior Documents

**Part I — Foundation**
Mission · Vision · Long-term goals · Research / engineering / scientific philosophy · What the ecosystem is and is not · Core definitions · Terminology · Design principles

**Part II — The Four Projects**
Per-project charters: MiniFlyWire · Noetica · Velith · Mini Prometheus

**Part III — How the Ecosystem Works**
The full path from human idea to factory to experience, explained step by step

**Part IV — The Three Flows**
Knowledge Flow · Code Flow · Experience Flow

**Part V — Cognitive Research (MiniFlyWire)**
Why cognition exists; the cognitive primitives; promotion and validation

**Part VI — Noetica (The Platform)**
Every subsystem, and why each exists

**Part VII — Velith (Engineering Intelligence)**

**Part VIII — Mini Prometheus (Manufacturing Intelligence)**

**Part IX — Boundaries and the Responsibility Matrix**

**Part X — Architecture Laws**

**Part XI — Governance**

**Part XII — Implementation Workflow**

**Part XIII — Checklists**

**Appendices**
A. Glossary · B. Prior-document map · C. Amendment / ADR / Promotion / CAP templates · D. Open research questions · E. Amendment history

---

# PREAMBLE — Authority, Scope, and Precedence

## P.1 What this document is

This handbook is the **Constitution** of the ecosystem whose four permanent projects are **MiniFlyWire, Noetica, Velith, and Mini Prometheus**, and whose decade-scale purpose is **AI Manufacturing Intelligence**. It is the single source of truth for the *shape* of the system: its layers, boundaries, ownership, dependency rules, flows, laws, and governance.

It exists because the ecosystem is a long-lived research program, not a product sprint. Programs that live for a decade fail not from any single wrong line of code but from **architectural drift**: boundaries that erode one convenient exception at a time until no one can say what belongs where or why. This Constitution is the fixed point against which every future decision is checked so that drift is detected the moment it is proposed rather than discovered years later.

## P.2 The authority hierarchy

When two instructions conflict, the higher item wins. This ordering is itself constitutional and may only be changed by amendment.

1. **This Handbook** (the Constitution) — architecture, boundaries, laws, governance.
2. **The Decision Record** (`DECISIONS.md`, entries D1–D21 and successors) — ratified engineering decisions. Where a decision and this Handbook appear to conflict, see P.4; the conflict is resolved explicitly, never by silent preference.
3. **The Vision** (`VISION.md`) — the *why* and *toward what*. Governs purpose and non-goals; does not prescribe structure.
4. **The scientific corpus** (research problem, ontology, computational theory, axioms, notebook) — governs MiniFlyWire's science; has no authority over engineering structure except as a *source of validated primitives* (Part V).
5. **Roadmaps, milestone specs, project-state records** — operational; must conform to everything above.
6. **Code, pull requests, models, configurations** — must conform to everything above.

No artifact below the Handbook may weaken a boundary the Handbook establishes. An artifact that needs to do so must first amend the Handbook (Part XI).

## P.3 Scope — what the Constitution governs and what it does not

**It governs:** which layer owns a capability; whether a dependency is legal; whether a thing is a mechanism or content; whether a capability may be promoted or extracted; how decisions are made and recorded; how the architecture is amended.

**It does not govern:** the internal implementation choices of a layer that respect its boundaries (language idioms, data-structure choices, private helper design), the scientific content of a hypothesis inside MiniFlyWire, or the specific engineering answer to an engineering problem inside Velith. The Constitution constrains *form and boundary*, not *craft*.

## P.4 Precedence and conflict resolution between existing documents

The ecosystem's prior documents were written across several months, under **evolving names** and at **different layers of the eventual stack**. They are internally valuable but not mutually consistent on their face. This Handbook does not discard them; it **re-frames** them under one canonical taxonomy (next section) and rules as follows:

- The **four-layer model and the eleven laws** ratified in *Architecture Constitution v1.0* are canonical and frozen. The project charter ("four permanent projects: MiniFlyWire → Noetica → Velith → Mini Prometheus; architecture frozen unless a Constitutional Amendment is approved") is the controlling frame.
- Where `VISION.md`, `DECISIONS.md`, `PROJECT_STATE.md`, or the research papers use an **older name** or describe the flagship as a **single system**, they are read through the canonical map in the next section. Their *substance* (verification-first, deterministic grounding, state-centric design, the compounding experiment, the migration ladder, the cognitive theory) is retained; their *naming and layer attribution* is normalized to this Handbook.
- A genuine contradiction that cannot be resolved by re-framing is a **constitutional defect** and is handled by the amendment procedure (Part XI), with the resolution recorded in `DECISIONS.md`. It is never resolved by quietly preferring one document.

---

# CANONICAL NAMING AND THE RECONCILIATION OF PRIOR DOCUMENTS

This section is load-bearing. Most apparent contradictions in the corpus are **naming collisions**, not architectural disagreements. Fixing the names dissolves the contradictions.

## N.1 The canonical taxonomy (frozen)

There are exactly **four permanent projects**, in a strict linear stack, plus one **outcome** that is not a project.

| Layer | Canonical name | One-line identity |
|---|---|---|
| 1 | **MiniFlyWire** | Cognitive research laboratory. Discovers and validates cognitive primitives. Output is *knowledge*, never production code. |
| 2 | **Noetica** | Agent Intelligence Platform. Owns reusable *mechanisms* and interfaces. Never owns domain content. |
| 3 | **Velith** | Engineering Intelligence. Owns engineering *content* — knowledge, physics/world model, CAD, simulation, engineering verification. Consumes Noetica. |
| 4 | **Mini Prometheus** | Manufacturing Intelligence. Owns manufacturing planning, factory workflows, robotics, supply chain, MES, production. Consumes Velith. |
| — | **AI Manufacturing Intelligence** | The *mission/outcome* the stack delivers. **Not a project, not a repository, not a fifth layer.** |

## N.2 The naming lineage (how prior documents map onto the canon)

During the program's earlier phases the flagship was discussed under several names. The following map is authoritative; apply it whenever an older document is read.

| Term as used in a prior document | Where it appears | Canonical reading in this Handbook |
|---|---|---|
| **PrometheusLite** (program) | `VISION.md` | The ecosystem/program as a whole. Not a single layer. |
| **Noetica** (as "the System") | `VISION.md` | Split by the canon: the *platform mechanisms* of that envisioned system are **Layer 2 Noetica**; its *engineering content* is **Layer 3 Velith**. VISION.md's principles govern both. |
| **Velith** (as "the ratified flagship") | `DECISIONS.md`, `PROJECT_STATE.md` | **Layer 3 Velith** (Engineering Intelligence). The `propose → verify → log` engineering loop and the SWE vertical are Velith's. |
| **Mini Prometheus** (as old program name) | early docs | Now specifically **Layer 4** (Manufacturing Intelligence). |
| **MiniNoetica** | `DECISIONS.md` D11 | A *separate, completed education reference project*. Read-only, not a dependency, not a layer. See Law and D11. |

## N.3 The single most important reconciliation ruling

The decision record `DECISIONS.md` (D1–D21) was authored under the name "Velith" for the *whole* verification-first engineering system, at a time when Layer 2 and Layer 3 were not yet separated. Under the frozen four-layer canon, those decisions are **re-attributed by mechanism-vs-content**, not discarded:

- The **engineering vertical, the SWE task domain, the migration ladder to manufacturing** (D4, D5) are **Velith** content decisions.
- The **reusable loop machinery** those decisions produced — the deterministic verifier *harness*, the provenance-complete *episode store*, the *content-hash* discipline, the *LLM adapter/routing seam*, the *orchestrator/runtime*, determinism levels, the held-out lock *mechanism* — are **Noetica** mechanisms, obtained by **extraction** from the Velith spike (Law of Platform-by-Extraction, Part X).
- The **concrete SWE verifier/oracle** remains **Velith**; the **verification protocol/harness interface** it implements is **Noetica**.

Therefore the M0/M1 work recorded in `PROJECT_STATE.md` (tagged `m1-complete`) is correctly understood as a **Velith engineering spike that is simultaneously the extraction seed for Noetica's platform mechanisms.** This is not a contradiction; it is exactly how the platform is meant to grow (Part X, Law 8).

## N.4 Consequence for readers

Whenever this Handbook says "Noetica owns X," and an older document appears to place X inside "Velith," the older document is using the pre-split name. Apply N.2/N.3. If after applying the map a real conflict remains, it is a defect for Part XI, not a judgment call for an implementer.

---

# PART I — FOUNDATION

## 1.1 Mission

> **The ecosystem exists to build an AI Manufacturing Intelligence: a stateful, grounded, self-improving system that can take a high-level statement of product intent and reason it down to a design that is verified, explained, and manufacturable — while honestly representing what it does not yet know — and that measurably compounds in competence over a decade.**

The mission is a single process expressed across four layers: **discover** the cognitive mechanisms that make grounded learning possible (MiniFlyWire), **turn** those mechanisms into reusable infrastructure (Noetica), **use** that infrastructure to solve real engineering problems under real verification (Velith), and **carry** verified engineering intelligence into the physical world of manufacturing (Mini Prometheus). Experience earned at the bottom flows back to the top to improve the science.

## 1.2 Vision

Engineering knowledge today does not accumulate inside our tools. A CAD kernel does not get better at design because a thousand engineers used it; a simulator does not learn which of its predictions were wrong; a language model can describe a bracket but cannot tell you, with calibrated confidence, whether it will survive its load — and forgets the answer once found. The result is a structural gap: we have powerful **generators** (LLMs, parametric CAD, solvers) and powerful **checkers** (compilers, FEA, DRC), but no system that closes the loop between them, holds persistent state about the artifact being designed, reasons about its own reliability, and turns verified experience into durable, compounding competence.

The ecosystem exists to close that loop. Its premise is that the path to real engineering intelligence is **not a larger model but a stateful, grounded, self-improving system** in which generative models are one component among several, never the architecture itself. The proving ground is deliberately the hardest one — physical manufacturing — because a system that reaches it has demonstrably *solved* the problem rather than avoided it.

## 1.3 Long-term goals (decade horizon)

Stated as research questions the program is organized to answer, not as features to ship:

1. **Grounded representation.** Can a single, typed, provenance-tracked world/design model serve as the substrate that every other capability reads and writes — across more than one engineering discipline?
2. **Compounding competence.** Can verified experience be converted into durable improvement — skills, concepts, calibrated models — such that grounded accuracy per unit compute rises over time?
3. **Causal engineering reasoning.** Can the system maintain interventional, not merely associational, models of design-variable-to-outcome relationships that survive distribution shift?
4. **Calibrated uncertainty.** Can stated confidence be forced to track grounded accuracy, with epistemic and aleatoric uncertainty separated and acted upon?
5. **Resource-rational meta-control.** Can the system *learn* — rather than have hand-tuned — its own policy for allocating compute, fidelity, and effort?
6. **Scientific discovery.** Can it close the loop from anomaly to hypothesis to experiment to revised model, adding *new* engineering principles rather than only applying known ones?
7. **Provably bounded self-improvement.** Can the system improve its own methods while a formal guarantee holds that it cannot circumvent its verifier or its human-oversight boundary?
8. **Manufacturability.** Can intent be reasoned down to designs that are actually buildable, honestly bounding the residual uncertainty of approximate physical verification?

The honest expectation: full, multi-discipline manufacturing intelligence is a funded-lab endeavor. The realistic decade target is a **deep, self-improving engineering intelligence in one or few domains, on a domain-agnostic substrate that sits on the path toward — not a dead-end branch away from — that endpoint.** Preserving that distinction is the entire value of the program's discipline.

## 1.4 Research philosophy

The ecosystem is a **science first, an engineering effort second, and never a demo.** Its research philosophy has four commitments.

**Mechanisms are hypotheses.** Every proposed cognitive component is a falsifiable scientific hypothesis, not a feature. It must be supported by a defined hypothesis, measurable criteria, reproducible experiments, and explicit comparison against baselines. A mechanism that fails to demonstrate measurable causal benefit under controlled ablation is rejected regardless of intuitive appeal or biological inspiration.

**Explanation over performance.** Behavioral success alone is not scientific understanding. The question is not only "Can the system solve the task?" but "*Which* mechanism caused the improvement, and can that contribution be isolated, measured, and reproduced?" Benchmark accuracy measures capability; it does not explain it.

**Falsifiability is the entry fee.** The program commits, in advance, to what failure looks like. Its central empirical claim (§1.7) is stated so that the program *will know if it is failing* and has agreed beforehand what failing means. A framework that cannot be falsified is retained as philosophy, never as a build constraint.

**Nothing is accepted because it sounds reasonable.** Ideas begin in a laboratory notebook, survive repeated attempts at falsification and cross-framework comparison, and only then are promoted into frozen theory. Rejected hypotheses are preserved, because a documented rejection is valuable scientific evidence.

## 1.5 Engineering philosophy

**Verification-first.** Truth is exogenous and grounded. No claim is trusted because a model produced it fluently; a claim is true only when an external verifier admits it. A confidently wrong answer is the primary failure mode and is treated as worse than an honest "I don't know."

**State-centric, not control-flow-centric.** A persistent, typed, provenance-tracked representation of the artifact is the substrate. Generators, solvers, planners, verifiers, and learners are typed *transformations over that shared state* — not the architecture itself. Intelligence is a control plane over shared state, never a central homunculus that "does the thinking" while everything serves it.

**Grow by extraction, not speculation.** The platform is not designed in the abstract ahead of its users. A capability earns its place in Noetica only when a real consumer needs it and a credible second consumer is on the horizon. Interfaces guessed before they have users are usually wrong; the platform crystallizes *out of* working applications.

**Wrap, don't rebuild.** We do not build physics engines, CAD kernels, solvers, or foundation models. The novelty budget is spent entirely on the loop that orchestrates, grounds, learns, and compounds. Everything else is wrapped behind an interface.

**Evolution over rewrite.** Milestones are designed so the next is a *hardening* of the last, not a replacement of it. A change that requires throwing away a working, boundary-respecting subsystem must justify itself against an evolutionary alternative and is the exception, not the norm.

**Honesty over impressiveness.** The program optimizes for being correct over a decade, not for demonstrations. Hidden assumptions are surfaced; failure conditions are stated; provenance is non-negotiable — if we cannot answer "why did it do that?", the system is a toy regardless of capability.

## 1.6 Scientific philosophy (the cognitive stance)

MiniFlyWire supplies the ecosystem's theory of cognition, and that theory constrains what the upper layers are *allowed to claim*. Its stance:

- **Cognition operates on computational objects transformed by operators**, not on loosely defined modules. Memory, reasoning, planning, and attention are *operators over objects*, not black boxes.
- **Three representational domains** are proposed as necessary and sufficient for engineering-capable cognition: **Reality** (the external world and its artifacts), the **Cognitive State** (transient working representations of an active episode), and the **Structured Generative World Model** (persistent learned knowledge).
- **Five universal computational functions** move information between those domains: **Perception, Inference, Evaluation, Learning, Execution.** More specialized capabilities (planning, retrieval, attention, curiosity, credit assignment) are *strategies or specializations* of these five, not new primitives.
- **Cognition is condition-driven, not pipeline-driven.** Functions activate when computational conditions are satisfied (external observation, internal inconsistency, active goal), permitting reactive, proactive, and background cognition within one framework.

These commitments are why the upper layers may never smuggle in a "Reasoner" or "Planner" that secretly *understands the world*. Understanding-content lives in a World Model owned by a domain layer; the *mechanisms* of perceiving, inferring, evaluating, learning, and executing are what Noetica owns.

## 1.7 The falsifiable commitment (the program's spine)

> If the program's premise is correct, then across a stream of grounded engineering episodes the **verification-measured description length of the system's experience decreases monotonically in expectation** — equivalently, **grounded predictive accuracy per unit compute rises**. If, under faithful grounding and an adequate budget, the system accumulates experience *without* compounding competence, the premise is **wrong**, and the architecture must be **replaced, not patched.**

Every layer above the experiment is *premised on compounding being real*. This single measurable commitment is what makes the ecosystem a scientific program rather than an aspiration, and it is why the first engineering vertical is chosen for measurement cleanliness rather than for glamour.

## 1.8 What this ecosystem IS

- A **long-term research program** to build grounded, compounding engineering — and ultimately manufacturing — intelligence.
- A **layered architecture** with a strict, acyclic dependency stack and one owner per capability.
- A **verification-first, state-centric** system in which LLMs are swappable components.
- A **science of cognitive mechanisms** (MiniFlyWire) feeding a **platform of reusable mechanisms** (Noetica) feeding **domain applications** (Velith, then Mini Prometheus).
- A program whose **moat is an agent that can think about physics** with grounded, calibrated confidence — not a clean Python architecture, though that architecture is necessary.

## 1.9 What this ecosystem IS NOT

- **Not a chatbot or general assistant.** It is a reasoning-and-verification system that *uses* language models.
- **Not another agent framework.** If a decision would make it indistinguishable from a generic agent-graph library, the decision is wrong by definition.
- **Not a CAD generator or an LLM wrapper.**
- **Not a foundation-model training effort.** Frontier and open-weight models are consumed; small task models (embeddings, rerankers, distilled experts) are in scope only when justified.
- **Not a homunculus.** There is no central mind that does the real thinking while everything serves it.
- **Not a premature-scale system.** No web-scale, multi-tenant, or distributed infrastructure until reality demands it. Single-machine discipline for years.
- **Not a benchmark-maximizer.** Static, hand-authored metrics invite Goodharting; measurement is held-out and generalization-tested.
- **Not five projects.** "AI Manufacturing Intelligence" is the outcome, not a repository.

## 1.10 Core definitions

These terms have fixed meanings throughout the Handbook. A fuller glossary is Appendix A.

- **Mechanism.** *How* something is done, independent of any domain: how to remember, plan, verify, reason, route a model call, track provenance. Mechanisms are Noetica's property.
- **Content.** *What* is remembered, planned, verified, or reasoned about: engineering knowledge, a physics model, a factory layout, an SWE test oracle. Content is a domain layer's property.
- **Interface.** A typed, versioned, public contract published by Noetica (e.g., `Verifier`, `MemoryStore`, `Plan`, `Tool`, `Skill`, `WorldModel`). Cross-layer contact happens only through interfaces.
- **Implementation.** A concrete class provided by a domain layer that satisfies an interface (e.g., `SweVerifier`, `FeaVerifier`, `CadTool`).
- **Cognitive primitive.** A mechanism of cognition (attention, memory, curiosity, reflection, planning, replay, confidence, forgetting, learning) that MiniFlyWire proposes, isolates, and validates as a falsifiable hypothesis.
- **Validated mechanism.** A cognitive primitive that has passed MiniFlyWire's promotion gate: hypothesis-defined, causally isolated, quantitatively measured, and falsification-tested.
- **Promotion.** The act of moving a *validated mechanism* from research (MiniFlyWire) into the platform (Noetica) by **re-implementation**, never by import.
- **Extraction.** The act of moving a *proven mechanism* from a domain application (Velith) up into the platform (Noetica) by refactoring it behind an interface, once it has a real consumer and a credible second.
- **Episode.** A provenance-complete, content-hashed record of one grounded attempt (task, proposal, verdict, cost, environment), which survives process exit and is first-class learning data.
- **Verifier / oracle.** The concrete check that admits or rejects a claim. Its *protocol/harness* is a Noetica mechanism; the *oracle itself* is domain content.
- **Verdict.** The grounded outcome of verification. Its taxonomy is closed; measurement-quality signals (e.g., flakiness) are provenance, not verdict states.
- **Provenance.** The derivation of every belief — where it came from and why. Non-negotiable and first-class.
- **State substrate.** The persistent, typed, provenance-tracked representation of the artifact and its environment that is the true core of the platform.
- **Digital twin engine vs. content.** The *mechanism* of state-sync/versioning/provenance for a world model is a Noetica capability; the *manufacturing twin content* is Mini Prometheus's.

## 1.11 Design principles (the ten constraints)

Every future decision is constrained by these. A proposal that violates one is rejected or must amend this Handbook with written justification. They restate, at Handbook authority, the principles ratified in `VISION.md` §5 and the decisions that implement them.

1. **Verification-first.** Truth is grounded in external evidence, never in the system's fluency.
2. **State-centric.** Persistent, provenance-tracked shared state is the substrate; everything else is a transformation over it.
3. **LLMs are components, never the mind.** The system's identity depends on no single model or vendor.
4. **Generality from architecture and depth, not breadth.** Full interfaces now; depth added on a schedule; one vertical proven before the next.
5. **Bounded rationality is first-class.** Computation is a costly act; the system reasons about how much to think, which model to call, and when to stop.
6. **Grounding and oversight are immutable.** The system may improve *how it designs*; it may never modify *how its success is judged* or *how it is overseen*.
7. **Provenance and observability are non-negotiable.** Every belief carries its derivation.
8. **Compounding is the test.** Experience without improvement is failure, however impressive a single output looks.
9. **Wrap, don't rebuild.** The novelty budget is spent on the loop, not on kernels, solvers, or models.
10. **Honesty over impressiveness.** Optimize for being correct over a decade; surface hidden assumptions; state failure conditions.

---

# PART II — THE FOUR PROJECTS

Each project is defined by the same charter template so that its boundary is unambiguous. Read a project's charter and you should be able to decide, for any candidate module, whether it belongs there — and if not, where it belongs instead.

The template fields are: **Purpose · Mission · Responsibilities · Inputs · Outputs · Public interfaces · Internal components · Workflow · Lifecycle · Consumers · Providers · Allowed dependencies · Forbidden dependencies · Good/bad examples · Anti-patterns and typical mistakes · Future evolution · Boundary with the previous project · Boundary with the next project · When code should move · When code must never move.**

---

## 2.1 MINIFLYWIRE — The Cognitive Research Laboratory

### Purpose
MiniFlyWire is a **computational laboratory for experimental artificial cognition**: a controlled, observable, reproducible environment in which computational mechanisms of cognition are proposed, implemented, measured, compared, and experimentally evaluated. Its purpose is to *increase scientific understanding*, not to maximize benchmark performance and not to ship software.

### Mission
To determine, by controlled experiment, **which computational mechanisms are necessary and sufficient for an artificial system to acquire, organize, construct, transfer, and apply knowledge through continuous interaction with its environment — and to demonstrate their causal contributions.** MiniFlyWire shifts the unit of analysis from *architecture* to *mechanism*, treating every mechanism as a falsifiable hypothesis.

### Responsibilities
- Maintain the ecosystem's **theory of cognition**: the ontology (computational objects and operators), the computational theory (three domains, five functions, five laws, condition-driven activation), the research problem, and the axioms.
- Propose cognitive primitives (attention, memory, curiosity, reflection, planning, replay, forgetting, confidence, learning) as hypotheses with measurable criteria.
- Run controlled ablation/intervention experiments isolating each mechanism's causal contribution.
- Maintain the **laboratory notebook** where hypotheses live before promotion, and the **rejected-ideas record** (rejections are evidence).
- Certify, through the promotion gate (Part V), which mechanisms are validated and therefore eligible for re-implementation by Noetica.

### Inputs
Research questions; cognitive hypotheses; datasets and controlled task environments; results and telemetry arriving via the Experience Flow from lower layers (as *research questions and datasets*, never as code dependencies).

### Outputs
**Validated (or falsified) mechanisms** accompanied by written specifications, measurable evidence, and reference — explicitly research-grade — implementations. The deliverable is *knowledge*: a specification precise enough that Noetica can re-implement the mechanism cleanly.

### Public interfaces
**None that are importable.** MiniFlyWire exposes *documents and validated-mechanism specifications*, not an API. Nothing in the ecosystem imports MiniFlyWire.

### Internal components
Simulation environments; RL/experimental harnesses; neural-activation and replay probes; measurement and ablation instrumentation; the cognitive ontology and theory documents; the notebook and rejected-ideas log. These are free to be messy, exploratory, and research-grade.

### Workflow
Observation → Hypothesis → Reduction → Falsification attempt → Cross-framework comparison → Revision → Acceptance or rejection → (if accepted) Promotion into permanent theory. No hypothesis is accepted because it sounds reasonable; every one must survive attempts to destroy it.

### Lifecycle
Permanent. MiniFlyWire never "completes." It continuously proposes and tests new primitives, and continuously receives new research questions from the Experience Flow. It is expected to run for the life of the ecosystem as its scientific engine.

### Consumers
**Noetica only**, and only by *reading specifications and re-implementing* validated mechanisms. No other layer consumes MiniFlyWire.

### Providers
Frontier/open-weight models and datasets as experimental substrate; research questions harvested from lower-layer experience.

### Allowed dependencies
May depend on general scientific and ML tooling for experimentation. **May depend on no other ecosystem project.**

### Forbidden dependencies
Must not import Noetica, Velith, or Mini Prometheus. Must not be imported *by* them. Must not carry a production-quality or availability obligation.

### Good example
`forgetting.py` and a `KnowledgeState` update rule that are falsified, ablated, shown domain-agnostic, and dependency-light — a mechanism spec Noetica can re-implement cleanly.

### Bad example
An `LLM-as-judge` module (`judge.py`) used as if it were a verifier. This is the precise anti-pattern the ecosystem exists to eliminate; it may exist inside MiniFlyWire *as a studied negative result*, but it may never be promoted.

### Anti-patterns and typical mistakes
- Treating benchmark score as the goal (MiniFlyWire measures *mechanism contribution*, not leaderboard rank).
- Letting research code acquire a production or availability obligation.
- Allowing another layer to import MiniFlyWire "just this once."
- Promoting a mechanism on intuition before it passes the gate.

### Future evolution
Deepen from software-flavored cognition toward **physical and spatial cognition** (spatial attention, geometric mental models, focusing on a single stress concentration in a large model) — the cognition a manufacturing intelligence ultimately needs. It must not drift into being an LLM prompt-engineering lab.

### Boundary with the next project (Noetica)
The boundary is a **dashed knowledge-transfer arrow**, not a code arrow. MiniFlyWire hands Noetica *specifications of validated mechanisms*; Noetica re-implements them to production standard. The arrow type here is fundamentally different from every arrow below it.

### When code should move
**Never as code.** A mechanism moves as a *specification* to be re-implemented, and only after it passes the promotion gate.

### When code must never move
Always. No MiniFlyWire code is ever imported. If a Noetica (or any) file imports MiniFlyWire, the boundary has been breached and the import must be reverted.

---

## 2.2 NOETICA — The Agent Intelligence Platform

### Purpose
Noetica is the **domain-agnostic platform** that turns validated cognitive mechanisms into reusable infrastructure. It owns *mechanisms and interfaces and the shared state substrate*. It never owns domain knowledge.

### Mission
To provide every mechanism a grounded agent needs — runtime, state substrate, memory, knowledge-store engine, context assembly, reasoning runtime, planning representation and execution, reflection, evaluation harness, verification protocol, tool and skill systems, model routing, budget/meta-control, provenance, observability, and developer surfaces — as typed, versioned interfaces with default implementations, such that a domain layer can build a real, grounded, compounding agent without re-implementing any mechanism.

### Responsibilities
- Own and version the **public interfaces** (`Agent`/`Runtime`, `MemoryStore`, `KnowledgeStore`, `Context`, `Plan`+`Planner`/`Executor`, `ReasoningLoop`, `Reflector`, `Tool`, `Skill`, `Verifier` (protocol), `EvalHarness`, `ModelRouter`, `BudgetMeter`, `Provenance`, `Guardrail`, `WorldModel` state-sync).
- Own the **state substrate and provenance/lineage** — the true core.
- Own **cross-cutting platform services**: guardrails/safety engine, logging, observability, evaluation harness, held-out-lock mechanism.
- Grow **only by extraction** from real consumers and **by re-implementation** of validated MiniFlyWire mechanisms.

### Inputs
A task/goal; a configured model + budget; registrations of tools, skills, and concrete verifiers; memory/knowledge handles; validated-mechanism specifications from MiniFlyWire.

### Outputs
Grounded agent runs with full provenance; updated memory/knowledge state; evaluation results; the stable, versioned interface surface that domains build on.

### Public interfaces
The interface catalog above — **stable and versioned**. Everything a domain needs is *an interface plus a default implementation*. Domains consume the interfaces, never Noetica's internal types.

### Internal components
Substrate storage; routing internals; harness plumbing; the reference/fake verifier used for self-testing; provenance store internals. These are private and may change without notice provided the public interfaces hold their contract.

### Workflow
Receive task + configuration → assemble context from memory/knowledge over the state substrate → run the reasoning/planning runtime, invoking registered tools/skills → submit candidate results to the verification protocol (whose concrete oracle is domain-supplied) → record a provenance-complete episode → update memory/knowledge under the write-filter policy → emit evaluation and observability signals.

### Lifecycle
Permanent, and **grown by extraction**. Noetica does not spring into existence as a 17-capability platform; each capability enters when a real consumer (first Velith) needs it and a credible second is on the horizon. Interfaces are designed early; depth is added on a schedule.

### Consumers
**Velith** directly; **Mini Prometheus** transitively (through Velith, and directly for platform mechanisms it legitimately needs). All consumption is through published interfaces.

### Providers
MiniFlyWire (validated mechanisms, by re-implementation); frontier/open-weight and small task models (wrapped behind the model router).

### Allowed dependencies
General-purpose libraries and wrapped model providers. **No ecosystem project.** Noetica imports nothing upward and nothing domain-specific.

### Forbidden dependencies
Must never import Velith, Mini Prometheus, or MiniFlyWire. Must never contain engineering or manufacturing content. Must never contain a domain verifier/oracle. Its self-tests must use a **reference/fake verifier**, never a real domain one.

### Good example
A `Verifier` *protocol* with a `Verdict` type whose construction validates its own fields; an `EpisodeStore` with a content-hash discipline separating reproducible identity from provenance; a `ModelRouter` behind which any vendor is swappable.

### Bad example
A `SweVerifier` (runs SWE hidden tests) placed inside Noetica. That is domain content leaking into the platform — a boundary breach. Noetica owns the `Verifier` *interface*; the SWE oracle is Velith's.

### Anti-patterns and typical mistakes
- **Homunculus creep**: adding a bare "Reasoner" or "Planner" that implies Noetica *understands the world*. Noetica owns the *form* (a reasoning runtime, a plan representation and executor, a reflection loop, verification seams) — never domain reasoning *content*.
- **Missing substrate**: listing only transformations and services and forgetting the state substrate as the core, drifting into a control-flow-centric bag-of-agents.
- **Duplicated abstractions**: `Memory`, `Knowledge`, and `Context` collapsing into each other because they were never defined crisply (see §6 for their precise, non-overlapping definitions).
- **Speculative generality**: building a capability with no real consumer.
- **Leaking concrete types** across a repo boundary instead of versioned interfaces.

### Future evolution
Deepen the substrate toward **probabilistic/belief state** (confidence, epistemic/aleatoric separation) so it can host approximate physical domains, and add an **experience-aggregation** mechanism so the Experience Flow has a first-class home. Both are added by extraction as Velith and Mini Prometheus create the need — not speculatively.

### Boundary with the previous project (MiniFlyWire)
Noetica *re-implements* MiniFlyWire's validated mechanisms; it never imports them. The mechanism arrives as a spec; Noetica owns the production implementation.

### Boundary with the next project (Velith)
Noetica publishes interfaces; Velith implements them with engineering content. The line is **mechanism (Noetica) vs. content (Velith)** and **interface (Noetica) vs. implementation (Velith)**. A domain verifier, a physics model, or an engineering ontology inside Noetica is a breach.

### When code should move
*Into* Noetica: when a mechanism inside Velith has proven itself, has a real consumer, and has a credible second consumer — it is **extracted** up behind an interface. *Out of* MiniFlyWire: never as code; only re-implemented from spec.

### When code must never move
Domain content must never move into Noetica. A capability must never be promoted into Noetica speculatively (no real consumer). Noetica must never reach upward for anything.

---

## 2.3 VELITH — Engineering Intelligence

### Purpose
Velith is the **first domain application**: an engineering intelligence that uses Noetica's mechanisms to solve real engineering problems under real, grounded verification. It owns engineering *content* — engineering knowledge, the physics/world model, CAD, simulation, optimization, and engineering verification.

### Mission
To demonstrate the ecosystem's central claim in the cleanest possible arena: that a grounded, verification-first engineering agent can **measurably improve its held-out performance through verified experience** — and then to climb the migration ladder toward physically manufacturable domains without ever abandoning measurement discipline.

### Responsibilities
- Own the **engineering vertical** and its task domain (first: repository-level software engineering, SWE).
- Provide **concrete implementations** of Noetica interfaces: the engineering `Verifier`/oracle, engineering `Tool`s (CAD, solvers), engineering `Skill`s, and the population of Noetica's knowledge store with engineering content.
- Own the **physics/world model content** and engineering ontology.
- Execute and honor the **compounding experiment** and its differential arms (A0–A4), the pre-registration freeze, and the mechanically-enforced held-out lock — configuring Noetica's harness, not re-implementing it.
- Climb the **migration ladder**: SWE → PCB/electronics → HDL/firmware → mechanical/FEA → manufacturing, introducing model-gap deliberately and only after the loop is proven.

### Inputs
Engineering intent and constraints; Noetica's runtime and interfaces; datasets and held-out benchmarks for the current vertical.

### Outputs
Verified engineering artifacts (designs, patches, analyses) with provenance and calibrated uncertainty; concrete `Verifier`/`Tool`/`Skill` implementations; a stream of grounded episodes that constitute the compounding evidence; engineering results consumed by Mini Prometheus.

### Public interfaces
`EngineeringTask`, `EngineeringResult`, `DesignArtifact`; the domain verifier/tool/skill implementations; engineering-ontology accessors. Mini Prometheus consumes *these*, not Noetica directly, for engineering concerns.

### Internal components
CAD/solver adapters; physics/material knowledge; engineering planners expressed *as Noetica plans*; the concrete deterministic verifier (compile + run hidden tests + static analysis) that implements Noetica's `Verifier` protocol; the episode-producing engineering loop.

### Workflow
Receive an engineering task → use Noetica's reasoning/planning runtime to propose a candidate artifact → **dispose** of it with the engineering verifier (deterministic where the model-gap is zero; approximate with calibrated uncertainty on higher rungs) → persist a provenance-complete episode via Noetica's store → let Noetica's memory policy convert verified experience into competence → measure held-out improvement under the frozen experimental protocol.

### Lifecycle
Permanent and central: Velith is the arena where the compounding hypothesis is tested and where the platform is grown by extraction. It advances milestone by milestone (M0 skeleton → M1 propose→verify→log → M2 hardened verifier → … ), each milestone a hardening of the last, never a rewrite.

### Consumers
**Mini Prometheus** (consumes engineering results and the engineering-task API). Also the ecosystem's *own measurement*: Velith's episodes are the evidence for §1.7.

### Providers
**Noetica** (all mechanisms, via interfaces). Wrapped external kernels/solvers/CAD. It does **not** consume MiniFlyWire.

### Allowed dependencies
**Noetica only**, through published interfaces. Wrapped third-party engineering tools behind adapters.

### Forbidden dependencies
Must never import Mini Prometheus (no upward import). Must never import MiniFlyWire. Must never re-implement a Noetica mechanism (memory, planning, runtime, provenance, routing, harness). Must never treat verification as a free oracle.

### Good example
A `SweVerifier` that implements Noetica's `Verifier` protocol and returns a `Verdict` from a closed taxonomy; an engineering planner expressed as a Noetica `Plan`; a CAD tool wrapped behind Noetica's `Tool` interface. The engineering *ontology* lives here but *populates Noetica's knowledge store*.

### Bad example
Velith writing its own episode store, its own model router, or its own provenance system because "it was easier" — duplicating Noetica mechanisms and eroding the boundary. Or Velith importing MiniFlyWire's research code directly.

### Anti-patterns and typical mistakes
- Re-implementing a platform capability instead of consuming Noetica's interface.
- Letting engineering content harden into Noetica prematurely (extraction requires a *second* credible consumer).
- Collapsing the A1/A2 experiment arms by giving them different retrievers (the experiment is void if the only legal difference — the write-filter — is not the only difference).
- Treating an approximate verifier (FEA/SPICE) as if it were exact, hiding the model-gap the higher rungs exist to study.

### Future evolution
Climb the migration ladder; grow a **physics-informed world model** (the "physical grounding" capability the reviews flagged) as engineering content that *uses* Noetica's substrate; supply, over time, the mechanisms that get extracted upward into Noetica.

### Boundary with the previous project (Noetica)
**Interface owned above, content owned here.** Velith's verifier implements Noetica's protocol; Velith's ontology populates Noetica's store. Velith configures Noetica's harness; it does not rebuild it.

### Boundary with the next project (Mini Prometheus)
Velith exposes engineering results and an engineering-task API. Mini Prometheus consumes those; it does not reach past Velith to re-implement engineering, and does not bypass Velith to use agent infrastructure for engineering concerns.

### When code should move
*Up into Noetica*: a Velith mechanism that is domain-agnostic, proven, and has a credible second consumer is **extracted** behind an interface. *Down from Noetica*: never — Velith consumes, it does not absorb the platform.

### When code must never move
Engineering content must never move into Noetica (only mechanisms extract upward). Velith code must never move into Mini Prometheus by copy; Mini Prometheus consumes Velith through its API.

---

## 2.4 MINI PROMETHEUS — Manufacturing Intelligence

### Purpose
Mini Prometheus is the **top application**: manufacturing intelligence that consumes Velith's engineering intelligence and carries it into the physical world of production. It owns manufacturing *content* — manufacturing planning, factory workflows, robotics, supply chain, MES, scheduling, and production execution.

### Mission
To turn verified engineering results into **manufacturable plans and running production**, and to be the ecosystem's contact point with physical reality — where verification is approximate and expensive, where the Sim2Real gap is real, and where the richest experience for the whole stack is generated.

### Responsibilities
- Own **manufacturing planning and scheduling**, **factory/robotics/supply-chain workflows**, **MES and production execution**.
- Own the **manufacturing digital-twin content** (the factory/product twin), instantiated on Noetica's twin/state-sync *engine*.
- Emit the **Experience Flow**: telemetry, failures, and grounded outcomes that propagate up through Velith and Noetica to MiniFlyWire.
- Honor the mechanism/content split: the twin *engine* (state sync, provenance, versioning) is Noetica's; the manufacturing twin *content* is Mini Prometheus's.

### Inputs
Product intent; Velith engineering intelligence and results; factory/industrial signals and telemetry.

### Outputs
Manufacturable plans; factory/robotics/supply-chain workflows; digital-twin state; production schedules; and — critically — the **experience stream** that flows back up the stack.

### Public interfaces
`ManufacturingTask`, `ProductionPlan`, manufacturing-twin content accessors. Consumers are end users and factory/industrial systems at the top of the stack.

### Internal components
MES/PLC/robotics adapters (wrapped, speaking standard industrial protocols such as OPC UA); scheduling and supply-chain logic; the manufacturing twin content; experience-collection instrumentation.

### Workflow
Receive product intent → obtain verified engineering results from Velith → plan manufacturing (process, factory, supply chain, schedule) → execute/monitor via wrapped industrial systems → sync the manufacturing digital twin on Noetica's engine → collect telemetry and failures → emit them up the Experience Flow.

### Lifecycle
The **last** layer to mature, and explicitly allowed to be **recursive** — large enough to become its own internal stack (planning vs. execution as separate internal sub-layers coordinating through Velith/Noetica contracts, never sibling-to-sibling imports). It is built only after Velith's loop is proven.

### Consumers
End users; physical factory and industrial systems.

### Providers
**Velith** (engineering results and API); **Noetica** transitively (platform mechanisms, including the twin/state-sync engine).

### Allowed dependencies
**Velith** (for engineering) and Noetica's platform mechanisms it legitimately needs (e.g., the twin engine, provenance), through interfaces. Wrapped industrial systems behind adapters.

### Forbidden dependencies
Must never import MiniFlyWire. Must never bypass Velith to re-implement engineering. Must never absorb Noetica mechanisms by re-implementation. Internal sub-verticals must never import each other directly.

### Good example
A `ProductionPlan` built from a Velith `EngineeringResult`; a factory twin whose *content* lives here but whose *state-sync/versioning/provenance* is Noetica's engine; a robotics adapter speaking OPC UA behind a wrapper.

### Bad example
Mini Prometheus writing its own engineering verifier or physics model (that is Velith's), or its own provenance/state-sync engine (that is Noetica's), or wiring one internal sub-vertical directly into another.

### Anti-patterns and typical mistakes
- Treating manufacturing as a deterministic logic puzzle and ignoring physical entropy, tool wear, and sensor drift (the substrate must carry uncertainty).
- Collapsing planning and execution into one flat module when the domain demands a recursive internal stack.
- Building the manufacturing twin *engine* here instead of consuming Noetica's.

### Future evolution
Split into internal sub-layers (planner vs. execution) as scope demands; deepen Sim2Real tracking (divergence between expected/simulated and sensed/actual physics); become the ecosystem's primary generator of grounded physical experience.

### Boundary with the previous project (Velith)
Consumes Velith's engineering results and API. Owns *manufacturing* content; Velith owns *engineering* content. The twin content is here; the twin engine is Noetica's.

### Boundary with the next project
There is none above it — Mini Prometheus is the top of the stack. Its "next" is the physical world and the Experience Flow that returns to research.

### When code should move
A domain-agnostic mechanism proven here may, like any layer, be **extracted upward** into Noetica behind an interface once it has a credible second consumer. Otherwise code does not move; layers consume through APIs.

### When code must never move
Manufacturing content must never move into Velith or Noetica. Mini Prometheus must never re-implement, by moving code downward, what Velith or Noetica already own.

---

# PART III — HOW THE ECOSYSTEM WORKS

This part explains the whole machine as if teaching a new engineer on their first day. It follows a single idea all the way from a human sentence to a physical product and back to the laboratory, with **no gaps**. Every arrow in the diagram below is a step, and every step is explained.

```
Human idea
   ↓  (framing)
Research            ── MiniFlyWire
   ↓  (validation)
Validated Primitive
   ↓  (re-implementation)
Noetica             ── the platform of mechanisms
   ↓  (consumption)
Engineering         ── Velith
   ↓  (verified results)
Manufacturing       ── Mini Prometheus
   ↓  (execution)
Factory             ── physical reality
   ↓  (telemetry, failures)
Experience
   ↓  (new questions + datasets)
Research            ── back to MiniFlyWire
```

## 3.1 Step 1 — A human idea

Everything starts with a human intent: sometimes a scientific question ("does a forgetting mechanism improve knowledge transfer?"), sometimes an engineering task ("fix this failing repository," later "design a bracket that survives this load"), eventually a product intent ("manufacture this part"). The ecosystem's job is to carry that intent down the stack and return a *verified, explained, manufacturable* answer — or an honest statement of what it does not yet know.

The human is not modeled as a mere operator. They are a **first-class oracle and overseer**: the richest source of tacit ground truth, and the holder of the immutable oversight boundary that the system may never modify.

## 3.2 Step 2 — Research (MiniFlyWire frames the cognition)

Before a capability can exist in the platform, the *mechanism* behind it must be understood scientifically. MiniFlyWire takes a cognitive question and turns it into a **falsifiable hypothesis**: it defines the mechanism as an operator over computational objects, designs an experiment that isolates that mechanism as the causal variable, and attempts to falsify it. This is where "memory," "reflection," "attention," "curiosity," "replay," and "forgetting" are given precise computational meaning rather than being assumed.

No gap here is allowed to be filled by intuition. If a mechanism cannot be defined computationally and measured causally, it does not proceed.

## 3.3 Step 3 — A validated primitive

An experiment either falsifies the mechanism (a valuable negative result, recorded) or shows a measurable, isolated, reproducible causal benefit. In the latter case the mechanism becomes a **validated primitive**: a written specification plus research-grade reference implementation plus evidence. It has passed the promotion gate (Part V). It is now *eligible* to enter the platform — but not by import.

## 3.4 Step 4 — Noetica re-implements the primitive into a mechanism

Noetica reads the specification and **re-implements** the primitive to production standard, behind a typed, versioned interface, with provenance and observability from the first commit. The research code is never imported; only the *idea*, expressed as a spec, crosses the boundary. This is the **Knowledge Flow** in action, and it is the only arrow in the whole stack that is *not* a code-import arrow.

At this step the mechanism becomes domain-agnostic infrastructure: a `MemoryStore`, a `ReasoningLoop`, a `Reflector`, a `Verifier` protocol — a *form* of cognition with no domain content inside it.

## 3.5 Step 5 — Engineering (Velith consumes the platform)

Velith takes a real engineering task and solves it *using* Noetica's mechanisms. It never rebuilds them. It supplies the **content**: the engineering knowledge, the concrete verifier/oracle, the CAD/solver tools wrapped behind Noetica's `Tool` interface, the engineering plans expressed as Noetica `Plan`s. The agent **proposes** a candidate; the verifier **disposes** of it against grounded truth; the outcome is written as a provenance-complete **episode**.

Crucially, this is where the ecosystem's central claim is tested: across a stream of grounded episodes, does verified experience make the system *measurably better* on held-out tasks? (§1.7.)

## 3.6 Step 6 — Manufacturing (Mini Prometheus consumes engineering)

When an engineering result is verified, Mini Prometheus consumes it and plans its *realization*: process planning, factory workflow, supply chain, scheduling. It instantiates a **manufacturing digital twin** — its own *content* — on Noetica's twin/state-sync *engine*. Here the verification economics get hard: physical checks are approximate, partial, and expensive, so verdicts carry calibrated uncertainty rather than a naked boolean.

## 3.7 Step 7 — Factory (contact with physical reality)

Plans meet the physical world through wrapped industrial systems (MES, PLC, robotics, speaking standard protocols). Reality does what reality does: tools wear, materials have impurities, sensors drift, a screw is threaded at a slightly different pitch than the CAD model. A brittle automation pipeline halts here. A cognitive system recalls a prior episode, hypothesizes a workaround, tests it in a micro-simulation, and proceeds — which is precisely why cognition, not just software, is the core.

## 3.8 Step 8 — Experience (the world teaches the system)

Every factory outcome — success, failure, drift, surprise — is captured as grounded experience. This is the ecosystem's most valuable raw material, because it is *reality's verdict*, not a model's opinion. It must be vectorized, provenance-tracked, and stored so it can improve the layers above.

## 3.9 Step 9 — Experience flows back up to research

Experience propagates upward as **data and questions, never as code**: Mini Prometheus's failures refine Velith's engineering constraints; aggregated outcomes refine Noetica's mechanisms (e.g., its memory or routing policy); and the anomalies that no current mechanism explains become **new research questions and datasets for MiniFlyWire**. The loop closes. The scientist that started the chain now has fresh, grounded phenomena to study.

## 3.10 Why the loop does not become a cycle

A careful reader notices that code flows **down** (Noetica → Velith → Mini Prometheus) while experience flows **up** (Mini Prometheus → Velith → Noetica → MiniFlyWire) and asks: isn't that a circular dependency? It is not, and the distinction is constitutional (Part IV and Law 12): the **down** arrows are *code-import* dependencies (a compile-time DAG); the **up** arrows are *data/telemetry* dependencies (runtime artifacts — episodes, datasets, questions — moving through storage and interfaces, never through imports). No layer ever *imports* a layer below it. The two flows share a diagram but not a dependency graph.

---

# PART IV — THE THREE FLOWS

The ecosystem has exactly three permanent flows. Every legitimate movement of anything — ideas, code, or experience — is one of these three. Anything that is none of them is suspect.

## 4.1 Knowledge Flow

**Direction.** MiniFlyWire → Noetica (down, top of stack only).

**What moves.** *Validated cognitive primitives*, expressed as specifications and research-grade reference implementations plus evidence.

**Mechanism of transfer.** **Re-implementation.** Noetica reads and rebuilds; it never imports MiniFlyWire.

**Purpose.** To let the platform stand on *experimentally validated* cognitive science rather than intuition, without inheriting research-grade code or the LLM-as-judge anti-pattern.

**Ownership.** MiniFlyWire owns the discovery and the spec; Noetica owns the production mechanism it builds from that spec.

**Examples.** A validated `forgetting` rule becomes a Noetica memory-decay mechanism; a validated reflection loop becomes Noetica's `Reflector`; a validated attention mechanism informs Noetica's context-assembly policy.

**Failure cases.** (a) *Import instead of re-implement* — Noetica imports MiniFlyWire, dragging research-grade code and its obligations into the platform: **illegal**. (b) *Promotion without validation* — a mechanism enters on intuition before passing the gate: **illegal**. (c) *Promoting a known anti-pattern* — e.g., LLM-as-judge: **forbidden by law**.

## 4.2 Code Flow

**Direction.** Noetica → Velith → Mini Prometheus (down, strictly one direction).

**What moves.** *Reusable mechanisms as importable interfaces and defaults.* Velith imports Noetica; Mini Prometheus imports Velith (and, where legitimate, Noetica's platform mechanisms).

**Mechanism of transfer.** **Typed, versioned public interfaces.** No concrete internal type crosses a repo/package boundary.

**Purpose.** To let each domain build on the mechanisms below it without re-implementing them, while keeping the dependency graph a strict acyclic DAG that a person can reason about for a decade.

**Ownership.** The **interface is owned above**; the **implementation is owned by the domain**. Noetica owns `Verifier`; Velith owns `SweVerifier`. Noetica owns the twin engine; Mini Prometheus owns the twin content.

**Examples.** Velith's `SweVerifier` implements Noetica's `Verifier` protocol; Mini Prometheus's `ProductionPlan` is built from Velith's `EngineeringResult`; a CAD tool is wrapped behind Noetica's `Tool` interface.

**Failure cases.** (a) *Upward import* — Velith imports Mini Prometheus, or Noetica imports Velith: **illegal, breaks the DAG**. (b) *Sibling import* — two Mini Prometheus sub-verticals import each other, or a domain reaches around Velith to use agent infra for an engineering concern: **illegal**. (c) *Re-implementation instead of consumption* — Velith rebuilds a Noetica mechanism: **illegal (Law 6)**. (d) *Concrete-type leakage* — sharing internal types by convention so a Noetica change silently breaks Velith: **illegal; use versioned interfaces**.

## 4.3 Experience Flow

**Direction.** Mini Prometheus → Velith → Noetica → MiniFlyWire (up the whole stack).

**What moves.** *Grounded experience* — telemetry, failures, verdicts, episodes — and the *new research questions and datasets* distilled from them. **Never code.**

**Mechanism of transfer.** *Versioned data contracts*, not imports: episodes in the store, datasets, and distilled questions all move through explicit, versioned schemas. The producer emits against a contract; the consumer reads against the same contract version. At no point does an upper layer import a lower one. Upward data contracts are held to **the same rigor as downward code interfaces** — a schema change is a versioned, migrated event, never an ad-hoc field addition (Law 21).

**Purpose.** To make the system **compound**: reality's verdicts refine engineering constraints, then platform policies, then the science itself. Without this flow the ecosystem would execute but never learn — and "experience without improvement is failure" (Law/Principle 8).

**Ownership.** Each layer owns the *aggregation and use* of experience relevant to it: Velith refines engineering constraints; Noetica refines mechanisms (memory/routing/eval policy) via extraction; MiniFlyWire turns unexplained anomalies into new hypotheses. A first-class **experience-aggregation** mechanism is Noetica's to provide (added by extraction as the need matures).

**Examples.** A factory failure (wrong thread pitch) becomes a Velith constraint update; 10,000 FEA outcomes become a dataset that refines a Noetica policy; an anomaly no mechanism explains becomes a MiniFlyWire research question.

**Failure cases.** (a) *Experience flowing as code* — an upper layer imports a lower one to "get its data": **illegal; move data, not imports**. (b) *Silent cycle* — wiring the up-flow as a compile-time dependency: **illegal; it must be a data/runtime artifact**. (c) *Experience logged but not learned from* — retained without ever improving competence: a **research failure** by §1.7, and the signal to replace, not patch. (d) *Ungrounded experience treated as truth* — self-assessed "successes" retained without a verdict: **the anti-grounding anti-pattern** the differential experiment (A3) exists to defeat. (e) *Unversioned schema drift* — a producer changing an episode/dataset schema without a contract version and migration: **illegal** (Law 21).

## 4.4 The three-flow invariant

> Ideas flow down once, by re-implementation (Knowledge). Code flows down, by versioned interfaces (Code). Experience flows up, by versioned data contracts (Experience). Nothing flows any other way. The Code Flow is the only compile-time dependency graph, and it is a strict DAG; the Experience Flow carries no imports, only contract-governed data.

---

# PART V — COGNITIVE RESEARCH (MINIFLYWIRE)

This part is the definitive account of the ecosystem's scientific engine: *why* cognition is the core, why each cognitive primitive matters, and how a discovery becomes a reusable mechanism. It is written so that a researcher joining MiniFlyWire can run the laboratory correctly and a platform engineer downstream can understand exactly what "validated" means before re-implementing anything.

## 5.1 Why cognition exists in this ecosystem

The tempting shortcut is to skip cognition entirely: wrap a frontier LLM in orchestration code and call it manufacturing intelligence. The ecosystem rejects this, from first principles, for a specific reason.

**Software is for knowns; cognition is for unknowns.** Traditional software and basic LLM wrappers operate on structured, predictable environments. Manufacturing is a *high-entropy* environment: tools break, materials have impurities, sensors drift. A pipeline that assumes the world matches its model halts the first time the world disagrees.

**Autoregressive LLMs are System-1 pattern matchers.** They predict the next token from training data. They cannot do reliable zero-shot physical planning without hallucinating, and they do not remember what reality told them last time. To solve grounded engineering problems you need **System-2 cognition**: search, backtracking, episodic memory, forgetting, reflection, and grounded verification — mechanisms that operate over persistent state.

**General models are not trained on your reality.** Frontier models are trained on internet text, not factory telemetry. No vendor will solve manufacturing-specific cognition for you: how an agent builds a spatial mental model, focuses attention on a single stress fracture in a massive CAD file, or curiously explores an engineering space. That is the science MiniFlyWire exists to do.

The conclusion is explicit and constitutional: **cognition must remain the core.** If the ecosystem abandoned cognition for pure software it would build an impressive but brittle automation pipeline. The moat is *an agent that can think about physics* with grounded, calibrated confidence.

## 5.2 The scientific frame (what MiniFlyWire actually studies)

MiniFlyWire studies **representation**, not behavior. The unanswered question it exists to attack is: *how do increasingly structured, interpretable, and transferable internal representations emerge from experience?* It therefore treats each cognitive mechanism as a **falsifiable hypothesis** and asks not "did the score go up?" but "*which mechanism* caused it, and can that contribution be isolated, measured, and reproduced?"

The frame rests on the computational theory (Part I §1.6): three representational domains (Reality, Cognitive State, Structured Generative World Model), five universal functions (Perception, Inference, Evaluation, Learning, Execution), five computational laws (representational locality; controlled information acquisition; persistent-knowledge-only-via-learning; reality-only-via-execution; adaptation-requires-evaluation), and condition-driven activation. Every primitive below is understood as a *strategy or specialization of those five functions*, never as a new fundamental operator.

## 5.3 The cognitive primitives — why each matters

Each primitive is a hypothesis about a mechanism that turns experience into competence. Each is defined computationally, isolated experimentally, and either validated or rejected.

**Why memory matters.** Without persistence there is nothing for intelligence to be *about*. Memory is the episodic/experiential store that lets the system recall what reality previously said — the precondition for compounding. The research question is not "store text" but *which* memory organization causally improves transfer and generalization.

**Why reflection matters.** A system that cannot examine its own attempt cannot correct it. Reflection is the self-critique loop that turns a failed episode into a revised approach. It is what converts raw experience into *learning* rather than mere logging.

**Why curiosity matters.** A purely reactive system only answers questions posed to it. Curiosity is the mechanism that generates the system's *own* questions where the world is *learnably* uncertain — the engine of scientific discovery and of exploring an engineering space rather than exhausting a prompt.

**Why attention matters.** Engineering artifacts are enormous; cognition is bounded. Attention is the mechanism that focuses finite compute on the part that matters — a single stress concentration in a large model, the one constraint that is binding. Without it, bounded rationality is impossible.

**Why replay matters.** Experience is expensive to acquire and easy to waste. Replay re-presents past episodes to consolidate learning without re-incurring the cost of new reality — the mechanism by which a small stream of grounded episodes yields outsized competence.

**Why forgetting matters.** Not all experience is worth keeping; stale or misleading episodes degrade retrieval. Forgetting is the principled pruning that keeps the knowledge structure useful. It is as important as remembering, and it is a mechanism, not an accident.

**Why confidence (calibrated uncertainty) matters.** "Verified vs. guessed" is a boolean where a *distribution* is required. Calibrated confidence — with epistemic and aleatoric uncertainty separated — is what lets the system decide when to gather more information and when to stop, and what makes an approximate physical verdict honest rather than falsely binary.

**Why planning matters (as form).** Planning is inference over possible futures — the mechanism that composes actions toward a goal. MiniFlyWire studies the *form* of planning (representation, search, backtracking); it never studies domain planning *content*, which belongs to Velith and Mini Prometheus.

**Why learning matters.** Learning is the only function that modifies persistent knowledge (Computational Law 3). Every other mechanism ultimately exists to produce the evaluative signal that makes principled learning possible. Learning is where experience becomes durable competence.

## 5.4 How a discovery becomes reusable (the promotion pipeline)

A validated primitive is not "released"; it is **promoted**, and promotion is a disciplined pipeline, not a judgment call.

1. **Notebook hypothesis.** The idea is recorded in the laboratory notebook. Nothing there is scientifically accepted. Every hypothesis begins here.
2. **Reduction.** The mechanism is reduced to an operator over defined computational objects. If it cannot be so reduced, it does not proceed.
3. **Isolation and falsification.** An experiment is designed in which the mechanism is the *single manipulated variable*, with appropriate baselines and ablations. The team actively tries to *destroy* the hypothesis.
4. **Cross-framework comparison and revision.** The result is compared against alternative explanations (does a simpler model explain it? is it just retrieval?). The hypothesis is revised or rejected as evidence dictates.
5. **Acceptance into frozen theory.** Only after surviving falsification is the mechanism written into the permanent research documents as validated, with its evidence and its spec.
6. **Hand-off to Noetica.** The validated spec crosses the Knowledge Flow. Noetica re-implements it. **No research code is imported.**

## 5.5 The promotion gate (validation criteria)

A mechanism is eligible for promotion only if it passes **all** of these — the gate is conjunctive:

- **Hypothesis-defined.** It expresses a clearly stated cognitive hypothesis, not a vague capability.
- **Causally isolated.** Its contribution is measured with the mechanism as the single manipulated variable (ablation/intervention), not inferred from an architecture's overall score.
- **Quantitatively measured.** Effect size and its variability are reported, not just significance; an underpowered or noisy positive is treated as *uninterpretable*, not a weak win.
- **Falsification-tested.** The experiment could have shown the mechanism *useless* and did not. A mechanism that cannot fail its test has not been tested.
- **Domain-agnostic.** The mechanism is a *form* of cognition, not domain content. (A mechanism that only works because of engineering-specific knowledge is content, and belongs in a domain layer.)
- **Dependency-light and re-implementable.** It can be specified cleanly enough for Noetica to rebuild without inheriting research scaffolding.
- **Not a known anti-pattern.** LLM-as-judge and any mechanism that corrupts the grounding signal are permanently barred from promotion regardless of apparent performance.

Failing any criterion returns the mechanism to the notebook. Passing all of them makes it a **validated mechanism** eligible for the Knowledge Flow.

## 5.6 The validation methodology (how experiments are run)

MiniFlyWire's experiments obey the same measurement discipline the whole ecosystem reuses (it is first defined here and inherited by Velith's compounding experiment):

- **Non-saturating baselines.** Use a baseline with headroom so a mechanism's *delta* is visible; a ceiling-level baseline masks real effects.
- **Pre-registration.** Freeze the sample size, seeds, minimum effect size, exact contrasts, and metrics *before* the first real run, hash-tagged.
- **Mechanically-enforced held-out lock.** Held-out data can never enter any arm's memory; enforced in code, not by discipline.
- **Frozen evaluation.** Measure on the frozen system with memory read-only, so memorization cannot counterfeit learning.
- **Staged spending.** A cheap go/no-go stage precedes the decisive run; a stage-1 win is *necessary but not sufficient* and is never mis-sold as confirmation.
- **Effect size over significance.** With few seeds, magnitude and seed-spread are the primary evidence.

## 5.7 The research workflow (day-to-day)

Observation → Hypothesis → Reduction → Falsification → Cross-framework comparison → Revision → Acceptance/rejection → Promotion. Rejected and reduced hypotheses are **preserved on purpose**, because a documented rejection prevents the ecosystem from re-litigating a settled question and is itself scientific evidence. Material is promoted out of the notebook *only* after successful falsification and external review.

## 5.8 What MiniFlyWire must never do

Never ship production code; never carry an availability obligation; never be imported; never promote a mechanism on intuition or biological inspiration alone; never promote a known anti-pattern; never let benchmark score replace mechanism-level explanation; never let itself decay into an LLM prompt-engineering lab instead of a cognition laboratory.

---

# PART VI — NOETICA (THE PLATFORM)

This is the definitive subsystem handbook for the platform. Every subsystem is described by **what it is** and, more importantly, **why it exists** — because a platform whose engineers understand only *what* will, under deadline pressure, put things in the wrong place. Each subsystem owns a *mechanism* and publishes an *interface*; none owns domain content.

> **The prime directive of Noetica.** Noetica owns mechanisms, interfaces, and the shared state substrate. It contains no engineering or manufacturing content, no domain verifier, and no homunculus. Every subsystem below is a *form*, never a *content*.

## 6.1 State Substrate — *the true core*

**What.** The persistent, typed, provenance-tracked representation of the artifact and its environment. Every other subsystem reads and writes it. Generators, planners, verifiers, and learners are transformations over this shared state.

**Why.** Because intelligence must be *about* something persistent. Without a substrate the platform degenerates into a control-flow-centric "bag of agents" passing stateless text — exactly what the state-centric principle (Design Principle 2, `DECISIONS.md` D9) forbids. The substrate is named the core so the architecture cannot drift away from it. Its long-term evolution is toward **belief/probabilistic state** (confidence, epistemic/aleatoric separation) so it can host approximate physical domains, not only deterministic ones.

## 6.2 Provenance & Lineage

**What.** The derivation record of every belief and artifact: where it came from, which transformation produced it, under what inputs. First-class, from the first commit.

**Why.** "If we cannot answer *why did it do that?*, the system is a toy regardless of capability" (Principle 7). Provenance is what makes grounding auditable, makes reproducibility possible, and makes the compounding experiment interpretable. Documentation/code divergence and untracked beliefs are provenance violations.

## 6.3 Runtime & Agent Lifecycle

**What.** The mechanism that runs an agent: sets up an episode, drives the condition-driven activation of functions, and tears down cleanly, owning operation order.

**Why.** Something must own *when* cognition proceeds without becoming the thing that *decides what to think* (that would be a homunculus). The runtime owns orchestration *form*; domain reasoning content stays in the layers above.

## 6.4 Memory Framework

**What.** The persistence of **episodes and experience over time**, and the write-filter policies that decide what is retained (e.g., verified-only vs. unfiltered).

**Why.** Compounding is impossible without memory, and *which* memory policy is used is the very thing the differential experiment manipulates. Memory is defined narrowly — persistence of experience — precisely so it does not collide with Knowledge or Context (see §6.20).

## 6.5 Knowledge Store Engine

**What.** The typed, provenance-tracked semantic/graph **store engine**: schema-agnostic storage and retrieval of structured knowledge (entities, relations, constraints, transitions and their properties).

**Why.** Domains need to accumulate *structured* knowledge, not just episodes. Noetica owns the *engine* (how to store/retrieve/version typed knowledge); domains **populate** it with content (engineering ontology, manufacturing concepts). Owning the engine but not the content is what keeps the platform domain-agnostic.

## 6.6 Context Engine

**What.** Working-set assembly and context-window budgeting for a *single* inference: selecting, from memory and the knowledge store, the relevant subset for the current step.

**Why.** Inference is bounded; the context window is a scarce resource. Context is a distinct mechanism from Memory (persistence) and Knowledge (structured store): it is the *momentary assembly* for one act of cognition. Retrieval here is driven by causal relevance and active constraints, not by semantic similarity alone (a MiniFlyWire finding).

## 6.7 Reasoning Runtime *(form, not mind)*

**What.** A reasoning *loop/runtime*: the mechanism that iterates inference, applies verification seams, and backtracks. It owns the **form** of reasoning.

**Why.** The ecosystem forbids a homunculus. Listing a bare "Reasoner" that *knows about the world* would smuggle domain content into the platform. Noetica owns *how* to run a reasoning loop; **what** is reasoned about is domain content (Velith, Mini Prometheus). This distinction is the single most common place the platform is tempted to breach its own boundary.

## 6.8 Planning Runtime *(representation + executor)*

**What.** A **plan representation** and a **plan executor**: the mechanism to express, sequence, and execute plans, with a reflection seam.

**Why.** Same reason as reasoning: planning *form* is a reusable mechanism; planning *content* (an engineering plan, a manufacturing schedule) is domain-owned. Domains express their plans *as Noetica plans*; they never rebuild the executor.

## 6.9 Reflection

**What.** The self-critique loop that inspects an attempt and proposes a revision. A re-implementation of MiniFlyWire's validated reflection primitive.

**Why.** Reflection converts experience into correction. It is a mechanism (form of self-critique), not domain knowledge, so it lives here and is used by every domain.

## 6.10 Evaluation Harness

**What.** The experiment machinery: arms, held-out lock, metrics, the `EvalHarness` interface, and the frozen-evaluation discipline. A cross-cutting platform service.

**Why.** Measurement discipline must be *owned once* and reused by every vertical and every rung of the migration ladder. Building it into the platform (rather than re-inventing it per domain) is what makes results comparable across the decade. Noetica's self-tests run this harness against a **reference/fake verifier**, never a real domain one.

## 6.11 Verification Protocol *(protocol here, oracle in the domain)*

**What.** The verification *harness/protocol*: how arms run, the held-out lock, the metrics, and the `Verifier` interface with its `Verdict` type. The **concrete oracle is not here.**

**Why.** This is the boundary the ecosystem's own history got wrong (a domain SWE verifier leaked toward the core). The rule is permanent: **Noetica owns the protocol; the domain owns the oracle.** The `Verdict` must be general enough to represent an *approximate oracle with calibrated uncertainty*, not only a boolean — because the higher rungs (FEA/SPICE/manufacturing) are approximate by nature.

## 6.12 Tool Runtime & Tool Interface

**What.** The tool system and the `Tool` interface. Domains implement concrete tools (CAD, solvers, MES, robots) behind it.

**Why.** "Wrap, don't rebuild." Noetica provides the *mechanism* of registering, invoking, and sandboxing tools; the tools themselves are wrapped external kernels owned by domains. Long-running tools (FEA/CFD taking minutes to days) require the runtime to support **asynchronous, non-blocking** invocation — the reasoning loop must never block on a multi-day solve.

## 6.13 Skill Runtime & Skill Interface

**What.** The skill system and the `Skill` interface: composable, learned units of competence. Domains implement concrete skills.

**Why.** Skills are how verified experience crystallizes into reusable competence — a mechanism of composition. The *form* is Noetica's; the *engineering/manufacturing skills* are domain content.

## 6.14 Budget / Meta-control (bounded rationality)

**What.** The `BudgetMeter` and meta-control policy: how much to think, which model to call, when to simulate, when to stop.

**Why.** "Computation is itself a costly act" (Principle 5). Without meta-control the system either under-thinks (cheap and wrong) or over-thinks (correct and bankrupt). This is a first-class mechanism, and the long-term goal is for the policy to be *learned*, not hand-tuned.

## 6.15 Model Abstraction & Routing

**What.** The `ModelRouter`: a thin abstraction over model providers so any frontier/open-weight/small task model is swappable, with a hard cost guard.

**Why.** "LLMs are components, never the mind" (Principle 3). The system's identity must not depend on any single model or vendor. Routing is the mechanism that guarantees swappability and enforces the cost guard. (Its seed is the thin LLM adapter first built in the Velith spike and **extracted** upward — `DECISIONS.md` D16.4.)

## 6.16 Guardrails / Safety Policy Engine

**What.** The safety policy *engine* (a cross-cutting service). Domains supply domain policy; Noetica supplies the engine that enforces it, including the immutable oversight boundary.

**Why.** "Grounding and oversight are immutable" (Principle 6). The engine that enforces the human-oversight boundary must live in the platform and be un-modifiable by the system's self-improvement. Domain-specific policy is content; the enforcement engine is mechanism.

## 6.17 Observability & Logging

**What.** Structured logging, metrics, and traces across the platform — the ability to see what the system did and why.

**Why.** Non-negotiable with provenance (Principle 7). Observability is what lets a human overseer, and the evaluation harness, understand and trust runs. It is a cross-cutting service, not a cognitive primitive, and lives in its own tier so abstraction levels do not mix.

## 6.18 Developer Surface — SDK, Plugin System, Public APIs

**What.** The `Agent`/`Runtime` SDK, the plugin system, and the stable public APIs through which domains build. These are **surfaces over** the core, grouped in their own tier.

**Why.** Domains need a clean, versioned way to consume the platform. Grouping developer surfaces separately (rather than listing them as peers of Memory or Planner) keeps abstraction levels from mixing and makes the stable contract explicit. Everything a domain needs is *an interface plus a default*.

## 6.19 Internal APIs

**What.** The private plumbing: substrate storage internals, routing internals, harness internals, the reference/fake verifier.

**Why.** These may change freely as long as the public interface contracts hold. Keeping them private (never consumed across a repo boundary) is what allows Noetica to evolve without breaking domains — provided versioning discipline (Part XI) is honored.

## 6.20 The three definitions that must never collide

Memory, Knowledge, and Context are three legitimate subsystems *only if* defined crisply. Written here so they can never be conflated:

- **Memory** = persistence of **episodes/experience over time**.
- **Knowledge** = the typed, provenance-tracked **semantic/graph store engine** (schema-agnostic).
- **Context** = **working-set assembly and window budgeting** for a single inference.

If any two of these begin to overlap in an implementation, it is a design defect to be corrected, not a convenience to be accepted.

## 6.21 Compute & Infrastructure Interfaces *(infrastructure is external to the architecture)*

**What.** Physical and virtual infrastructure — cloud, Kubernetes, GPUs, edge devices, storage, networking, and the like — is **external to the four-layer architecture**. It is *execution substrate*, not a project, and it is **not a fifth layer**. The architecture touches it through a clean, three-part ownership split:

- **Noetica owns the compute interface and budgeting.** The platform publishes the abstract compute/execution interface (request compute, place work, meter and cap cost) and owns the `BudgetMeter`/meta-control that governs it (§6.14). This is a *mechanism*: how the system asks for and bounds compute, independent of any vendor.
- **Domain layers own the adapters.** Velith and Mini Prometheus implement concrete adapters behind Noetica's compute interface (e.g., a solver-cluster adapter, a GPU-scheduler adapter, an edge/robot-execution adapter, an OPC UA execution bridge). Adapters are *implementations* of a Noetica interface, exactly like any other `Tool` (§6.12).
- **External infrastructure owns execution.** The actual running of containers, pods, jobs, and hardware belongs to the infrastructure itself, outside all four projects. The architecture never *becomes* the infrastructure and never rebuilds it ("wrap, don't rebuild").

**Why.** Two failure modes are prevented. First, **infrastructure creep into the platform** — Noetica growing Kubernetes/cluster logic and ceasing to be domain- and vendor-agnostic. Second, **a phantom fifth project** — treating "infra" as a peer of the four layers, which would duplicate ownership and invite an unbounded scope. Keeping infrastructure external, with a Noetica compute interface + budget above and domain adapters below, preserves the mechanism/content line and the strict DAG while honoring the single-machine-until-reality-demands-otherwise discipline (a scale posture, not an architectural layer). See the matrix rows in §9.2 and Law 3/Law 5 (no domain or infra content in the core).

---

# PART VII — VELITH (ENGINEERING INTELLIGENCE)

Velith is where the ecosystem's central claim is tested and where the platform is grown by extraction. This part defines what engineering intelligence means here, what Velith owns, how it consumes Noetica, and — as importantly — what it must never own.

## 7.1 What Velith is

Velith is a **domain application**, the first consumer of Noetica. It is an engineering intelligence: it takes engineering intent under constraints and returns a **verified, explained** engineering artifact with calibrated uncertainty. It is *state-centric* like the whole ecosystem — the artifact under design is a persistent representation on Noetica's substrate, and Velith's generators, solvers, and verifiers are transformations over that state.

Its identity is guarded by the same non-goals as the program: it is not a chatbot, not a CAD generator, not an agent framework, not an LLM wrapper. If a Velith decision would make it indistinguishable from those, the decision is wrong.

## 7.2 Engineering as universal cognition over an engineering world model

A central, hard-won research result (MiniFlyWire H3, corroborated by review): **engineering introduces no new fundamental computational operators.** Engineering is *universal cognition operating over an engineering world model.* The five functions (Perception, Inference, Evaluation, Learning, Execution) are unchanged; what changes is the *content* of the World Model and the *constraints* in play.

The consequences are constitutional:
- Velith does **not** get its own reasoning/planning/memory *mechanisms* — those are Noetica's. It gets its own *content*.
- Domain expertise does **not** require separate expert agents (H4/R2/R3 rejected). Expert behavior emerges by activating the relevant portion of the World Model, not by spawning a new engine per discipline.
- Engineering cognition operates on an **evolving realizable representation** (H9): the computational object progressively transformed toward realization while satisfying constraints — a component, product, assembly, factory, or system. This "realizable representation" is engineering *content* on Noetica's substrate, not a new platform primitive.

## 7.3 What Velith owns

- **Engineering knowledge and ontology** (materials, physics relationships, engineering constraints), populating Noetica's knowledge store.
- **The physics / world-model content** — the "physical grounding" the reviews called for — expressed as content over Noetica's substrate, so a text-native model can be given spatial/physical meaning (torque, gravity, geometry) without bloating the platform.
- **CAD, simulation, optimization** as wrapped external kernels behind Noetica's `Tool` interface.
- **Engineering verification** — the concrete oracle implementing Noetica's `Verifier` protocol: deterministic where the model-gap is zero (SWE), approximate-with-calibrated-uncertainty on higher rungs.
- **The engineering vertical and its migration ladder** (below).

## 7.4 What Velith consumes from Noetica (and never rebuilds)

Velith consumes, through interfaces: the runtime and agent lifecycle; the state substrate and provenance; memory and its write-filter policies; the knowledge-store engine; context assembly; the reasoning and planning runtimes; reflection; the evaluation harness and held-out lock; the verification protocol and `Verdict` type; the tool and skill systems; model routing; budget/meta-control; guardrails; observability.

It **never re-implements** any of these. The three standing rules are kept verbatim from the ratified charter: *never reimplement memory; never reimplement planning; never reimplement runtime.* Extend the list to every Noetica mechanism.

## 7.5 The engineering loop (propose → verify → log)

Velith's irreducible core, already real on the ground at milestone M1: for an engineering task, a model **proposes** a candidate; a containerized, deterministic verifier **disposes** of it against grounded truth (hidden tests / static analysis); the outcome is persisted as a **provenance-complete, content-hashed episode** that survives process exit. Determinism is located in the *verifier*, not in the stochastic proposer — a clarification (`DECISIONS.md` D16.1) that strengthens grounding. A test *failure* is a valid grounded outcome and first-class learning data, never an error; only infrastructure faults are errors.

This loop is simultaneously (a) Velith's engineering mechanism and (b) the **extraction seed** for Noetica's episode store, verifier protocol, provenance discipline, and model-routing adapter (see N.3). That dual role is the platform-by-extraction law working as intended.

## 7.6 The compounding experiment (Velith's scientific obligation)

Velith runs the experiment that justifies the whole program (§1.7): *can a grounded, verification-first engineering agent measurably improve its held-out performance through verified experience?* It is a **differential** experiment with the experience-retention write-filter as the single manipulated variable, across arms:

- **A0 — Cold:** no memory (baseline + variance).
- **A1 — Unfiltered memory:** all attempts retained (the RAG/null control).
- **A2 — Verified memory (treatment):** only verification-passing solutions and verified failure signatures retained.
- **A3 — Anti-grounding (falsification arm):** retains solutions the model *believed* correct, without running the verifier.
- **A4 — Verified-success-only (ablation):** isolates the value of grounded *failure* learning.

The decisive criterion is **A2 strictly beats A1**. A2≈A1 is the "grounding adds nothing over retrieval" verdict; A2≈A3 would put the entire verification-first premise in question. **A1 and A2 must share an identical retriever, embedder, and top-k**; the only legal difference is the write-filter — if their retrievers ever differ, the experiment is void. This invariant is enforced as a permanent test.

## 7.7 The migration ladder (how Velith reaches manufacturing without abandoning rigor)

Generality is reached by a pre-committed ladder so "software-first" can never quietly become "software-only":

1. **Software (repo-level SWE)** — prove the loop compounds; zero model-gap; external held-out benchmark.
2. **Electronics / PCB** — first *deliberate* model-gap (approximate SPICE) and a literally manufacturable artifact (Gerbers).
3. **HDL / firmware** — exhaustive formal verification; first contact with timing/physical constraints.
4. **Mechanical / FEA → manufacturing** — the north star, attempted only after the loop has survived progressively widening model-gaps.

The architecture stays domain-agnostic so each new vertical is a **registration, not a rewrite**. Each rung reuses the measurement discipline; each widens the verification model-gap deliberately and only after the prior rung is proven.

## 7.8 What Velith must never own or do

- Never own a Noetica mechanism (memory, planning, runtime, provenance, routing, evaluation harness, verification protocol).
- Never treat verification as a free oracle; never hide the model-gap on approximate rungs.
- Never import Mini Prometheus or MiniFlyWire.
- Never let engineering content harden into Noetica without a *second* credible consumer (extraction requires it).
- Never spawn per-discipline engines or per-expert agents; expertise is World-Model activation, not new agents.
- Never optimize a fixed benchmark as the goal; measurement is held-out and generalization-tested.

## 7.9 Boundaries

**With Noetica (below):** interface owned above, implementation owned here; content populates the platform's stores; Velith configures the harness, never rebuilds it. **With Mini Prometheus (above):** Velith exposes engineering results and an engineering-task API; Mini Prometheus consumes those and never reaches past Velith to re-implement engineering.

---

# PART VIII — MINI PROMETHEUS (MANUFACTURING INTELLIGENCE)

Mini Prometheus is the top of the stack and the ecosystem's contact point with physical reality. This part defines what it owns, how it consumes Velith, how it handles the probabilistic physical world, and how it feeds experience back up.

## 8.1 What Mini Prometheus is

Mini Prometheus is the **manufacturing-intelligence application**. It consumes Velith's verified engineering intelligence and turns it into **manufacturable plans and running production**. It owns manufacturing content: process and factory planning, scheduling, robotics, supply chain, MES, and production execution. It is where the decade-scale north star — turning product intent into things that can actually be built — is finally pursued.

## 8.2 What it owns

- **Manufacturing planning and scheduling** — the manufacturing planner is Mini Prometheus's heart.
- **Factory workflows, robotics, supply chain, MES, production execution** — as wrapped industrial systems behind adapters (OPC UA and similar standard protocols).
- **The manufacturing digital-twin content** — the factory/product twin, instantiated on Noetica's twin/state-sync *engine*.
- **Experience collection** — the instrumentation that captures reality's verdicts and emits the Experience Flow.

## 8.3 The probabilistic reality problem

Manufacturing is not a deterministic logic puzzle. Tool wear, thermal dynamics, sensor noise, material impurities, and Sim2Real divergence make it inherently **probabilistic**. Two constitutional consequences follow:

- The state the twin syncs must carry **confidence and belief**, not just binary values — which is why Noetica's substrate is evolving toward probabilistic/belief state (§6.1). "I am 80% sure this model is valid" is a first-class state, not a rounding of true/false.
- Verdicts at this layer are **distributions with calibrated uncertainty**, not booleans ("success with 85% confidence given thermal margins"). The `Verifier`/`Verdict` mechanism was made general enough for exactly this (§6.11).

**Sim2Real** is named explicitly: the divergence between expected (simulated) physics and actual (sensed) physics must be *tracked*, not assumed away. This tracking is manufacturing content that uses Noetica's substrate and provenance.

## 8.4 The digital twin — engine vs. content (a boundary that is easy to get wrong)

A digital twin is *not merely* state synchronization. But the ecosystem still splits it cleanly: the **twin engine** — state sync, versioning, provenance — is a **Noetica** mechanism; the **manufacturing twin content** — the physical world model of this factory/product, its temporal simulation and predictive physics — is **Mini Prometheus**'s (with engineering-physics content sourced from Velith). Building the twin *engine* inside Mini Prometheus, or pushing the twin *content* down into Noetica, are both breaches.

## 8.5 Recursive layering (why Mini Prometheus may become its own stack)

Manufacturing's scope (planning, factory automation, supply chain, robotics, scheduling, twin) is broad enough to become its **own internal stack**. The architecture is explicitly **recursive**: Mini Prometheus may split internally — for example, a **manufacturing planner** sub-layer and a separate **execution** sub-layer (robotics, MES) coordinating through Velith/Noetica contracts and standard industrial protocols. Internal sub-verticals **never import each other directly**; they coordinate through contracts, exactly like the top-level layers. This prevents the manufacturing layer from collapsing into one unmaintainable flat module.

## 8.6 The Experience Flow originates here

Mini Prometheus is the ecosystem's primary generator of **grounded physical experience**. Every production outcome — success, failure, drift — is captured, vectorized, and provenance-tracked, then emitted **up** the stack as data (never code): to Velith as refined engineering constraints, to Noetica as inputs that refine mechanisms via extraction, and to MiniFlyWire as new research questions and datasets. This is what closes the compounding loop for the whole ecosystem.

## 8.7 What Mini Prometheus must never own or do

- Never re-implement engineering (that is Velith) or platform mechanisms (that is Noetica).
- Never build the twin *engine*; consume Noetica's.
- Never import MiniFlyWire; never bypass Velith for engineering concerns.
- Never wire internal sub-verticals sibling-to-sibling.
- Never treat physical verification as exact or free; never emit experience as code.

## 8.8 Boundaries

**With Velith (below):** consumes engineering results and API; owns manufacturing content; twin content here, twin engine in Noetica, engineering physics from Velith. **Above:** the physical world and the Experience Flow back to research — there is no software layer above it.

---

# PART IX — BOUNDARIES AND THE RESPONSIBILITY MATRIX

This is the definitive ownership table. **Every capability has exactly one owner.** The matrix is how a contributor decides where a module belongs; if a capability is not here, it must be added by amendment before it is built.

## 9.1 How to read the matrix

- **Owner** — the single layer responsible for the capability.
- **impl** — implements an interface owned above (the mechanism is owned above; the concrete implementation lives here).
- **uses / consumes** — depends on the capability through a published interface.
- **populates** — supplies content into an engine owned above.
- **(feeds)** — contributes ideas via re-implementation (Knowledge Flow), never code.
- **—** — must not touch.

The governing invariant: **Noetica owns mechanisms, interfaces, and the shared state substrate; domain layers own content and the concrete implementations of those interfaces; MiniFlyWire owns discovery and is a feeder, never a dependency.**

## 9.2 The Responsibility Matrix

| Capability | MiniFlyWire | Noetica | Velith | Mini Prometheus |
|---|---|---|---|---|
| Cognitive research / hypothesis testing | **Owner** | — | — | — |
| Validated-mechanism discovery | **Owner** | (consumes as ideas) | — | — |
| Shared **state substrate / blackboard** | (feeds) | **Owner** | uses | uses |
| **Belief / probabilistic state** (confidence, epistemic/aleatoric) | (feeds) | **Owner** | uses | uses |
| **Provenance & lineage** | (feeds) | **Owner** | uses | uses |
| **Memory** (episodic/experiential persistence) | (feeds) | **Owner (framework)** | uses | uses |
| **Knowledge store engine** (typed graph, retrieval) | (feeds) | **Owner (engine)** | populates (eng.) | populates (mfg.) |
| **Context** assembly / window budgeting | (feeds) | **Owner** | uses | uses |
| Reasoning **runtime/loop** (form) | (feeds) | **Owner** | uses | uses |
| Reasoning **content** (domain reasoning) | — | — | **Owner (eng.)** | **Owner (mfg.)** |
| Planning **representation + executor** (form) | (feeds) | **Owner** | uses | uses |
| Planning **content** (eng./mfg. plans) | — | — | **Owner** | **Owner** |
| Reflection / self-critique loop | (feeds) | **Owner** | uses | uses |
| Tool system + **Tool** interface | — | **Owner** | impl (CAD, solvers) | impl (MES, PLC, robots) |
| Skill system + **Skill** interface | — | **Owner** | impl (eng. skills) | impl (mfg. skills) |
| Agent runtime & lifecycle | — | **Owner** | uses | uses |
| Multi-agent coordination | (feeds) | **Owner** | uses | uses |
| Model abstraction / routing / cost guard | — | **Owner** | uses | uses |
| Meta-control / budget (bounded rationality) | (feeds) | **Owner** | uses | uses |
| **Verification protocol / harness** | (feeds) | **Owner** | uses | uses |
| **Verifier / oracle** (concrete) | — | interface only | **Owner** (SWE, FEA, SPICE) | **Owner** (mfg checks) |
| Evaluation / experiment arms / held-out lock | (feeds) | **Owner** | configures | configures |
| Guardrails / safety policy engine | (feeds) | **Owner (engine)** | domain policy | domain policy |
| Human-oversight boundary enforcement | — | **Owner (immutable)** | respects | respects |
| Logging / observability | — | **Owner** | emits | emits |
| Developer SDK / plugin / public APIs | — | **Owner** | consumes | consumes |
| **Experience aggregation** mechanism | (feeds) | **Owner** | emits + uses | emits |
| Engineering ontology & physics/material knowledge | — | — | **Owner** | consumes |
| Physics / spatial world-model **content** | (feeds) | — (substrate only) | **Owner** | consumes |
| CAD / simulation / optimization orchestration | — | — | **Owner** | consumes |
| **Digital-twin engine** (state sync mechanism) | (feeds) | **Owner** | uses | uses |
| Digital-twin **content** (factory/product twin) | — | — | (eng. models) | **Owner** |
| Sim2Real divergence tracking | (feeds) | (substrate support) | uses | **Owner** |
| Manufacturing planning / scheduling / MES | — | — | — | **Owner** |
| Factory automation / robotics / supply chain | — | — | — | **Owner** |
| **Compute interface & budgeting** (mechanism) | (feeds) | **Owner** | uses | uses |
| **Infrastructure adapters** (cloud/K8s/GPU/edge/storage/net) | — | interface only | impl | impl |
| External infrastructure **execution** (containers, pods, hardware) | — | — | — | — · **External** |
| **Experience data contracts** (schema + versioning) | consumes | **Owner (authority)** | emits/consumes | emits/consumes |
| **Experience data lifecycle** (compression, retention, pruning) | (feeds) | **Owner (framework)** | configures | configures |

> **Infrastructure note (Amendment 3).** External infrastructure — cloud, Kubernetes, GPUs, edge devices, storage, networking — is **outside the four-layer architecture entirely.** It is execution substrate, not a project and not a fifth layer. Noetica owns the compute *interface* and *budgeting*; domain layers own the *adapters*; the infrastructure owns *execution*. See §6.21.

## 9.3 Why one owner per capability

Shared ownership is how boundaries rot. Two owners means two mental models, two change cadences, and an inevitable moment where a change that is correct for one owner silently breaks the other. A single owner per capability makes every change's blast radius knowable, makes the dependency graph a true DAG, and makes the question "who decides?" always answerable. When a capability seems to need two owners, it is almost always **one mechanism (owned above) and one content/implementation (owned by the domain)** that were not yet distinguished — split them along the mechanism/content line and the single-owner rule holds.

---

# PART X — ARCHITECTURE LAWS

These are the **immutable laws** of the ecosystem. They are changed only by the amendment procedure (Part XI), never by exception. Laws 1–11 are the ratified constitutional laws, restated at Handbook authority; Laws 12–20 are the additional laws established at Handbook v1.0 to close gaps the ratified set left implicit; Laws 21–23 were ratified as constitutional amendments at the final review stage (Handbook v1.1). Every law is stated so a violation is *detectable*.

## The Laws

**Law 1 — Vision is fixed.** The mission, the four-layer direction, and the definition of success are frozen. They change only by recorded amendment. *Violation:* a roadmap or module that redefines the mission or the layer direction without an amendment.

**Law 2 — One owner per capability.** Every capability has exactly one owner (Part IX). *Violation:* two layers implementing or claiming the same capability.

**Law 3 — Mechanism ≠ Content.** Noetica owns mechanisms and interfaces; domains own content and implementations. *Violation:* domain content inside Noetica, or a domain re-owning a mechanism.

**Law 4 — MiniFlyWire never becomes production.** Research is never imported and never carries a production/availability obligation. *Violation:* any import of MiniFlyWire, or MiniFlyWire code shipped as production.

**Law 5 — Noetica never contains engineering or manufacturing logic.** The platform is domain-agnostic. *Violation:* a concrete oracle, physics model, engineering ontology, or manufacturing rule inside Noetica.

**Law 6 — Velith never reimplements Noetica.** Domains consume platform mechanisms; they do not rebuild them. *Violation:* a domain-local memory store, router, provenance system, or harness that duplicates Noetica's.

**Law 7 — Promotion requires validation and re-implementation.** A cognitive primitive enters Noetica only after passing MiniFlyWire's promotion gate, and only by re-implementation. *Violation:* a mechanism promoted on intuition, or imported rather than re-implemented.

**Law 8 — Platform grows by extraction, not speculation.** A capability enters Noetica only when it has a real consumer and a credible second on the horizon; it is harvested from a working application, not designed in the abstract. *Violation:* a platform capability with no real consumer.

**Law 9 — Strict dependency DAG.** The Code Flow is a strict acyclic graph: Noetica → Velith → Mini Prometheus, one direction only. *Violation:* any upward or cyclic import.

**Law 10 — Cognition remains core research.** The ecosystem does not abandon cognition for pure software orchestration; MiniFlyWire remains alive and funded as the scientific engine. *Violation:* dissolving cognitive research into LLM prompt-engineering.

**Law 11 — Constitution-check before implementation.** Every new feature is checked against this Handbook *before* it is built (Part XII). *Violation:* implementation that skipped the decision protocol.

**Law 12 — Experience flows up as data, never as code.** Telemetry, failures, episodes, and derived questions move upward through storage and interfaces; no upper layer ever imports a lower one. *Violation:* an upward or cyclic import justified as "getting the data." (This is the law that lets the Experience Flow exist without breaking Law 9.)

**Law 13 — No duplicated abstractions.** A concept has one representation. Memory, Knowledge, and Context (and any future trio) must remain crisply distinct (§6.20). *Violation:* two subsystems that do the same job, or three that blur into one.

**Law 14 — Cross-layer contact is through versioned, typed interfaces only.** No concrete internal type crosses a repo/package boundary; contracts are semantically versioned. *Violation:* sharing concrete types by convention, or an unversioned breaking change to a public interface.

**Law 15 — Verification protocol is owned above; the oracle is owned by the domain.** Noetica owns the `Verifier` protocol and `Verdict` type; the concrete oracle is domain content. *Violation:* a domain verifier in the core, or a domain re-defining the protocol.

**Law 16 — Verdicts may be distributions, and grounding must be honest.** The verification mechanism supports approximate oracles with calibrated uncertainty; no layer may treat an approximate verifier as exact or as a free oracle. *Violation:* a boolean verdict masking an approximate check, or hidden model-gap.

**Law 17 — Grounding and oversight are immutable.** The system may improve how it designs; it may never modify how its success is judged or how it is overseen. *Violation:* any self-improvement path that can reach the verifier or the oversight boundary.

**Law 18 — Provenance and observability are non-negotiable and first-class.** Every belief carries its derivation from the first commit; documentation must not diverge from code. *Violation:* an untracked belief, or docs describing code that does not exist.

**Law 19 — No sibling-to-sibling imports.** Sibling verticals (including Mini Prometheus's internal sub-layers) coordinate through Velith/Noetica contracts, never by importing each other. *Violation:* a direct import between siblings.

**Law 20 — Self-tests use a reference/fake verifier.** Noetica's evaluation and verification self-tests run against a reference/fake verifier, never a real domain one, so the platform can never acquire a domain dependency through its tests. *Violation:* a Noetica test importing a domain oracle.

**Law 21 — Data Contract Law (the Experience Flow is contract-governed).** The Experience Flow moves only through **versioned data contracts**. Every episode, dataset, and derived-question schema is an explicit, versioned contract; any schema change requires a new version and a migration path. Upward data contracts are held to **the same rigor as downward code interfaces** (Law 14): a producer may not change a schema ad hoc, and a consumer reads against a declared contract version. *Violation:* an unversioned or unmigrated change to an experience/episode/dataset schema, or a consumer reading a schema without a declared contract version. (See §4.3, §11.7, §11.11.)

**Law 22 — AI Contributor Oversight (AI may reject, never ratify).** AI reviewers and AI contributors **may reject** constitutional, architectural, or boundary violations, and are expected to. They **may never be the final authority.** Any constitutional, architectural, or platform-level change requires **explicit human approval** before it is valid; an AI's approval is a recommendation, never a ratification. *Violation:* an AI reviewer's approval merged as final authority on a constitutional/architectural/platform change without recorded human ratification; or an AI blocking overriding a human ratifier's authority. (See §11.1, §11.10, §13.8.)

**Law 23 — Architectural Stability (the Constitution is presumed correct).** The Constitution is presumed correct. **No roadmap, implementation, AI suggestion, repository, benchmark result, or engineering convenience may modify it.** Any architectural change requires a **Constitution Amendment Proposal (CAP)** carrying every mandatory field (§11.6), an independent architecture review, and **explicit ratification by the project owner.** No constitutional change becomes valid until formally ratified. *Violation:* any de facto architectural change made through code, tooling, benchmark-chasing, or convenience without a ratified CAP. (See §11.6, Appendix C.)

## 10.1 The status of the laws

A law may be *added* by amendment when a new class of violation is discovered. A law is *removed or weakened* only by an amendment that names the law, states the evidence that it is wrong, and records the replacement — the same standard as any constitutional change (Part XI). Until then, a law admits **no exceptions**: "just this once" is precisely how a decade-scale architecture dies.

---

# PART XI — GOVERNANCE

Governance is how the ecosystem changes *without drifting*. It defines who decides, how architecture is reviewed, how capabilities are promoted and extracted, how the Constitution is amended, and how repositories, versions, and deprecations are managed.

## 11.1 Roles and authority

- **The Constitution (this Handbook)** is the highest authority. No role overrides it; roles *apply* it.
- **The Constitutional Architect** is the steward of this Handbook and the arbiter of boundary disputes. This role does not *decide* the architecture by preference; it *interprets and enforces* the Handbook, proposes amendments, and rejects violations. When uncertain, it optimizes for long-term maintainability, scientific correctness, modularity, clean architecture, and the AI Manufacturing Intelligence mission.
- **The Research Director / Scientific Council** governs MiniFlyWire's science: they own the promotion gate and certify validated mechanisms. Their acceptance is required before a primitive enters the Knowledge Flow.
- **Layer owners** are responsible for their layer's conformance to the Handbook and for proposing extractions upward.
- **Contributors (human or AI)** must run the Decision Protocol (Part XII) before implementing and must record decisions in the appropriate ledger.
- **AI reviewers and AI contributors** may **reject** constitutional, architectural, or boundary violations — and are expected to — but are **never the final authority** (Law 22). An AI's approval is a recommendation; it never ratifies a constitutional, architectural, or platform-level change.
- **The project owner (human ratifier)** holds final authority over the Constitution. Every constitutional, architectural, or platform-level change requires the project owner's **explicit human approval** to become valid. This authority may not be delegated to an automated reviewer.

No role may weaken a boundary silently. Every boundary change is an amendment (a ratified CAP, §11.6).

## 11.2 The architecture review process

Every proposed roadmap, module, milestone, repository change, or significant refactor is reviewed against the Handbook *before* work begins. The review answers the Decision Protocol questions (Part XII) and produces one of three outcomes:

- **Conforms** — proceed; record the decision.
- **Conforms with conditions** — proceed once named conditions (e.g., "extract behind an interface first," "add the missing test") are met.
- **Violates** — rejected. The reviewer states which law/boundary is violated and, where possible, the conforming alternative (usually an evolutionary one).

Reviews prefer **evolutionary improvement over rewrite**: a proposal that discards a working, boundary-respecting subsystem must justify itself against an evolutionary path and is the exception.

## 11.3 The promotion process (research → platform)

Governed by the Knowledge Flow, Law 7, and the promotion gate (Part V §5.5). Steps:

1. **Certification.** The Research Director/Scientific Council certifies that a primitive passed the conjunctive gate (hypothesis-defined, causally isolated, quantitatively measured, falsification-tested, domain-agnostic, dependency-light, not an anti-pattern).
2. **Registration.** The primitive is entered in the **Primitive Registry** (§11.5) with its spec, evidence, and version.
3. **Re-implementation.** Noetica re-implements the primitive behind a versioned interface, with provenance/observability from the first commit. No research code is imported.
4. **Record.** A decision entry records the promotion, superseding any prior treatment of that primitive.

A primitive that fails certification returns to the notebook. A promoted primitive that later fails in production is **demoted** by a recorded decision (§11.8).

## 11.4 The extraction process (application → platform)

Governed by Law 8. A capability inside a domain (first, Velith) is extracted up into Noetica only when: (a) it is a *mechanism*, not content; (b) it is domain-agnostic; (c) it has a real consumer *and* a credible second on the horizon; (d) it can be expressed behind a clean interface. Steps: propose extraction → review against Law 8 → define the interface → move the mechanism up, leaving the domain to consume it → record the decision. **Speculative extraction (no second consumer) is rejected.**

## 11.5 The Primitive Registry

A permanent, versioned registry of every promoted primitive and extracted mechanism, recording: name, source (MiniFlyWire spec or extraction origin), the interface it is exposed as, its version, its evidence/rationale, and its status (active / deprecated / demoted). The registry is the authoritative answer to "what mechanisms does Noetica own, why, and since when." Nothing enters Noetica's public surface without a registry entry.

## 11.6 Architecture amendments — the Constitution Amendment Proposal (CAP)

The Constitution is **presumed correct** (Law 23). The four-layer direction and the laws are frozen; **no roadmap, implementation, AI suggestion, repository, benchmark result, or engineering convenience may modify them.** Any architectural change requires a **Constitution Amendment Proposal (CAP)**, and no constitutional change becomes valid until it is **formally ratified by the project owner** (Law 22).

**Every CAP must include, in full:**

1. **Problem Statement** — what is wrong or newly required.
2. **Why the Constitution is insufficient** — the specific reason the current text cannot accommodate the need.
3. **Alternatives Considered** — including the evolutionary, no-amendment option.
4. **Impact on MiniFlyWire.**
5. **Impact on Noetica.**
6. **Impact on Velith.**
7. **Impact on Mini Prometheus.**
8. **Dependency impact** — effect on the Code Flow DAG, the Experience Flow contracts, and cross-layer interfaces.
9. **Migration strategy** — how existing code, data contracts, and records move to the amended state.
10. **Backward compatibility** — what is preserved, what is deprecated, and the deprecation window.
11. **Independent architecture review** — a review by a party other than the author (e.g., an external reviewer such as the Gemini/ChatGPT reviews used at this ratification stage).
12. **Explicit ratification by the project owner** — the human final authority (Law 22). An AI may review and recommend; it may not ratify.

**Recording.** A ratified CAP is recorded as a new dated decision in `DECISIONS.md` in the standard format, explicitly superseding any prior one, and — if it changes the Handbook — bumps the Handbook version and is logged in Appendix E. Decisions are **never edited away silently or removed**; a superseded decision remains in the record so future reviewers can see *why* the system is shaped as it is. The Constitution is allowed to change — it is **never** allowed to change *quietly* or *without ratification*.

## 11.7 The decision record and versioning

- **`DECISIONS.md` (the ADR ledger)** is the permanent, append-only record of ratified engineering decisions (D1–D21 and successors). Each entry carries ID, status, decision, rationale, alternatives rejected, and consequences.
- **This Handbook is versioned** (Handbook vN). A change to the Handbook is itself an amendment with a decision entry and a version bump.
- **Interfaces are semantically versioned.** A breaking change to any Noetica public interface (the state substrate schema, `Verifier`, `Verdict`, `MemoryStore`, `Plan`, `Tool`, `Skill`, `WorldModel`, etc.) requires a major-version bump, a migration note, and a deprecation window (§11.8). Because every layer depends on Noetica's interfaces, an unversioned breaking change is a constitutional violation (Law 14).
- **Experience data contracts are versioned with equal rigor (Law 21).** Every upward data contract — episode schema, dataset schema, derived-question schema — is semantically versioned; a schema change requires a version bump and a migration path, exactly as a downward code interface does. Noetica is the **contract authority** (it publishes and versions the contracts); producers emit against a contract version and consumers read against one. An unversioned or unmigrated schema change is a constitutional violation (Law 21).
- **Content hashing separates identity from provenance.** Reproducible identity (a function of task, patch, environment) lives in the content hash; non-reproducible provenance (timing, flakiness) is recorded outside it. Determinism is graded in levels, and the verifier targets reproducibility structurally, not incidentally.

## 11.8 Deprecation and demotion policy

- **Deprecation.** A public interface is deprecated by a recorded decision that names its replacement, provides a migration path, and sets a window during which both are supported. Removal happens only after the window and only by a further recorded decision.
- **Demotion.** A promoted primitive or extracted mechanism that fails in production is demoted (marked deprecated/removed in the Primitive Registry) by a recorded decision stating the evidence. Demotion is a normal, honest act — the record of *why* is what protects the next contributor.
- **Postponement.** Capabilities may be *intentionally postponed* (gated on a specific validation result), and the postponement is recorded so the ecosystem knows exactly what earns the right to decide them. Building a postponed item before its gate is a deviation requiring a recorded justification.

## 11.9 Repository rules

- The **boundary is architectural; the packaging is pragmatic.** The four layers are enforced as a **package-level DAG**, whether they live in one repository or several. Consolidated packaging is the default; a layer is split into its own repository only when it needs an independent release cadence or an independent team.
- **MiniFlyWire stays separate** (different license/quality bar, research-grade). Noetica + Velith (+ later Mini Prometheus) may begin as one repository with enforced internal package boundaries.
- **The package DAG is enforced in CI** (§12 and Law 9/12/19/20): a build fails if Noetica acquires a domain import, if a layer imports a sibling, if an upper layer imports a lower one, or if a Noetica self-test imports a domain oracle.
- **MiniNoetica** remains a separate, completed, read-only reference repository with zero coupling. If any ecosystem file imports it, the boundary has been crossed and must be reverted.

## 11.10 Violation detection and enforcement

The Constitution is enforced, not merely stated:

- **Static import checks** enforce the package DAG (Laws 9, 12, 19, 20) and the no-import-of-research rule (Law 4).
- **A boundary test** verifies Noetica's self-tests use only the reference/fake verifier (Law 20).
- **An experiment-integrity test** verifies the A1/A2 arms share an identical retriever (the only legal difference is the write-filter).
- **A reproducibility test** verifies the content-hash identity discipline.
- **Documentation–code parity** is checked so the record cannot silently diverge from reality (Law 18).
- **A data-contract check** verifies every experience/episode/dataset schema carries a contract version and that changes ship a migration (Law 21).
- **A data-lifecycle check** verifies retention, pruning, and bounded-storage policies are declared and honored (§11.11).
- **A human-ratification gate** blocks any constitutional, architectural, or platform-level change from merging without recorded project-owner approval (Laws 22, 23).
- **The AI-review checklist** (Part XIII) is run on every change, by the automated reviewer, before merge.

A detected violation blocks the change: an AI reviewer **may reject** it and name the violated law and the conforming (preferably evolutionary) alternative. But an AI reviewer **may never ratify** a constitutional, architectural, or platform-level change — that requires explicit human approval by the project owner (Law 22). The automated reviewer's role is to *catch* violations, never to *authorize* changes to the architecture.

## 11.11 Data lifecycle governance (bounded experience over a decade)

The ecosystem runs for a decade and generates grounded experience continuously (Part IV). Without governance, the experience store grows without bound and eventually becomes unusable — the opposite of compounding. The Constitution therefore mandates a **data lifecycle** for all experience, owned by Noetica as a *framework* (a mechanism) and *configured* by the domains that produce the data. Forgetting is a first-class mechanism (Part V §5.3), and this section is its governance expression.

**Mandatory lifecycle stages.** Every experience store must declare, and honor, an explicit policy for:

- **Compression** — grounded episodes are compacted (e.g., deduplicated, delta-encoded) once past an active window, preserving reproducible identity (content hash) and provenance.
- **Summarization** — streams of episodes are distilled into higher-order competence (skills, concepts, calibrated models) and aggregate statistics, so value is retained without retaining every raw record forever.
- **Archival** — cold data moves to lower-cost storage under a declared schedule, remaining retrievable but out of the hot path.
- **Pruning** — stale, superseded, or low-value episodes (including flaky-flagged and superseded-schema records) are removed under a principled rule, never silently and never in a way that erases provenance of *decisions* already made.
- **Retention** — every class of experience has a declared retention period and a declared minimum (what must never be deleted, e.g., ratification-relevant provenance).
- **Bounded storage** — each store has a declared size/growth bound; exceeding it triggers compression/archival/pruning, never uncontrolled growth.

**Ownership and rules.**
- **Noetica owns the lifecycle framework** (the mechanism of compression/summarization/archival/pruning/retention and the bound enforcement); **domains configure it** with domain-appropriate policies (see the matrix row in §9.2).
- **Provenance survives pruning.** Pruning may remove raw episodes but must never destroy the provenance needed to explain a decision the system already made or a result already ratified (Law 18).
- **Lifecycle changes are contract-versioned.** Because lifecycle operates on the data contracts of Law 21, a change to what is compressed, summarized, or pruned is a versioned, migrated change — not an ad-hoc script.
- **Bounded storage is enforced** as a declared policy checked at review (§11.10). Unbounded accumulation is a constitutional violation.

---

# PART XII — IMPLEMENTATION WORKFLOW

No feature is implemented until it has passed this workflow. The workflow operationalizes Law 11 ("Constitution-check before implementation"). It applies to every module, API, refactor, milestone, and pull request — authored by a human or an AI.

## The Decision Protocol (the gate every change passes)

Before any roadmap, module, implementation, refactor, milestone, or repository change, answer all five. Proceed **only if all answers are consistent** with the Handbook.

1. **Which layer owns this?** (Locate it in the Responsibility Matrix, Part IX.)
2. **Does it violate ownership?** (Is it a mechanism being put in a domain, or content being put in the platform?)
3. **Does it respect the dependency DAG?** (No upward, cyclic, or sibling import; experience moves as data, not code.)
4. **Is it mechanism or content?** (Mechanism → Noetica; content → the domain.)
5. **Should it be promoted from research or extracted from Velith?** (Does it need the promotion gate or the extraction test, or neither?)

## The eight steps

**Step 1 — Read the Constitution.** Locate the capability in the matrix and the relevant laws. If the capability is not in the matrix, stop: it must be added by amendment (Part XI) before it can be built. *Output: the owning layer and the laws in play.*

**Step 2 — Determine the owner.** Confirm exactly one owner. If it appears to need two, split it along the mechanism/content line until it has one. *Output: a single owning layer, and — if it is a mechanism used by a domain — the interface it belongs behind.*

**Step 3 — Validate the dependency.** Check every dependency the change introduces against the DAG: is any import upward, cyclic, or sibling-to-sibling? Is any experience being moved as code instead of data? *Output: a dependency list that is a strict DAG, or a rejection.*

**Step 4 — Validate the boundary.** Confirm the change puts mechanism in Noetica and content in the domain; that any verifier is an oracle implementing Noetica's protocol, not a core addition; that provenance/observability are included; that no known anti-pattern (LLM-as-judge, free-oracle, homunculus) is present. *Output: a boundary-clean design, or a rejection with the conforming alternative.*

**Step 5 — Implement.** Build the change, smallest viable increment first, each milestone a hardening of the last (not a rewrite). Provenance and observability are present from the first commit. Consume Noetica interfaces; never re-implement a mechanism. Wrap external kernels; never rebuild them. *Output: a boundary-respecting, tested increment.*

**Step 6 — Review.** Run the architecture review (Part XI) and the checklists (Part XIII), including the automated import/boundary/experiment-integrity/reproducibility/parity/data-contract/data-lifecycle checks. A violation blocks the merge, and an AI reviewer may reject it — but an AI reviewer may never ratify. **If the change is constitutional, architectural, or platform-level, it additionally requires a ratified CAP (§11.6) and explicit human approval by the project owner** (Laws 22, 23). *Output: a pass, or a named violation and its fix; for architectural changes, a ratified CAP.*

**Step 7 — Promotion / extraction (if applicable).** If the change created a mechanism that belongs in the platform, run the promotion gate (research origin) or the extraction test (Velith origin), register it in the Primitive Registry, and record the decision. If not applicable, skip. *Output: a registry entry and decision record, or nothing.*

**Step 8 — Documentation.** Update the affected records so documentation does not diverge from code (Law 18): the decision ledger, the Primitive Registry, interface versions/migration notes, and the project-state record. *Output: records consistent with the code as merged.*

## 12.1 What a contributor may never skip

The Decision Protocol (Steps 1–4) is never skipped, even under deadline. A change that "just needs to ship" is exactly the change most likely to breach a boundary. If the protocol cannot be satisfied, the correct action is to *amend the Constitution first* or to *not build the thing*, never to build it in violation.

---

# PART XIII — CHECKLISTS

These checklists make the Constitution operational at every gate. Each item is phrased so that a "no" is a stop. They are run by contributors and by the automated AI reviewer.

## 13.1 Architecture checklist (new module or subsystem)

- [ ] The capability appears in the Responsibility Matrix (Part IX); if not, an amendment was filed first.
- [ ] Exactly one owner; if it seemed to need two, it was split along the mechanism/content line.
- [ ] Mechanism lives in Noetica; content lives in the domain.
- [ ] If it is a mechanism used by a domain, it is exposed behind a versioned, typed interface.
- [ ] If it is a verifier, it is an oracle implementing Noetica's protocol — not a core addition.
- [ ] No known anti-pattern (LLM-as-judge, verification-as-free-oracle, homunculus, bag-of-agents).
- [ ] Provenance and observability are designed in from the first commit.
- [ ] The state substrate is the core; this module is a transformation over shared state, not a control-flow island.
- [ ] It does not duplicate an existing abstraction (Memory/Knowledge/Context kept distinct).

## 13.2 Pull-request checklist

- [ ] The Decision Protocol (five questions) is answered in the PR description.
- [ ] No upward, cyclic, or sibling import; experience moves as data, not code.
- [ ] No re-implementation of a Noetica mechanism inside a domain.
- [ ] No domain content added to Noetica; no domain oracle in the core.
- [ ] External kernels are wrapped behind an interface, not rebuilt.
- [ ] Provenance fields and observability are present and correct.
- [ ] Interface changes are semantically versioned with a migration note.
- [ ] Experience/episode/dataset schema changes carry a data-contract version and migration (Law 21).
- [ ] Any change to compression/summarization/pruning/retention respects the declared data lifecycle and bounded-storage policy (§11.11).
- [ ] Documentation/records updated so they do not diverge from the code (Law 18).
- [ ] If the change is constitutional, architectural, or platform-level: a ratified CAP and explicit project-owner approval are attached (Laws 22, 23).
- [ ] Relevant automated checks pass (import DAG, boundary, experiment-integrity, reproducibility, parity, data-contract, data-lifecycle).

## 13.3 Code-review checklist

- [ ] The change is boundary-clean per Parts IX–X (reviewer names any violated law).
- [ ] The change is evolutionary, not a gratuitous rewrite of a working, boundary-respecting subsystem.
- [ ] Grounding is honest: no approximate verifier treated as exact; no free-oracle assumption.
- [ ] No self-improvement path can reach the verifier or the oversight boundary (Law 17).
- [ ] Verdicts respect the closed taxonomy; measurement-quality signals are provenance, not verdict states.
- [ ] Tests exist and, for Noetica, use only the reference/fake verifier (Law 20).
- [ ] The reviewer offered the conforming alternative for any rejection.

## 13.4 Repository checklist

- [ ] The package-level DAG is enforced in CI; a violating import fails the build.
- [ ] MiniFlyWire is separate; nothing imports it; MiniNoetica is read-only with zero coupling.
- [ ] Packaging is consolidated by default; a split is justified by independent release cadence or team.
- [ ] A fresh clone goes green with one documented command in the ratified environment.
- [ ] CI is hermetic; live-model paths are documented acceptance steps, not gates.
- [ ] Capability-gated tests run-with-capability or skip-with-reason — never silently pass.
- [ ] External infrastructure (cloud/K8s/GPU/edge/storage/net) sits outside the four layers; Noetica owns the compute interface + budget, domains own adapters (§6.21).
- [ ] Every experience store declares a bounded-storage, retention, and pruning policy; no unbounded accumulation (§11.11).

## 13.5 Research checklist (MiniFlyWire)

- [ ] The mechanism is stated as a falsifiable hypothesis with measurable criteria.
- [ ] The experiment isolates the mechanism as the single manipulated variable (ablation/intervention).
- [ ] Baselines are non-saturating; the experiment is pre-registered and hash-tagged.
- [ ] Held-out data is mechanically locked out of memory; evaluation is on the frozen system.
- [ ] Effect size and seed-spread are reported, not just significance.
- [ ] Rejected/reduced hypotheses are preserved in the record.
- [ ] Promotion is proposed only after the conjunctive gate is fully passed.

## 13.6 Roadmap checklist

- [ ] Every milestone produces a *running system*; none exists solely to produce documentation.
- [ ] Each milestone is a hardening of the prior, not a rewrite.
- [ ] Interfaces are designed early; depth is added on a schedule; only the interfaces the current loop exercises are built.
- [ ] The migration ladder is respected: no rung is attempted before the prior rung is proven.
- [ ] Postponed items are gated on a specific validation result and recorded as postponed.

## 13.7 Milestone checklist

- [ ] The milestone has a ratified specification before implementation.
- [ ] Definition-of-Done is explicit, grounded, and reproducible.
- [ ] The state is captured in the project-state record at the milestone boundary (not improvised mid-implementation).
- [ ] Provenance-complete episodes (where applicable) survive process exit with a verifying hash.
- [ ] Known limitations and deferred work are recorded for the next team.

## 13.8 AI-review checklist (run by the automated reviewer on every change)

- [ ] Which layer owns this? (Answerable from the matrix.)
- [ ] Does it violate ownership, the DAG, or the mechanism/content line?
- [ ] Is it mechanism or content, and is it placed accordingly?
- [ ] Should it be promoted (research) or extracted (Velith), and was the correct gate run?
- [ ] Does it introduce any forbidden import (upward, cyclic, sibling, research, MiniNoetica)?
- [ ] Do experience schema changes carry a data-contract version and migration (Law 21)?
- [ ] Does experience storage respect the bounded-storage, retention, and pruning policy (§11.11)?
- [ ] Does it preserve grounding, provenance, and the immutable oversight boundary?
- [ ] If any answer is inconsistent with the Handbook: **reject, name the law, and state the conforming alternative.**
- [ ] **Authority check (Law 22):** the AI reviewer may reject, but may **not** ratify. A constitutional, architectural, or platform-level change is *escalated for explicit human approval by the project owner* and is invalid until ratified via a CAP (§11.6).

---

# APPENDICES

## Appendix A — Glossary

**AI Manufacturing Intelligence** — the ecosystem's decade-scale outcome (Level 3 success); not a project or repository.
**AI reviewer authority** — an AI may *reject* constitutional/architectural/platform violations but may *never ratify*; explicit human project-owner approval is required (Law 22).
**Belief state** — probabilistic state carrying confidence and epistemic/aleatoric uncertainty; the substrate's evolution target.
**Bounded storage** — a declared size/growth limit on an experience store; exceeding it triggers compression/archival/pruning, never uncontrolled growth (§11.11).
**CAP (Constitution Amendment Proposal)** — the only valid instrument for changing the Constitution; carries the twelve mandatory fields (§11.6) and requires explicit project-owner ratification (Law 23).
**Cognitive primitive** — a falsifiable mechanism of cognition studied by MiniFlyWire (attention, memory, curiosity, reflection, replay, forgetting, confidence, planning, learning).
**Cognitive State** — transient working representation of an active episode (one of the three representational domains).
**Compounding** — the measurable rise in grounded competence per unit compute over a stream of grounded episodes; the program's central test.
**Content** — *what* is remembered/planned/verified/reasoned about; owned by domain layers.
**Content hash** — a digest over the reproducible identity of an episode (task, patch, environment), excluding non-reproducible provenance.
**Data contract** — a versioned schema governing the Experience Flow (episode/dataset/derived-question); changes require versioning and migration, held to the same rigor as downward code interfaces (Law 21).
**Data lifecycle** — the mandated compression, summarization, archival, pruning, retention, and bounded-storage governance for experience (§11.11).
**Determinism levels** — graded reproducibility (same verdict ⊂ same hash ⊂ same output ⊂ same environment).
**Digital-twin engine vs. content** — state-sync mechanism (Noetica) vs. factory/product world-model (Mini Prometheus).
**Episode** — a provenance-complete, content-hashed record of one grounded attempt; first-class learning data.
**Extraction** — moving a proven mechanism up from a domain into Noetica behind an interface (Law 8).
**Grounding** — establishing truth by external verifier, not by model fluency.
**Held-out lock** — mechanically enforced exclusion of evaluation data from any memory.
**Homunculus** — a forbidden central mind that does the real thinking while everything serves it.
**Infrastructure (external)** — cloud, Kubernetes, GPUs, edge, storage, networking; execution substrate *outside the four layers*. Noetica owns the compute interface + budget; domains own adapters; infrastructure owns execution (§6.21). Not a fifth project.
**Interface / Implementation** — Noetica publishes typed interfaces; domains provide concrete implementations.
**Mechanism** — *how* something is done, domain-independent; owned by Noetica.
**Migration ladder** — SWE → PCB → HDL → mechanical/FEA → manufacturing; widening the verification model-gap deliberately.
**MiniNoetica** — a separate, completed, read-only education reference project; not a dependency; not a layer.
**Model-gap** — the divergence between an approximate verifier and true correctness; zero for SWE, positive for physical domains.
**Promotion** — moving a validated primitive from MiniFlyWire into Noetica by re-implementation (Law 7).
**Provenance** — the derivation record of every belief; first-class and non-negotiable.
**Reality / Structured Generative World Model** — the external world / persistent learned knowledge (the other two representational domains).
**State substrate** — the persistent, typed, provenance-tracked shared representation; the platform's true core.
**Verifier / oracle / protocol** — the concrete check (domain) implementing Noetica's verification protocol (platform).
**Verdict** — the closed-taxonomy grounded outcome of verification; may be a distribution with calibrated uncertainty.

## Appendix B — Prior-document map (where the corpus is absorbed)

| Prior document | Role in the corpus | Absorbed into |
|---|---|---|
| *Architecture Constitution v1.0* (PDF) | Ratified four-layer model, 3 flows, 11 laws | Parts I, IV, X (canonical, frozen) |
| Project instructions / charter | Freezes the four projects; amendment-only change | Preamble, Part XI |
| `VISION.md` (PrometheusLite/Noetica) | Purpose, principles, non-goals, success levels, falsifiable commitment | Parts I, §1.7; naming via N.2 |
| `DECISIONS.md` (D1–D21, "Velith") | Ratified engineering decisions | Parts II, VII, XI; naming via N.2/N.3 |
| `PROJECT_STATE.md` (Velith M0/M1) | Verified milestone state; the propose→verify→log loop | Parts VII §7.5, N.3 |
| `research_problem.md`, `00_research_vision*`, `00_project_definition.md` | MiniFlyWire's scientific frame | Part V, §1.6 |
| `ontology.md`, `01_cognitive_ontology.md` | Computational objects and operators | §1.6, Part V |
| `computational_theory.md` | Three domains, five functions, five laws, activation | §1.6, Part V |
| `00_research_axioms.md` | Candidate axioms and evaluation framework | Part V (research method) |
| `10_research_notebook.md` | Working/rejected hypotheses (H1–H31, R1–R7) | Parts V, VII §7.2; Appendix D |
| `NOTES.md` | Capability-gating / verifier isolation practice | Part XIII repo/milestone checklists |
| `Gemini_Review.txt`, `ARCHITECTURE_DECISION.md` | External challenge + first-principles review | Absorbed as the probabilistic-substrate, experience-flow, Sim2Real, and mechanism/content resolutions throughout |
| `RESEARCH.md`, `ROADMAP.md` | Empty placeholders | To be written under this Handbook; slots noted in Part XI/XII |

## Appendix C — Templates

**CAP — Constitution Amendment Proposal template** *(the only valid instrument for architectural change; Law 23, §11.6)*
```
CAP-<n> — <title>
Supersedes: <law / matrix row / decision / vision statement>
1.  Problem Statement: <what is wrong or newly required>
2.  Why the Constitution is insufficient: <why current text cannot accommodate it>
3.  Alternatives Considered: <including the evolutionary, no-amendment option>
4.  Impact on MiniFlyWire: <...>
5.  Impact on Noetica: <...>
6.  Impact on Velith: <...>
7.  Impact on Mini Prometheus: <...>
8.  Dependency impact: <Code Flow DAG, Experience Flow contracts, interfaces>
9.  Migration strategy: <code, data contracts, records>
10. Backward compatibility: <preserved / deprecated + deprecation window>
11. Independent architecture review: <reviewer + outcome>
12. Explicit ratification by the project owner: <name + date> (AI may recommend, never ratify)
Recording: <DECISIONS.md entry ID; Handbook version bump; Appendix E log line>
```

**ADR (decision) template**
```
D<n> — <title>
Status: Accepted | Superseded | Postponed
Decision: <what was decided, flatly>
Rationale: <why>
Alternatives rejected: <what was considered and not chosen>
Consequences: <what this commits or forecloses>
```

**Promotion / extraction request template**
```
PR-<n> — <mechanism name>
Origin: MiniFlyWire (promotion) | Velith (extraction)
Gate evidence: <promotion gate results OR real consumer + credible second>
Mechanism vs content: <argument that this is a mechanism>
Interface: <the versioned interface it will be exposed as>
Registry entry: <name, version, status>
```

## Appendix D — Open research questions (parked, gated on validation)

These are recorded so the ecosystem knows what it has *not* yet decided. Each is gated on a specific result and must not be built before its gate (Law 8, §11.8).

- **Extended vs. internal cognition (α vs. β).** Should cognition be internal-only, or extended over external artifacts (CAD, twins, blueprints)? External artifacts currently belong to **Reality**; a new ontology object requires falsification first.
- **Cognitive Workspace / Task Model.** Are these primitives, or scoped views of the Cognitive State? Current finding: likely reducible to scoped Cognitive State — *capability, not timescale*, is the criterion for a new primitive.
- **Representation Transformation as the universal principle.** Is "Abstraction → Realization" merely the engineering specialization of a deeper invariant (perception runs concrete → abstract)? Under active falsification.
- **Probabilistic substrate depth.** How much belief-state machinery does the substrate need before the first approximate (PCB/FEA) rung? Gated on reaching that rung.
- **Experience-aggregation mechanism.** The concrete form of the upward experience loop in Noetica — gated on a real second consumer (extraction discipline).
- **Learned meta-control.** When does the budget/meta-control policy move from hand-tuned to learned? Gated on the compounding result.
- **Free-energy framework.** Retained as decade-scale theory and conceptual filter only; forbidden from constraining any near-term mechanism until a running spike justifies it.

## Appendix E — Amendment history

Every change to this Handbook is recorded here (Law 23, §11.6). Superseded text is never erased silently; the record preserves *why* the Constitution is shaped as it is.

**Handbook v1.0 — RATIFIED.** Initial Constitution: Preamble, canonical naming reconciliation (N), Parts I–XIII, Laws 1–20, Appendices A–D.

**Handbook v1.1 — RATIFIED (final review stage).** Integrated five approved constitutional amendments after independent review by Gemini and ChatGPT. No architecture, project boundary, or existing numbering was redesigned; all additions are appends and cross-references.

| # | Amendment | Instrument | Primary locations |
|---|---|---|---|
| 1 | **Data Contract Law** — the Experience Flow uses versioned data contracts; schema changes require versioning + migration; upward contracts held to downward-interface rigor. | **Law 21** | §4.3, §4.4, §11.7, §11.10, §9.2, glossary, checklists 13.2/13.8 |
| 2 | **AI Contributor Oversight** — AI reviewers may reject but are never final authority; constitutional/architectural/platform changes require explicit human approval. | **Law 22** | §11.1, §11.10, §12 Step 6, glossary, checklists 13.2/13.8 |
| 3 | **Infrastructure Ownership** — infrastructure is external to the architecture; Noetica owns the compute interface + budget, domains own adapters, infrastructure owns execution; no fifth project. | **§6.21** + matrix | §6.21, §9.2 (matrix rows + note), glossary, checklist 13.4 |
| 4 | **Data Lifecycle Governance** — constitutional rules for compression, summarization, archival, pruning, retention, and bounded storage; no unbounded accumulation. | **§11.11** | §11.11, §11.10, §9.2, glossary, checklists 13.2/13.4/13.8 |
| 5 | **Architectural Stability** — the Constitution is presumed correct; only a ratified CAP may change it; CAP mandatory fields + independent review + project-owner ratification. | **Law 23** + CAP | §10 (Law 23), §11.6, Appendix C (CAP template), glossary |

---

*End of Handbook v1.1. This document governs the ecosystem. It is amended only by the CAP procedure in Part XI (Law 23), ratified by the project owner (Law 22), and never changed silently.*








