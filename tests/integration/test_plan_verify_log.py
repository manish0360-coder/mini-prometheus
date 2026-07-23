"""Integration: the RM1 plan -> verify -> log loop (spec §8).

Hermetic; deterministic verdict + content hash; grounded negative outcome; both intake paths;
and the INFRA_ERROR path that writes no episode.
"""
from __future__ import annotations

import pathlib

from mini_prometheus._contracts import ManufacturingRequest, ProcessOp
from mini_prometheus.integrations.velith.adapter import from_engineering_result
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
)
from mini_prometheus.orchestration import runner

from support import FIXED_TIME


def _lines(path: str) -> int:
    p = pathlib.Path(path)
    return sum(1 for _ in p.open()) if p.exists() else 0


def test_full_loop_manufacturable_and_logged(engineer_request, store_path):
    result = runner.run_from_request(engineer_request, produced_at=FIXED_TIME, store_path=store_path)
    assert result.status == "MANUFACTURABLE"
    assert not result.is_error
    assert result.plan is not None and result.episode is not None
    assert _lines(store_path) == 1  # one episode, survives process (written to disk)


def test_determinism_same_inputs_same_hashes(engineer_request, store_path):
    r1 = runner.run_from_request(engineer_request, produced_at="2026-01-01T00:00:00+00:00", store_path=store_path)
    r2 = runner.run_from_request(engineer_request, produced_at="2026-12-31T23:59:59+00:00", store_path=store_path)
    assert r1.plan.content_hash == r2.plan.content_hash
    assert r1.episode.content_hash == r2.episode.content_hash
    assert r1.episode.episode_id == r2.episode.episode_id


def test_negative_capability_absent_is_grounded_not_manufacturable(store_path):
    from mini_prometheus._contracts import DeclaredOperation, StockForm

    req = ManufacturingRequest(
        schema_version="1.0.0", request_id="22222222-2222-2222-2222-222222222222",
        material="Aluminum 6061", stock_form=StockForm.bar,
        declared_operations=[DeclaredOperation(op=ProcessOp.turn)], quantity=1,
    )
    di = intake(req, produced_at=FIXED_TIME)
    model_no_lathe = ProcessCapabilityModel(
        version="1.0.0", op_capability=default_model().op_capability,
        resources={k: v for k, v in default_model().resources.items() if k != "lathe01"},
        supported_materials=default_model().supported_materials,
    )
    result = runner.run(di, capability_model=model_no_lathe, produced_at=FIXED_TIME, store_path=store_path)
    assert result.status == "NOT_MANUFACTURABLE"
    assert "CAPABILITY_MISSING" in result.verdict.reason_codes
    assert not result.is_error  # grounded outcome -> success, episode written
    assert _lines(store_path) == 1


def test_both_intake_paths_converge_to_same_design_input_contract(engineer_request, velith_result):
    di_engineer = intake(engineer_request, produced_at=FIXED_TIME)
    di_velith = from_engineering_result(velith_result, engineer_request, produced_at=FIXED_TIME)
    # same manufacturing intent, differing only in verification status/source (spec §7)
    assert di_engineer.engineering_verification_status.value == "engineer_declared"
    assert di_velith.engineering_verification_status.value == "velith_verified"
    assert [o.op for o in di_engineer.declared_operations] == [o.op for o in di_velith.declared_operations]
    assert di_engineer.material == di_velith.material


def test_honesty_chain_status_carried_into_episode(velith_result, engineer_request, store_path):
    di = from_engineering_result(velith_result, engineer_request, produced_at=FIXED_TIME)
    result = runner.run(di, produced_at=FIXED_TIME, store_path=store_path)
    assert result.episode.engineering_verification_status.value == "velith_verified"


def test_infra_error_writes_no_episode(engineer_request, store_path):
    class _BoomOracle:
        def verify(self, plan, capability_model):
            raise RuntimeError("simulated infrastructure fault")

    di = intake(engineer_request, produced_at=FIXED_TIME)
    result = runner.run(di, oracle=_BoomOracle(), produced_at=FIXED_TIME, store_path=store_path)
    assert result.status == "INFRA_ERROR"
    assert result.is_error
    assert result.episode is None
    assert _lines(store_path) == 0  # no episode persisted (spec §5.3)
