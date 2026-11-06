# ADR 0021 — Stage 0 record reconciliation and owner rulings

- **Status:** Accepted
- **Date:** 2026-11-06
- **Deciders:** Project owner (rulings Q1–Q5, Laws 22/23); Chief Systems Engineer (forensic audit, record). The audit
  is AI-authored analysis and is a recommendation only.
- **Constitution in force:** v1.1.0
- **Related:** CAP-0001, ADR-0004, ADR-0009, ADR-0019 (RM15), ADR-0020 (RDAI-1); local branch `rm6.0-admission`
  (`c2e3b98`, holds an unmerged ADR-0018)

## Context

The owner commissioned a read-only forensic audit of the repository at HEAD `ab8cc44`. The audit verified that the
software is healthy: 696 tests pass in the Docker verifier, mypy is clean and all import contracts are kept. It also
found that the written record had diverged from Git:

- `docs/ROADMAP.md` and `CHANGELOG.md` stopped at RM14.
- RM15 (four commits and a tag) and RDAI-1 (two commits) had no ADR, report or roadmap entry.
- RM15's measurement output existed only in the gitignored `artifacts/`.
- Five research notes in `research/` were untracked.
- ADR-0018 (RM6.0) sat "Accepted" on an unpushed local branch. It cites `research/rm6-api0-compat-audit.md`, which
  could not be found.
- The roadmap still said "pending" for the `rm4-complete` and `rm14-complete` tags, which exist.

The audit also found that the commissioning directive described Mini Prometheus as owning the Situation State,
Engineering World Model, Constraint Network, engineering cognition and provenance management. CAP-0001 overturned that
ownership model in July.

## Owner rulings (2026-11-06)

1. **Q1 — Ownership: CAP-0001 stands.** Mini Prometheus owns manufacturing content. The state substrate and provenance
   mechanisms are Noetica's. The engineering world model, geometry and engineering verification are Velith's. The
   directive's ownership list is not adopted, and no new CAP is opened.
2. **Q2 — RM6.0: parked.** Branch `rm6.0-admission` stays unmerged. Its premise ("no physical design media type exists
   in Velith") is stale. A read-only check on 2026-11-06 found that Velith has tag `v0.1.0` (API-0, software) and an
   untagged `0.2.0` on its `origin/main` that emits `application/vnd.velith.geometry-facts+json`. Its `model/step`-only
   allowlist would reject that type. ADR number **0018 is reserved** for that branch so that the numbers never collide.
   RM6.0 is re-specified when Velith work resumes.
3. **Q3 — RM15 and RDAI-1: record after reproduction.** RM15 was re-run in the Docker verifier at HEAD. Its identity hash
   reproduced exactly, and it is recorded with its mixed result in ADR-0019. RDAI-1 is recorded from its actual history
   in ADR-0020, without claiming independent verification.
4. **Q4 — Research notes: admitted as proposed records.** The five notes move verbatim from `research/` to
   `docs/research/` and are indexed in `docs/research/README.md` as **proposed, not ratified**. This includes the RM4
   "Decision A" wording recommendation, which stays unratified.
5. **Q5 — Real shop data: not yet available.** No participating shop or historical jobs with known outcomes exist.
   - The next candidate milestone, **MP-S1 Declared Shop Capability Model**, may proceed to specification on
     synthetic shop models. Where useful, it may also use public machine specifications, labelled as **non-real
     evidence**.
   - Public specifications must never be presented as real shop data.
   - **MP-E1** (real-world evaluation) is **blocked** until a shop and historical jobs with known outcomes are
     obtained.

## Decision

Reconcile the record in one documentation-only commit:

- the RM15 completion report and frozen evidence JSON (ADR-0019);
- the RDAI-1 retrospective (ADR-0020);
- this ADR;
- the research notes moved and indexed;
- the ADR index, roadmap, changelog and README status corrected.

No source, contract, schema, test, fixture, dependency, CI or version change is made.

## Consequences

- Git, the roadmap and the changelog agree again (Law 18).
- MP-S1 is the next candidate but is **not yet authorised for implementation**. It follows the project workflow:
  research, then architecture review, then specification, then owner authorisation.
- RM6 and RM7 stay planned and gated. Velith work is paused by the owner, independent of Velith's release status.
- The milestone naming "MP-S1 / MP-E1" is used provisionally. RM15 is not reused for integration.
