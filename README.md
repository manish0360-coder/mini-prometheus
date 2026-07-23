# Mini Prometheus

The **Manufacturing Intelligence** layer (Layer 4) of the ecosystem. Mini Prometheus owns
manufacturing **content** and consumes the **Velith** engineering layer (and, transitively,
**Noetica** platform mechanisms) through versioned interfaces. It does **not** import MiniFlyWire
(Law 4) and does **not** re-implement platform or engineering mechanisms (Laws 3/6).

> Mini Prometheus is **not** a research project. The research is complete and frozen. This
> repository engineers the frozen theory into a working manufacturing intelligence.

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

Implementations depend on `contracts/` only. **Velith** and **Noetica** are consumed as **pinned,
versioned package dependencies**, touched only through `src/mini_prometheus/integrations/`. MiniFlyWire
is never imported (Law 4).

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

Python orchestration + Rust/C++ performance core. See `CONTRIBUTING.md` (build instructions land
with the first implementation milestone).
