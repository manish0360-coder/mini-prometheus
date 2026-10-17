"""RDAI-1 C1 unit tests: real STEP-file intake adapter (byte-grounded, fail-closed, deterministic).

The expected hash/id are computed INDEPENDENTLY of the adapter (stdlib ``hashlib``/``uuid`` over the
fixture's raw bytes), never obtained from ``ingest()`` and fed back as its own oracle. No frozen file,
contract, runtime version, or Git state is touched; the adapter examines NO geometry.
"""
from __future__ import annotations

import hashlib
import pathlib
import uuid

import pytest

from mini_prometheus._hashing import NS_MP
from mini_prometheus.artifact_intake import step_intake
from mini_prometheus.artifact_intake.step_intake import UnsupportedArtifactError
from mini_prometheus._contracts import StepArtifactRef

_FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "step"
_VALID = _FIX / "valid_minimal.step"

# Independently computed oracle (NOT via ingest): pinned value + recomputation from raw bytes.
_PINNED_HASH = "sha256:9dbd6120d9380deba56e41dd3fe9e53c39b16d0306304075c716fc9e30c9b57f"


def _independent_hash(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _independent_id(content_hash: str) -> str:
    return str(uuid.uuid5(NS_MP, content_hash))


def test_valid_step_yields_byte_grounded_ref_matching_independent_oracle():
    raw = _VALID.read_bytes()
    expected_hash = _independent_hash(raw)
    assert expected_hash == _PINNED_HASH                       # pinned == recomputed (both independent)
    ref = step_intake.ingest(_VALID)
    assert isinstance(ref, StepArtifactRef)
    assert ref.media_type == "model/step"
    assert ref.content_hash == expected_hash                   # adapter == independent oracle
    assert ref.id == _independent_id(expected_hash)            # id independently recomputed via uuid5(NS_MP,·)


def test_identity_is_deterministic():
    a = step_intake.ingest(_VALID)
    b = step_intake.ingest(_VALID)
    assert (a.content_hash, a.id, a.media_type) == (b.content_hash, b.id, b.media_type)


def test_byte_sensitivity_changes_hash(tmp_path):
    raw = _VALID.read_bytes()
    mutated_bytes = raw.replace(b"minimal.step", b"minimbl.step")   # same length, still a valid container
    assert mutated_bytes != raw
    mutated = tmp_path / "mutated.step"
    mutated.write_bytes(mutated_bytes)
    got = step_intake.ingest(mutated)
    assert got.content_hash == _independent_hash(mutated_bytes)     # independent oracle for the mutated bytes
    assert got.content_hash != _PINNED_HASH                         # a one-token change flips the hash


@pytest.mark.parametrize(
    "fixture,msg_substr",
    [
        ("empty.step", "empty"),
        ("not_step.txt", "not an ISO-10303-21 container"),
        ("missing_footer.step", "not an ISO-10303-21 container"),
        ("bad_section_order.step", "malformed STEP container structure"),
        ("nonutf8.bin", "invalid text encoding"),
        ("nul_between_markers.step", "illegal control characters"),
    ],
)
def test_malformed_inputs_fail_closed(fixture, msg_substr):
    with pytest.raises(UnsupportedArtifactError) as ei:
        step_intake.ingest(_FIX / fixture)
    assert msg_substr in str(ei.value)


def test_unreadable_path_fails_closed(tmp_path):
    with pytest.raises(UnsupportedArtifactError):
        step_intake.ingest(tmp_path / "does_not_exist.step")


@pytest.mark.parametrize(
    "body",
    [
        # all six markers present but out of order; each must fail the strict ordering check:
        "ISO-10303-21;\nENDSEC;\nHEADER;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n",  # ENDSEC before HEADER
        "ISO-10303-21;\nHEADER;\nENDSEC;\nENDSEC;\nDATA;\nEND-ISO-10303-21;\n",  # DATA after both ENDSEC
        "ISO-10303-21;\nDATA;\nHEADER;\nENDSEC;\nENDSEC;\nEND-ISO-10303-21;\n",  # DATA before HEADER
    ],
)
def test_marker_order_is_strictly_enforced(tmp_path, body):
    f = tmp_path / "order.step"
    f.write_text(body, encoding="utf-8")
    with pytest.raises(UnsupportedArtifactError) as ei:
        step_intake.ingest(f)
    assert "malformed STEP container structure" in str(ei.value)
