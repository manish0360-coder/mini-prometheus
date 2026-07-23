# ADR 0004 — Conform repository to HANDBOOK_v1.1 (ratified CAP-0001)

- **Status:** Accepted (records ratified **CAP-0001**)
- **Date:** 2026-07-23
- **Deciders:** Project owner **Mack** (ratifier, Laws 22/23); Chief Systems Engineer (author/executor)
- **Supersedes:** the `src/` ownership charter of ADR-0001; the RM1 scope of ADR-0003
- **Constitution version in force:** **1.1.0** (adopted from Handbook v1.1)
- **Evidence:** `docs/governance/constitutional-evolution-report.md`; `docs/governance/CAP-0001-adopt-handbook-and-conform-repository.md`; primary sources VISION.md, DECISIONS.md (D1–D25), ARCHITECTURE_DECISION.md, HANDBOOK_v1.1.md.

## Context

An architectural archaeology across five repositories (MiniFlyWire, Noetica-agent-lab, Velith,
pcos-samantha, mini-prometheus) plus the founding VISION/DECISIONS ledgers reconstructed the project's
legal history. It established, on evidence rather than self-declaration, that HANDBOOK_v1.1 governs, and
that the `mini-prometheus` repository's ownership claims were the single genuine conflict (Report Part 5,
Conflict C1) — an outlier contradicted by VISION §5.2, DECISIONS D9/D11, ARCHITECTURE_DECISION STEP 5–6,
and Handbook Laws 3/4/6/9. Verdict: **(3) Repository ownership correction required** — not a redesign,
because the prior evolution is internally consistent and the machinery is already Handbook-aligned.

The project owner ratified the correction: *"you have full permission to make the repository match the
constitutional evolution it reconstructed."*

## Decision (executed under this ratification)

1. **Governance.** HANDBOOK_v1.1 is the governing Constitution, transcribed verbatim into
   `constitution/HANDBOOK_v1.1.md` (with `ARCHITECTURE_DECISION.md`); the seven topic files are cited
   extractions; `constitution/VERSION` = **1.1.0**.
2. **Ownership.** Mini Prometheus owns manufacturing **content** only. `src/` packages renamed:
   `situation_state → manufacturing_state`, `world_model → manufacturing_twin`,
   `constraint_network → manufacturing_constraints`. Docstrings state they are content on Noetica/Velith
   mechanisms, not re-implementations.
3. **Dependencies.** `src/mini_prometheus/integrations/miniflywire/` **removed** (Law 4). `integrations/`
   consumes **Velith** (engineering entry) and **Noetica** (platform mechanisms) only.
4. **Withdrawals.** The M2/M3 "Engineering cognition/reasoning" packages are withdrawn (Velith content).
   `specs/interfaces/situation-state.md` is withdrawn; RM1 is re-scoped to a manufacturing-content slice.
5. **Docs.** `README.md`, `CODEOWNERS`, `constitution/README.md`, and `docs/architecture/repository-architecture.md`
   corrected; the architecture doc carries a superseding banner over its former ownership charter.

## Consequences

- The repository now matches the reconstructed constitution. Repository *machinery* (contract spine,
  five-layer hierarchy, dependency rules, ADR/CAP governance, no-speculative-folders) is unchanged.
- **RM1 must be re-specified** as manufacturing content (candidate: manufacturing planning/scheduling
  seed, or manufacturing twin-state content) over consumed interfaces. Prerequisite (CAP-0001 Field 8):
  confirm Velith and Noetica publish pinned, consumable packages (Velith is at M0–M1).
- Provenance preserved: ADR-0001/0003 and the withdrawn spec remain in the record (Law 18; §11.6
  "decisions never edited away silently").

## Alternatives rejected

Terminology-only reconciliation (insufficient — real Law 4/6/9 violations); fundamental redesign
(unjustified — prior evolution is internally consistent); keeping the charter-summary ownership
(contradicted by four governing documents). Full rationale in CAP-0001 Field 3 and Report Part 5.
