# ADR 0023 — Shop-owner pilot demonstrator (`demo/pilot/`)

- **Status:** Accepted
- **Date:** 2026-11-07
- **Deciders:**
  - Project owner: approved Option A (a static demonstrator inside this repository) and authorised this ADR and
    the implementation plan, with decisions D1–D3.
  - Research Director: the shop-facing UI placement audit and its recommendation. This is input, not ratification
    (Law 22).
  - Chief Systems Engineer: placement audit, ADR, implementation and verification.
- **Constitution in force:** v1.1.0. Ownership per CAP-0001 (affirmed in ADR-0021 Q1).
- **Related:** ADR-0001 (repository architecture, rules 4–5), ADR-0022 (MP-S1), the real-shop pilot plan (outreach
  and consent; not in this repository).

## Context

The real-shop pilot needs something a workshop owner can understand in about five minutes:
- what Mini Prometheus does with a workshop's declaration;
- why it answers "yes" or "no" for a job;
- what it does not know.

Today the only interface is the CLI. The placement audit found:
- No repository has an HTTP service, authentication or storage that a shop-facing application could sit on.
- Building one now would be speculative (repository-architecture rule 5). It would also risk Law 6, because a service
  runtime may be a Noetica mechanism.
- A second implementation of the verdict logic in the browser would duplicate MP logic (Law 13) and could disagree
  with MP-S1.

## Decision

1. **A new top-level `demo/` directory.** It traces to Handbook §2.4, "Consumers: end users" (repository-architecture
   rule 4). It holds one static demonstrator, `demo/pilot/`.
   - No build step.
   - No backend, authentication, database, hosting or separate repository.
   - Not part of the wheel. `pyproject.toml` already includes only `src/mini_prometheus`, `contracts` and the `.pth`
     file.
2. **The page displays only actual MP-S1 CLI output.**
   - `demo/pilot/capture.py` runs the shipped single-job CLI entry point in-process. The command is
     `python -m mini_prometheus.orchestration.runner <job> --capability-model-file <shop>`.
   - The episode store is redirected to a temporary file, so nothing is written to the repository.
   - It records the stdout verbatim (only the temporary store path is redacted), plus the plan steps and verdict from
     the episode the CLI stored.
   - `snapshots/MANIFEST.json` records:
     - every source path with its SHA-256;
     - the Mini Prometheus commit;
     - the exact command for each case.
   - `index.html` reads `snapshots/data.js`. It contains no verdict logic and no verdict or reason-code literal.
3. **Synthetic data, labelled as such.**
   - The shop is a new synthetic declaration, `inputs/shop.example_workshop.json` (D2). It is derived from the
     three-cell synthetic shop and adds per-capability tolerances, so that a tolerance refusal can be shown.
   - Its `evidence_class` is `synthetic`.
   - The four jobs are synthetic `ManufacturingRequest`s.
   - Every screen distinguishes four kinds of content: example data, shop-declared information, actual CLI output,
     and explanation text.
4. **Four screens:** the workshop, a job, the check, and what it does not know.
   - **Lead time is excluded (D3).** The example jobs declare no durations, and the page offers no cost, cycle-time
     or delivery prediction.
   - The page shows nothing that suggests Velith geometry, drawing interpretation or live evaluation.
5. **Plain language, ready for Hindi.**
   - Every visible word lives in `demo/pilot/strings.js` under `en`.
   - Hindi is added by filling `hi` with the same keys. Missing keys fall back to English.
   - The language switch appears only once `hi` has a key.
6. **A consistency gate.** `tests/boundary/test_demo_pilot.py` checks that:
   - every manifest hash matches its file;
   - re-running the capture reproduces every snapshot byte for byte;
   - each displayed status and reason equals both the printed CLI line and the stored episode;
   - every code shown has a label;
   - the page holds no verdict literal and loads nothing from the network;
   - the shop input is synthetic and passes the real MP-S1 loader;
   - no lead-time or other unsupported prediction is presented.

   `docker/verifier.Dockerfile` gains one line, `COPY demo/ ./demo/` (D1), so the gate runs in the authoritative
   verifier.

## Captured result (Mini Prometheus `f020608`)

| Example job | Status | Reason |
|---|---|---|
| Aluminium bracket | `MANUFACTURABLE` | — |
| Turned steel shaft | `NOT_MANUFACTURABLE` | `CAPABILITY_MISSING` (no lathe) |
| Brass cover | `NOT_MANUFACTURABLE` | `MATERIAL_UNSUPPORTED` |
| Precision plate (0.01 mm) | `NOT_MANUFACTURABLE` | `TOLERANCE_UNSUPPORTED` (milling holds 0.02 mm) |

Shop declaration hash: `sha256:77f39940f9a613a34b025bb045e0cda326165a1c44f72e61f54f2d342ef33a07`.

## Consequences

- **No existing contract, schema, source file, gate or ownership boundary changes.** Runtime and contract versions
  are unchanged.
  - The only change to existing files is the Dockerfile line.
  - The RM2 and RM4 byte gates are unaffected.
- **If MP-S1 behaviour changes, the demonstrator test fails** until the snapshots are re-captured with
  `python demo/pilot/capture.py --commit <sha>` and reviewed. The screens cannot drift silently.
- **The demonstrator is evidence of presentation only.** It is not real-shop validation, and MP-E1 stays blocked.
- **Deferred until a real shop is using it:**
  - live evaluation from a UI, which first needs a CAP or ADR on where a service runtime belongs;
  - accounts;
  - storage of a shop's declarations;
  - editing the declaration in the UI;
  - hosting;
  - Velith-backed views.
- **Real-shop outreach remains the critical path.** This demonstrator does not delay it.
