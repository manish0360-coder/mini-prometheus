# RM4 Engineering Package — Engineering Judgment (first implementation: Engineering Critique)

- **Status:** Draft — Engineering package. **No code, no pseudocode, no contracts, no schemas, no implementation.** Transforms the frozen RM4 specification into a buildable module structure.
- **Derives from (frozen, unchanged):** the RM4 Specification (identity **Engineering Judgment**; first implementation **Engineering Critique**; **EngineeringSituation internal**), and the frozen RM1/RM2/RM3 specifications, contract packages, and engineering packages.
- **Invariants preserved (non-negotiable):** RM1/RM2/RM3 are frozen (zero diff); RM4 is **purely additive**; **RM4 introduces NO contract** — the contract suite stays frozen at `0.4.0`; **EngineeringSituation stays INTERNAL** (no contract, no schema, no persistence, no exposure); Law-3 mechanism/content split; Law-6 (no Noetica store engine); Law-4 (no MiniFlyWire); determinism; **read-only**; RM1/RM2/RM3 compatibility.

---

## 1. Module decomposition

RM4 is a new Mini Prometheus domain-reasoning capability whose identity is **Engineering Judgment**. It lives in a **new package** named for the *identity*, `judgment/`, plus **one new composition file** under `orchestration/`. The package is deliberately named `judgment/` (not `critique/`) so that future forms of judgment — comparison, ranking, evaluation, optimization advice — become additional modules **beneath the same identity** without a rename or a boundary change. RM4 consumes the outputs of RM1 and RM3 read-only; it imports **no** RM1/RM2/RM3 *mechanism* and re-derives nothing.

| Module (new) | Layer role | Kind |
|---|---|---|
| `judgment/__init__.py` | package marker + boundary docstring (identity = Engineering Judgment) | package |
| `judgment/engineering_situation.py` | assemble + hold the **internal EngineeringSituation** — the coherent engineering state of one case | mechanism (internal; extraction-seed candidate) |
| `judgment/critic_model.py` | the deterministic, **versioned judgment model** — what constitutes a *situated finding* (domain content) | content |
| `judgment/engineering_critique.py` | **the first implementation of Engineering Judgment** — derive findings + assessment and assemble the advisory critique result (RM4's identity in code) | content (identity) |
| `orchestration/judgment_runner.py` | thin composition entry: receive the case's existing artifacts → assemble situation → judge → return the critique | composition root |

Two deliberate separations, mirroring the proven RM3 seed/identity split:

- **Situation-assembly (mechanism) is separate from judgment (content).** `engineering_situation` builds the coherent substrate; `engineering_critique` reasons over it. Keeping them apart (a) makes the situation's load-bearing shape *observable in isolation* (the spec's "reveal, not predict" purpose), and (b) makes any future extraction of the situation primitive a localized change that never touches the judgment content.
- **The judgment model (content) is separate from the judgment producer.** `critic_model` owns *what makes a plan sound in context*; `engineering_critique` applies it. Future judgment forms reuse the model surface without redefining identity.

## 2. File creation plan

All files are **additive**. No existing RM1/RM2/RM3 source file is edited; **no file under `contracts/` is created or modified** (RM4 adds no contract — the single most important line of this plan).

Create, in build order:

1. `src/mini_prometheus/judgment/__init__.py`
2. `src/mini_prometheus/judgment/engineering_situation.py`
3. `src/mini_prometheus/judgment/critic_model.py`
4. `src/mini_prometheus/judgment/engineering_critique.py`
5. `src/mini_prometheus/orchestration/judgment_runner.py`
6. `tests/unit/test_engineering_situation.py`
7. `tests/unit/test_critic_model.py`
8. `tests/unit/test_engineering_critique.py`
9. `tests/integration/test_engineering_judgment.py`
10. `tests/boundary/test_judgment_boundaries.py`
11. modify `.github/workflows/ci.yml` — extend the zero-diff / boundary stages to cover `judgment/` (RM1/RM2/RM3 remain zero-diff; contract-freeze remains `0.4.0`).

