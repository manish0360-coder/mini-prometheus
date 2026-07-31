"""RM3-M3 unit tests: Engineering Precedent Reasoning (signal, report assembly, identity, honesty).

Feeds the reasoner ``RankedPrecedent`` hand-offs (the sole input) — synthetic episodes built by
``dataclasses.replace`` on one real RM1 episode so verdict status/reason_codes are controlled, plus one
test driving the reasoner directly from the RM3-M2 ``retriever`` to prove the hand-off. Verdicts are
never recomputed here (no manufacturing verification) — the reasoner only reads the stored verdicts.
"""
from __future__ import annotations

import dataclasses

import jsonschema

from mini_prometheus import _hashing as h
from mini_prometheus import _validate
from mini_prometheus._contracts import (
    DeclaredOperation,
    EngineeringVerificationStatus,
    ManufacturabilityVerdictStatus,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.orchestration import runner
from mini_prometheus.precedent import reasoner, retriever
from mini_prometheus.experience import episode_store_reader
from mini_prometheus.precedent.precedent_model import PRECEDENT_MODEL_VERSION, default_model
from mini_prometheus.precedent.retriever import RankedPrecedent

from contracts.python.manufacturing.precedent_report_schema import PrecedentReport, PrecedentSignal

from support import FIXED_TIME

_REPORT_SCHEMA_ID = "https://contracts.mini-prometheus.dev/v1/manufacturing/precedent_report.schema.json"


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


def _query(**over):
    return intake(_request(**over), produced_at=FIXED_TIME)


def _real_episode(store_path):
    ep = runner.run_from_request(_request(), produced_at=FIXED_TIME, store_path=store_path).episode
    assert ep is not None and ep.design_input is not None
    return ep


def _mk(base, tag, status, reason_codes):
    """A synthetic precedent episode: distinct id/content_hash, chosen verdict (read-only inputs)."""
    verdict = dataclasses.replace(base.verdict, status=status, reason_codes=list(reason_codes))
    return dataclasses.replace(
        base,
        episode_id=f"00000000-0000-0000-0000-{tag:012d}",
        content_hash="sha256:" + f"{tag:064x}",
        verdict=verdict,
    )


def _ranked(base, *specs):
    """Build a ranked hand-off list [(tag, status, reason_codes, score), ...] in the given order."""
    return [
        RankedPrecedent(episode=_mk(base, tag, status, rc), relevance_score=score)
        for (tag, status, rc, score) in specs
    ]


def _schema_errors(report: PrecedentReport):
    reg = _validate._registry()
    schema = reg.get_or_retrieve(_REPORT_SCHEMA_ID).value.contents
    d = h.to_contract_dict(report)
    d["signal_source_rank"] = report.signal_source_rank  # preserve null (generic serializer drops None)
    validator = jsonschema.Draft202012Validator(schema, registry=reg)
    return list(validator.iter_errors(d))


# --- signal derivation ------------------------------------------------------------------------------

def test_supporting_signal(store_path):
    base = _real_episode(store_path)
    ranked = _ranked(base, (1, "MANUFACTURABLE", [], 900))
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    assert report.signal == PrecedentSignal.SUPPORTING
    assert report.signal_source_rank == 0


def test_cautionary_signal_surfaces_reason_codes(store_path):
    base = _real_episode(store_path)
    ranked = _ranked(base, (2, "NOT_MANUFACTURABLE", ["MATERIAL_UNSUPPORTED", "CAPABILITY_MISSING"], 880))
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    assert report.signal == PrecedentSignal.CAUTIONARY
    assert report.signal_source_rank == 0
    assert [c.value for c in report.precedents[0].reason_codes] == [
        "MATERIAL_UNSUPPORTED",
        "CAPABILITY_MISSING",
    ]


def test_none_on_empty_corpus():
    report = reasoner.reason(_query(), [], produced_at=FIXED_TIME)
    assert report.signal == PrecedentSignal.NONE
    assert report.signal_source_rank is None
    assert report.precedents == []


def test_none_when_below_threshold(store_path):
    base = _real_episode(store_path)
    # default threshold 1: a score-0 precedent shares nothing -> not signal-eligible
    r0 = reasoner.reason(_query(), _ranked(base, (3, "MANUFACTURABLE", [], 0)), produced_at=FIXED_TIME)
    assert r0.signal == PrecedentSignal.NONE and r0.signal_source_rank is None
    # a raised threshold makes an otherwise-eligible precedent fall short
    r1 = reasoner.reason(
        _query(), _ranked(base, (4, "MANUFACTURABLE", [], 500)),
        relevance_threshold=600, produced_at=FIXED_TIME,
    )
    assert r1.signal == PrecedentSignal.NONE and r1.signal_source_rank is None


def test_nearest_decisive_precedent_selected(store_path):
    base = _real_episode(store_path)
    # rank 0 is PLAN_INVALID (not a manufacturability outcome) -> skipped; rank 1 decides the signal
    ranked = _ranked(
        base,
        (5, "PLAN_INVALID", ["PLAN_MALFORMED"], 1000),
        (6, "NOT_MANUFACTURABLE", ["TOLERANCE_UNSUPPORTED"], 900),
    )
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    assert report.signal == PrecedentSignal.CAUTIONARY
    assert report.signal_source_rank == 1


# --- entries, ordering, identity --------------------------------------------------------------------

def test_entry_fields_and_rank_contiguity(store_path):
    base = _real_episode(store_path)
    ranked = _ranked(
        base,
        (7, "MANUFACTURABLE", [], 950),
        (8, "NOT_MANUFACTURABLE", ["MATERIAL_UNSUPPORTED"], 800),
        (9, "MANUFACTURABLE", [], 700),
    )
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    assert [e.rank for e in report.precedents] == [0, 1, 2]  # contiguous, input order preserved
    for entry, rp in zip(report.precedents, ranked):
        assert entry.episode_ref.id == rp.episode.episode_id
        assert entry.episode_ref.content_hash == rp.episode.content_hash
        assert entry.relevance_score == rp.relevance_score
        assert entry.verdict_status.value == rp.episode.verdict.status
        assert isinstance(entry.precedent_verification_status, EngineeringVerificationStatus)


def test_signal_source_points_at_a_consistent_entry(store_path):
    base = _real_episode(store_path)
    report = reasoner.reason(
        _query(),
        _ranked(base, (10, "NOT_MANUFACTURABLE", ["CAPABILITY_MISSING"], 900)),
        produced_at=FIXED_TIME,
    )
    src = report.precedents[report.signal_source_rank]
    assert report.signal == PrecedentSignal.CAUTIONARY
    assert src.verdict_status == ManufacturabilityVerdictStatus.NOT_MANUFACTURABLE  # invariant 2


def test_precedent_model_version_recorded(store_path):
    base = _real_episode(store_path)
    report = reasoner.reason(
        _query(), _ranked(base, (11, "MANUFACTURABLE", [], 900)), produced_at=FIXED_TIME
    )
    assert report.precedent_model_version == PRECEDENT_MODEL_VERSION == "1.0.0"


# --- determinism, honesty, contract, provenance -----------------------------------------------------

def test_deterministic_content_hash_and_report_id(store_path):
    base = _real_episode(store_path)
    ranked = _ranked(base, (12, "MANUFACTURABLE", [], 900), (13, "NOT_MANUFACTURABLE", ["PLAN_MALFORMED"], 700))
    a = reasoner.reason(_query(), ranked, produced_at="2026-07-23T00:00:00+00:00")
    b = reasoner.reason(_query(), ranked, produced_at="2030-01-01T12:00:00+00:00")  # different time
    assert a.content_hash == b.content_hash  # produced_at excluded from identity
    assert a.report_id == b.report_id
    assert a.report_id == h.derive_uuid(a.content_hash)  # report_id = uuid5(NS_MP, content_hash)


def test_structural_honesty_no_query_verdict_field():
    names = {f.name for f in dataclasses.fields(PrecedentReport)}
    assert "query_design_input_ref" in names
    assert not any("verdict" in n for n in names)  # no query-verdict field exists at report level


def test_report_validates_against_frozen_schema(store_path):
    base = _real_episode(store_path)
    ranked = _ranked(base, (14, "MANUFACTURABLE", [], 900), (15, "NOT_MANUFACTURABLE", ["MATERIAL_UNSUPPORTED"], 650))
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    assert _schema_errors(report) == []
    # a NONE report (null signal_source_rank) must also be schema-valid
    assert _schema_errors(reasoner.reason(_query(), [], produced_at=FIXED_TIME)) == []


def test_provenance_sentinel_and_source_refs(store_path):
    base = _real_episode(store_path)
    ranked = _ranked(base, (16, "MANUFACTURABLE", [], 900), (17, "MANUFACTURABLE", [], 800))
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    prov = report.provenance
    assert prov.capability_model_version == "0.0.0"  # sentinel (contract package §6)
    assert prov.rule_id == "precedent.reasoning"
    expected = [report.query_design_input_ref, *[e.episode_ref for e in report.precedents]]
    assert prov.source_refs == expected


def test_reasoner_consumes_retriever_ranked_precedents(store_path):
    # The retriever (RM3-M2) is the sole source of ranked precedents; the reasoner consumes its output.
    runner.run_from_request(_request(), produced_at=FIXED_TIME, store_path=store_path)
    runner.run_from_request(_request(quantity=5), produced_at=FIXED_TIME, store_path=store_path)
    corpus = episode_store_reader.load(store_path)
    ranked = retriever.rank(_query(), corpus, model=default_model())
    report = reasoner.reason(_query(), ranked, produced_at=FIXED_TIME)
    assert [e.relevance_score for e in report.precedents] == [r.relevance_score for r in ranked]
    assert [e.episode_ref.content_hash for e in report.precedents] == [
        r.episode.content_hash for r in ranked
    ]
    assert _schema_errors(report) == []
