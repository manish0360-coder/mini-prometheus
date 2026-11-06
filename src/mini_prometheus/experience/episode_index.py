"""RM2-M2: deterministic index over episodes, keyed by the composite reuse key.

``ReuseKey = (design_input_identity_hash, capability_model_version, shop_declaration_hash | None)``
(plan §0.3; third component MP-S1, ADR-0022). A key is equal across two runs exactly when the
manufacturing intent **and** the capability model match — so reuse can never serve a plan computed
under a different capability model. For a LOADED shop declaration the third component is its
``shop_declaration_hash`` (content + evidence basis), so a changed shop or evidence basis is a miss
and is re-planned, never a stale hit. For the built-in code models it is ``None`` and behaviour is
exactly RM2's. This is a transient in-memory index built from a list of episodes; it holds no
persistent state, no retention, and no query engine (Law 6).
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import DesignInput, ManufacturingEpisode

# (design_input_identity_hash, capability_model_version, shop_declaration_hash or None)
ReuseKey = tuple[str, str, str | None]


def key_for_episode(episode: ManufacturingEpisode) -> ReuseKey:
    """The reuse key of a stored episode: (design_ref.content_hash, capability_model_version,
    the shop declaration hash its plan carries, or None)."""
    ref = episode.plan.capability_model_ref
    return (
        episode.design_ref.content_hash,
        episode.capability_model_version,
        ref.shop_declaration_hash if ref is not None else None,
    )


def design_input_key(
    design_input: DesignInput,
    capability_model_version: str,
    *,
    shop_declaration_hash: str | None = None,
) -> ReuseKey:
    """The reuse key of a new request: (hash(design_input identity), capability_model_version,
    shop_declaration_hash).

    Equals ``key_for_episode`` for a matching episode, because RM1 sets an episode's ``design_ref``
    content_hash to ``content_hash(design_input_identity(design_input))`` and MP-S1's planner writes
    the model's declaration hash into the plan.
    """
    return (
        h.content_hash(h.design_input_identity(design_input)),
        capability_model_version,
        shop_declaration_hash,
    )


class EpisodeIndex:
    """A deterministic map ``ReuseKey -> ManufacturingEpisode`` for exact-key retrieval."""

    def __init__(self, by_key: dict[ReuseKey, ManufacturingEpisode]) -> None:
        self._by_key = by_key

    @classmethod
    def build(cls, episodes: list[ManufacturingEpisode]) -> "EpisodeIndex":
        by_key: dict[ReuseKey, ManufacturingEpisode] = {}
        for episode in episodes:
            by_key[key_for_episode(episode)] = episode  # idempotent store => one episode per key
        return cls(by_key)

    def lookup(self, key: ReuseKey) -> ManufacturingEpisode | None:
        return self._by_key.get(key)

    def __len__(self) -> int:
        return len(self._by_key)
