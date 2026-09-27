# Mini Prometheus

The **Manufacturing Intelligence** layer (Layer 4) of the MiniFlyWire → Noetica → Velith → Mini
Prometheus ecosystem. Mini Prometheus owns manufacturing **content**. It is designed to consume the
**Velith** engineering layer (and, through it, **Noetica** platform mechanisms) through pinned,
versioned packages. **That seam is not connected yet:** Velith and Noetica are not published as
packages, and `integrations/velith` targets a consumed *stub* contract that only test fixtures exercise.
It does **not** import MiniFlyWire (Law 4) and does **not** re-implement platform or engineering
mechanisms (Laws 3/6).

> Mini Prometheus is **not** a research project. The research is complete and frozen. This
> repository engineers the frozen theory into a working manufacturing intelligence.

**Status:** RM14 complete (`rm14-complete`, runtime `0.12.0`). RM1–RM14 deliver the manufacturing
pipeline on **engineer-declared** requests:
- `plan → verify → log` and verified experience reuse;
- precedent reasoning and engineering judgment;
- constraint reasoning and resource availability;
- declared operation times;
- deterministic, independently checked multi-job scheduling with downtime, an opt-in tie-break rule and
  sequence-dependent changeover.

Consuming a real Velith engineering result is gated on Noetica and Velith publishing packages. See
[`docs/ROADMAP.md`](docs/ROADMAP.md).

## Where to start

- **Frozen theory:** [`constitution/`](constitution/)
- **Repository architecture (read this first):** [`docs/architecture/repository-architecture.md`](docs/architecture/repository-architecture.md)
- **How we work:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Decisions:** [`docs/adr/`](docs/adr/)

## Architecture at a glance

```
frozen theory  →  stable contracts  →  implementations
 (constitution/)     (contracts/)         (src/, native/)
```

Implementations depend on `contracts/` only. **Velith** and **Noetica** are to be consumed as **pinned,
versioned package dependencies**, touched only through `src/mini_prometheus/integrations/`. Neither is
published yet; see the commented placeholders in `pyproject.toml`. MiniFlyWire is never imported (Law 4).

## Owned by this repository (manufacturing content)

Manufacturing planning & scheduling · factory/robotics/supply-chain/MES adapters ·
manufacturing digital-twin content (on Noetica's twin engine) · Sim2Real divergence tracking ·
experience collection · manufacturing runtime orchestration.

**Consumed, never owned:** the state substrate, provenance, `WorldModel`, twin engine, verification
protocol, memory/knowledge/routing frameworks (Noetica mechanisms); engineering ontology, physics,
CAD/sim, the engineering oracle and engineering reasoning content (Velith). See
[`constitution/HANDBOOK_v1.1.md`](constitution/HANDBOOK_v1.1.md) §2.4 and
[`docs/governance/constitutional-evolution-report.md`](docs/governance/constitutional-evolution-report.md).

## Build

Python ≥ 3.11; `jsonschema` is the only runtime dependency. The authoritative gate runs in the Docker
verifier (`docker/verifier.Dockerfile`), and `tools/verify_installed_wheel.py` checks the installed
wheel. `native/` is a placeholder for a future performance core; no native code exists yet. See
`CONTRIBUTING.md`.
