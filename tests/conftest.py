"""Test harness setup + shared fixtures.

- Ensures the repo root, ``src`` and ``tests`` are importable (``contracts.python``,
  ``mini_prometheus``, ``support``).
- The project targets Python >= 3.11 (pyproject); this file provides a guarded ``enum.StrEnum``
  fallback so the suite also runs on 3.10 dev shells / CI runners. It is a no-op on 3.11+.
"""
from __future__ import annotations

import enum
import pathlib
import sys

_REPO = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(_REPO), str(_REPO / "src"), str(_REPO / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if not hasattr(enum, "StrEnum"):  # pragma: no cover - 3.10 fallback only
    class StrEnum(str, enum.Enum):
        pass

    enum.StrEnum = StrEnum  # type: ignore[attr-defined]

import pytest  # noqa: E402

import support  # noqa: E402


@pytest.fixture
def engineer_request():
    return support.build_request(support.load_json("engineer_request_machined_bracket.json"))


@pytest.fixture
def velith_result():
    from mini_prometheus._contracts import DesignArtifact, EngineeringResult, ProducedBy

    return EngineeringResult(
        result_id="44444444-4444-4444-4444-444444444444",
        content_hash="sha256:" + "a" * 64,
        verified=True,
        verifier=ProducedBy(component="velith-swe-verifier", version="0.1.0"),
        design_artifact=DesignArtifact(
            media_type="model/step",
            ref="55555555-5555-5555-5555-555555555555",
            content_hash="sha256:" + "b" * 64,
        ),
    )


@pytest.fixture
def store_path(tmp_path):
    return str(tmp_path / "episodes.jsonl")