Explicitly **not** created: any `contracts/schemas/**`, `contracts/python/**`, ADR, or schema file. The internal EngineeringSituation and the Engineering Critique **result** are ordinary in-memory runtime structures inside `judgment/` (the same category as RM1's run result and RM2's reuse result — runtime objects, not contracts). Governance/version/close-out documents belong to the milestone plan, not to this package.

## 3. Dependency graph

```
contracts.python  (frozen RM1/RM2/RM3 bindings: Episode/Plan/Verdict/PrecedentReport — read-only; RM4 adds none)
        ▲                      ▲                         ▲
        │                      │                         │
   critic_model         engineering_critique  ─────────► _hashing, _provenance   (read-only MP mechanisms)
        ▲                 ▲            ▲
        │                 │            │
        │        engineering_situation │      (internal coherent case-state assembly;
        │                 ▲            │        consumes PASSED-IN RM1 episode + RM3 PrecedentReport objects)
        └─────────────────┤            │
                          │            │
        orchestration/judgment_runner ─┘      (receive case artifacts → assemble situation → judge → critique)
```

Direction rules (all satisfied):

- Everything depends **only** on `contracts.python` (frozen bindings, read-only) + the read-only MP mechanisms `_hashing`/`_provenance` + stdlib. **Nothing** in RM1/RM2/RM3 depends on `judgment/`.
- `engineering_situation` is the **sole assembler** of the internal situation, and it consumes **already-produced artifacts passed to the runner** — it never opens the episode store, never imports `experience/`, `planner`, `oracle`, or `precedent.retriever`. RM4 therefore does **not** become a second consumer of the RM2 read side, and the RM3 "retriever is sole RM2-read-side consumer" boundary is untouched.
- RM4 reads RM3's output **type** (`PrecedentReport`) and RM1's output types (`ManufacturingEpisode` → its `ProductionPlan`/`Verdict`/design) as data; it imports **no** RM3/RM1 reasoning or construction mechanism, so it re-plans nothing, re-verifies nothing, re-retrieves nothing.
- No module imports MiniFlyWire (Law 4); no persistence/store engine anywhere (Law 6); `engineering_situation` never leaves `judgment/`.

## 4. Internal EngineeringSituation assembly

`engineering_situation` realizes the spec's primitive: **the coherent engineering state of one manufacturing case**, held only in memory, only inside `judgment/`, only for the duration of one act of judgment.

- **Inputs (received, never fetched).** The composition root hands the assembler the case's **already-produced** artifacts — the RM1 episode (which bundles the case's design/intent, its `ProductionPlan`, and its grounded `Verdict`) and the RM3 `PrecedentReport` for the same case. The assembler re-derives nothing.
- **Coherence invariant (fail-closed).** The assembler admits constituents only if they belong to the *same* case, checked by **referential hash match** against the existing content hashes — e.g., the precedent report's query-design reference must match the episode's design reference, and the plan/verdict must be the episode's own. If coherence cannot be established, assembly **raises** and no critique is produced (spec invariant 7). No new hashes are minted; only existing ones are compared, via the read-only `_hashing` mechanism.
- **Contingent, revealed membership.** The assembler treats its constituent set as **observed, not definitional**. The current constituents (request/design, plan, verdict, precedent) are present **because Engineering Judgment (RM4) — the primitive's first consumer — requires them** (today through its first implementation, Engineering Critique). The assembler records which constituents it actually supplied so the milestone can document the load-bearing set (the "primitive revelation" acceptance artifact). Adding a future constituent is an evidence-driven change to this module, never an anticipatory one.
- **State, not behavior.** The situation performs no reasoning, planning, verification, or retrieval; it is a coherent, read-only bundle plus its coherence guarantee.
- **Determinism.** Assembly is pure and order-stable: identical inputs yield an identical internal situation; it depends on no clock, no unordered-iteration order, and no process state.
- **Containment.** The situation type and its assembler are importable **only within `judgment/`**; they are never persisted, never returned to a caller as an output, and never given an externally-depended-upon identity. Extraction to a shared/contract form is gated by the spec's §12 criteria and is out of scope here.

