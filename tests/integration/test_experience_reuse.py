"""RM2-M3 integration tests: idempotent reuse composition + reproducibility guard."""
from __future__ import annotations

import pathlib

import pytest

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
)
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
)
from mini_prometheus.orchestration import reuse_runner
from mini_prometheus.orchestration.reuse_runner import (
    ExperienceConsistencyError,
    run_with_reuse,
)

from support import FIXED_TIME


def _lines(path: str) -> int:
    p = pathlib.Path(path)
    return sum(1 for ln in p.open() if ln.strip()) if p.exists() else 0


def _model_v2() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(
        version="2.0.0",
        op_capability=base.op_capability,
        resources=base.resources,
        supported_materials=base.supported_materials,
    )


def _other_request() -> ManufacturingRequest:
    return ManufacturingRequest(
        schema_version="1.0.0",
        request_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        material="Steel 1018",
        stock_form=StockForm.bar,
        declared_operations=[DeclaredOperation(op=ProcessOp.turn), DeclaredOperation(op=ProcessOp.inspect)],
        quantity=4,
    )


def test_miss_then_hit_reuses_without_duplicate(engineer_request, store_path):
    r1 = run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    assert r1.reused is False
    assert _lines(store_path) == 1

    r2 = run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    assert r2.reused is True
    assert r2.plan.content_hash == r1.plan.content_hash
    assert r2.verdict.status == r1.verdict.status
    assert _lines(store_path) == 1  # idempotent: no duplicate episode written
    assert r2.source_episode is not None and r2.source_episode.id == r1.episode.episode_id


def test_different_request_is_a_miss(engineer_request, store_path):
    run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    r2 = run_with_reuse(_other_request(), produced_at=FIXED_TIME, store_path=store_path)
    assert r2.reused is False
    assert _lines(store_path) == 2


def test_guard_success_on_default(engineer_request, store_path):
    run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    r = run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path, verify_reuse=True)
    assert r.reused is True and not r.is_error  # guard passed, reuse served


def test_guard_failure_raises(engineer_request, store_path, monkeypatch):
    run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path)  # seed a real episode

    real_plan = reuse_runner.planner.plan

    def _drifted(design_input, model, *, produced_at=None):
        task, plan = real_plan(design_input, model, produced_at=produced_at)
        plan.content_hash = "sha256:" + "f" * 64  # simulate planner drift / corruption
        return task, plan

    monkeypatch.setattr(reuse_runner.planner, "plan", _drifted)
    with pytest.raises(ExperienceConsistencyError):
        run_with_reuse(engineer_request, produced_at=FIXED_TIME, store_path=store_path)


def test_same_request_different_model_is_a_miss(engineer_request, store_path):
    r1 = run_with_reuse(
        engineer_request, capability_model=default_model(), produced_at=FIXED_TIME, store_path=store_path
    )
    r2 = run_with_reuse(
        engineer_request, capability_model=_model_v2(), produced_at=FIXED_TIME, store_path=store_path
    )
    assert r1.reused is False and r2.reused is False  # different capability_model_version => distinct key
    assert _lines(store_path) == 2


def test_infra_error_on_miss_writes_no_episode(engineer_request, store_path):
    class _BoomOracle:
        def verify(self, plan, capability_model):
            raise RuntimeError("simulated infrastructure fault")

    r = run_with_reuse(engineer_request, oracle=_BoomOracle(), produced_at=FIXED_TIME, store_path=store_path)
    assert r.status == "INFRA_ERROR"
    assert r.is_error is True
    assert r.episode is None
    assert r.reused is False
    assert _lines(store_path) == 0
