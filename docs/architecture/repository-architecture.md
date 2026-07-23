# Mini Prometheus — Repository Architecture

**Status:** Adopted (Phase 1)
**Scope:** The architecture of the *repository itself* — not the runtime cognition architecture.
**Authority:** Derived from the frozen Mini Prometheus Constitution. This document does **not** redesign the computational theory or the runtime architecture; it engineers a home for them.
**Owner:** Architecture Board
**Change control:** Amendments require an ADR (see `docs/adr/`). Directories mapped to a *frozen* constitutional clause require constitutional amendment, not a routine ADR.

---

## 1. Purpose and constraints

Mini Prometheus is the **runtime orchestration layer** that integrates three constitutionally frozen, independently released upstreams (MiniFlyWire, Noetica, Velith) and owns the engineering-cognition runtime built on top of them.

This document derives the **permanent repository architecture** under the following hard constraints, taken directly from the request and the Constitution:

1. Scale for many years and many engineers working independently.
2. Cleanly separate: architecture documents, specifications, runtime source, interfaces, tests, datasets, experiments, deployment, tooling, and generated artifacts.
3. **Separate stable contracts from implementation.**
4. Every top-level directory must trace back to a frozen constitutional clause.
5. No speculative folders. Future milestones are *documented here* but **not created** until their milestone opens.
6. Preserve clean repository boundaries: the three upstreams are consumed as **versioned package dependencies**, never vendored as source and never merged into a monorepo.

### Resolved architectural decisions

| Decision | Choice | Consequence for the tree |
|---|---|---|
| Upstream consumption | **Versioned package dependencies** (pinned to frozen releases) | No `vendor/` or submodules. Upstreams appear only in dependency manifests. Our code touches them only through `src/mini_prometheus/integrations/` adapters. |
| Primary runtime | **Python orchestration + Rust/C++ performance core** | Two source roots: `src/` (Python) and `native/` (Rust/C++ crates with Python bindings). A single language-neutral contract layer binds both. |
| Contract representation | **Language-neutral schemas + generated language bindings** | `contracts/` holds the source-of-truth schemas; Python ABCs/Protocols and native bindings are generated/mirrored from them so Python and Rust cannot disagree about a computational object. |

---

## 2. Governing principle: contracts are the spine

The Constitution freezes **Ontology, Computational Objects, Operators, Runtime Architecture, Repository Responsibilities, and the Promotion Workflow**. Everything frozen is *interface-shaped*: it says *what* the objects and operators are, not *how* they are computed.

The repository is therefore organized around one load-bearing separation. In full, the derivation
chain has five layers, each depending only on the layer to its left (formalized in §12):

```
Constitution   →   Specification   →   Contract       →   Implementation    →   Verification
(constitution/)     (specs/)            (contracts/)       (src/, native/)       (tests/, .github/)
frozen theory       human "what"        stable interface   the "how"             proof of compliance
```

- **`constitution/`** holds the frozen theory verbatim. It is read-mostly and amendment-gated.
- **`specs/`** is the human-authored specification: the intended *what*, derived from the frozen theory, before it is frozen into a machine-checkable interface.
- **`contracts/`** is the machine-checkable projection of the frozen Computational Objects, Operators, and Runtime Architecture into versioned interfaces (schemas + generated bindings). It is the *only* thing implementations, tests, and integrations are allowed to depend on across module boundaries. `contracts/` holds only **external architectural contracts** — the surface guaranteed across package and repository boundaries — never internal implementation APIs (see §13).
- **`src/` and `native/`** implement those contracts. They may be rewritten freely as long as they keep satisfying the contracts and their compliance tests. Everything they expose beyond the contract is an **internal implementation API** with no cross-boundary stability guarantee.
- **`tests/` and CI** verify that implementations satisfy the contracts. Verification is a layer, not an afterthought.

This is what makes independent engineering safe: a team owning `constraint_network` can rewrite its internals — even swap the Python reference for a Rust core — without any other team changing a line, because the contract and its compliance suite are unchanged. It is also what makes "prefer extraction over duplication" enforceable: shared behavior lives behind a contract, not copied between modules.