## 5. Critic model decomposition

`critic_model` owns the deterministic, **versioned** judgment content — *what makes a proposed plan sound in its situation* — carried as a `critic_model_version` (the same convention as `capability_model_version` and `precedent_model_version`; dataclass-based, introducing no Pydantic surface and therefore no new `model_`-namespace warning). It defines a **closed taxonomy of situated finding families** for the first implementation and the deterministic rule for each; it does **not** re-verify manufacturability and **does not** re-run any RM1/RM3 mechanism — it reasons over artifacts already in the situation.

First-implementation finding families (decomposition of responsibility, not fields or codes):

- **Intent-alignment findings.** Judge whether the proposed plan structurally serves the case's declared intent/design (e.g., the declared operations and quantity are all represented in the plan). Derived purely from design + plan already in the situation.
- **Precedent-consistency findings.** Judge the plan/design against the strongly-relevant precedent the situation already carries: a strongly-relevant precedent whose verified verdict was *not manufacturable* yields a **cautionary** finding that surfaces that precedent's reason codes; a strongly-relevant *manufacturable* precedent yields a **supporting** finding. This consumes the RM3 `PrecedentReport` as-is; it never re-retrieves or re-scores.
- **Internal-consistency findings.** Judge coherence between the plan and its own grounded verdict as recorded (advisory surfacing only; never a re-verification).

The model also owns the deterministic **summary-assessment** derivation (supportive / cautionary / neutral in spirit) from the ordered findings — the analogue of RM3's signal derivation, and the natural seam at which future judgment forms (comparison, ranking, evaluation) plug in without altering identity. Every finding is **grounded** by reference to the specific situation constituent that produced it; any severity is bounded and integer-valued.

**Governance and versioning of `critic_model_version`.** The judgment model is versioned by SemVer and follows the **same discipline already established** for `capability_model_version` (RM1) and `precedent_model_version` (RM3): every critique carries the exact model version that produced it, and that version is part of the critique's content-hash identity, so critiques are reproducible and comparable across model revisions. The finding-family taxonomy is a **closed taxonomy** — adding or removing a family is a **MAJOR** bump (the same rule RM1/RM3 apply to their closed taxonomies); changing a family's deterministic rule, a bounded severity, or the summary-assessment derivation in any way that can alter an output is at least a **MINOR** bump; only provably output-preserving edits are **PATCH**. A default model is pinned, and its version is the frozen default. **Changing model behavior without bumping `critic_model_version` is forbidden** — it would silently break reproducibility; conversely, a bump records a new, comparable model. Crucially, none of this is a contract change: `critic_model_version` governs a runtime model only, so the versioning discipline holds while RM4 still introduces no contract (suite frozen at `0.4.0`).

`engineering_critique` applies the model to the situation, orders the findings by a total order with a deterministic tie-break, derives the assessment, and assembles the advisory critique **result object** — computing its reproducible content-hash identity over an internal identity view (via read-only `_hashing`) and its provenance (via read-only `_provenance`, `rule_id` for engineering-judgment critique, capability sentinel `"0.0.0"`, model version = `critic_model_version`). The result is a runtime object, **not** a contract.

## 6. Test strategy

By category (what each proves; concrete gates, not a test-by-test list):

- **Situation assembly (unit).** Coherent inputs assemble; incoherent inputs (mismatched case references) **fail closed**; assembly is deterministic and order-stable; the situation is never written anywhere; the recorded constituent set matches what was supplied.
- **Critic model (unit).** Each finding family is derived deterministically and only from constituents present in the situation; the summary assessment follows deterministically; a versioned model is carried; no re-verification / no re-retrieval occurs (verified structurally in §8).
- **Engineering Critique (unit).** Findings are grounded (every finding references a real situation constituent); ordering is a stable total order; the critique's `content_hash`/identity are computed per the reused mechanism; **structural honesty** — the critique carries no field that could be read as the case's manufacturability verdict; identical inputs ⇒ identical critique.
- **Engineering Judgment end-to-end (integration).** Given an RM1 episode and an RM3 precedent report for a case, `judgment_runner` returns a deterministic advisory critique; **situated value is demonstrated** — a plan that is structurally valid per RM1 yet resembles a strongly-relevant *not-manufacturable* precedent yields a **cautionary** finding that isolated verification could not produce; empty/neutral situations yield a neutral assessment; **read-only** (the episode, its plan/verdict, the report, and all stores are unchanged); **internality** (the EngineeringSituation is never surfaced or persisted).
- **Boundary / constitutional (see §8).**
- **Determinism proofs (see §7).**

