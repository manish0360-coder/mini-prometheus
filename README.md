# Mini Prometheus

The flagship **AI Manufacturing Intelligence** runtime. Mini Prometheus is the runtime
orchestration layer that integrates three constitutionally frozen, independently released
upstreams — **MiniFlyWire**, **Noetica**, and **Velith** — and owns the engineering-cognition
runtime built on top of them.

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

Implementations depend on `contracts/` only. The three upstreams are consumed as **pinned,
versioned package dependencies** and are touched only through `src/mini_prometheus/integrations/`.

## Owned by this repository

Engineering cognition · Situation State · Engineering World Model · Constraint Network ·
Runtime orchestration · Engineering reasoning · Multi-disciplinary coordination · AI Manufacturing workflow.

## Build

Python orchestration + Rust/C++ performance core. See `CONTRIBUTING.md` (build instructions land
with the first implementation milestone).
