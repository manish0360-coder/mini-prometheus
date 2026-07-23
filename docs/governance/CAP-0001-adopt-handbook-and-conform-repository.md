# CAP-0001 — Adopt HANDBOOK_v1.1 as governing Constitution and conform the repository

- **Instrument:** Constitution Amendment Proposal (Handbook §11.6, Law 23). The only valid instrument for an architectural change.
- **Status:** **RATIFIED by the project owner (Mack), 2026-07-23.** Authorization: "you have full permission to make the repository match the constitutional evolution it reconstructed." Per Law 22 this human ratification is what makes the change valid; this document records it.
- **Author:** Chief Systems Engineer (AI contributor — proposes and executes; does not ratify).
- **Evidence base:** `docs/governance/constitutional-evolution-report.md` (the archaeology), backed by primary sources: `Velith/docs/VISION.md`, `Velith/docs/DECISIONS.md` (D1–D25), `ARCHITECTURE_DECISION.md`, `HANDBOOK_v1.1.md`.
- **Supersedes hypotheses in:** the pre-archaeology draft of this CAP and `docs/architecture/constitution-source-audit.md` §5 (proposal). Those were written before the repository history was reconstructed; every claim below is now evidence-backed, not assumed.
- **Affects:** `constitution/`, `src/mini_prometheus/`, `integrations/`, ADR-0001, ADR-0003, RM1 scope.
- **Does the Handbook text change?** No. This CAP ratifies the Handbook as governing and conforms our repository to it.

---

## Field 1 — Problem Statement

The `mini-prometheus` repository declared ownership that contradicts the project's own governing documents. Its README lists MP as owning *"Engineering cognition · Situation State · Engineering World Model · Constraint Network · … Engineering reasoning"* and integrating **all three** upstreams, including a `src/mini_prometheus/integrations/miniflywire/` adapter.

The Constitutional Evolution Report (Part 5, Conflict **C1**) establishes by evidence that this is the **single genuine conflict** in the corpus, and that the repository — not the Handbook — is the outlier. It is contradicted **simultaneously** by every governing document:

- **VISION.md §5.2** — the persistent, provenance-tracked state representation is *the substrate*, a platform property, not a manufacturing-layer possession.
- **DECISIONS.md D9** — "state-centric architecture… a persistent, typed, provenance-tracked representation of the artifact is the substrate; generators, verifiers, planners, and learners are typed transformations over that shared state." The substrate is the system core, not a Layer-4 object.
- **DECISIONS.md D11** — research/education cognitive code (MiniNoetica / MiniFlyWire class) is "a completed reference… not a dependency… If a Velith file ever imports from MiniNoetica, that is the signal the boundary has been crossed." A MiniFlyWire *adapter* is exactly that crossing.
- **ARCHITECTURE_DECISION.md STEP 5–6** — responsibility matrix assigns the state substrate, `WorldModel`, provenance, reasoning/planning *form* to Noetica; engineering *content* to Velith; manufacturing content to Mini Prometheus. STEP 6 rule 4: "MiniFlyWire is imported by no one."
- **HANDBOOK_v1.1** §1.10, §2.4 and **Laws 3, 4, 6, 9** — mechanism (Noetica) ≠ content (domain); MiniFlyWire never imported; domains never re-implement Noetica; strict acyclic DAG.

## Field 2 — Why the Constitution is insufficient (i.e., why a CAP is required)

The Constitution is **not** insufficient. The Constitutional Evolution Report (Part 2) proves — from the documents' own supersession clauses, a dated naming lineage, verbatim principle-continuity, and independent corroboration — that VISION → DECISIONS → boundary-review → Handbook form **one internally consistent, self-superseding lineage**, and that the Handbook governs *on the evidence*, not by its self-declared supremacy (P.2).

The defect is that our **repository artifacts diverged** from that lineage, having been written from a pre-Handbook charter summary. Law 23 requires that correcting our own frozen repository architecture — and formally ratifying which document governs — pass through a CAP. Hence this instrument. The charter summary's terms are reconciled, not discarded, via the Handbook's **N.2/N.3** ruling and the primary **DECISIONS.md naming lineage**: *"working names PrometheusLite / Mini Prometheus (program) and Noetica (system)… the ratified flagship name is Velith. Where earlier internal documents use the older names, they refer to this same project."*