---

## 3. Complete repository tree

Legend: **[P1]** = created in Phase 1. **[Mn]** = future milestone, documented here but **not** created yet (respects "no speculative folders"). **(gen)** = generated, git-ignored.

```
mini-prometheus/
├── README.md                      [P1]  Entry point: what this repo is, how to build, links to constitution & this doc
├── LICENSE                        [P1]
├── CODEOWNERS                     [P1]  Enforces file ownership / independent-team review
├── CONTRIBUTING.md                [P1]  Development workflow + conventions (points here)
├── CHANGELOG.md                   [P1]  Human-facing release history (contracts + runtime)
├── pyproject.toml                 [P1]  Python build, pinned upstream deps, tool config
├── .gitignore                     [P1]  Ignores artifacts/, build outputs, caches
├── .github/                       [P1]  CI/CD as the machine enforcement of the frozen workflow
│   └── workflows/
│       ├── ci.yml                 [P1]  spec-lint → build → test → contract-compliance → verify
│       └── release.yml            [M1]  packaging & publish of runtime + contract versions
│
├── constitution/                  [P1]  FROZEN theory (the inputs). Amendment-gated, not routine edits.
│   ├── README.md                        Explains freeze status & amendment procedure
│   ├── ontology.md                      Frozen Ontology
│   ├── computational-objects.md         Frozen Computational Objects
│   ├── operators.md                     Frozen Operators
│   ├── runtime-architecture.md          Frozen Runtime Architecture
│   ├── repository-responsibilities.md   Frozen Repository Responsibilities matrix
│   ├── promotion-workflow.md            Frozen Promotion Workflow
│   └── responsibility-matrix.md         Frozen ownership boundaries across the 4 repos
│
├── docs/                          [P1]  EVOLVING engineering knowledge (distinct from frozen theory)
│   ├── README.md
│   ├── architecture/
│   │   └── repository-architecture.md   THIS document
│   ├── adr/                             Architecture Decision Records (the change log of design)
│   │   ├── README.md
│   │   └── 0001-adopt-repository-architecture.md
│   └── design/                          Per-subsystem software design docs (workflow step 2)
│       └── README.md
│
├── specs/                         [P1]  SPECIFICATIONS: the versioned "what", between theory and code
│   ├── README.md
│   └── interfaces/                      Formal interface specs for owned objects/operators
│       └── README.md
│
├── contracts/                     [P1]  STABLE CONTRACTS — the interface spine (separated from impl)
│   ├── README.md
│   ├── VERSION                          Contract-suite SemVer (compatibility guarantee)
│   ├── schemas/                         Language-neutral source of truth (JSON Schema / protobuf)
│   │   └── README.md
│   ├── python/                          Generated/mirrored Protocols & ABCs (NO logic)
│   │   └── README.md
│   └── native/                          Generated Rust/C++ trait & header bindings (NO logic)
│       └── README.md
│
├── src/                           [P1]  Python runtime source (implements contracts)
│   └── mini_prometheus/
│       ├── __init__.py
│       ├── situation_state/       [P1]  OWNED: Situation State
│       ├── world_model/           [P1]  OWNED: Engineering World Model (expandable namespace — see §12)
│       ├── constraint_network/    [P1]  OWNED: Constraint Network (Python reference impl; expandable namespace — see §12)
│       ├── orchestration/         [P1]  OWNED: Runtime orchestration (composition root — see §14)
│       ├── integrations/          [P1]  Adapters ONLY — no business logic (see §12/§14)
│       │   ├── miniflywire/             Adapter to MiniFlyWire package
│       │   ├── noetica/                 Adapter to Noetica package
│       │   └── velith/                  Adapter to Velith package
│       ├── cognition/             [M2]  OWNED: Engineering cognition
│       ├── reasoning/             [M2]  OWNED: Engineering reasoning
│       ├── coordination/          [M3]  OWNED: Multi-disciplinary engineering coordination
│       └── workflow/              [M3]  OWNED: AI Manufacturing workflow
│
├── native/                        [P1]  Rust/C++ performance core (constraint-network hot paths, world-model kernels)
│   ├── README.md                        Boundary established P1; accelerated impls land incrementally
│   └── constraint_kernels/        [M2]  First native crate (opens when Python reference is bottleneck-proven)
│
├── tests/                         [P1]  Verification (the frozen workflow's non-skippable gate)
│   ├── README.md
│   ├── contracts/                       Contract-compliance suites (impl-agnostic)
│   ├── unit/                            Per-module unit tests
│   └── integration/                     Cross-module + upstream-adapter tests
│
├── tools/                         [P1]  Repo tooling: codegen (schemas→bindings), linters, dev scripts
│   └── README.md
│
├── deploy/                        [P1]  Deployment: packaging, containers, environment definitions
│   └── README.md
│
├── experiments/                   [M2]  Scientific experimentation harnesses (needs a working runtime first)
├── data/                          [M2]  Versioned datasets & fixtures (DVC/pointer-tracked, not raw blobs)
├── benchmarks/                    [M2]  Performance baselines that justify native acceleration
└── artifacts/                     (gen) Generated outputs: build products, provenance bundles, reports
```

