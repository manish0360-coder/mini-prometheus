# ADR 0023 — Shop-owner pilot demonstrator in `demo/pilot/`

- **Status:** Accepted
- **Date:** 2026-11-07 (revised 2026-11-07; see "Revision record")
- **Deciders:**
  - Research Director: Option A approval with boundaries 1–9. This is input, not ratification (Law 22).
  - Project owner: authorisation "as recommended", with D1–D3.
  - Chief Systems Engineer: author.
- **Constitution in force:** v1.1.0. Ownership per CAP-0001 (affirmed ADR-0021 Q1). No CAP: no ownership change.
- **Related:** Handbook §2.4, N.1, Laws 4/5/6/13/18; `docs/architecture/repository-architecture.md` rules 4–5;
  ADR-0022 (MP-S1)

## Context

A read-only audit of all four repositories (2026-11-07) found that no repository has a shop-facing UI, an HTTP API,
authentication or deployment. The only web UI in the ecosystem is MiniFlyWire's research visualiser, which can never
become production (Law 4).

Handbook §2.4 names Mini Prometheus's consumers as "End users; physical factory and industrial systems"
(`constitution/HANDBOOK_v1.1.md`, §2.4 "Consumers", line 532). A manufacturing-facing explanation for a workshop
owner is therefore Mini Prometheus content.

Repository-architecture rule 4 requires every top-level directory to trace to a frozen clause, and rule 5 forbids
speculative folders. So the folder opens by this ADR.

## Decision

1. **New top-level folder `demo/`,** tracing to Handbook §2.4 (Consumers: end users). Its first and only content is
   `demo/pilot/`: a static, build-free, four-screen demonstrator for a pilot conversation with a shop owner.
2. **The page displays captured output of the existing MP-S1 CLI** (`mini_prometheus.orchestration.runner`
   `--capability-model-file`) on synthetic fixtures.
   - It never computes a verdict and never re-implements MP logic. Law 13 says a concept has one representation.
   - It offers only pre-captured cases.
3. **Provenance (Law 18).** `snapshots/MANIFEST.json` records, for every case:
   - the input paths and their SHA-256;
   - the exact command and the MP commit;
   - the captured stdout and its SHA-256;
   - the parsed status, reasons and hashes.

   A test re-runs the capture and requires byte equality with the committed snapshots. The temporary episode-store
   path is the only thing excluded, and it is redacted.
4. **Labels.** Every element on screen is labelled as one of:
   - synthetic example;
   - shop-declared (not independently verified);
   - actual MP-S1 output on example data;
   - explanation text;
   - limitation.
5. **Not shown, and not implied:**
   - Velith geometry;
   - drawing or STEP interpretation;
   - live evaluation;
   - cost, cycle-time or lead-time prediction;
   - real shop data.
6. **No new infrastructure:** no backend, authentication, database, hosting, framework, build step, dependency or
   separate repository.
7. **Packaging and gates.**
   - `demo/` is outside the wheel (`only-include`) and outside the byte-freeze gates.
   - The verifier image gains one `COPY demo/ ./demo/` line so the consistency test runs in Docker (D1).
   - No source, contract, schema or existing test changes.
8. **Text.** Text lives in one string table keyed by id, so a language can be added without touching layout or
   data. English came first; Hindi was added in the 2026-11-07 revision.

Owner decisions on authorisation:
- **D1:** the Dockerfile line above.
- **D2:** a new synthetic example shop, `inputs/shop.example_workshop.json`. It is derived from
  `three_cell_synthetic`, with mill and drill tolerance minimums added so that a tolerance refusal can be shown.
- **D3:** lead time is left out of the pilot screens.

## Consequences

- **An honest, reproducible explanation exists for the pilot visit.** It can never drift from MP-S1 silently,
  because the consistency test re-runs the CLI.
- **It is not a product, and not a precedent for a backend.** A live application needs its own decision first:
  whether a service runtime is a Noetica mechanism (Law 6: domains consume platform mechanisms and do not rebuild
  them) or MP composition.
- `repository-architecture.md` §3, §4 and §5 gain one `demo/` entry, with its trace.

## Alternatives rejected

- **A separate repository:** a fifth project, contract drift, and nothing to deploy.
- **Hosting in another repository:** Laws 4 and 5, and the Velith boundary.
- **A JavaScript re-implementation of the oracle for interactivity:** Law 13.

## Captured result (Mini Prometheus `f020608`)

| Example job | Status | Reason |
|---|---|---|
| Aluminium bracket | `MANUFACTURABLE` | — |
| Turned steel shaft | `NOT_MANUFACTURABLE` | `CAPABILITY_MISSING` (turning is declared not in-house) |
| Brass cover | `NOT_MANUFACTURABLE` | `MATERIAL_UNSUPPORTED` |
| Precision plate (0.01 mm) | `NOT_MANUFACTURABLE` | `TOLERANCE_UNSUPPORTED` (milling holds 0.02 mm) |

Shop declaration hash: `sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07`.

## Revision record

**2026-11-07, record correction.** The Decision and Consequences committed in `bc75bbb` had been rewritten from
memory after a context reset, and the commit report said so.
- This revision restores the text of the approved draft, taken word for word from the session record.
- It adds the owner decisions D1–D3, and the date and line reference for the §2.4 citation.
- Each citation was checked against `constitution/HANDBOOK_v1.1.md`:
  - §2.4 "Consumers" (line 532);
  - Laws 4, 5 and 6 (lines 1142–1146);
  - Law 13 (line 1160);
  - Law 18 (line 1170).
- One factual error is corrected: `bc75bbb` credited the Option A approval to the project owner, but it was the
  Research Director's. The owner authorised the implementation.
- The decision itself did not change.

**2026-11-07, demonstration-ready UI (Research Director instruction, owner-approved with amendments).**
- **Interface:** one design system, step navigation with Back/Next and the keyboard arrows, and a persistent
  example-data badge. Phone and desktop layouts.
- **Check screen:** a "What was compared" panel and plain machine names.
- **Bookmarks:** `?lang=`, `?job=` and `?theme=` bookmark a starting state.
- **Language:** complete Hindi text. The page itself is still display only:
  - the comparison panel places declared inputs side by side and compares nothing;
  - every status and reason still comes from `snapshots/data.js`.
- **The snapshots were not re-captured.** They are byte-identical to `bc75bbb`, and every manifest hash is unchanged.
- **The consistency test now also requires:**
  - the same key set in English and Hindi;
  - a label for every machine, material and operation target shown.
- **The Hindi is a first draft.** A Hindi-speaking person must read it before it is shown to a shop owner.