## Field 3 — Alternatives Considered

1. **(Ratified) Conform the repository to the Handbook via mechanism/content re-reading.** Evolution report Part 5 verdict **(3) Repository ownership correction required**. Evolutionary: preserves all repository machinery, corrects only the `src/` charter, `integrations/`, and RM1 scope.
2. **Keep the charter-summary ownership.** Rejected on evidence: contradicted by four independent governing documents at once (Field 1); it is the outlier (report Part 2/Part 5 C1).
3. **Terminology reconciliation only** (evolution report outcome 2). Rejected as **insufficient**: "MP owns Engineering cognition/reasoning" and the MiniFlyWire adapter are real ownership/DAG violations (Laws 4/6/9), not naming (report Part 5).
4. **Fundamental redesign** (outcome 4). Rejected because the report proves the prior evolution is **internally consistent** (Part 2); a redesign is warranted only on proven inconsistency, which does not exist. The machinery is already Handbook-aligned (Laws 8, 11, 14).

## Field 4 — Impact on MiniFlyWire

None to MiniFlyWire itself (research lab, R1; JavaScript brain-inspired architecture — evolution report Part 1 Phase 0). Repository effect: **remove `src/mini_prometheus/integrations/miniflywire/`**. Evidence: Law 4, ARCHITECTURE_DECISION STEP 6 rule 4, DECISIONS D11. Transfer from research is by re-implementation, never import (Law 7; report Part 4 "two arrow types").

## Field 5 — Impact on Noetica

None to Noetica's ownership. This CAP **confirms** MP *consumes* Noetica mechanisms — state substrate, provenance, `WorldModel`, twin/state-sync engine — through versioned interfaces (Law 14), never re-implements them (Law 6; DECISIONS D9). Evolution report Part 3 ("platform mechanisms — consumed, never owned"). Prerequisite: Noetica available as a pinned package (Field 8).

## Field 6 — Impact on Velith

None to Velith's ownership. This CAP **confirms** MP consumes Velith's engineering API (`EngineeringTask`/`EngineeringResult`, ARCHITECTURE_DECISION STEP 7) as its engineering entry point and must **not bypass Velith** for engineering (Law 9; DECISIONS D5 migration ladder places manufacturing above the engineering loop). Engineering world-model and reasoning *content* are Velith's (report Part 3). Prerequisite: Velith available as a pinned package (Field 8) — note Velith is at M0–M1 (`m0-complete` 2026-06-21), so a consumable release is a real gate.

## Field 7 — Impact on Mini Prometheus

Substantive, localized to charter/scope — not machinery. Reconciled ownership (evolution report Part 3 + Part 5; Handbook §2.4; DECISIONS naming lineage):

| Charter-summary term | Reconciled reading (evidence) | Repository change |
|---|---|---|
| MP "Situation State" | Manufacturing situation/twin **content** on Noetica's State Substrate (Handbook §1.10; D9). No canonical object by this name (report Part 5). | `situation_state/` → `manufacturing_state/` (content) |
| MP "Engineering World Model" | Manufacturing digital-twin **content** (Handbook §2.4/§8.4), on Noetica's twin engine; engineering model is Velith's. | `world_model/` → `manufacturing_twin/` (content) |
| MP "Constraint Network" | Manufacturing **constraint content** in Noetica's knowledge store (Handbook §6.5). No canonical object (report Part 5). | `constraint_network/` → `manufacturing_constraints/` (content) |
| MP "Engineering cognition / reasoning" | **Consumed** from Velith (report Part 3); MP owns manufacturing planning/scheduling. | removed from README ownership list |
| `integrations/{miniflywire,noetica,velith}` | Velith (engineering entry) + Noetica (platform mechanisms) only. | drop `miniflywire/` |

What MP legitimately owns (Handbook §2.4; report Part 3 "manufacturing content"): manufacturing planning & scheduling ("its heart"), factory/robotics/supply-chain/MES adapters, manufacturing digital-twin content, Sim2Real divergence tracking, experience collection.

