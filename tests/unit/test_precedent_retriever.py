"""RM3-M2 unit tests: the retrieval mechanism (deterministic ranking, read-only, top-K).

Builds a real verified-episode corpus with RM1's runner (episodes carry the embedded ``DesignInput``
per the ratified RM1 correction), then exercises the retriever against it. Verdict semantics belong to
RM3-M3 and are not asserted here; these tests cover ranking order, tie-break, top-K, determinism,
read-only behavior, legacy exclusion, and empty/missing corpora.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.experience import episode_store_reader
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.orchestration import runner
from mini_prometheus.precedent import retriever
from mini_prometheus.precedent.precedent_model import default_model

from support import FIXED_TIME

_BASE_OPS = [
    DeclaredOperation(op=ProcessOp.cut_stock),
    DeclaredOperation(op=ProcessOp.face_mill),
    DeclaredOperation(op=ProcessOp.drill),
    DeclaredOperation(op=ProcessOp.drill),
    DeclaredOperation(op=ProcessOp.deburr),
    DeclaredOperation(op=ProcessOp.inspect),
]


def _request(**over) -> ManufacturingRequest:
    fields = dict(
        schema_version="1.0.0",
        request_id="11111111-1111-1111-1111-111111111111",
        material="Aluminum 6061",
        material_code="AL6061",
        stock_form=StockForm.block,
        declared_operations=list(_BASE_OPS),
        quantity=25,
        tolerances=Tolerances(general_tolerance_mm=0.1),
    )
    fields.update(over)
    return ManufacturingRequest(**fields)


def _query(**over):
    return intake(_request(**over), produced_at=FIXED_TIME)


def _persist(store_path, **over):
    """Run a request through RM1 and return the persisted episode (carries embedded design_input)."""
    episode = runner.run_from_request(
        _request(**over), produced_at=FIXED_TIME, store_path=store_path
    ).episode
    assert episode is not None and episode.design_input is not None
    return episode


def _corpus(store_path):
    """A five-episode corpus with pairwise-distinct relevance to the base query.

    Relevance to base query (from the frozen model, verified in test_precedent_model):
    identical=1000, quantity=5 ->920, tolerances=None ->900, stock_form=plate ->850, material ->700.
    """
    _persist(store_path)  # identical -> 1000
    _persist(store_path, quantity=5)  # -> 920
    _persist(store_path, tolerances=None)  # -> 900
    _persist(store_path, stock_form=StockForm.plate)  # -> 850
    _persist(store_path, material="Steel 1018", material_code="ST1018")  # -> 700
    return episode_store_reader.load(store_path)


def test_ranks_by_relevance_descending(store_path):
    corpus = _corpus(store_path)
    ranked = retriever.rank(_query(), corpus, model=default_model())
    assert [r.relevance_score for r in ranked] == [1000, 920, 900, 850, 700]


def test_tie_break_by_episode_content_hash_ascending(store_path):
    # Two different mismatched materials each lose exactly the material weight -> both score 700.
    _persist(store_path, material="Steel 1018", material_code="ST1018")
    _persist(store_path, material="Titanium Grade 5", material_code=None)
    corpus = episode_store_reader.load(store_path)
    ranked = retriever.rank(_query(), corpus, model=default_model())
    assert [r.relevance_score for r in ranked] == [700, 700]
    hashes = [r.episode.content_hash for r in ranked]
    assert hashes == sorted(hashes)  # tie-break is content_hash ascending


def test_top_k_truncates_the_total_order(store_path):
    corpus = _corpus(store_path)
    full = retriever.rank(_query(), corpus)
    assert [r.relevance_score for r in retriever.rank(_query(), corpus, top_k=2)] == [1000, 920]
    assert retriever.rank(_query(), corpus, top_k=0) == []
    assert retriever.rank(_query(), corpus, top_k=99) == full  # K > n returns the full ranking


def test_top_k_negative_is_rejected(store_path):
    corpus = _corpus(store_path)
    with pytest.raises(ValueError):
        retriever.rank(_query(), corpus, top_k=-1)


def test_deterministic_identical_corpus_identical_ranking(store_path):
    corpus = _corpus(store_path)
    a = retriever.rank(_query(), corpus)
    b = retriever.rank(_query(), corpus)
    assert [(r.episode.episode_id, r.relevance_score) for r in a] == [
        (r.episode.episode_id, r.relevance_score) for r in b
    ]


def test_identical_design_scores_1000_and_ranks_first(store_path):
    corpus = _corpus(store_path)
    ranked = retriever.rank(_query(), corpus, model=default_model())
    assert ranked[0].relevance_score == 1000
    # the top precedent is the one whose embedded design equals the query design
    assert ranked[0].episode.design_input.material == "Aluminum 6061"


def test_legacy_episode_without_design_input_is_excluded(store_path):
    corpus = _corpus(store_path)
    legacy = dataclasses.replace(corpus[0], design_input=None)  # simulate a 1.0.0 episode
    mixed = [legacy, *corpus]
    ranked = retriever.rank(_query(), mixed)
    # the unscorable legacy episode is absent; every scorable episode is still ranked
    assert len(ranked) == len(corpus)
    assert legacy not in [r.episode for r in ranked]


def test_rank_does_not_mutate_the_corpus(store_path):
    corpus = _corpus(store_path)
    before = [e.episode_id for e in corpus]
    retriever.rank(_query(), corpus)
    assert [e.episode_id for e in corpus] == before  # input order/content untouched


def test_retrieve_is_read_only(store_path):
    _corpus(store_path)
    path = Path(store_path)
    before_bytes = path.read_bytes()
    before_lines = len(episode_store_reader.load(store_path))
    ranked = retriever.retrieve(_query(), store_path=store_path, model=default_model())
    assert [r.relevance_score for r in ranked] == [1000, 920, 900, 850, 700]
    assert path.read_bytes() == before_bytes  # corpus file byte-unchanged
    assert len(episode_store_reader.load(store_path)) == before_lines


def test_retrieve_matches_pure_rank(store_path):
    corpus = _corpus(store_path)
    via_retrieve = retriever.retrieve(_query(), store_path=store_path)
    via_rank = retriever.rank(_query(), corpus)
    assert [(r.episode.episode_id, r.relevance_score) for r in via_retrieve] == [
        (r.episode.episode_id, r.relevance_score) for r in via_rank
    ]


def test_empty_and_missing_corpus_yield_empty_ranking(tmp_path):
    assert retriever.rank(_query(), []) == []
    assert retriever.retrieve(_query(), store_path=str(tmp_path / "does_not_exist.jsonl")) == []
