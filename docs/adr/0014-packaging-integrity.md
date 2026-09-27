# ADR 0014 — Packaging integrity: the installed wheel carries the contracts tree

- **Status:** Accepted (Director directive, 2026-09-27 — maintenance milestone between RM11 and RM12)
- **Date:** 2026-09-27
- **Deciders:** Project owner / Research Director (directive); Chief Systems Engineer (author)
- **Constitution in force:** v1.1.0
- **Related:** ADR-0013 (RM11), ADR-0010 (the RM1/RM2 byte-freeze), `tools/verify_installed_wheel.py`

## Context

Read-only audit of `rm11-complete` (Docker verifier, Python 3.11):

| Question | Finding |
|---|---|
| Wheel inclusion | `packages = ["src/mini_prometheus"]` — the wheel held only `mini_prometheus/` (49 files) + dist-info |
| Contracts packaging | `contracts/` is a namespace package at the repository root (no `__init__.py`): generated bindings `contracts/python/**` + JSON schemas `contracts/schemas/**`; **not in the wheel** |
| Runtime coupling | `_contracts.py` imports `contracts.python.*` (top level); `_validate.py` reads `Path(__file__).parents[2] / "contracts" / "schemas"` — the repository root in development, `lib/python3.11` when installed |
| RM10 CLI, installed, neutral cwd | `ModuleNotFoundError: No module named 'contracts'` |
| RM11 CLI, installed, neutral cwd | same |
| RM10 CLI, installed, cwd = repository (bindings importable) | `referencing.exceptions.NoSuchResource: …manufacturing_request.schema.json` |
| Repository / CI | unaffected: tests use the repo-root `pythonpath`; CI installs editable (`<repo>/src` on `sys.path`) |

Two defects, both from the installed layout: the bindings package is absent, and the schema lookup is relative to
the source tree. Both `_contracts.py` and `_validate.py` are byte-frozen RM1/RM2 files (CI zero-diff vs
`rm2-complete`), and the directive requires the repository and CI behavior to stay unchanged.

## Decision

Make the installed wheel reproduce the repository layout instead of changing any source file:

```
site-packages/
  mini-prometheus-runtime/            # not importable itself (hyphenated)
    src/mini_prometheus/…             # the package, byte-identical to src/mini_prometheus
    contracts/{python,schemas,…}      # the whole contracts tree, byte-identical
  mini_prometheus.pth                 # "mini-prometheus-runtime/src" and "mini-prometheus-runtime"
```

`pyproject.toml` (`[tool.hatch.build.targets.wheel]`): `only-include` = `src/mini_prometheus`, `contracts`,
`distribution/mini_prometheus.pth`; `sources` maps `src` → `mini-prometheus-runtime/src`, `contracts` →
`mini-prometheus-runtime/contracts`, `distribution` → the wheel root; `dev-mode-dirs = ["src"]`. The new file
`distribution/mini_prometheus.pth` holds the two `sys.path` entries (relative to site-packages). With this layout
`import mini_prometheus` and `import contracts.python` resolve from the runtime tree, and `_validate.py`'s
`parents[2]` is `mini-prometheus-runtime`, whose `contracts/schemas` exists — every source-relative path keeps its
repository meaning. Runtime `0.9.0 → 0.9.1`.

Editable installs (CI's `pip install -e`) put exactly `<repo>/src` on `sys.path`, as before (only the name of
hatch's helper `.pth` changes); the runtime `.pth` is never part of an editable wheel. The verifier Dockerfile copies
`distribution/` before building (hatch silently skips a missing include path); CI checks out the whole repository.

## Verification

- `tools/verify_installed_wheel.py` (Docker verifier): the wheel builds; carries the whole contracts tree and every
  source file byte-identical; the `.pth` holds both roots; nothing else is installed at the top level; it installs
  into a clean venv; from a neutral directory the installed package and contracts are imported (not the repository),
  the RM10 CLI prints `lead time: 108 min`, an invalid request is rejected by the frozen schema
  (`manufacturing_request violates contract at ['schema_version']`), the RM11 CLI prints `makespan: 68 min` with a
  schedule digest equal to the repository-source digest, and nothing is written to the working directory.
- `tests/boundary/test_packaging_integrity.py` pins the configuration, the `.pth`, the source-relative layout and the
  unchanged repository mode.
- Anti-vacuity: the pre-fix configuration (P1), a `.pth` without the contracts root (P2) and a wheel without the
  `.pth` (P3) each fail the static tests and the installed-wheel check.
- Full suite, goldens, mypy, import-linter, contract drift and the CI git gates unchanged; no `src/`, `contracts/` or
  CI file changed.

## Consequences

- `pip install mini_prometheus-0.9.1-py3-none-any.whl` gives working RM10 and RM11 CLIs anywhere.
- The installation relies on standard `.pth` processing of site-packages (virtual environments, system and user
  installs). Installs that bypass site processing (`pip install --target`, `python -S`) are not supported.
- The top-level names `mini_prometheus` and `contracts` become importable in the environment, as they already are in
  the repository (`contracts` is generic; a colliding distribution earlier on `sys.path` would shadow it).
- Pre-existing and unchanged (outside this milestone): the RM1 default episode store and the RM5 experiment corpus
  are resolved relative to the source tree, so an installed RM10 CLI appends its episode log under
  `site-packages/mini-prometheus-runtime/artifacts/`, and the RM5 experiment needs the repository's `tests/fixtures`.
  A configurable store location would be an RM1 behavior change and needs its own decision.

## Alternatives rejected

- **Ship `contracts` as a top-level package and resolve the schemas via the bindings' location** (the conventional
  layout): requires editing the byte-frozen `_validate.py` and amending the RM1/RM2 CI byte gate — both excluded by
  the directive (protected files and CI unchanged). It remains available if the Director later ratifies that gate
  amendment.
- **Install the schemas under the interpreter prefix (wheel `data`)** so `parents[2]` happens to match:
  platform- and layout-dependent.
- **Patch `_validate` at import time from `mini_prometheus/__init__.py`:** action at a distance.
