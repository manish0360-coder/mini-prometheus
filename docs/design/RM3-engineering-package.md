# RM3 Engineering Package — Engineering Precedent Reasoning

- **Status:** Draft — Engineering package. **No code, no pseudocode, no JSON Schema, no bindings, no
  implementation plan.** Transforms the frozen architecture into a buildable structure.
- **Derives from (frozen, unchanged):** `specs/milestones/RM3-engineering-precedent-reasoning.md` and
  `contracts/RM3-contract-package.md`.
- **Invariants preserved (non-negotiable):** RM1 and RM2 are frozen (zero diff); RM3 contracts are additive only;
  Law-3 mechanism/content split; Law-6 (no Noetica store engine); determinism; **read-only**; RM1/RM2 compatibility.

---

## 1. Module decomposition

RM3 is a new Mini Prometheus domain-reasoning capability. It lives in a **new package** `precedent/` (the domain
content) plus **one new composition file** under `orchestration/` (the entry point). It **consumes** RM2's read
side (`experience/`) as its retrieval substrate. RM1 and RM2 modules are imported read-only and unmodified.

| Module (new) | Layer role | Kind |
|---|---|---|
| `precedent/__init__.py` | package marker + boundary docstring | package |
| `precedent/precedent_model.py` | the deterministic, versioned **engineering relevance model** (domain content) | content |
| `precedent/retriever.py` | the **retrieval mechanism** — ranks the corpus by the model (the **Extraction Seed**) | mechanism (seed) |
| `precedent/reasoner.py` | **Engineering Precedent Reasoning** — signal derivation + `PrecedentReport` assembly (RM3's identity) | content (identity) |
| `orchestration/precedent_runner.py` | thin composition entry: intake → retrieve → reason → report | composition root |

Deliberately **two separate modules** for retrieval vs reasoning: the *retriever* is the mechanism (extraction
seed, replaceable by Noetica later); the *reasoner* is RM3's architectural identity. Keeping them apart lets the
seed extract into Noetica without touching the reasoner or the contracts.

## 2. Responsibility of every module

- **`precedent_model.py` (content).** Defines the deterministic, **versioned** engineering relevance model: given
  a query `DesignInput` and a precedent `DesignInput`, produce a deterministic **per-mille relevance** over the
  frozen feature set (material, stock form, ordered declared-operation sequence, quantity, tolerances; geometry
  excluded). Owns the `precedent_model_version` and its default. No I/O. This is domain content — *what makes two
  engineering cases relevant.* (Analogous to RM1's capability model.)
- **`retriever.py` (mechanism / extraction seed).** Given the query `DesignInput` and the episode corpus (obtained
  read-only via RM2's `experience` reader + index), score every candidate with `precedent_model`, and return a
  **deterministically ranked** candidate set (relevance desc, tie-break by episode `content_hash` asc; top-K per
  the model). It owns *no* precedent semantics and *no* report shape — only ranking. It is the isolated mechanism
  that a future Noetica retrieval mechanism will replace.
- **`reasoner.py` (RM3 identity).** From the ranked candidates and their **verified** verdicts, derive the
  `PrecedentSignal` (supporting / cautionary / none) and its `signal_source_rank`, assemble the `PrecedentReport`
  (report-level) and its `PrecedentEntry[]` (entry-level), populate provenance, and compute `content_hash` +
  deterministic `report_id`. Read-only: it produces a report object and writes nothing. This is *Engineering
  Precedent Reasoning.*
- **`orchestration/precedent_runner.py` (composition).** The thin entry that composes RM1 intake (request →
  `DesignInput`, read-only), the retriever, and the reasoner into a single call returning a `PrecedentReport`. It
  changes neither RM1's `run`/`runner.py` nor RM2's `reuse_runner.py`; it is a new file.

## 3. Dependency graph

```
contracts (frozen RM1/RM2 + additive RM3: PrecedentReport/Entry/Signal)
      ▲            ▲                    ▲
      │            │                    │
precedent_model   reasoner ───────────► _hashing (read-only: canonical_json, content_hash, uuid5)
      ▲            ▲
      │            │
   retriever ──► experience.reader + experience.index   (RM2, read-only)
      ▲
      │
orchestration/precedent_runner ──► intake (RM1, read-only)
```

Direction rules (all satisfied): everything depends **only** on `contracts/` + RM1/RM2 read-only + stdlib;
**nothing** in RM1/RM2 depends on `precedent/`; the **retriever** is the sole module touching the RM2 read side;
the **reasoner** never imports the retriever's internals beyond the ranked-candidate hand-off (seed/identity
separation); no module imports MiniFlyWire (Law 4); no persistence/store engine anywhere (Law 6).

## 4. End-to-end data flow

```
ManufacturingRequest
   │  intake (RM1, read-only)
   ▼
DesignInput (query)  ── precedent_model.version ──┐
   │                                              │
   ▼   retriever: load corpus (experience.reader) │
corpus of verified ManufacturingEpisodes  ────────┘
   │  retriever: score each precedent via precedent_model → rank (relevance desc, tie-break by episode content_hash)
   ▼
ranked candidate precedents (episode + per-mille relevance)
   │  reasoner: build PrecedentEntry[] (rank, episode_ref, relevance_score, verdict_status, reason_codes, precedent_verification_status)
   │  reasoner: derive PrecedentSignal (+ signal_source_rank) from the nearest strongly-relevant verdict
   │  reasoner: assemble PrecedentReport (query_design_input_ref, precedents, signal, precedent_model_version, provenance)
   │  reasoner: content_hash = sha256(canonical_json(identity_view));  report_id = uuid5(NS_MP, content_hash)
   ▼
PrecedentReport   ── advisory only; writes nothing; RM1 plan/verdict unchanged; corpus unchanged
```

Notes: the corpus read is the only I/O, and it is read-only (episodes are integrity-verified by the RM2 reader).
`D = 0` (identical intent) surfaces as relevance `1000` — the RM2 exact case, now generalized. Empty corpus ⇒
empty `precedents` ⇒ `signal = NONE`.

## 5. Verification strategy

Strategy by category (what each *proves*; concrete gates listed, not a test-by-test plan):

- **Determinism (unit + integration):** identical query + identical corpus + identical `precedent_model_version`
  ⇒ identical `PrecedentReport` `content_hash` and `report_id`; `produced_at`/provenance excluded from identity;
  relevance is integer per-mille (no float hashing hazard).
- **Precedent model (unit):** relevance is a deterministic, versioned function of the frozen features; identical
  designs ⇒ relevance `1000`; changing the version is a distinct, recorded model.
- **Retriever (unit):** total-order ranking with the fixed tie-break; correct top-K; ranking depends only on the
  model + corpus (no hidden state); it reads the corpus and mutates nothing.
- **Reasoner / identity (unit):** signal derivation is correct and deterministic (supporting/cautionary/none with
  a valid `signal_source_rank`); report and entries populate exactly the contract fields; `content_hash`/`report_id`
  computed per the contract; **honesty is structural** — the report has no query-verdict field.
- **Generalization (integration):** a *similar but not identical* prior request is surfaced as a precedent (which
  RM2 exact reuse would miss); an identical one appears at relevance `1000`; a strongly-relevant
  `NOT_MANUFACTURABLE` precedent yields a `CAUTIONARY` signal with its reason codes; empty corpus ⇒ `NONE`.
- **Read-only (integration):** a precedent query leaves the corpus (episode store) unchanged; RM1's plan/verdict
  for the query are unchanged.
- **Contract compliance:** `PrecedentReport`/`PrecedentEntry`/`PrecedentSignal` instances validate against the RM3
  schemas (once generated); closed enums exact; content-hash stability.
- **Boundary / constitutional gates (CI):** `precedent/` + `precedent_runner` import only `contracts/` + RM1/RM2
  read-only + stdlib; **no** ML/embeddings/vector DB; **no** store/retention/pruning engine (Law 6); **no**
  MiniFlyWire (Law 4); the retriever is the only RM2-read-side consumer (seed/identity separation); **RM1/RM2
  zero-diff** vs their tags; **contracts frozen** except the additive RM3 set (suite `0.2.0 → 0.3.0`).

## 6. Safe implementation order (module build order — not a milestone/commit plan)

Ordered so each step is independently verifiable and RM1/RM2 stay green throughout:

1. **Prerequisite — RM3 contract artifacts.** Generate the RM3 schemas + bindings from the frozen
   `contracts/RM3-contract-package.md` (`PrecedentReport`/`Entry`/`Signal`) and bump `contracts/VERSION` to
   `0.3.0`. *(This is contract-artifact generation, not RM3 logic; it must exist before typed reasoning is built.)*
2. **`precedent_model`** — foundational, no dependencies beyond contracts; verifiable in isolation (determinism,
   versioning, relevance range).
3. **`retriever`** — depends on `precedent_model` + RM2 read side; verifiable via ranking determinism / top-K /
   tie-break / read-only.
4. **`reasoner`** — depends on contracts + `precedent_model` (version) + read-only `_hashing`; verifiable via
   signal derivation, report assembly, identity/hash, and the structural honesty check.
5. **`orchestration/precedent_runner`** — composes intake + retriever + reasoner; verifiable end-to-end
   (generalization, cautionary signal, empty corpus, read-only).
6. **Constitutional + regression gates** — boundary, determinism, read-only, RM1/RM2 zero-diff, contract-freeze.

Rationale: content before mechanism-consumer before identity before composition; the retriever (seed) is isolated
early so the reasoner (identity) never depends on retrieval internals — keeping the future Noetica extraction a
localized change.

## 7. Preservation checklist (how each required property is held)

| Preserved property | How this package holds it |
|---|---|
| **RM3 Specification** | Modules map 1:1 to spec §2 responsibilities, §4 outputs, §5 model; no new architectural idea added. |
| **RM3 Contracts** | Only `PrecedentReport`/`Entry`/`Signal` produced; report identity/hash/provenance exactly as the contract package; no contract changed. |
| **Constitutional boundaries** | Retriever = mechanism/extraction seed (isolated); reasoner = domain content/identity (Law 3); no store engine (Law 6); no MiniFlyWire (Law 4); never bypasses Velith (Law 9). |
| **Ownership rules** | RM3 owns manufacturing precedent content; the retrieval mechanism is MP-local seed for Noetica (Law 8), not RM3's identity. |
| **Determinism** | Versioned deterministic model; total-order ranking; per-mille relevance; deterministic signal; content-hash/`report_id`; volatile fields excluded. |
| **Read-only behavior** | Corpus read-only (RM2 reader); no writes, no persistence; report is advisory; RM1 plan/verdict untouched. |
| **Compatibility with RM1/RM2** | New package + one new orchestration file; RM1/RM2 imported read-only and byte-unchanged; enforced by a CI zero-diff gate. |

---

*RM3 engineering package. No code, pseudocode, JSON Schema, bindings, or implementation plan. On approval, the
implementation plan (milestones, files, tests, gates) is produced next, then implementation.*