**Evidence-grounding acceptance rule (mandatory).** Every finding in any produced critique **must be traceable to explicit evidence present in the assembled situation**: each finding names the specific situation constituent(s) that justify it, and a finding with no situation grounding is a defect that **fails the gate**. This is enforced as an acceptance assertion over produced critiques (unit and integration) — grounding is a pass/fail property of the output, not merely documentation.

**Scientific success criterion (measurable; hypothesis H1).** RM4 is scientifically successful if, on a curated set of cases each pairing a structurally-valid plan with a strongly-relevant precedent of known verdict, the critique's situated assessment agrees with that precedent's verdict on **≥ 95%** of cases, while emitting **zero** cautionary findings on control cases that carry no relevant adverse precedent (precision-first — no false alarms). This is the measurable form of H1; per the frozen spec it is **assessed by a later evaluation milestone and is not an evaluation harness implemented inside RM4**.

Reused harness only: the existing `tests/conftest.py`, `tests/support.py`, pytest `pythonpath`, and the StrEnum shim — unchanged.

## 7. Determinism requirements

- **Versioned judgment model:** every critique carries `critic_model_version`; identical model + inputs ⇒ identical judgment.
- **Pure, order-stable situation assembly:** no clock, no unordered-iteration dependence, no process state.
- **Total, reproducible finding order** with a deterministic tie-break (e.g., by grounding constituent's content hash), so identical inputs yield identical ordering and identical `rank`ing of findings.
- **No floating-point identity hazard:** any severity/score is bounded and integer-valued; canonical-JSON identity discipline reused unchanged.
- **Reproducible identity:** `content_hash` and derived id are computed over an internal identity view that **excludes** volatile fields (timestamps/timing/provenance); identical `(episode, precedent_report, critic_model_version)` ⇒ identical critique `content_hash` and id.
- **Proof obligation:** an explicit determinism check (identical inputs across differing `produced_at` and an independent re-assembly ⇒ identical critique fingerprint), in addition to the unit/integration determinism assertions.

## 8. Boundary tests

`tests/boundary/test_judgment_boundaries.py` — AST-based (the proven precedent-boundary pattern), targeting `judgment/__init__.py`, `judgment/engineering_situation.py`, `judgment/critic_model.py`, `judgment/engineering_critique.py`, and `orchestration/judgment_runner.py`:

- **Import discipline:** import only `contracts` + RM1/RM2/RM3 read-only mechanisms + stdlib; **never** MiniFlyWire (Law 4) or Noetica; **no** ML/embeddings/vector-DB; **no** persistence/store engine (Law 6).
- **No re-derivation:** the judgment layer imports **no** construction or reasoning mechanism — not `manufacturing_planning`, not `manufacturing_constraints` (oracle), not `experience` (RM2 read side), and not `precedent.retriever`/`precedent.reasoner` functions. It consumes only output **types** (Episode/Plan/Verdict/PrecedentReport). This encodes "no planning / no verification / no retrieval."
- **Situation internality:** `engineering_situation` is imported **only** within `judgment/` (no other package references it); the judgment layer performs **no filesystem writes** (no `open()`, no write/emit/dump) — read-only, no persistence, no exposed situation.
- **Sole assembler:** `engineering_situation` is the only module that constructs the situation (seed/identity separation preserved).
- **No-lifecycle symbols:** no retention/prune/compress/evict/archival machinery (Law 6, §11.11).
- **No new contract:** a gate asserting `contracts/VERSION` is unchanged (`0.4.0`) and `contracts/**` is byte-unchanged — RM4 introduces no contract or schema.

## 9. Verification gates

Run at each module gate; RM4 adopts the workstation's Docker verifier as the authoritative gate. The canonical command is the one already green on the workstation:

```
docker compose run --rm verifier bash -lc "ruff check . && ruff format --check . && mypy src tests && pytest -q"
```

Plus the repository-specific constitutional gates:

- `ruff check` clean and `ruff format --check` clean (formatting is now gate-enforced).
- `mypy src tests` clean — `judgment/` is fully typed (the internal situation and critique result carry annotations); this is a first-class RM4 gate, matching the workstation pipeline.
- `pytest -q` green across the whole suite (RM1 + RM2 + RM3 + RM4-so-far), including the new unit, integration, and boundary tests.
- **Evidence-grounding:** every finding in every produced critique references explicit situation evidence — no ungrounded finding is emitted (acceptance assertion, per §6).
- Contract-drift: regeneration of `contracts/python` is drift-stable (RM4 changes nothing there).
- Contract-freeze: `contracts/VERSION == 0.4.0` (RM4 adds no contract).
- Import-linter (`lint-imports`): dependency direction intact (implementations → contracts only).
- **RM1/RM2/RM3 zero-diff:** the frozen behavioral core is byte-unchanged versus its frozen anchor; `judgment/` and `judgment_runner` are additions, not diffs.
- Boundary suite (§8) green.
- **Docker verification gate GREEN** end-to-end (the single pass/fail signal). The known benign Pydantic `model_version` protected-namespace warning is unchanged and non-blocking; RM4 introduces no new Pydantic model, so it neither resolves nor worsens it.

## 10. Commit boundary

RM4 has **no contract milestone** (it adds no contract), so the partition is content-only. Each commit is one atomic, independently-verifiable unit that ends with its gate green; RM1/RM2/RM3 stay byte-unchanged and `contracts/VERSION` stays `0.4.0` throughout; EngineeringSituation stays internal in every commit; **no commit introduces a contract**. A green commit is a safe rollback target.

- **Commit 1 — internal situation.** `engineering_situation` + `test_engineering_situation.py`. Gate: assembly determinism, coherence fail-closed, internality/no-write, RM1/RM2/RM3 zero-diff, contracts frozen.
- **Commit 2 — judgment model.** `critic_model` + `test_critic_model.py`. Gate: per-family determinism, versioning, no re-derivation.
- **Commit 3 — first judgment implementation.** `engineering_critique` + `test_engineering_critique.py`. Gate: grounded findings, stable ordering, identity/hash, structural honesty.
- **Commit 4 — composition (integration checkpoint).** `orchestration/judgment_runner.py` + `tests/integration/test_engineering_judgment.py`. Gate: end-to-end determinism, situated-value demonstration, read-only, internality; full suite green.
- **Commit 5 — constitutional gates.** `tests/boundary/test_judgment_boundaries.py` + `.github/workflows/ci.yml` wiring. Gate: boundary suite green, zero-diff, contract-freeze, import-linter, Docker gate GREEN.
- **Commit 6 — governance close-out (milestone-plan, not this package).** Version bump, changelog, roadmap, completion report, and the **primitive-revelation record** (the observed load-bearing constituent set of EngineeringSituation, and whether it has stabilized — the input to the §12 extraction decision).

**Commit-boundary rule.** Never combine a module with its consumer in one commit unless the gate requires it; each commit is independently green; the internal situation is never exposed, persisted, or given an external identity in any commit; and the EngineeringSituation extraction decision is deferred to a later, separately-ratified milestone per the frozen spec's §12.

---

*RM4 engineering package. No code, no pseudocode, no contracts, no schemas, no implementation. Identity = Engineering Judgment; first implementation = Engineering Critique; EngineeringSituation internal throughout. On approval, the implementation proceeds commit-by-commit under the gates above, with the situation primitive's extraction gated on evidence, not anticipation.*
