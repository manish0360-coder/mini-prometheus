# Responsibility Matrix

> **Authoritative source: `constitution/HANDBOOK_v1.1.md` (Constitution v1.1).** This file is a cited
> extraction for navigation; on any discrepancy the Handbook governs (P.2, Law 23). Amend only by CAP.

One owner per capability (HANDBOOK_v1.1 §9.2; ARCHITECTURE_DECISION STEP 5). Summary for the
Mini-Prometheus boundary (full matrix in the Handbook / boundary review):

| Capability | Owner | Mini Prometheus |
|---|---|---|
| State substrate / provenance / twin engine | **Noetica** | consumes |
| Verification protocol / harness | **Noetica** | uses; provides mfg checks (oracle) |
| Reasoning/planning **form**, memory/knowledge/context frameworks | **Noetica** | consumes |
| Engineering ontology, physics, CAD/sim, engineering oracle, engineering reasoning **content** | **Velith** | consumes via Velith API |
| Manufacturing planning/scheduling, factory/robotics/supply-chain/MES | — | **Owner** |
| Manufacturing digital-twin **content**, Sim2Real, experience collection | — | **Owner** |

Mini Prometheus never imports MiniFlyWire (Law 4) and never bypasses Velith for engineering (Law 9).
