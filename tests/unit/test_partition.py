"""RM5 C1 unit tests: deterministic content-addressed partitioning + checkpoint identity.

Operates on the committed fixture corpus (loaded + integrity-verified via the RM2 reader), so it is fast
and does not regenerate. Pins content-addressed design-level integrity, leakage-safe disjointness, and
that the partition reproduces the committed checkpoint_id.
"""
from __future__ import annotations

import json
import pathlib

from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import partition as P

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm5_corpus"
_EPISODES = load(_FIXTURE / "episodes.jsonl")


def test_design_bucket_is_deterministic_and_bounded():
    hx = "sha256:" + "a" * 64
    assert P.design_bucket(hx) == P.design_bucket(hx)
    assert 0 <= P.design_bucket(hx) < P.HOLD_OUT_MODULO


def test_partition_content_addressed_with_design_integrity():
    part = P.partition(_EPISODES)
    by_hash = {e.content_hash: e for e in _EPISODES}
    exp_designs = {by_hash[hx].design_ref.content_hash for hx in part.experience}
    hel_designs = {by_hash[hx].design_ref.content_hash for hx in part.held_out}
    assert exp_designs.isdisjoint(hel_designs)  # a design never spans the boundary (VG3/VG4 basis)
    assert set(part.experience).isdisjoint(set(part.held_out))
    assert len(part.experience) + len(part.held_out) == len(_EPISODES)


def test_checkpoint_id_matches_committed_fixture():
    committed = json.loads((_FIXTURE / "checkpoint.json").read_text(encoding="utf-8"))
    assert P.checkpoint_id(P.partition(_EPISODES)) == committed["checkpoint_id"]
