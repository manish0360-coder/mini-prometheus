"""RM5 C1 — deterministic content-addressed held-out partitioning + checkpoint identity.

Splits an episode corpus into experience / held-out partitions by **design identity**
(``design_ref.content_hash``) under a fixed rule, with **design-level integrity** (a design never spans
the boundary), and produces a leakage-safe ``checkpoint_id`` over the sorted experience manifest.

Pure and minimal: depends only on the frozen contracts + ``_hashing`` + stdlib. It imports **no** RM1/RM3/
RM4 mechanism and performs no I/O — so the evaluation runner can consume it without pulling in the corpus
generator (which uses the RM1 planner).
"""
from __future__ import annotations

from dataclasses import dataclass

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import ManufacturingEpisode

# An episode is HELD-OUT iff its design bucket == 0 (1-in-HOLD_OUT_MODULO of designs).
HOLD_OUT_MODULO = 4


@dataclass(frozen=True)
class Partition:
    experience: tuple[str, ...]  # episode content_hashes (sorted)
    held_out: tuple[str, ...]


def design_bucket(design_content_hash: str, modulo: int = HOLD_OUT_MODULO) -> int:
    """Deterministic bucket of a design identity ('sha256:<hex>') for the content-addressed split."""
    return int(design_content_hash.split(":", 1)[1], 16) % modulo


def partition(episodes: list[ManufacturingEpisode], modulo: int = HOLD_OUT_MODULO) -> Partition:
    """Content-addressed split by design identity; design-level integrity (a design is wholly in one side)."""
    experience: list[str] = []
    held_out: list[str] = []
    for e in episodes:
        target = held_out if design_bucket(e.design_ref.content_hash, modulo) == 0 else experience
        target.append(e.content_hash)
    return Partition(experience=tuple(sorted(experience)), held_out=tuple(sorted(held_out)))


def checkpoint_id(part: Partition) -> str:
    """Leakage-safe deterministic id over the sorted experience manifest."""
    return h.content_hash({"experience": list(part.experience)})
