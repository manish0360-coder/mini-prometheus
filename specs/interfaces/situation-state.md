# RM1 Specification — Situation State (interface specification)

- **Status:** ⛔ **WITHDRAWN / SUPERSEDED (CAP-0001, ADR-0004, 2026-07-23).** The archaeology proved
  "Situation State" is not a canonical object and that an MP-owned state substrate would breach Laws 3/6
  (state substrate is a Noetica mechanism). RM1 is re-scoped to a manufacturing-content slice over
  consumed Velith→Noetica interfaces. This document is retained for provenance only; do not implement it.
  See `docs/governance/constitutional-evolution-report.md` and `docs/governance/CAP-0001-...md`.
- **Status (original):** Draft — Specification stage. **Blocked** on constitutional transcription (§2).
- **Milestone:** RM1 (first runtime implementation milestone).
- **Layer:** Specification (`specs/`) — the human-authored *what*, to be frozen into `contracts/` (§12.1 of the architecture doc). This document is **not** a contract, schema, or implementation.
- **Owner:** World-Model team. Contract-surface review: Architecture Board + Staff.
- **Constitution version in force:** 1.0.0.
- **Related:** ADR-0003 (runtime implementation order), `docs/architecture/repository-architecture.md` §§12–15.

> **This document invents no theory.** Where the frozen definition of Situation State is required but
> not yet transcribed into `constitution/`, the relevant statement is quarantined in §5 as an
> assumption requiring Board confirmation. Nothing here redesigns the runtime architecture.

---

## 1. Purpose and scope

Specify the *external interface intent* of **Situation State**, the first owned Computational Object
to be implemented (RM1). Situation State is the runtime's canonical state substrate — the object the
Engineering World Model is a view over and the Constraint Network ultimately constrains. RM1 implements
this object end-to-end and, in doing so, stands up the reusable contract pipeline (schema→bindings
codegen, contract-compliance harness, real CI gate) that every later object reuses.

In scope for this spec: the interface *what* — identity, state derivation, access, invariants, and the
non-functional properties (determinism, serializability) that downstream verification depends on.

Out of scope for this spec: the schema itself (`contracts/schemas/`, next stage), any implementation,
and any other subsystem (World Model, Constraint Network, orchestration, integrations).

---

## 2. Constitutional preconditions — transcription checklist (BLOCKER)

RM1's Specification cannot be finalized until the frozen Situation State definition is transcribed
from the frozen theory into `constitution/` (those files are currently `FROZEN` placeholders). This is
a Board transcription action, **not** a redesign. Until it lands, §4 is provisional and §5 governs.

Required frozen inputs and what this spec needs from each:

| Frozen source | What this spec must reconcile against |
|---|---|
| `constitution/computational-objects.md` → *Situation State* | The authoritative definition: what Situation State represents, its constituent structure, its identity and lifetime semantics. |
| `constitution/ontology.md` | The ontological entities Situation State references (so the state substrate speaks the frozen vocabulary, not an invented one). |
| `constitution/operators.md` | The frozen Operators that read from / produce Situation State, and their semantics (these dictate the interface's operations). |
| `constitution/runtime-architecture.md` | Where Situation State sits in the runtime, its lifecycle, and its relationship to World Model / Constraint Network. |
| `constitution/promotion-workflow.md` | Whether/how Situation State participates in promotion (affects provenance/versioning requirements). |

**Action to unblock:** Architecture Board transcribes the frozen Situation State definition into the
files above and bumps nothing (transcription of already-frozen theory is version-neutral if the
placeholders are understood as "not yet written down"; if transcription reveals content, treat as the
authoritative 1.0.0 text). This spec is then reconciled and its §5 assumptions are confirmed or
corrected.

---

## 3. Position in the architecture (recap — not a redesign)

- **Layer:** Implementation target sitting behind a Contract (§12.1). This spec is the Specification
  layer that the contract will formalize.
- **Ownership:** `src/mini_prometheus/situation_state/` — World-Model team (§6).
- **Dependency rules (§14):** Situation State depends on `contracts/` only. It does **not** import
  `world_model`, `constraint_network`, `orchestration`, or `integrations`, and nothing imports its
  internals across the boundary — only its contract surface is public.
- **Expandable namespace (§12.2):** `situation_state/` is a package namespace expected to grow internal
  submodules; only its contract surface is stable.

---

## 4. Specified interface (the "what")

Provisional pending §2. Stated at interface level; semantics attributed to a frozen source or flagged
in §5.

### 4.1 Identity and versioning
- A Situation State value has a stable **identity** and a **version/lineage** marker, so any derived
  artifact can be traced back to the exact state it was computed from (required for Velith-style
  provenance and reproducible verification). *(Provenance requirement — see §5.A.)*

### 4.2 State derivation (transitions)
- New Situation State values are **derived** from a prior value plus a frozen Operator's output, rather
  than mutated in place. The set of legal derivations is dictated by `constitution/operators.md`.
  *(Immutability/derivation model — see §5.B.)*

### 4.3 Access (read) semantics
- Read access exposes the state's content in terms of the frozen ontology vocabulary only. Readers
  receive contract-typed views; internal representation is not exposed across the boundary (§13).

### 4.4 Invariants
- Every Situation State value is **well-formed** against the frozen Computational Object definition at
  all times (no partially-constructed public value).
- Identity + version uniquely determine content (content-addressable lineage). *(See §5.A.)*

### 4.5 Determinism and serializability
- Given identical inputs, derivation is **deterministic** (no hidden nondeterminism), and every value is
  **serializable** to a canonical form. Both are required so Velith can verify and reproduce runs.
  *(Determinism/serialization requirement — see §5.C.)*

### 4.6 Error conditions
- Illegal derivations (not permitted by the frozen operator set) and malformed reads are surfaced as
  typed, contract-defined errors — never silent partial states.

### 4.7 External contract surface vs internal (§13)
- **External (goes to `contracts/`):** the value's identity/version accessors, the derivation
  entry point(s) corresponding to frozen operators, the read/view accessors, the canonical
  serialization, and the typed error set.
- **Internal (stays in `src/`, unguaranteed):** concrete storage layout, indexing, caching, and any
  helper decomposition of the `situation_state/` namespace.

---

## 5. Assumptions pending constitutional confirmation

Each item is used by §4 but originates in frozen theory not yet transcribed. **The Board must confirm or
correct each against the actual frozen text.** If any is wrong, §4 changes accordingly before the
contract is drafted.

- **§5.A — Provenance/lineage is a first-class requirement of Situation State.** Assumed because Velith
  is the frozen provenance/verification authority and downstream artifacts must trace to the state they
  derive from. *Confirm: does the frozen definition make identity+lineage intrinsic to Situation State,
  or is provenance layered externally by Velith integration?*
- **§5.B — Situation State is derived (append/functional), not mutated in place.** Assumed to support
  reproducibility and clean concurrency. *Confirm against the frozen Computational Object + Operator
  semantics; if the frozen model permits in-place mutation, §4.2/§4.4 change.*
- **§5.C — Determinism and canonical serialization are required.** Assumed from Velith's reproducible-
  evaluation mandate. *Confirm this obligation belongs to Situation State (vs being solely Velith's).*
- **§5.D — Situation State references the frozen ontology vocabulary directly.** Assumed so the substrate
  is not an invented type system. *Confirm the exact ontological entities it must expose.*

---

## 6. Non-goals (explicit)

- No World Model, Constraint Network, orchestration, integration, or native code — and their contracts
  are **not** drafted in RM1 (prevents scope creep).
- No performance optimization or native acceleration (benchmark-justified, M2).
- No new theory: this spec does not define what Situation State *is* beyond the frozen definition; it
  specifies the *interface* to it.

---

## 7. Contract mapping (Specification → Contract, next stage)

When this spec is accepted, the Contract stage produces:
- `contracts/schemas/situation_state/…` — language-neutral source of truth for the §4.7-external surface.
- `contracts/python/situation_state/…` — **generated** Protocols/ABCs (no logic; `tools/` codegen).
- `contracts/VERSION` bump per SemVer if this establishes/changes the contract (initial add on a `0.x`
  line).
No internal-API detail (§4.7-internal) enters `contracts/`.

---

## 8. Acceptance criteria and verification intent

RM1 is "logically complete" when all hold:
1. The frozen Situation State definition is transcribed (§2) and §5 assumptions are confirmed/corrected.
2. A contract exists in `contracts/schemas` with generated bindings; hand-editing a binding fails CI.
3. `tests/contracts/situation_state/` contains an **implementation-agnostic** compliance suite asserting
   §4 invariants (well-formedness, identity/lineage determinism, canonical serialization round-trip,
   typed errors on illegal derivation).
4. `src/mini_prometheus/situation_state/` passes the compliance suite and its own unit tests.
5. CI runs real stages (build → unit → contract-compliance) — placeholders replaced — and an
   import-linter rule proves `situation_state` depends on `contracts/` only (§14).
6. No other subsystem was added; no frozen content changed except the §2 transcription.

---

## 9. Open questions for the Architecture Board

1. Confirm §5.A–§5.D against the frozen text.
2. Does Situation State participate in the Promotion Workflow, and if so, what provenance obligations
   does that impose on its contract?
3. Is canonical serialization owned by Situation State's contract, or delegated to a shared
   provenance/serialization contract that Velith integration also uses (affects where the schema lives)?

---

*Specification stage only. Contract, implementation, and tests follow in later stages once §2 is
unblocked and §5 is confirmed.*