---

## 4. Purpose of every top-level directory (and its constitutional trace)

Every directory below answers three questions: **why it exists**, **which frozen clause it traces to**, and **why it is separate** from its neighbours.

### `constitution/` — the frozen inputs
Holds the frozen theory verbatim: Ontology, Computational Objects, Operators, Runtime Architecture, Repository Responsibilities, Promotion Workflow, Responsibility Matrix. It exists because the Constitution declares these "constitutionally frozen unless a proven contradiction is discovered." Keeping them in-repo but physically segregated makes the freeze *legible and enforceable*: CODEOWNERS routes any change here to the Architecture Board, and CI can diff against it. **Separate from `docs/`** because `docs/` evolves freely and `constitution/` may not.
**Traces to:** *Frozen Constitution* section.

### `docs/` — evolving engineering knowledge
Architecture documents, ADRs, and per-subsystem software design docs. This is where the workflow's **Software Design** step lives and where every non-frozen decision is recorded. ADRs give many-year auditability: future engineers see *why*, not just *what*. **Separate from `constitution/`** (evolving vs frozen) and from `specs/` (prose rationale vs formal interface).
**Traces to:** workflow step *Software Design*; request requirement "architecture documents."

### `specs/` — specifications
The versioned formal "what" that sits between frozen theory and concrete contracts: interface specifications and behavioural specs for the owned objects and operators. This is the workflow's **Specification** step. **Separate from `contracts/`** because a spec is human-authored intent; a contract is the machine-checkable artifact derived from it. Keeping them apart prevents "the spec drifted from the schema" ambiguity — the schema is authoritative, the spec explains it.
**Traces to:** workflow step *Specification*; Operators & Computational Objects.

### `contracts/` — stable contracts (the spine)
The single cross-boundary dependency. Language-neutral `schemas/` are the source of truth for every Computational Object and Operator signature; `python/` and `native/` hold generated bindings with **no logic**. `VERSION` carries a SemVer that is a compatibility promise. This directory is the concrete realization of requirement 3 (*separate stable contracts from implementation*) and of the Constitution's "reusable interfaces over tightly coupled modules" and "preserve architectural contracts." **Separate from `src/`/`native/`** so implementations depend on interfaces, never on each other.
**Traces to:** frozen *Computational Objects*, *Operators*, *Runtime Architecture*; "Every implementation must preserve architectural contracts."

### `src/` — Python runtime source
Implements the objects Mini Prometheus **owns**. Its subpackages are a 1:1 image of the Constitution's ownership list (see traceability matrix §5). `integrations/` is the *only* place that talks to the three upstreams, keeping repository boundaries clean and making an upstream version bump a localized change. **Separate from `native/`** by language/build system; **separate from `contracts/`** by the contracts-vs-impl rule.
**Traces to:** "Mini Prometheus owns: Engineering cognition, Situation State, Engineering World Model, Constraint Network, Runtime orchestration, Engineering reasoning, Multi-disciplinary coordination, AI Manufacturing workflow"; "Mini Prometheus is the runtime orchestration layer. It integrates MiniFlyWire, Noetica, Velith."

