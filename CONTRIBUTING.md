# Contributing to Mini Prometheus

The authoritative reference is
[`docs/architecture/repository-architecture.md`](docs/architecture/repository-architecture.md).
This file is the operational summary.

## Engineering workflow (frozen)

```
Specification → Software Design → Implementation → Testing → Verification → Commit → Review
```

1. **Specification** — write/refine a spec in `specs/`. If it touches an interface, update
   `contracts/schemas/` in the *same* change set (schemas are the source of truth).
2. **Software Design** — record the approach in `docs/design/`; structural decisions get an ADR
   in `docs/adr/`.
3. **Implementation** — one atomic change per PR, scoped to a single owned package under `src/`
   (or one `native/` crate). Depend on `contracts/` only — never on a sibling package's internals.
4. **Testing** — extend `tests/unit`; if behaviour is contract-visible, extend `tests/contracts`.
5. **Verification** — CI (`.github/workflows/ci.yml`) is the non-skippable gate. Red CI blocks merge.
6. **Commit** — [Conventional Commits](https://www.conventionalcommits.org/). Reference the spec/ADR satisfied.
7. **Review** — routed by `CODEOWNERS`; scrutiny scales toward the contract spine.

## Hard rules

- **Contracts are the only cross-boundary dependency.** `implementations → contracts`, never the reverse.
- **External contracts vs internal APIs.** Only `contracts/` is public across boundaries. Everything else
  a package exposes is internal, unguaranteed, and marked (`_`-prefixed or `_internal`). Cross-package
  import of a non-contract symbol fails CI. (Arch doc §13.)
- **Manufacturing-content packages are peers.** `manufacturing_state`, `manufacturing_twin`,
  `manufacturing_constraints` depend on `contracts/` only — never on each other, orchestration, or
  integrations. `orchestration` is the sole composition root allowed to import concrete packages to wire
  them. (Arch doc §14.)
- **`integrations/` is adapters only — no business logic.** Adapters consume **Velith** (engineering entry)
  and **Noetica** (platform mechanisms) via versioned interfaces; **never MiniFlyWire** (Law 4). An adapter
  only translates upstream ↔ contract types; logic there is an architectural violation. (Arch doc §14.)
- **Layer hierarchy.** Constitution → Specification → Contract → Implementation → Verification; never skip
  a layer (no implementation assumption without a contract behind it). (Arch doc §12.1.)
- **Constitution is versioned.** `constitution/VERSION` (baseline 1.0.0) bumps only on amendment, cited by
  an ADR. (Arch doc §15.)
- **Generated bindings are never hand-edited.** `contracts/python` and `contracts/native` are
  produced from `contracts/schemas` by `tools/`. Hand edits fail CI.
- **Upstreams are pinned.** MiniFlyWire/Noetica/Velith are exact-pinned; bumps are isolated PRs
  owned by Runtime/Platform touching only `pyproject.toml` and `src/.../integrations/`.
- **No speculative folders.** Future-milestone directories exist only in the architecture doc until
  their milestone opens.
- **ADRs are append-only.** Supersede, never delete.

## Conventions

- Directories & Python modules: `snake_case`. Docs: `kebab-case.md`. ADRs: `NNNN-title.md`.
- `src/`-layout package (`import mini_prometheus`); tests live outside the package tree.
- Short-lived branches off protected `main`; linear history (rebase/squash); no direct pushes.
- Runtime SemVer and `contracts/VERSION` SemVer are independent. A breaking schema change is a
  contract MAJOR bump shipped with an updated compliance suite.
