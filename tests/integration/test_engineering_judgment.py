"""RM4 Commit 4 integration: the Engineering Judgment pipeline, end-to-end (spec acceptance).

Proves the composed (RM1 episode, RM3 precedent report) -> EngineeringSituation -> EngineeringCritique
path: determinism, the headline situated-value case (cautionary despite a structurally-valid plan),
supportive end-to-end, read-only behavior, pure composition, and fail-closed on a cross-case pairing.
Corpus + reports are produced by the unchanged RM1 runner and RM3 precedent runner.
"""
from __future__ import annotations

import pathlib

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.judgment.critic_model import Assessment, FindingKind
from mini_prometheus.judgment.engineering_critique import critique
from mini_prometheus.judgment.engineering_situation import SituationCoherenceError, assemble
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model as capability_default_model,
)
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.judgment_runner import run_judgment
from mini_prometheus.orchestration.precedent_runner import run_precedent

import pytest

from support import FIXED_TIME


def _request(**over) -> ManufacturingRequest:
    fields = dict(
        schema_version="1.0.0",
        request_id="11111111-1111-1111-1111-111111111111",
        material="Aluminum 6061",
        material_code="AL6061",
        stock_form=StockForm.block,
        declared_operations=[
            DeclaredOperation(op=ProcessOp.cut_stock),
            DeclaredOperation(op=ProcessOp.face_mill),
            DeclaredOperation(op=ProcessOp.drill),
            DeclaredOperation(op=ProcessOp.inspect),
        ],
        quantity=25,
        tolerances=Tolerances(general_tolerance_mm=0.1),
    )
    fields.update(over)
    return ManufacturingRequest(**fields)


def _turn_request() -> ManufacturingRequest:
    return ManufacturingRequest(
        schema_version="1.0.0",
        request_id="22222222-2222-2222-2222-222222222222",
        material="Aluminum 6061",
        stock_form=StockForm.bar,
        declared_operations=[DeclaredOperation(op=ProcessOp.turn)],
        quantity=1,
    )


def _lathe_less_model() -> ProcessCapabilityModel:
    base = capability_default_model()
    return ProcessCapabilityModel(
        version="1.0.0",
        op_capability=base.op_capability,
        resources={k: v for k, v in base.resources.items() if k != "lathe01"},
        supported_materials=base.supported_materials,
    )


def _machined_case(store_path):
    req = _request()
    episode = runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path).episode
    report = run_precedent(req, store_path=store_path, produced_at=FIXED_TIME)
    return episode, report


def test_deterministic_judgment(store_path):
    episode, report = _machined_case(store_path)
    a = run_judgment(episode, report, produced_at="2026-07-23T00:00:00+00:00")
    b = run_judgment(episode, report, produced_at="2031-01-01T00:00:00+00:00")
    assert a.content_hash == b.content_hash  # produced_at excluded from identity


def test_situated_value_cautionary_despite_manufacturable_plan(tmp_path):
    # Precedent P: the turned design, REJECTED under a lathe-less model.
    store_bad = str(tmp_path / "bad.jsonl")
    turn_req = _turn_request()
    runner.run(
        intake(turn_req, produced_at=FIXED_TIME),
        capability_model=_lathe_less_model(),
        produced_at=FIXED_TIME,
        store_path=store_bad,
    )
    # Query Q: the same design, MANUFACTURABLE under the default (lathe-equipped) model.
    store_ok = str(tmp_path / "ok.jsonl")
    episode_q = runner.run(
        intake(turn_req, produced_at=FIXED_TIME), produced_at=FIXED_TIME, store_path=store_ok
    ).episode
    assert episode_q.verdict.status == "MANUFACTURABLE"  # Q's own plan is structurally fine
    # Precedent report drawn from the corpus containing only the REJECTED precedent.
    report = run_precedent(turn_req, store_path=store_bad, produced_at=FIXED_TIME)

    c = run_judgment(episode_q, report)
    # isolated verification (RM1) said MANUFACTURABLE; situated judgment says CAUTIONARY
    assert c.assessment is Assessment.CAUTIONARY
    kinds = {f.kind for f in c.findings}
    assert FindingKind.PRECEDENT_CONSISTENCY in kinds
    assert FindingKind.INTERNAL_VERDICT not in kinds  # Q's own verdict was MANUFACTURABLE


def test_supportive_end_to_end(store_path):
    episode, report = _machined_case(store_path)
    assert run_judgment(episode, report).assessment is Assessment.SUPPORTIVE


def test_read_only_writes_nothing(store_path):
    episode, report = _machined_case(store_path)
    path = pathlib.Path(store_path)
    before = path.read_bytes()
    run_judgment(episode, report)
    assert path.read_bytes() == before  # the pipeline mutates no store and writes no file


def test_runner_is_pure_composition(store_path):
    episode, report = _machined_case(store_path)
    expected = critique(assemble(episode, report), produced_at=FIXED_TIME)
    got = run_judgment(episode, report, produced_at=FIXED_TIME)
    assert got.content_hash == expected.content_hash
    assert got.assessment is expected.assessment


def test_fail_closed_on_cross_case_pairing(store_path):
    episode, _ = _machined_case(store_path)
    other_report = run_precedent(
        _request(material="Steel 1018", material_code="ST1018"),
        store_path=store_path,
        produced_at=FIXED_TIME,
    )
    with pytest.raises(SituationCoherenceError):
        run_judgment(episode, other_report)
