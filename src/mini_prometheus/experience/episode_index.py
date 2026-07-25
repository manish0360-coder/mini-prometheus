"""RM2-M2: deterministic index over episodes, keyed by the composite reuse key.

``ReuseKey = (design_input_identity_hash, capability_model_version)`` (plan §0.3). A key is equal
across two runs exactly when the manufacturing intent **and** the capability model match — so reuse can
never serve a plan computed under a different capability model. This is a transient in-memory index
built from a list of episodes; it holds no persistent state, no retention, and no query engine (Law 6).
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import DesignInput, ManufacturingEpisode

ReuseKey = tuple[str, str]  # (design_input_identity_hash, capability_model_version)


def key_for_episode(episode: ManufacturingEpisode) -> ReuseKey:
    """The reuse key of a stored episode: (design_ref.content_hash, capability_model_version)."""
    return (episode.design_ref.content_hash, episode.capability_model_version)


def design_input_key(design_input: DesignInput, capability_model_version: str) -> ReuseKey:
    """The reuse key of a new request: (hash(design_input identity), capability_model_version).

    Equals ``key_for_episode`` for a matching episode, because RM1 sets an episode's ``design_ref``
    content_hash to ``content_hash(design_input_identity(design_input))``.
    """
    return (h.content_hash(h.design_input_identity(design_input)), capability_model_version)


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
