"""RM2-M1 unit tests: experience episode store reader (read side)."""
from __future__ import annotations

import json

import pytest

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DeclaredOperation,
    EngineeringVerificationStatus,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
)
from mini_prometheus.experience.episode_store_reader import EpisodeIntegrityError, load
from mini_prometheus.orchestration import runner

from support import FIXED_TIME


def _seed_two(store_path: str, engineer_request) -> None:
    runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    req2 = ManufacturingRequest(
        schema_version="1.0.0",
        request_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        material="Steel 1018",
        stock_form=StockForm.bar,
        declared_operations=[DeclaredOperation(op=ProcessOp.turn), DeclaredOperation(op=ProcessOp.inspect)],
        quantity=3,
    )
    runner.run_from_request(req2, produced_at=FIXED_TIME, store_path=store_path)


def test_load_returns_verified_episodes(engineer_request, store_path):
    _seed_two(store_path, engineer_request)
    episodes = load(store_path)
    assert len(episodes) == 2
    for ep in episodes:  # integrity re-verifies (load would have raised otherwise)
        assert h.content_hash(h.episode_identity(ep)) == ep.content_hash


def test_round_trip_matches_stored_json(engineer_request, store_path):
    _seed_two(store_path, engineer_request)
    lines = [ln for ln in open(store_path, encoding="utf-8").read().splitlines() if ln.strip()]
    episodes = load(store_path)
    assert len(lines) == len(episodes) == 2
    for line, ep in zip(lines, episodes):
        assert h.to_contract_dict(ep) == json.loads(line)


def test_missing_store_returns_empty():
    assert load("/nonexistent/path/manufacturing_episodes.jsonl") == []


def test_tampered_hashed_field_raises(engineer_request, store_path):
    runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    line0 = open(store_path, encoding="utf-8").read().splitlines()[0]
    d = json.loads(line0)
    # verdict.status is part of the episode identity (hashed) — mutate it without recomputing the hash.
    d["verdict"]["status"] = (
        "NOT_MANUFACTURABLE" if d["verdict"]["status"] == "MANUFACTURABLE" else "MANUFACTURABLE"
    )
    open(store_path, "w", encoding="utf-8").write(h.canonical_json(d) + "\n")
    with pytest.raises(EpisodeIntegrityError):
        load(store_path)


def test_enum_reconstruction(engineer_request, store_path):
    runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    ep = load(store_path)[0]
    assert isinstance(ep.engineering_verification_status, EngineeringVerificationStatus)
    assert isinstance(ep.plan.steps[0].op, ProcessOp)
