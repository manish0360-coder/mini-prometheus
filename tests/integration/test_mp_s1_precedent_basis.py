"""MP-S1 §3.7 cross-shop precedent (AC6; T11.1-T11.3). Guarantee 1 (no import path from a verdict to
precedent/judgment) is in tests/boundary/test_mp_s1_gates.py and the import-linter contract.

Each of the five bases is produced from a real store, and only SAME_DECLARATION may count as
(advisory) capability evidence. The verdict is shown to be identical with or without cross-shop
precedent in the store. All fixtures are synthetic.
"""

from __future__ import annotations

import dataclasses

import mp_s1_support as s
from mini_prometheus import _hashing as h
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.precedent_basis import (
    NON_AUTHORITATIVE_NOTE,
    PrecedentBasis,
    SignalAuthority,
    annotate_precedent_basis,
    run_precedent_for_shop,
)

T = "2026-11-06T00:00:00+00:00"


def _store(tmp_path, *models):
    path = str(tmp_path / "episodes.jsonl")
    for model in models:
        runner.run(
            intake(s.bracket(), produced_at=T),
            capability_model=model,
            produced_at=T,
            store_path=path,
        )
    return path


def _bases(annotation):
    return [entry.basis for entry in annotation.entries]


def test_same_declaration_is_advisory_evidence(tmp_path):
    model = s.model("default_1.0.0")
    report, annotation = run_precedent_for_shop(
        s.bracket(), capability_model=model, store_path=_store(tmp_path, model)
    )
    assert _bases(annotation) == [PrecedentBasis.SAME_DECLARATION]
    assert annotation.entries[0].capability_evidence is True
    assert annotation.signal_authority == SignalAuthority.SAME_DECLARATION_ADVISORY
    assert annotation.report_content_hash == report.content_hash


def test_same_content_other_declaration_is_not_evidence(tmp_path):
    store = _store(tmp_path, s.model("variants/declarer_changed"))
    _, annotation = run_precedent_for_shop(
        s.bracket(), capability_model=s.model("default_1.0.0"), store_path=store
    )
    assert _bases(annotation) == [PrecedentBasis.SAME_CONTENT_OTHER_DECLARATION]
    assert annotation.entries[0].capability_evidence is False
    assert annotation.signal_authority == SignalAuthority.NON_AUTHORITATIVE_CROSS_BASIS
    assert annotation.note == NON_AUTHORITATIVE_NOTE


def test_other_shop_is_not_evidence(tmp_path):
    store = _store(tmp_path, s.model("three_cell_synthetic"))
    _, annotation = run_precedent_for_shop(
        s.bracket(), capability_model=s.model("default_1.0.0"), store_path=store
    )
    assert _bases(annotation) == [PrecedentBasis.OTHER_SHOP]
    assert not annotation.entries[0].capability_evidence


def test_unknown_basis_for_legacy_precedent_and_for_a_code_model_query(tmp_path):
    store = _store(tmp_path, default_model())
    _, annotation = run_precedent_for_shop(
        s.bracket(), capability_model=s.model("default_1.0.0"), store_path=store
    )
    assert _bases(annotation) == [PrecedentBasis.UNKNOWN_BASIS]
    (tmp_path / "declared").mkdir()
    store2 = _store(tmp_path / "declared", s.model("default_1.0.0"))
    _, annotation = run_precedent_for_shop(
        s.bracket(), capability_model=default_model(), store_path=store2
    )
    assert set(_bases(annotation)) == {PrecedentBasis.UNKNOWN_BASIS}


def test_unresolved_when_the_episode_is_not_in_the_given_store(tmp_path):
    model = s.model("default_1.0.0")
    report, _ = run_precedent_for_shop(
        s.bracket(), capability_model=model, store_path=_store(tmp_path, model)
    )
    annotation = annotate_precedent_basis(report, [], model)
    assert _bases(annotation) == [PrecedentBasis.UNRESOLVED]
    assert not annotation.entries[0].capability_evidence


def test_a_mixed_report_is_non_authoritative(tmp_path):
    model = s.model("default_1.0.0")
    store = _store(tmp_path, model, s.model("variants/declarer_changed"))
    _, annotation = run_precedent_for_shop(s.bracket(), capability_model=model, store_path=store)
    assert set(_bases(annotation)) == {
        PrecedentBasis.SAME_DECLARATION,
        PrecedentBasis.SAME_CONTENT_OTHER_DECLARATION,
    }
    assert annotation.signal_authority == SignalAuthority.NON_AUTHORITATIVE_CROSS_BASIS


def test_the_frozen_report_is_not_modified_by_annotation(tmp_path):
    model = s.model("default_1.0.0")
    report, _ = run_precedent_for_shop(
        s.bracket(), capability_model=model, store_path=_store(tmp_path, model)
    )
    before = h.to_contract_dict(report)
    annotate_precedent_basis(report, load(str(tmp_path / "episodes.jsonl")), model)
    assert h.to_contract_dict(report) == before


def test_cross_shop_precedent_cannot_change_a_verdict(tmp_path):
    """T11.3: the same query under the same declared shop, with an empty store and with a store full of
    foreign-shop precedent, gives a byte-identical verdict and plan."""
    model = s.model("variants/material_removed")
    crowded = _store(tmp_path, s.model("default_1.0.0"), s.model("three_cell_synthetic"))
    with_precedent = runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=model,
        produced_at=T,
        store_path=crowded,
    )
    (tmp_path / "empty").mkdir()
    alone = runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=model,
        produced_at=T,
        store_path=str(tmp_path / "empty" / "e.jsonl"),
    )
    assert h.to_contract_dict(with_precedent.verdict) == h.to_contract_dict(alone.verdict)
    assert with_precedent.plan.content_hash == alone.plan.content_hash
    assert dataclasses.asdict(with_precedent.verdict)["status"] == "NOT_MANUFACTURABLE"
