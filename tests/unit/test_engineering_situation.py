"""RM4 Commit 1 unit tests: internal EngineeringSituation assembly.

Covers coherent assembly, the observed-constituent record, determinism, fail-closed behavior on a
cross-case precedent report and on a legacy episode without an embedded design input, and the
no-external-identity invariant. Coherent (episode, precedent_report) pairs are produced by the unchanged
RM1 runner and RM3 precedent runner and consumed read-only — RM4 re-derives nothing.
"""
from __future__ import annotations

import dataclasses

import pytest

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.judgment.engineering_situation import (
    EngineeringSituation,
    SituationCoherenceError,
    assemble,
)
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.precedent_runner import run_precedent

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


def _case(store_path, **over):
    """A coherent (episode, precedent_report) pair for one case — produced by RM1 + RM3, read-only to RM4."""
    req = _request(**over)
    episode = runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path).episode
    report = run_precedent(req, store_path=store_path, produced_at=FIXED_TIME)
    return episode, report


def test_assemble_returns_the_case_constituents(store_path):
    episode, report = _case(store_path)
    s = assemble(episode, report)
    assert isinstance(s, EngineeringSituation)
    # aggregation, not re-derivation: the situation holds the very same artifact objects
    assert s.design_input is episode.design_input
    assert s.plan is episode.plan
    assert s.verdict is episode.verdict
    assert s.precedent_report is report


def test_constituents_records_observed_set(store_path):
    episode, report = _case(store_path)
    assert assemble(episode, report).constituents == (
        "design_input",
        "plan",
        "verdict",
        "precedent_report",
    )


def test_assembly_is_deterministic(store_path):
    episode, report = _case(store_path)
    assert assemble(episode, report) == assemble(episode, report)


def test_incoherent_precedent_report_fails_closed(store_path):
    episode, _ = _case(store_path)
    # a precedent report for a DIFFERENT case (different material) queried a different design
    other_report = run_precedent(
        _request(material="Steel 1018", material_code="ST1018"),
        store_path=store_path,
        produced_at=FIXED_TIME,
    )
    with pytest.raises(SituationCoherenceError):
        assemble(episode, other_report)


def test_missing_embedded_design_input_fails_closed(store_path):
    episode, report = _case(store_path)
    legacy = dataclasses.replace(episode, design_input=None)  # simulate a legacy 1.0.0 episode
    with pytest.raises(SituationCoherenceError):
        assemble(legacy, report)


def test_situation_carries_no_external_identity(store_path):
    episode, report = _case(store_path)
    s = assemble(episode, report)
    for attr in ("content_hash", "id", "report_id", "situation_id"):
        assert not hasattr(s, attr)  # internal state only — no external identity
