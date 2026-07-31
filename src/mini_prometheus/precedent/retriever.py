"""RM3-M2: the retrieval mechanism — the Extraction Seed.

Ranks Mini Prometheus's own verified ``ManufacturingEpisode`` corpus by engineering relevance to a
query ``DesignInput`` using the **frozen** RM3 ``precedent_model`` (RM3-M1). This module is *mechanism
only* (RM3 spec §7): it owns no precedent semantics, no signal, and no ``PrecedentReport`` shape — only
a deterministic total-ordered ranking. Signal derivation and report assembly are RM3-M3's identity
(the reasoner); nothing of that belongs here.

Determinism (RM3 spec §5; contract package §5): scored precedents are ordered by ``relevance_score``
**descending**, tie-broken by episode ``content_hash`` **ascending** — a total order, so an identical
query + identical corpus + identical ``precedent_model_version`` always yield an identical ranking.

Precedent source (ratified RM1 correction): the retriever consumes the **embedded** ``DesignInput``
carried on each episode (``episode.design_input``). It never reconstructs engineering features from
free-text summaries or planner outputs. An episode without an embedded ``DesignInput`` (a legacy
``1.0.0`` episode) carries no comparable engineering features and is therefore not scorable by this
feature-based mechanism; such episodes are simply absent from the ranking. This is a structural
property of feature-based retrieval, **not** a retention or eligibility classification (that policy is
deferred per the ratified RM1-correction note): the episode is neither mutated, removed, nor labeled.

Read-only, pure ranking; no persistence, no caching, no mutation, no ML/embeddings/vector DB, no
Noetica/MiniFlyWire. Depends only on the frozen contracts, the RM2 read side (read-only), the RM3-M1
model, and stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mini_prometheus._contracts import DesignInput, ManufacturingEpisode
from mini_prometheus.experience import episode_store_reader
from mini_prometheus.precedent.precedent_model import PrecedentModel, relevance


@dataclass(frozen=True)
class RankedPrecedent:
    """One scored precedent, in ranked position: the stored episode and its per-mille relevance.

    Mechanism-level hand-off to the reasoner (RM3-M3); intentionally **not** a contract type. Rank is
    the entry's position in the returned list (relevance desc, tie-break by episode ``content_hash``
    asc), so it is not duplicated as a field here — the reasoner assigns the contract ``rank``.
    """

    episode: ManufacturingEpisode
    relevance_score: int  # per-mille integer in [0, 1000], from precedent_model.relevance


def rank(
    query: DesignInput,
    corpus: list[ManufacturingEpisode],
    model: PrecedentModel | None = None,
    top_k: int | None = None,
) -> list[RankedPrecedent]:
    """Deterministically rank ``corpus`` by relevance of each episode's embedded design to ``query``.

    Pure (no I/O, no mutation of ``corpus``): scores every *scorable* episode (one that carries an
    embedded ``design_input``) with the frozen ``precedent_model`` and returns them ordered by
    ``relevance_score`` descending, tie-broken by episode ``content_hash`` ascending — a total order.
    ``top_k`` (if given, must be ``>= 0``) truncates to the first ``K`` of that order; ``None`` returns
    the full ranking. ``model`` defaults to the frozen ``precedent_model`` default.
    """
    if top_k is not None and top_k < 0:
        raise ValueError(f"top_k must be >= 0, got {top_k}")
    scored = [
        RankedPrecedent(episode=e, relevance_score=relevance(query, e.design_input, model))
        for e in corpus
        if e.design_input is not None
    ]
    scored.sort(key=lambda rp: (-rp.relevance_score, rp.episode.content_hash))
    return scored if top_k is None else scored[:top_k]


def retrieve(
    query: DesignInput,
    store_path: str | Path | None = None,
    model: PrecedentModel | None = None,
    top_k: int | None = None,
) -> list[RankedPrecedent]:
    """Load the episode corpus read-only (RM2 reader) and rank it against ``query``.

    Thin read-only acquisition over ``rank``: loads and integrity-verifies the corpus via the RM2
    ``episode_store_reader`` (a missing store yields an empty ranking), then applies the pure ranking.
    Performs no write, mutation, persistence, or caching.
    """
    corpus = episode_store_reader.load(store_path)
    return rank(query, corpus, model=model, top_k=top_k)
