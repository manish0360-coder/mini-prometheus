"""RM5 C3 unit tests: the three arms compose RM1/RM3/RM4 and satisfy the Arm1==Arm2 validity control."""
from __future__ import annotations

import functools
import pathlib

from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import arms, partition
from contracts.python.manufacturing.precedent_report_schema import PrecedentSignal

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm5_corpus"


@functools.lru_cache(maxsize=1)
def _fixture():
    episodes = load(_FIXTURE / "episodes.jsonl")
    part = partition.partition(episodes)
    by_hash = {e.content_hash: e for e in episodes}
    experience = [by_hash[hx] for hx in part.experience]
    held_out = [by_hash[hx] for hx in part.held_out]
    return experience, held_out


def test_cold_start_and_no_precedent_are_exactly_equal():
    experience, held_out = _fixture()
    for episode in held_out:
        a1 = arms.cold_start(episode)
        a2 = arms.no_precedent(episode)
        assert a1.critique_content_hash == a2.critique_content_hash  # Arm1 == Arm2 validity control
        assert a1.signal is PrecedentSignal.NONE and a2.signal is PrecedentSignal.NONE


def test_full_system_is_deterministic_and_coherent():
    experience, held_out = _fixture()
    episode = held_out[0]
    first = arms.full_system(episode, experience)
    second = arms.full_system(episode, experience)
    assert first.critique_content_hash == second.critique_content_hash  # deterministic


def test_full_system_produces_a_real_signal_somewhere():
    """Over the held-out set, Arm 3 must produce at least one non-NONE precedent signal (coverage>0)."""
    experience, held_out = _fixture()
    signals = {arms.full_system(e, experience).signal for e in held_out}
    assert signals - {PrecedentSignal.NONE}  # at least one SUPPORTING or CAUTIONARY


def test_empty_experience_makes_full_system_equal_cold_start():
    """N=0 boundary: an empty experience corpus collapses Arm 3 to the NONE report (curve starts at 0)."""
    _, held_out = _fixture()
    episode = held_out[0]
    assert arms.full_system(episode, []).critique_content_hash == arms.cold_start(episode).critique_content_hash
