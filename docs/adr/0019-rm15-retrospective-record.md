# ADR 0019 — RM15 (Enriched-Oracle Compounding Re-Measurement) retrospective record

- **Status:** Accepted as a **retrospective record**. Recorded 2026-11-06 under Stage 0 record reconciliation (ADR-0021).
- **Date of the work:** 2026-10-16/17. **Date of this record:** 2026-11-06.
- **Deciders:** Project owner (Stage 0 ruling Q3: re-run, compare, then record without misrepresenting the result);
  Chief Systems Engineer (reproduction and record).
- **Constitution in force:** v1.1.0
- **Related:** `docs/milestones/RM15-completion-report.md`, `docs/milestones/evidence/rm15_report.json`, ADR-0009 (RM5),
  ADR-0010 (RM8 `constrained_model()`), tag `rm15-corpus-frozen`

## Context

RM15 was implemented in commits `30d8785`, `11a8c59`, `f2892ba` and `6571d84` (EC1–EC4) and measured locally on
2026-10-16T19:28:45Z. No specification, ADR, completion report, roadmap entry or changelog entry was committed, and the
measurement output was written only to the gitignored `artifacts/` folder. The 2026-11-06 Stage 0 audit found this gap.
The audit also found that "RM15" had been used elsewhere to mean "consume a real Velith `EngineeringResult`". In this
repository that milestone is RM6 (ADR-0009).

## Decision

1. RM15 is recorded as the **enriched-oracle compounding re-measurement**. The name RM15 does not refer to Velith
   integration.
2. The owner required reproduction before recording. The measurement was re-run in the Docker verifier against an
   exact export of HEAD `ab8cc44`. The identity `content_hash`
   (`sha256:e00acabaaa69f4bd69a5d159a56ffb29d8f201dcebe32aa909ed841ddedf5085`) matched the original. The only
   differing field was the volatile `provenance.produced_at`, which is excluded from identity by design.
3. The original output is committed byte-for-byte as `docs/milestones/evidence/rm15_report.json` (sha256
   `f4f61166aff87709e93bc315aecac08152fe13955ae2c8775927193416725a61`). `artifacts/` stays gitignored. The evidence
   copy lives under `docs/` as a frozen record, not as generated output.
4. The result is recorded as **mixed**:
   - **H1 met** (67/70), but only against a structurally abstaining baseline. It is not a paired improvement.
   - **H2 not met** (3/70 cautionary false alarms on MANUFACTURABLE controls).
   - **H3 met.**
   - **H4 not met** (curve 0 → 65 → 63 → 67).
5. No source, contract, test, fixture, dependency or CI change is made by this record.

## Consequences

- The record now matches the code (Law 18). Any later work on judgment false alarms should start from the three H2
  cases recorded in the evidence file.
- The RM15 specification and the governance notes that the source docstrings cite stay missing. This ADR does not
  reconstruct them, and it does not claim an independent review that never happened.

## Alternatives rejected

- **Recording without re-running.** This was rejected by the owner, because the result had not been reproduced.
- **Committing the 2026-11-06 re-run output instead of the original.** Rejected: the original is the measurement of
  record. The re-run is reproduction evidence and is described in the completion report.
- **Reporting RM15 as a success.** Rejected because H2 and H4 failed and H1 has a structural caveat.
