# docs/research/

Research records. A research note is **evidence and analysis, not a decision**. Nothing here is ratified unless an ADR or
CAP says so.

| Note | Date | Status | Summary |
|---|---|---|---|
| [RM3-research-report.md](RM3-research-report.md) | 2026-07-28 | Input to RM3 (ADR-0007) | Engineering precedent reasoning research |
| [verification-contract-gap-audit.md](verification-contract-gap-audit.md) | 2026-10-23 | **Proposed, not ratified**; partly corrected by the next note | Judgment does not condition on recorded verification status |
| [rm4-verification-provenance-decision.md](rm4-verification-provenance-decision.md) | 2026-10-23 | **Proposed, not ratified** | Recommends "Decision A": keep RM4 behaviour, clarify the word "verified". The wording change has not been made. |
| [next-capability-gap-assessment.md](next-capability-gap-assessment.md) | 2026-10-23 | **Proposed, not ratified** | Capability-model version is a label not bound to content (addendum A1–A7). Input to the MP-S1 candidate. |
| [capability-to-evidence-assessment.md](capability-to-evidence-assessment.md) | 2026-10-23 | **Proposed, not ratified** | Compares STEP interpretation, a geometry check, and real Velith integration |
| [artifact-blocker-sourcing.md](artifact-blocker-sourcing.md) | 2026-10-23 | **Proposed, not ratified** | Names MFCAD++ (CC BY) as a possible public source of labelled STEP parts. No data was downloaded. |

## Notes on the 2026-10-23 records

- They were moved verbatim from the untracked `research/` folder on 2026-11-06 (ADR-0021, ruling Q4). Paths inside
  them that start with `research/` now resolve under `docs/research/`.
- Several notes describe Velith as `0.0.0` with no `EngineeringResult` API. That was accurate when they were written
  but is now stale. On 2026-11-06 Velith had tag `v0.1.0` and an untagged `0.2.0` with a geometry-facts result (ADR-0021).
- `research/rm6-api0-compat-audit.md`, cited by the unmerged ADR-0018 on branch `rm6.0-admission`, was not found and
  is not here.
