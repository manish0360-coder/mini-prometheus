"""Packaging integrity (ADR-0014): the installed wheel reproduces the repository layout.

The runtime imports the generated bindings as ``contracts.python.*`` and reads the schemas at
``_validate.py``'s ``parents[2] / "contracts" / "schemas"`` (the repository root in development).
The wheel therefore installs ``mini-prometheus-runtime/{src/mini_prometheus, contracts}`` and a
``mini_prometheus.pth`` that puts ``mini-prometheus-runtime/src`` and ``mini-prometheus-runtime`` on
``sys.path``; editable installs keep exactly ``<repo>/src``. The end-to-end build/install/CLI check
is ``tools/verify_installed_wheel.py`` (run in the Docker verifier); these tests pin the static
configuration so a wheel without the contracts tree or the .pth cannot be built by accident.
"""

from __future__ import annotations

import pathlib
import tomllib
from pathlib import PurePosixPath

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNTIME = "mini-prometheus-runtime"


def _wheel_config() -> dict:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]


def _pth_lines() -> list[str]:
    return (ROOT / "distribution" / "mini_prometheus.pth").read_text(encoding="utf-8").split()


def test_wheel_installs_the_repository_layout_and_the_pth():
    config = _wheel_config()
    assert config["only-include"] == [
        "src/mini_prometheus",
        "contracts",
        "distribution/mini_prometheus.pth",
    ]
    assert config["sources"] == {
        "src": f"{RUNTIME}/src",
        "contracts": f"{RUNTIME}/contracts",
        "distribution": "",
    }
    assert "packages" not in config and "force-include" not in config
    assert all(
        (ROOT / path).exists() for path in config["only-include"]
    )  # hatch skips missing paths


def test_editable_installs_keep_exactly_the_source_root():
    assert _wheel_config()["dev-mode-dirs"] == ["src"]


def test_pth_puts_the_package_root_and_the_contracts_root_on_sys_path():
    assert _pth_lines() == [f"{RUNTIME}/src", RUNTIME]


def test_installed_layout_preserves_every_source_relative_path():
    sources = _wheel_config()["sources"]
    src, contracts = PurePosixPath(sources["src"]), PurePosixPath(sources["contracts"])
    assert (
        src.parent == contracts.parent == PurePosixPath(RUNTIME)
    )  # siblings, as in the repository
    validate = src / "mini_prometheus" / "_validate.py"
    assert validate.parents[2] / "contracts" == contracts  # _validate: parents[2]/contracts/schemas
    assert _pth_lines() == [str(src), str(contracts.parent)]


def test_repository_mode_is_unchanged():
    from mini_prometheus import _validate

    assert _validate._SCHEMAS == ROOT / "contracts" / "schemas" and _validate._SCHEMAS.is_dir()
