"""RM15 EC1 unit tests: deterministic enriched corpus + §9 adequacy gates + committed-fixture checkpoint.

Exercises ONLY corpus construction and the frozen adequacy gates — no arms, no runner, no Arm2/Arm3
experimental outcome is computed here (that is EC3/EC4, separately authorized). The corpus is generated
under RM8 ``constrained_model()`` via the unchanged RM1 pipeline; verdict axes are read empirically from
the oracle's reason codes.
"""
from __future__ import annotations

import functools
import json
import pathlib

from mini_prometheus.experiment import enriched_corpus as ec
from mini_prometheus.experiment.partition import checkpoint_id, partition
from mini_prometheus.manufacturing_constraints.capability_model import constrained_model

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm15_corpus"


@functools.lru_cache(maxsize=1)
def _gen():
    return tuple(ec.generate())


def test_generation_is_deterministic():
    a, b = ec.generate(), ec.generate()
    assert [e.content_hash for e in a] == [e.content_hash for e in b]
    assert checkpoint_id(partition(a)) == checkpoint_id(partition(b))


def test_regime_is_constrained_model():
    m = constrained_model()
    assert m.version == "1.1.0"
    assert m.capability_tolerance_mm and m.ordering_constraints  # enriched: tolerance + precedence data
    assert not m.unavailable_resources  # NO RM9 availability in the primary experiment


def test_adequacy_gates_hold():
    eps = list(_gen())
    rep = ec.verify_guarantees(eps, partition(eps))  # raises on any deficiency
    c = rep.class_counts_held_out_analogous
    assert c["MANUFACTURABLE"] >= ec.GATE_MANUFACTURABLE
    for axis in ("material", "precedence", "tolerance"):
        assert c[axis] >= ec.GATE_SINGLE_CAUSE_PER_AXIS
    assert rep.near_miss_material >= 1 and rep.near_miss_precedence >= 1 and rep.near_miss_tolerance >= 1
    assert rep.cross_partition_exact_duplicates == 0
    assert rep.held_out_non_analogous == 0  # every held-out case has a relevant experience precedent


def test_all_verdict_axes_present():
    classes = {ec.classify(e) for e in _gen()}
    assert {"MANUFACTURABLE", "material", "precedence", "tolerance", "multi"} <= classes


def test_single_cause_cases_have_exactly_one_reason():
    for e in _gen():
        label = ec.classify(e)
        if label in ("material", "precedence", "tolerance"):
            assert len(e.verdict.reason_codes) == 1, (label, e.verdict.reason_codes)


def test_committed_fixture_reproduces_checkpoint():
    eps = list(_gen())
    committed = json.loads((_FIXTURE / "checkpoint.json").read_text(encoding="utf-8"))
    assert checkpoint_id(partition(eps)) == committed["checkpoint_id"]
    assert committed["n_total"] == len(eps)
    assert committed["capability_model_version"] == "1.1.0"
    lines = [ln for ln in (_FIXTURE / "episodes.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == len(eps)
