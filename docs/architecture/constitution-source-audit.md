# Constitution Source Audit — RM1 theory-existence check & reconciliation findings

- **Status:** Findings for project-owner ruling. **AI-authored analysis — recommendation only, not a ratification** (Handbook Law 22).
- **Trigger:** RM1 (Situation State) treated `constitution/` placeholders as a blocker. Owner asked whether the theory is *missing* or merely *un-transcribed*.
- **Sources audited:** `HANDBOOK_v1.1.md` ("THE ENGINEERING CONSTITUTION AND ARCHITECTURE HANDBOOK") and `ARCHITECTURE_DECISION.md` (ratified boundary review), both uploaded 2026-07-23.
- **Bottom line:** The theory **exists and is frozen** — RM1 is **not** blocked by missing theory. But the audit uncovered a **genuine constitutional conflict**: the objects RM1 targets (Situation State, Constraint Network) and several ownership claims in our repository architecture do **not** match the frozen Constitution. This is a Part XI / CAP matter requiring owner ratification (Laws 22, 23) **before** RM1 proceeds to the Contract stage.

---

## 1. What the frozen sources actually are

`HANDBOOK_v1.1.md` is not a supporting doc — it **is the Constitution**. Its Preamble (P.1) states it is "the single source of truth for the shape of the system," and P.2 places it at the **top of the authority hierarchy**, above the Decision Record, Vision, and all roadmaps, code, and configurations. Law 23 (Architectural Stability) makes it presumed-correct and changeable only by a ratified Constitution Amendment Proposal (CAP).

**Consequence:** where our project charter / earlier "Mini Prometheus Constitution" summary and this Handbook disagree, the Handbook governs by its own terms (P.2, P.4, Law 23). The disagreement is not mine to resolve — it is a defect routed to governance (P.4, Law 22).

## 2. Per-required-file determination

| Required `constitution/` file | Exists in frozen theory? | Authoritative source | Transcription sufficient, or theory missing? |
|---|---|---|---|
| `ontology.md` | **Yes** | Handbook N.1 (canonical taxonomy, frozen), §1.10 (core definitions), §1.11 (ten principles), Appendix A (glossary) | **Transcription sufficient.** The frozen vocabulary — the three representational domains (Cognitive State; Reality / Structured Generative World Model; State Substrate), Mechanism/Content, Interface/Implementation, Provenance, Episode, Verdict — is fully specified. |
| `runtime-architecture.md` | **Yes** | Handbook Part III (9-step ecosystem loop), Part IV (three flows + invariant), Part VI (Noetica runtime, substrate, lifecycle), Part X (23 Laws); `ARCHITECTURE_DECISION.md` STEP 6 (dependency rules) | **Transcription sufficient.** Runtime shape, flows, dependency DAG, and laws are all frozen. |
| `computational-objects.md` | **Partially — with a conflict** | Handbook §6.1 State Substrate, §6.2 Provenance, §1.10 Episode/Verdict/WorldModel, §6.5 Knowledge Store, glossary | **Transcription sufficient for the *canonical* objects, but they are not the objects RM1 named.** See §3. The frozen objects are **Noetica** objects; "Situation State" and "Constraint Network" do **not appear anywhere** in the Constitution (0 occurrences). |
| `operators.md` | **Yes (as the five universal functions), not as a per-op signature catalog** | Handbook §7.2 ("engineering introduces **no new fundamental computational operators**"; the five functions: Perception, Inference, Evaluation, Learning, Execution), §6.1 (transformations over substrate), §7.5 (propose→verify→log) | **Transcription sufficient for the operator *set*.** Formal per-operator signatures are Contract-stage interface work (legitimate, not new theory). Note: operators are **universal/Noetica-level**; manufacturing introduces none. |

**Answer to the owner's question:** for every required file the information **already exists** in the frozen Handbook; this is an **extraction/transcription** task, not new research. RM1 is therefore **not blocked by missing theory.**

## 3. Finding A — the RM1 objects are not in the canon

Word-level check against `HANDBOOK_v1.1.md`:

- "Situation State" — **0 occurrences.**
- "Constraint Network" — **0 occurrences.**
- "State Substrate" / "substrate" — present, defined as the platform core.
- "world model" / `WorldModel` — present, as a **Noetica-published interface** (§1.10) whose **engineering content is Velith's** (§7.2) and whose **manufacturing twin content is Mini Prometheus's** (§8.4).

