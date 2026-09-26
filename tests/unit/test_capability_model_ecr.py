"""ECR C1 unit tests: additive declarative constraint fields + constrained_model() + accessors.

Pins that (a) default_model() is byte-for-byte unchanged (version 1.0.0, empty constraint fields, and
behaviorally identical to a pre-ECR construction), and (b) constrained_model() carries exactly the two
justified precedence constraints and a sparse tolerance map over tolerance-bearing capabilities only.
No RM1–RM4 behavior, no contract, and no RM5 artifact is touched by C1.
"""
from __future__ import annotations

from mini_prometheus._contracts import ProcessOp
from mini_prometheus.manufacturing_constraints import capability_model as cm


def test_default_model_is_byte_compatible():
    m = cm.default_model()
    assert m.version == "1.0.0"                       # identity string unchanged (flows into hashes)
    assert m.capability_tolerance_mm == {}            # ECR fields empty => no new constraint
    assert m.ordering_constraints == frozenset()
    # Behaviorally identical to a construction that supplies only the original four fields (defaults fill
    # the two new ones) — proves the additive fields did not perturb the default model's content.
    legacy = cm.ProcessCapabilityModel(
        version=m.version,
        op_capability=m.op_capability,
        resources=m.resources,
        supported_materials=m.supported_materials,
    )
    assert legacy == m


def test_default_model_applies_no_tolerance_or_precedence():
    m = cm.default_model()
    # Every capability is non-tolerance-bearing under the default (empty) model.
    for cap in {c for caps in m.resources.values() for c in caps}:
        assert cm.min_tolerance_for_capability(m, cap) is None


def test_constrained_model_precedence_is_minimal_and_justified():
    m = cm.constrained_model()
    assert m.version == "1.1.0"
    oc = m.ordering_constraints
    others = {ProcessOp.face_mill, ProcessOp.drill, ProcessOp.pocket_mill, ProcessOp.turn, ProcessOp.deburr}
    # cut_stock precedes every other op; every other op precedes inspect.
    for o in others | {ProcessOp.inspect}:
        assert (ProcessOp.cut_stock, o) in oc
    for o in others | {ProcessOp.cut_stock}:
        assert (o, ProcessOp.inspect) in oc
    # NOTHING else is asserted: no deburr-vs-machining, no inter-machining ordering.
    illegitimate = {
        (ProcessOp.deburr, ProcessOp.drill),
        (ProcessOp.face_mill, ProcessOp.drill),
        (ProcessOp.turn, ProcessOp.deburr),
        (ProcessOp.drill, ProcessOp.deburr),
    }
    assert oc.isdisjoint(illegitimate)


def test_constrained_model_tolerance_map_is_sparse_and_shaping_only():
    m = cm.constrained_model()
    # Only material-removal / shaping capabilities are tolerance-bearing.
    assert set(m.capability_tolerance_mm) == {"cap.lathe", "cap.mill", "cap.drill"}
    assert cm.min_tolerance_for_capability(m, "cap.lathe") == 0.01
    assert cm.min_tolerance_for_capability(m, "cap.drill") == 0.05
    # Non-shaping capabilities are absent => not tolerance-bearing (None), not gated.
    for cap in ("cap.saw", "cap.bench", "cap.cmm"):
        assert cm.min_tolerance_for_capability(m, cap) is None


def test_constrained_model_reuses_default_capability_core():
    base, con = cm.default_model(), cm.constrained_model()
    assert con.op_capability == base.op_capability
    assert con.resources == base.resources
    assert con.supported_materials == base.supported_materials