### `native/` — Rust/C++ performance core
Home for performance-critical kernels (constraint propagation, world-model updates) exposed to Python via bindings generated from `contracts/`. The boundary is established in Phase 1; individual crates open only when a Python reference implementation is *measured* to be a bottleneck (benchmark-justified, never speculative). **Separate top-level root** because it is a different language and build toolchain, but it realizes the *same* contracts as `src/`.
**Traces to:** frozen *Runtime Architecture* (performance requirements of the Constraint Network / World Model); "production quality."

### `tests/` — verification
The non-negotiable gate. `contracts/` compliance suites validate *any* implementation against the interface; `unit/` and `integration/` cover module internals and upstream adapters. The Constitution says "Never skip verification. Never bypass tests." — this directory plus CI is how that rule is mechanized. **Separate top-level** (not co-located per module) so contract-compliance suites can run against multiple implementations (Python reference vs native) identically.
**Traces to:** workflow steps *Testing* and *Verification*; "Never skip verification."

### `tools/` — repository tooling
Codegen (schemas → language bindings), linters, spec validators, developer scripts. Exists so the contract spine stays automatically consistent and the workflow gates are runnable locally, not just in CI. **Separate from `src/`** because it is developer-facing infrastructure, not runtime cognition.
**Traces to:** "reusable mechanisms," "avoid duplication" (codegen is the mechanism that prevents Python/native contract drift).

### `deploy/` — deployment
Packaging, container definitions, environment specs, release plumbing. Exists because Mini Prometheus is "NOT a research project" — it must ship as a runtime. **Separate from `native`/`src`** so build-and-ship concerns never leak into runtime code.
**Traces to:** Mission ("engineer the frozen theory into a working manufacturing intelligence"); workflow steps *Commit* → runtime delivery.

### Future milestone directories (documented, not created)
`experiments/` (scientific experimentation harnesses), `data/` (versioned datasets/fixtures), `benchmarks/` (performance baselines that *justify* native crates), and `artifacts/` (generated, git-ignored provenance/build outputs). Each is a real constitutional need (scientific experimentation, grounding data, provenance), but creating them before their milestone would violate "do not create speculative folders." They open per §7.
**Trace:** experiments/benchmarks → scientific reasoning & performance; data → grounding/provenance; artifacts → provenance & reproducible evaluation.

---

## 5. Constitutional traceability matrix

Every top-level directory maps to a frozen clause. Nothing exists "for convenience."

| Directory | Frozen constitutional source | Phase |
|---|---|---|
| `constitution/` | Frozen Constitution (Ontology, Objects, Operators, Runtime Arch, Repo Responsibilities, Promotion Workflow) | P1 |
| `docs/` | Engineering Workflow → *Software Design*; long-term maintainability | P1 |
| `specs/` | Engineering Workflow → *Specification*; Operators & Computational Objects | P1 |
| `contracts/` | Computational Objects + Operators + Runtime Architecture; "preserve architectural contracts" | P1 |
| `src/mini_prometheus/situation_state/` | Owns: **Situation State** | P1 |
| `src/mini_prometheus/world_model/` | Owns: **Engineering World Model** | P1 |
| `src/mini_prometheus/constraint_network/` | Owns: **Constraint Network** | P1 |
| `src/mini_prometheus/orchestration/` | Owns: **Runtime orchestration** | P1 |
| `src/mini_prometheus/integrations/` | "integrates MiniFlyWire, Noetica, Velith"; clean repository boundaries | P1 |
| `src/mini_prometheus/cognition/` | Owns: **Engineering cognition** | M2 |
| `src/mini_prometheus/reasoning/` | Owns: **Engineering reasoning** | M2 |
| `src/mini_prometheus/coordination/` | Owns: **Multi-disciplinary engineering coordination** | M3 |
| `src/mini_prometheus/workflow/` | Owns: **AI Manufacturing workflow** | M3 |
| `native/` | Runtime Architecture performance requirements; production quality | P1 (boundary), M2 (crates) |
| `tests/` | Engineering Workflow → *Testing*, *Verification*; "never skip verification" | P1 |
| `tools/` | "reusable mechanisms," "prefer extraction over duplication" | P1 |
| `deploy/` | Mission (ship a working intelligence); *Commit* → delivery | P1 |
| `experiments/` | Scientific reasoning / experimentation (MiniFlyWire integration) | M2 |
| `data/` | Grounding & provenance (Velith); reproducible evaluation | M2 |
| `benchmarks/` | Justification for native acceleration; performance rigor | M2 |
| `artifacts/` | Provenance, reproducible evaluation (generated outputs) | gen |