The frozen state-related computational objects are the **three representational domains** (Appendix A): **Cognitive State**, **Reality / Structured Generative World Model**, and the **State Substrate** — all defined at the **Noetica** layer. There is no Mini-Prometheus-owned "Situation State" object and no "Constraint Network" object anywhere in the Constitution. Constraints appear only as **content** (stored in Noetica's Knowledge Store Engine, §6.5; engineering constraints owned by Velith, §7.2).

## 4. Finding B — ownership & dependency conflicts vs. our repository architecture

Our repository architecture (ADR-0001) placed, inside `src/mini_prometheus/`, **owned implementation packages** `situation_state/`, `world_model/`, `constraint_network/`, plus integration adapters to **all three** upstreams. Measured against the frozen Handbook, several of these conflict with immutable Laws:

| Our architecture assumed | Frozen Constitution says | Law breached |
|---|---|---|
| MP **owns/implements** Situation State (a state object) | The **State Substrate is Noetica's** mechanism; domains **use** it, never rebuild it (§6.1, matrix §9.2) | **Law 3** (Mechanism≠Content), **Law 6** (domains never reimplement Noetica) |
| MP **owns** an Engineering World Model implementation | `WorldModel` is a **Noetica interface**; the **engineering** world model is **Velith** content; MP owns only **manufacturing twin content** (§7.2, §8.4) | **Law 2** (one owner), **Law 3** |
| MP owns a "Constraint Network" object | No such object exists; constraints are **content** in Noetica's knowledge store / Velith's ontology (§6.5, §7.2) | **Law 13** (no duplicated/invented abstractions) |
| `integrations/miniflywire/` adapter exists | **MiniFlyWire is imported by no one**; it is a feeder, never a dependency (§Step 6 rule 4, **Law 4**) | **Law 4**, **Law 9** |
| `integrations/noetica/` used directly for engineering concerns | MP imports **Velith** (transitively Noetica); it must **not reach past Velith** for engineering (Step 6 rule 3) | **Law 9** (DAG discipline) |
| MP "owns Engineering cognition / Engineering reasoning" (charter summary) | **Engineering reasoning content is Velith's**; reasoning *form* is Noetica's (§7.2, matrix) | **Law 2**, **Law 3** |

What MP **does** own, per §8.2 and the matrix: **manufacturing planning & scheduling** (its "heart"), **factory/robotics/supply-chain/MES adapters**, **manufacturing digital-twin content**, **Sim2Real divergence tracking**, and **experience collection** — all *consuming* Velith→Noetica through versioned interfaces (Law 14).

**Note on our own architecture's soundness:** the *machinery* (contract spine, five-layer hierarchy, versioned contracts, ADR governance, no-speculative-folders) is fully Handbook-aligned (Laws 14, 8, 11). The defect is localized to the **content of `src/mini_prometheus/` and `integrations/`** and to charter wording — it was derived from the pre-Handbook charter summary, not from `HANDBOOK_v1.1.md`.

## 5. Recommended reconciliation (proposal for owner ratification — not a ratification)

The Handbook's own N.2/N.3 precedent resolves exactly this kind of pre-split renaming by **re-framing under the mechanism/content invariant** rather than discarding. Proposed mapping:

| Charter term (pre-Handbook) | Reconciled reading under `HANDBOOK_v1.1.md` |
|---|---|
| MP "Situation State" | MP's **manufacturing situation/twin *content*** instantiated on **Noetica's State Substrate** interface. Not a re-implemented substrate. |
| MP "Engineering World Model" | The **manufacturing digital-twin *content*** (§8.4), sourced from Velith engineering physics, on Noetica's twin/state-sync engine. Not the Velith engineering model, not the Noetica engine. |
| MP "Constraint Network" | Manufacturing **constraint *content*** in Noetica's Knowledge Store (§6.5). Not a new engine/object. |
| MP "Engineering cognition/reasoning" | **Consumed** from Velith; MP owns **manufacturing** planning/scheduling content. |
| `integrations/` | **Velith only** as the engineering entry point (transitively Noetica). **Remove** the MiniFlyWire adapter (Law 4). Direct-Noetica use limited to platform mechanisms that don't bypass Velith for engineering. |

Under this reading nothing in the frozen theory is missing or contradicted; our repository just needs its `src/` package charter and `integrations/` corrected to match, via a CAP.

## 6. Impact on RM1

If the reconciliation is ratified, **RM1 as currently specified is not the correct first slice.** "Implement Situation State as a state substrate" would breach Laws 3 and 6. The correct first manufacturing slice must:

- **Consume** Noetica's State Substrate + Provenance + `WorldModel` interfaces (available as pinned Velith→Noetica package deps — a hard prerequisite), and
- Implement the smallest piece of **manufacturing content** MP legitimately owns — the leading candidate is the **manufacturing planning/scheduling** seed or the **manufacturing twin state content**, expressed over consumed interfaces.

This also means a prerequisite check: **are Velith and Noetica actually published as consumable pinned packages yet?** If not, RM1 has an external dependency gate independent of the theory question.

## 7. Required governance action

Per Law 22 (AI may reject/flag, never ratify) and Law 23 (no architectural change without a ratified CAP), the next step is a **Constitution Amendment Proposal** (or a project-owner ruling that the charter summary is superseded by `HANDBOOK_v1.1.md`), covering: (a) transcribing the Handbook into `constitution/` with `constitution/VERSION` set from the Handbook (v1.1); (b) correcting the `src/mini_prometheus/` package charter and `integrations/` per §5; (c) re-scoping RM1 per §6. Recorded as an ADR once ratified.

---

## 8. Independent re-verification (2026-07-23, RM1 planning session)

The §2–§4 claims were re-checked **directly against `HANDBOOK_v1.1.md` (1,576 lines)**, not taken from
this audit on trust. All confirmed:

- **Word-level (grep):** "Situation State" **0**, "Constraint Network" **0**, "state substrate" 14,
  "world model" 14 / "worldmodel" 3, "cognitive state" 5. The RM1 object names are absent from the canon.
- **Handbook is the Constitution.** Preamble P.1–P.2 (L64–99): single source of truth, top of the
  authority hierarchy above all roadmaps/code/config. Amended only by ratified CAP — **Law 23** (L1180);
  owner is sole ratifier, **Law 22** (L1178, "AI may reject, never ratify").
- **Canonical taxonomy N.1** (L109–115): Noetica owns *mechanisms and interfaces, never domain content*;
  Mini Prometheus owns *manufacturing content*.
- **Core definitions §1.10** (L240–253): **State substrate = the platform (Noetica) core**; `WorldModel`
  = a **Noetica interface**; digital-twin **engine = Noetica mechanism**, manufacturing twin **content =
  Mini Prometheus**.
- **Cognitive stance §1.6** (L205–209): the **three representational domains** (Reality; Cognitive State;
  Structured Generative World Model) and the **five universal functions** (Perception, Inference,
  Evaluation, Learning, Execution); more specialized capabilities are strategies of these five, not new
  primitives.
- **Mini Prometheus charter §2.4** (L499–567): owns manufacturing planning/scheduling, factory/robotics/
  supply-chain/MES, manufacturing twin **content** on Noetica's engine, and experience collection.
  *Bad example* (L547): building "its own provenance/state-sync engine (that is Noetica's)". *Forbidden
  dependencies* (L541): never import MiniFlyWire, never bypass Velith, never re-implement Noetica.
- **Laws (Part X, L1130–1180)** cited by this audit confirmed verbatim: Laws 2, 3, 4, 5, 6, 9, 13, 14,
  19, 22, 23.

**Verified determination:** Findings A and B are accurate against the source. Theory **exists**
(transcription sufficient for all four required files); RM1 is **not** blocked by missing theory. But the
RM1 target objects and the `src/mini_prometheus/` ownership conflict with the canon — an owner ruling +
CAP is required (Laws 22, 23) before RM1 proceeds to the Contract stage. Note: `constitution/VERSION`
currently reads `1.0.0`; if the Handbook is ratified as the source, it should be set to `1.1.0`.

---

*This document records findings and a recommendation. It changes no frozen content and ratifies nothing. The project owner rules (Laws 22, 23).*
