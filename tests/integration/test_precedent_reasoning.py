"""RM3-M4 integration: the Engineering Precedent Composition, end-to-end (spec §9 acceptance).

Proves the composed request → DesignInput → retriever → reasoner → PrecedentReport path: determinism,
generalization (a non-identical prior is surfaced; an identical one at relevance 1000), a cautionary
signal from a real NOT_MANUFACTURABLE precedent, empty corpus ⇒ NONE, read-only behavior, and that the
orchestrator is pure composition (adds no logic). Corpus episodes are produced by the unchanged RM1
runner, so their embedded design_input and verified verdicts are real.
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
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
)
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.precedent_runner import run_precedent
from mini_prometheus.precedent import reasoner, retriever
from mini_prometheus.precedent.precedent_model import PRECEDENT_MODEL_VERSION

from contracts.python.manufacturing.precedent_report_schema import PrecedentSignal

from support import FIXED_TIME


def _lines(path: str) -> int:
    p = pathlib.Path(path)
    return sum(1 for _ in p.open()) if p.exists() else 0


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


def _seed(store_path, *requests):
    for req in requests:
        runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path)


def test_deterministic_report(store_path):
    _seed(store_path, _request(), _request(quantity=5))
    a = run_precedent(_request(), store_path=store_path, produced_at="2026-07-23T00:00:00+00:00")
    b = run_precedent(_request(), store_path=store_path, produced_at="2031-01-01T00:00:00+00:00")
    assert a.content_hash == b.content_hash  # produced_at excluded from identity
    assert a.report_id == b.report_id


def test_generalization_surfaces_similar_and_identical(store_path):
    # A identical to the query; B similar (different quantity) — RM2 exact reuse would miss B.
    _seed(store_path, _request(), _request(quantity=5))
    report = run_precedent(_request(), store_path=store_path)
    scores = [e.relevance_score for e in report.precedents]
    assert scores == [1000, 920]  # identical at 1000; a non-identical prior surfaced (<1000)
    assert report.signal == PrecedentSignal.SUPPORTING  # nearest strongly-relevant was MANUFACTURABLE
    assert report.signal_source_rank == 0


def test_cautionary_signal_from_not_manufacturable_precedent(store_path):
    # Seed a real NOT_MANUFACTURABLE precedent: a turned part under a lathe-less capability model.
    model_no_lathe = ProcessCapabilityModel(
        version="1.0.0",
        op_capability=default_model().op_capability,
        resources={k: v for k, v in default_model().resources.items() if k != "lathe01"},
        supported_materials=default_model().supported_materials,
    )
    turn_req = _turn_request()
    neg = runner.run(
        intake(turn_req, produced_at=FIXED_TIME),
        capability_model=model_no_lathe,
        produced_at=FIXED_TIME,
        store_path=store_path,
    )
    assert neg.status == "NOT_MANUFACTURABLE" and "CAPABILITY_MISSING" in neg.verdict.reason_codes

    report = run_precedent(turn_req, store_path=store_path)
    assert report.signal == PrecedentSignal.CAUTIONARY
    assert report.signal_source_rank == 0
    src = report.precedents[0]
    assert src.relevance_score == 1000  # query design is identical to the rejected precedent
    assert "CAPABILITY_MISSING" in [c.value for c in src.reason_codes]  # its reason codes surfaced


def test_empty_corpus_yields_none(tmp_path):
    report = run_precedent(_request(), store_path=str(tmp_path / "empty.jsonl"))
    assert report.signal == PrecedentSignal.NONE
    assert report.signal_source_rank is None
    assert report.precedents == []


def test_read_only_leaves_corpus_unchanged(store_path):
    _seed(store_path, _request(), _request(quantity=5), _request(material="Steel 1018", material_code="ST1018"))
    path = pathlib.Path(store_path)
    before_bytes = path.read_bytes()
    before_lines = _lines(store_path)
    run_precedent(_request(), store_path=store_path)
    assert path.read_bytes() == before_bytes  # corpus file byte-unchanged
    assert _lines(store_path) == before_lines  # no episode written by a precedent query


def test_orchestrator_is_pure_composition(store_path):
    # run_precedent must equal manually composing intake -> retrieve -> reason (no added logic).
    _seed(store_path, _request(), _request(quantity=5))
    produced_at = FIXED_TIME
    di = intake(_request(), produced_at=produced_at)
    ranked = retriever.retrieve(di, store_path=store_path)
    expected = reasoner.reason(
        di, ranked, precedent_model_version=PRECEDENT_MODEL_VERSION, produced_at=produced_at
    )
    got = run_precedent(_request(), store_path=store_path, produced_at=produced_at)
    assert got.content_hash == expected.content_hash
    assert got.report_id == expected.report_id