---

## 6. File ownership

Ownership is enforced by `CODEOWNERS` and mapped to independent teams so engineers can work in parallel without stepping on each other. Review authority scales with blast radius: the closer a change is to the frozen spine, the more senior the required review.

| Path | Owning group | Review rule |
|---|---|---|
| `constitution/**` | **Architecture Board** | Amendment only; requires proven contradiction + board sign-off. Not a routine PR. |
| `contracts/**` | **Architecture Board + Staff Engineers** | Contract change ⇒ SemVer bump + compliance-suite update + 2 senior approvals. Highest scrutiny after `constitution/`. |
| `docs/adr/**` | Architecture Board | New ADR per accepted decision; ADRs are append-only (superseded, never deleted). |
| `docs/**`, `specs/**` | Authoring team + one reviewer | Normal PR. |
| `src/.../situation_state,world_model,constraint_network` | **World-Model team** | Package-scoped; must keep contract-compliance green. |
| `src/.../orchestration`, `src/.../integrations/**` | **Runtime/Platform team** | Owns integration; upstream version bumps land here only. |
| `native/**` | **Core-Performance team** | Must pass the *same* contract-compliance suite as the Python reference. |
| `tests/contracts/**` | Architecture Board + Staff | Compliance suite is part of the contract; changes reviewed with `contracts/`. |
| `tests/unit,integration` | Owning team of the code under test | Co-reviewed with the change. |
| `tools/**`, `deploy/**`, `.github/**` | **Infra/Tooling team** | Normal PR; break-glass reviewed by two. |

Rationale for independence: because cross-module dependencies are only allowed *through* `contracts/`, a team can merge freely inside its package once the compliance suite passes. The only globally-coordinated artifact is the contract suite itself — deliberately small, deliberately high-scrutiny.

---

## 7. Phase 1 vs future milestones

**Phase 1 (now) — establish the spine and the load-bearing substrate.** Governance, the full contract layer, and the runtime substrate the rest depends on:
`constitution/`, `docs/` (+ ADR-0001), `specs/`, `contracts/` (all of it), `src/` substrate (`situation_state`, `world_model`, `constraint_network`, `orchestration`, `integrations`), `native/` boundary, `tests/`, `tools/`, `deploy/`, CI. Contracts for the *future* owned modules are drafted in Phase 1 even where their implementations are not — freeze interfaces early, implement behind them later.

**M2 — cognition & scientific loop.** `src/cognition`, `src/reasoning`, first `native/` crate (benchmark-justified), `experiments/`, `data/`, `benchmarks/`.

**M3 — coordination & manufacturing workflow.** `src/coordination`, `src/workflow`, `release.yml` hardening.

**Rule:** a future directory is created only when its milestone opens and there is real content to place in it. Until then it exists *only* in this document. This is the concrete enforcement of "do not create speculative folders."

---

## 8. Development workflow

The Constitution's workflow is **Specification → Software Design → Implementation → Testing → Verification → Commit → Review**. It maps to git/CI as follows:

1. **Specification** — open/refine a spec in `specs/`; if it touches an interface, update the `contracts/schemas/` source of truth in the *same* change set.
2. **Software Design** — record the approach in `docs/design/`; a decision that changes structure gets an ADR in `docs/adr/`.
3. **Implementation** — one atomic change per PR, scoped to a single owned package under `src/` (or a `native/` crate). Depend only on `contracts/`, never on a sibling package's internals.
4. **Testing** — add/extend `tests/unit`; if behaviour is contract-visible, extend `tests/contracts`.
5. **Verification** — CI runs `ci.yml`: spec-lint → build (Python + native) → unit → **contract-compliance** → integration. This gate is non-skippable; red CI blocks merge.
6. **Commit** — Conventional Commits; the PR references the spec/ADR it satisfies.
7. **Review** — routed by `CODEOWNERS`; scrutiny scales toward the spine (§6).

Branching: short-lived feature branches off protected `main`; linear history (rebase/squash). No direct pushes to `main`. Upstream dependency bumps (MiniFlyWire/Noetica/Velith) are their own isolated PRs owned by Runtime/Platform, touching only `pyproject.toml` and `src/.../integrations/`.

---

## 9. Repository conventions

- **Versioning.** Runtime uses SemVer. `contracts/VERSION` is a *separate* SemVer and is a compatibility contract: a breaking schema change is a MAJOR bump and must ship with an updated compliance suite. The three upstreams are **pinned to exact frozen versions**; no floating ranges.
- **Contracts are generated, not hand-synced.** `contracts/python` and `contracts/native` are produced from `contracts/schemas` by `tools/`. Editing a generated binding by hand is a CI failure. This mechanizes "never duplicate logic."
- **Dependency direction is one-way.** `implementations → contracts`. Never `contracts → implementations`; never `src ↔ src` across packages except through `contracts`. Enforced by an import-linter rule in `tools/`.
- **Layout.** `src/`-layout Python package (`import mini_prometheus`); tests outside the package; native crates self-contained under `native/`.
- **Naming.** Directories and Python modules `snake_case`; native crates `snake_case`; docs `kebab-case.md`; ADRs `NNNN-title.md` (zero-padded, append-only).
- **ADRs.** Every accepted architectural decision is an ADR. ADRs are immutable once accepted; revisiting means a new ADR that supersedes the old.
- **Generated artifacts** never enter git — `artifacts/` and build outputs are git-ignored. Provenance bundles are outputs, not sources.
- **Docstrings/specs are authoritative for behaviour**, tests are authoritative for correctness, contracts are authoritative for shape. If they disagree, that is the "proven contradiction" that may reopen the relevant frozen clause — flagged via ADR, not silently patched.

---

## 10. Recommended first commit

**Intent:** the first commit establishes *governance and the contract spine only* — zero business logic. It makes the repository's constitution, contracts, ownership, and verification gate real before any implementation is written. This is deliberate: contracts and ownership must predate code so that independent teams start from a fixed spine.

Contents:

- Root governance: `README.md`, `LICENSE`, `CODEOWNERS`, `CONTRIBUTING.md`, `CHANGELOG.md`, `.gitignore`, `pyproject.toml`.
- `constitution/` — the seven frozen documents (transcribed from the frozen theory; placeholders until transcription lands, marked FROZEN).
- `docs/` — this `repository-architecture.md` and `adr/0001-adopt-repository-architecture.md`.
- `specs/`, `contracts/` (schemas + binding dirs + `VERSION` = `0.1.0`), and the Phase 1 `src/`/`native/`/`tests/`/`tools/`/`deploy/` skeleton with README placeholders (no logic).
- `.github/workflows/ci.yml` wired to the workflow gate (initially: structure-lint + placeholder test stages).

Suggested message:

```
chore(repo): establish Mini Prometheus repository architecture (Phase 1)

Governance + contract spine only; no runtime logic.
Derived from the frozen Constitution. See docs/architecture/repository-architecture.md
and docs/adr/0001-adopt-repository-architecture.md.
```

---

## 11. Risks and mitigations (Chief Systems Engineer review)

