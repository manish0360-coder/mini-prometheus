"""MP-S1 evolved regression gates (spec §9, ratified in ADR-0022).

1. ``orchestration/reuse_runner.py`` left the CI RM1/RM2 byte-diff set against ``rm2-complete``. It is
   re-frozen here at its ratified content. The ONLY difference from ``rm2-complete`` is the MP-S1
   reuse-key change (two lines, recorded in ADR-0022). Any further edit trips this gate. It runs in
   CI and in the Docker verifier (no ``.git`` needed).
2. The 0.4.0 contracts manifest (generated once from ``rm14-complete`` by the committed probe) is frozen
   by its own digest and the probe's. ``assert_0_4_0_contracts_intact`` proves file by file that the
   0.4.0 suite is unchanged except one structurally checked additive property.
3. Guarantee 1 of spec §3.7: the verdict paths never import precedent or judgment (AST scan,
   mirroring the new import-linter contract).
"""

from __future__ import annotations

import ast
import hashlib
import pathlib

from contracts_manifest_check import MANIFEST_PATH, assert_0_4_0_contracts_intact, manifest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "mini_prometheus"

REUSE_RUNNER_RATIFIED_SHA256 = "7e45fee7b3eea3c8374f3ce1a10625cfcfe31d12ea59576de9e9bcc62c518479"
MANIFEST_SHA256 = "34f179739550f8ea19ddc74bbe3cb8067f2afb18c21c11f8d7388e8dfdd6f407"
PROBE_SHA256 = "1f4e8fbb30417345f5245b447047e456621ef172b4963343d766432f3412ac63"
RM14_COMPLETE = "b040e35a75462901a448da0ba984712ef6b40133"


def _lf_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_reuse_runner_is_frozen_at_its_ratified_mp_s1_content():
    path = SRC / "orchestration" / "reuse_runner.py"
    assert (
        _lf_sha256(path) == REUSE_RUNNER_RATIFIED_SHA256
    ), "reuse_runner.py changed after ratification"


def test_manifest_is_the_frozen_rm14_complete_one():
    assert (
        _lf_sha256(MANIFEST_PATH) == MANIFEST_SHA256
    ), "the frozen contracts manifest was modified"
    assert manifest()["generated_from"] == {"tag": "rm14-complete", "commit": RM14_COMPLETE}
    assert manifest()["suite_version"] == "0.4.0"
    probe = ROOT / "tests" / "contracts_manifest_probe.py"
    assert _lf_sha256(probe) == PROBE_SHA256 == manifest()["probe_sha256"], "the probe was modified"


def test_0_4_0_contracts_are_intact_except_the_one_additive_property():
    assert_0_4_0_contracts_intact()


def test_suite_version_is_the_ratified_0_5_0():
    assert (ROOT / "contracts" / "VERSION").read_text(encoding="utf-8").strip() == "0.5.0"


_VERDICT_PATHS = [
    *sorted((SRC / "manufacturing_constraints").glob("*.py")),
    *sorted((SRC / "manufacturing_planning").glob("*.py")),
    *sorted((SRC / "manufacturing_scheduling").glob("*.py")),
    *sorted((SRC / "shop_declaration").glob("*.py")),
    SRC / "orchestration" / "runner.py",
    SRC / "orchestration" / "reuse_runner.py",
    SRC / "orchestration" / "schedule_runner.py",
    SRC / "orchestration" / "verdict_trace.py",
    SRC / "orchestration" / "shop_model_file.py",
]
_FORBIDDEN = (
    "mini_prometheus.precedent",
    "mini_prometheus.judgment",
    "precedent_runner",
    "judgment_runner",
)


def test_verdict_paths_never_import_precedent_or_judgment():
    for path in _VERDICT_PATHS:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else []
            )
            for name in names:
                assert not any(bad in name for bad in _FORBIDDEN), f"{path.name} imports {name}"
