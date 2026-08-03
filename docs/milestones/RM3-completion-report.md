# RM3 Completion Report — Engineering Precedent Reasoning

- **Milestone:** RM3 (third runtime implementation milestone).
- **Status:** ✅ Complete and frozen — documented in the consolidated `0.4.0` release (2026-08-03). Runtime `0.4.0`.
- **Constitution in force:** v1.1.0. Contract suite: `0.4.0` (additive `PrecedentReport` set + the ratified RM1 correction).
- **Frozen artifacts:** `specs/milestones/RM3-engineering-precedent-reasoning.md` (spec), `contracts/RM3-contract-package.md`,
  `docs/design/RM3-engineering-package.md`, `docs/design/RM3-implementation-plan.md`, ADR-0007 (acceptance).

## 1. What RM3 delivered

A deterministic, read-only **precedent reasoning** capability: for a new `ManufacturingRequest`, Mini Prometheus
surfaces the most *relevant prior verified* manufacturing cases and derives a **supporting / cautionary / none**
signal from their verified verdicts. This is **compounding rung 2** — it generalizes RM2's exact reuse (near-zero
real-world hit rate) to *analogous* cases, so accumulated experience actually counts (`D = 0` ⇔ the RM2 exact case).

## 2. Delivered across the frozen milestones (RM3-M2…M5; M0/M1 = contracts + model)

| Milestone | Deliverable | Files (new) |
|---|---|---|
| **M0/M1** | Additive `PrecedentReport` contracts + deterministic versioned `precedent_model` | `contracts/.../precedent_report.schema.json` (+binding), `precedent/precedent_model.py` |
| **M2** | Retriever — extraction-seed ranking mechanism | `precedent/retriever.py`, `tests/unit/test_precedent_retriever.py` |
| **M3** | Reasoner — signal + `PrecedentReport` (RM3 identity) | `precedent/reasoner.py`, `tests/unit/test_precedent_reasoner.py` |
| **M4** | Composition entry | `orchestration/precedent_runner.py`, `tests/integration/test_precedent_reasoning.py` |
| **M5** | Boundary/freeze gates + CI | `tests/boundary/test_precedent_boundaries.py`, `.github/workflows/ci.yml` (edit) |

## 3. Verification & boundaries

- Deterministic total-order ranking (relevance desc, tie-break by episode `content_hash`); reproducible report
  `content_hash`/`report_id`; structural honesty (no query-verdict field).
- **Seed/identity separation (Law 3/8):** the retriever is the isolated extraction-seed *mechanism*; the reasoner
  is the domain *identity*. The retriever is the sole RM2-read-side consumer (boundary-test enforced).
- **No ML/embeddings/vector DB; no store/retention engine (Law 6); no MiniFlyWire (Law 4); read-only.**
- Additive: RM1/RM2 behavioral core byte-unchanged; contracts additive only.

## 4. Architectural debt (recorded, not implemented)

`docs/governance/RM3-architectural-debt.md`: the O(N) retriever is an intentional MP-local **extraction seed**;
large-scale indexed retrieval belongs to future **Noetica** extraction (Law 8, N.3) — not an RM3 task. The
signal-relevance threshold's canonical home in `precedent_model_version` is a flagged consolidation item.

## 5. Note on this report

RM3's runtime close-out was deferred at the time (work continued directly into the RM1 correction and RM4). This
report and ADR-0007 **retroactively** record RM3's acceptance as part of the consolidated `0.4.0` release; RM3's
code has been frozen and unchanged since it was committed.

*RM3 is closed. Do not modify unless a critical defect is discovered.*
