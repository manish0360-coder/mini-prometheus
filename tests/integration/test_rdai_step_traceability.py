"""RDAI-1 C2 integration: a real STEP file's byte-identity survives end-to-end into the serialized
``ManufacturingEpisode`` JSONL, through the UNCHANGED RM1 pipeline (intake -> plan -> verify -> emit).

No production code is added by C2: the frozen path already carries ``design_artifact_ref`` opaquely. The
expected SHA-256 is computed INDEPENDENTLY (stdlib ``hashlib`` over the fixture bytes), never taken from
``ingest()``. Nothing here evaluates geometry or asserts manufacturability of the solid.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.artifact_intake import step_intake
from mini_prometheus.artifact_intake.step_intake import UnsupportedArtifactError
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.orchestration import runner

from support import FIXED_TIME

_STEP = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "step"
_VALID = _STEP / "valid_minimal.step"


def _independent_hash(path: pathlib.Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _request_with(ref, *, request_id: str) -> ManufacturingRequest:
    # Declared intent chosen to yield a grounded MANUFACTURABLE verdict under the default model
    # (all capabilities present, supported material); RM8 precedence/tolerance are inert here.
    return ManufacturingRequest(
        schema_version="1.0.0",
        request_id=request_id,
        material="Aluminum 6061",
        stock_form=StockForm.block,
        declared_operations=[
            DeclaredOperation(op=ProcessOp.cut_stock),
            DeclaredOperation(op=ProcessOp.face_mill),
            DeclaredOperation(op=ProcessOp.inspect),
        ],
        quantity=10,
        tolerances=Tolerances(general_tolerance_mm=0.1),
        step_artifact_ref=ref,
    )


def _last_record(store_path: str) -> dict:
    lines = [ln for ln in pathlib.Path(store_path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 1, f"expected exactly one emitted episode, got {len(lines)}"
    return json.loads(lines[0])


def test_step_byte_hash_survives_verbatim_into_serialized_episode(store_path):
    ref = step_intake.ingest(_VALID)
    expected_hash = _independent_hash(_VALID)          # independent oracle, not via ingest
    assert ref.content_hash == expected_hash

    res = runner.run_from_request(
        _request_with(ref, request_id="aaaaaaaa-0000-4000-8000-000000000001"),
        produced_at=FIXED_TIME, store_path=store_path,
    )
    assert res.status == "MANUFACTURABLE" and not res.is_error

    rec = _last_record(store_path)
    dar = rec["design_input"]["design_artifact_ref"]
    assert dar == {"media_type": "model/step", "id": ref.id, "content_hash": expected_hash}


def test_artifact_hash_is_committed_in_design_and_episode_identity(store_path):
    ref = step_intake.ingest(_VALID)
    expected_hash = _independent_hash(_VALID)
    runner.run_from_request(
        _request_with(ref, request_id="aaaaaaaa-0000-4000-8000-000000000002"),
        produced_at=FIXED_TIME, store_path=store_path,
    )
    ep = load(store_path)[-1]                           # reconstruct via the frozen RM2 reader
    assert ep.design_input is not None
    assert ep.design_input.design_artifact_ref is not None
    assert ep.design_input.design_artifact_ref.content_hash == expected_hash
    # Cryptographic commitment: the byte-hash is folded into the design identity -> design_ref.
    assert h.content_hash(h.design_input_identity(ep.design_input)) == ep.design_ref.content_hash


def test_request_without_step_artifact_omits_design_artifact_ref(store_path):
    # Contrast/negative: no artifact ingested -> the serialized record carries NO design_artifact_ref,
    # so a verdict is never falsely attributed to an artifact.
    req = _request_with(None, request_id="aaaaaaaa-0000-4000-8000-000000000003")
    runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path)
    rec = _last_record(store_path)
    assert "design_artifact_ref" not in rec["design_input"]


def test_malformed_step_fails_closed_before_the_pipeline(store_path):
    # Failure boundary: a malformed STEP is rejected at ingest, so the pipeline never runs and no
    # episode is emitted (the store file is never created).
    with pytest.raises(UnsupportedArtifactError):
        step_intake.ingest(_STEP / "bad_section_order.step")
    assert not pathlib.Path(store_path).exists()