**RM1 re-scope (consequence):** RM1's "Situation State substrate" target is **withdrawn** (it would re-implement a Noetica mechanism — Laws 3/6). The corrected first milestone is the smallest slice of **MP-owned manufacturing content** over consumed Velith→Noetica interfaces (leading candidate: a manufacturing planning/scheduling seed, or manufacturing twin-state content). `specs/interfaces/situation-state.md` is superseded.

## Field 8 — Dependency impact (Code Flow DAG, Experience Flow, interfaces)

- **DAG reaffirmed** (identical across DECISIONS, ARCHITECTURE_DECISION STEP 6, Handbook Law 9; report "Dependency map"): `MiniPrometheus → Velith → Noetica`, one direction. MiniFlyWire imported by no one (Law 4). No sibling imports (Law 19). Cross-layer only via versioned typed interfaces (Law 14). Experience flows up as **data, not code** (Law 12/21).
- **Repository:** `pyproject.toml` pins **Velith** and **Noetica** (not MiniFlyWire). `integrations/` reduces to `velith/` + `noetica/`.
- **Hard prerequisite (unchanged, evidence-confirmed):** MP consumes what must exist as packages. Velith is at M0–M1; **confirm Velith and Noetica publish pinned, consumable packages** before RM1 leaves Specification.

## Field 9 — Migration strategy (executed under this ratification)

Sequenced; executed in this turn under the owner's authorization and recorded in **ADR-0004**:

1. **Ratify** the Handbook as governing (done — this document, owner-authorized).
2. **Transcribe** the Handbook verbatim into `constitution/` (`HANDBOOK_v1.1.md` + `ARCHITECTURE_DECISION.md` as authoritative sources; the seven topic files rewritten as cited extractions); set `constitution/VERSION` = **1.1.0**.
3. **Correct** `src/mini_prometheus/` package charter (renames per Field 7) and reduce `integrations/` to `velith/` + `noetica/`. No runtime logic exists (packages are placeholders), so this is charter correction, not a code rewrite.
4. **Supersede** ADR-0001's `src/` charter and ADR-0003's RM1 scope via **ADR-0004** (append-only; originals preserved — §11.6). Withdraw `specs/interfaces/situation-state.md`.
5. **Correct ownership docs:** README ownership list, CODEOWNERS, `repository-architecture.md` ownership/traceability.
6. **Record** in the decision ledger and CHANGELOG, superseding prior entries without deleting them (§11.7).

## Field 10 — Backward compatibility

- **Preserved:** all repository machinery (contract spine, five-layer hierarchy, contract/constitution versioning, ADR/CAP governance, CI gate, no-speculative-folders). ADR-0001's structural decisions stand except the `src/` package charter and the MiniFlyWire adapter.
- **Withdrawn:** the object names *Situation State / World Model / Constraint Network* as MP-owned implementations; the `integrations/miniflywire/` adapter; RM1's substrate framing; `specs/interfaces/situation-state.md`.
- **No code deprecation window needed** — no runtime code exists (RM1 stopped at Specification). Cheapest possible moment to correct.

## Field 11 — Independent architecture review

**Satisfied by** `docs/governance/constitutional-evolution-report.md` — an independent reconstruction from primary repository sources (five repositories, VISION, DECISIONS D1–D25, the boundary review, the Handbook), reaching verdict **(3) Repository ownership correction required** with per-claim evidence. It corroborates, rather than assumes, the mechanism/content boundary (report Part 2 §"convergent evidence"). Note: the Handbook itself (§11.6 field 11) contemplates external model reviews; a further external review may be attached but is not required for this conformance correction, which contradicts no governing document.

## Field 12 — Explicit ratification by the project owner

**Granted.** Project owner Mack authorized execution on 2026-07-23 ("full permission to make the repository match the constitutional evolution it reconstructed"). Per Laws 22/23 this human ratification is the sole source of validity; the AI author proposed and executed, and did not ratify. Recorded in ADR-0004 and CHANGELOG.

---

*Ratified CAP under Handbook §11.6. Changes no frozen Handbook text; conforms the repository to it on the evidence of the Constitutional Evolution Report. The project owner ruled (Laws 22, 23).*