| Risk | Mitigation baked into this architecture |
|---|---|
| Contract drift between Python and native impls | Single schema source of truth + codegen; hand-edited bindings fail CI; one shared compliance suite runs against both. |
| Two-language build complexity | Native crates open only when benchmark-justified (M2), not preemptively; `native/` boundary is cheap in P1. |
| Upstream freeze violated by accident | Upstreams pinned exactly; only `integrations/` may reference them; bumps are isolated, owned PRs. |
| Speculative structure creeping in | Milestone gating (§7): future dirs live only in this doc until opened. |
| Ownership contention across teams | Cross-package coupling only through `contracts/`; everything else is package-local and independently mergeable. |
| Erosion of the freeze over time | `constitution/` is amendment-gated; contradictions surface as ADRs, never silent edits. |

---

## 12. Refinement pass (external review, ADR-0002)

This section records a documentation-only refinement performed after the Phase 1 foundation was
committed and frozen. It changes **no** frozen constitutional content and introduces **no** runtime
code. It sharpens six points that external review found under-specified. §§13–16 give the normative
detail; this section is the index.

1. **External contracts vs internal APIs** — §13.
2. **The Constitution → Specification → Contract → Implementation → Verification hierarchy** — formalized in §12.1 below and reflected in the §2 diagram.
3. **`world_model/` and `constraint_network/` are expandable package namespaces** — §12.2 below.
4. **`integrations/` is adapters-only, no business logic** — §14.
5. **Inter-package dependency rules** — §14.
6. **Constitution versioning** — §15.

### 12.1 The five-layer hierarchy (formal)

Each layer is *derived from and constrained by* the layer above it, and may not reach past its
neighbour:

| Layer | Home | Answers | Stability | Who may change it |
|---|---|---|---|---|
| **Constitution** | `constitution/` | The frozen theory (ontology, objects, operators, runtime arch) | Frozen; amendment-gated | Architecture Board, only on proven contradiction |
| **Specification** | `specs/` | The intended *what*, in human terms, derived from the Constitution | Versioned, evolvable | Authoring team + review |
| **Contract** | `contracts/` | The machine-checkable *interface* the spec is frozen into | SemVer; breaking = MAJOR | Architecture Board + Staff |
| **Implementation** | `src/`, `native/` | The *how* — code satisfying the contract | Free to change behind the contract | Owning team |
| **Verification** | `tests/`, `.github/` | *Proof* the implementation satisfies the contract | Tracks the contract | Owning team + Staff for `tests/contracts` |

Directional rule: a specification may only realize what the Constitution permits; a contract may only
formalize what a specification defines; an implementation may only depend on contracts; verification
asserts the implementation against the contract. Nothing skips a layer — e.g. an implementation may
never encode an assumption that has no contract behind it.

### 12.2 Expandable package namespaces

`world_model/` and `constraint_network/` (and, when they open, `cognition/`, `reasoning/`,
`coordination/`, `workflow/`) are **expandable package namespaces**, not single modules. Their
*external* contract is small and stable and lives in `contracts/`; their *internal* structure is
expected to grow many submodules over time (e.g. `constraint_network/` accruing constraint families,
propagation strategies, solvers; `world_model/` accruing model layers, stores, projections).

Consequences:

- Growth **inside** these packages is an internal-API change (§13): it needs no new top-level
  directory and no contract change, so it does not violate "no speculative folders."
- The package's public, cross-boundary surface remains *only* what `contracts/` exposes. New internal
  submodules are private (§13) until and unless they are promoted into a contract.
- This is exactly why these are directories, not files: the namespace is designed to expand without
  structural churn or re-architecture.

## 13. External architectural contracts vs internal implementation APIs

Two kinds of interface exist in this repository and must never be conflated:

**External architectural contracts** — everything in `contracts/`. These are the surfaces guaranteed
*across package and repository boundaries*: the shapes of Computational Objects, the signatures of
Operators, the runtime-architecture seams. They are versioned (`contracts/VERSION`, SemVer), carry a
compliance suite (`tests/contracts/`), and change only through high-scrutiny review. Any code — a
sibling package, a test, an integration adapter, an external consumer — may depend on them.

