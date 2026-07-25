"""RM2-M2 unit tests: episode index (composite-key retrieval)."""
from __future__ import annotations

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
)
from mini_prometheus.experience.episode_index import (
    EpisodeIndex,
    design_input_key,
    key_for_episode,
)
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
)
from mini_prometheus.orchestration import runner

from support import FIXED_TIME


def _model_v2() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(
        version="2.0.0",  # same content, different version string
        op_capability=base.op_capability,
        resources=base.resources,
        supported_materials=base.supported_materials,
    )


def test_build_and_lookup_hit(engineer_request, store_path):
    runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    episodes = load(store_path)
    index = EpisodeIndex.build(episodes)
    ep = episodes[0]
    assert index.lookup(key_for_episode(ep)) is ep
    # a new request's key matches its stored episode's key
    di = intake(engineer_request, produced_at=FIXED_TIME)
    assert design_input_key(di, ep.capability_model_version) == key_for_episode(ep)


def test_lookup_miss_returns_none(engineer_request, store_path):
    runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    index = EpisodeIndex.build(load(store_path))
    assert index.lookup(("sha256:" + "0" * 64, "9.9.9")) is None


def test_same_design_different_model_version_are_distinct(engineer_request, store_path):
    di = intake(engineer_request, produced_at=FIXED_TIME)
    r1 = runner.run(di, capability_model=default_model(), produced_at=FIXED_TIME, store_path=store_path)
    r2 = runner.run(di, capability_model=_model_v2(), produced_at=FIXED_TIME, store_path=store_path)
    index = EpisodeIndex.build(load(store_path))
    assert len(index) == 2  # same design identity, different capability_model_version => distinct keys
    assert index.lookup(design_input_key(di, "1.0.0")) is not None
    assert index.lookup(design_input_key(di, "2.0.0")) is not None
    assert index.lookup(design_input_key(di, "1.0.0")).plan.content_hash == r1.plan.content_hash
    assert index.lookup(design_input_key(di, "2.0.0")).plan.content_hash == r2.plan.content_hash


def test_build_is_deterministic(engineer_request, store_path):
    req2 = ManufacturingRequest(
        schema_version="1.0.0",
        request_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        material="Aluminum 6061",
        stock_form=StockForm.plate,
        declared_operations=[DeclaredOperation(op=ProcessOp.face_mill), DeclaredOperation(op=ProcessOp.inspect)],
        quantity=2,
    )
    runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    runner.run_from_request(req2, produced_at=FIXED_TIME, store_path=store_path)
    episodes = load(store_path)
    idx_a = EpisodeIndex.build(episodes)
    idx_b = EpisodeIndex.build(episodes)
    for ep in episodes:
        k = key_for_episode(ep)
        assert idx_a.lookup(k) is idx_b.lookup(k) is ep
