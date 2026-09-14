"""RM5 C0 unit tests: deterministic corpus generator + committed fixture integrity + U2 guarantees.

The generator produces the corpus under R* (default_model minus lathe01) via the unchanged RM1 pipeline;
these tests pin its determinism, the frozen U2 guarantees (both verdict classes, analogous non-identical
held-out cases per class, near-miss pairs, no cross-partition duplicates), leakage-safe content-addressed
partitioning, and that a fresh generation reproduces the committed checkpoint (AC8).
"""
from __future__ import annotations

import functools
import json
import pathlib

from mini_prometheus.experiment import corpus

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm5_corpus"


@functools.lru_cache(maxsize=1)
def _gen():
    """Generate the corpus once for the whole module (generation is deterministic but expensive)."""
    return tuple(corpus.generate())


def test_generation_is_deterministic():
    a = corpus.generate()
    b = corpus.generate()
    assert [e.content_hash for e in a] == [e.content_hash for e in b]
    assert corpus.checkpoint_id(corpus.partition(a)) == corpus.checkpoint_id(corpus.partition(b))


def test_r_star_regime_is_default_minus_lathe():
    m = corpus.r_star()
    assert m.version == "2.0.0"
    assert "lathe01" not in m.resources  # the removed resource -> `turn` is NOT_MANUFACTURABLE under R*
    assert "lathe01" in corpus.default_model().resources  # sanity: it exists in the base
    assert "lathe01" not in corpus.r_star_descriptor()["resources"]


def test_u2_guarantees_hold():
    eps = list(_gen())
    rep = corpus.verify_guarantees(eps, corpus.partition(eps))  # raises on any deficiency
    assert rep.manufacturable > 0 and rep.not_manufacturable > 0  # both verdict classes
    assert rep.analogous_manufacturable_held_out > 0  # analogous held-out MANUFACTURABLE with a precedent
    assert rep.analogous_not_manufacturable_held_out > 0  # analogous held-out NOT with a precedent
    assert rep.near_miss_pairs > 0  # near-miss analogous pairs with differing verdicts
    assert rep.cross_partition_exact_duplicates == 0


def test_committed_fixture_reproduces_checkpoint():
    eps = list(_gen())
    committed = json.loads((_FIXTURE / "checkpoint.json").read_text(encoding="utf-8"))
    assert corpus.checkpoint_id(corpus.partition(eps)) == committed["checkpoint_id"]  # AC8
    assert committed["n_total"] == len(eps)
    lines = [ln for ln in (_FIXTURE / "episodes.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == len(eps)
    assert committed["capability_regime"]["derivation"] == "default_model() minus resource 'lathe01'"