**Internal implementation APIs** — every symbol a `src/` or `native/` package exposes that is *not*
in `contracts/`. Helper classes, private functions, sub-package structure, native FFI details. These
carry **no** stability guarantee and may change in any commit.

Conventions that keep the line bright:

- A package's cross-boundary surface is *exactly* its contract. Nothing else it defines is public.
- Internal-only code is marked as such: underscore-prefixed names or an `_internal` submodule.
  `tools/` ships an import-linter rule so a cross-package import of a non-contract symbol fails CI.
- Promoting an internal API to an external contract is a deliberate act: write/extend the spec, add
  the schema, regenerate bindings, extend the compliance suite, bump `contracts/VERSION`. There is no
  accidental promotion.

Rationale: this is what lets implementations be rewritten freely (the whole point of the spine) while
still giving independent teams a fixed surface to build against.

## 14. Runtime package dependency rules

All cross-package coupling flows through `contracts/`; direct implementation-to-implementation imports
are prohibited except at the single composition root. Concretely, the Phase 1 packages form this DAG:

| Package | May depend on | May **not** depend on |
|---|---|---|
| `situation_state`, `world_model`, `constraint_network` (owned objects) | `contracts/` only | each other; `orchestration`; `integrations`; upstream packages |
| `integrations/{miniflywire,noetica,velith}` | `contracts/` + its one pinned upstream package | any owned object package; any other integration; anything with business logic |
| `orchestration` (composition root) | `contracts/`; may import the concrete object and integration packages **solely to instantiate/wire them** | anything that would invert this direction (nothing may depend *on* `orchestration` except the entrypoint) |

Two rules deserve emphasis:

- **Owned object packages are peers, not a stack.** `world_model` does not import `constraint_network`
  and vice-versa. Any relationship between two Computational Objects is expressed through
  contract-typed interfaces and *wired by* `orchestration`. This prevents a hidden dependency lattice
  from forming among the core objects.
- **`integrations/` contains adapters only — no business logic.** Each adapter's sole job is to
  translate between a frozen upstream's types and our `contracts/` types. Reasoning, orchestration,
  or domain decisions in an adapter are an architectural violation: they belong in an owned package.
  This keeps an upstream version bump a localized, mechanical change and preserves the clean
  repository boundary the Constitution requires.

Enforcement: these rules are expressed as import-linter contracts under `[tool.importlinter]` in
`pyproject.toml`, run in CI. The rules are documentation today and become executable when the first
implementation lands; no runtime code is added by stating them.

## 15. Constitution versioning

To make the freeze auditable over many years, the Constitution carries an explicit version:
`constitution/VERSION`, starting at **`1.0.0`** — the frozen Phase 1 baseline. This is additive
traceability metadata; it does **not** alter any frozen document's content.

Policy:

- The Constitution changes **only** by amendment on a proven contradiction (unchanged from the frozen
  rules). Every amendment bumps `constitution/VERSION` and is recorded by an ADR that cites the
  contradiction and the affected clause.
- Versioning semantics: **MAJOR** = a frozen clause changed or removed; **MINOR** = a clause clarified
  or added without invalidating existing implementations; **PATCH** = editorial/transcription fixes
  with no semantic change.
- Downstream artifacts record the Constitution version they were derived under: `contracts/VERSION`
  and release notes reference the `constitution/VERSION` in force. This yields an unbroken trace from
  any shipped artifact back to the exact frozen theory it implements.
- `constitution/VERSION` is owned by the Architecture Board and is amendment-gated like the rest of
  `constitution/`.

## 16. What this refinement did not change

For the record: no frozen document under `constitution/` had its content modified; no directory was
added or removed; no runtime code was written. The refinement is confined to `docs/`, one additive
`constitution/VERSION` metadata file, `CONTRIBUTING.md`, and ADR-0002. The Phase 1 foundation remains
frozen; this pass only makes its existing rules explicit.

---

*This document is the permanent repository architecture for Mini Prometheus. It derives structure from the frozen Constitution and does not alter the computational theory or runtime architecture.*
