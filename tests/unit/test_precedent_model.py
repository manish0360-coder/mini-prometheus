"""RM3-M1 unit tests: the deterministic engineering relevance model."""
from __future__ import annotations

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.precedent.precedent_model import (
    PRECEDENT_MODEL_VERSION,
    default_model,
    relevance,
)

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


def _di(**over):
    return intake(_request(**over), produced_at=FIXED_TIME)


def test_identical_design_is_1000():
    base = _di()
    assert relevance(base, base) == 1000
    # two separate intakes of the same design (different ids/provenance) still score 1000
    assert relevance(_di(), _di()) == 1000


def test_output_is_int_and_in_range():
    base = _di()
    for other in (_di(), _di(material="Steel 1018", material_code="ST1018"), _di(quantity=1),
                  _di(declared_operations=[DeclaredOperation(op=ProcessOp.turn)]), _di(tolerances=None)):
        r = relevance(base, other)
        assert isinstance(r, int)
        assert 0 <= r <= 1000


def test_deterministic_repeated_and_reintaken():
    a, b = _di(quantity=10), _di(quantity=5)
    assert relevance(a, b) == relevance(a, b)
    # identical features via fresh intakes give identical scores
    assert relevance(_di(quantity=10), _di(quantity=5)) == relevance(a, b)


def test_material_mismatch_costs_material_weight():
    # identical except material -> lose the 300 material weight
    assert relevance(_di(), _di(material="Steel 1018", material_code="ST1018")) == 700


def test_stock_form_mismatch_costs_stock_weight():
    assert relevance(_di(), _di(stock_form=StockForm.plate)) == 850


def test_disjoint_operations_cost_operations_weight():
    # ops with no common subsequence -> lose the 350 operations weight
    disjoint = [DeclaredOperation(op=ProcessOp.pocket_mill), DeclaredOperation(op=ProcessOp.turn)]
    assert relevance(_di(), _di(declared_operations=disjoint)) == 650


def test_quantity_ratio_is_deterministic_integer():
    # 100 * min(5,25)//max(5,25) = 20 -> 1000 - 100 + 20 = 920
    assert relevance(_di(), _di(quantity=5)) == 920


def test_tolerance_presence_mismatch_costs_tolerance_weight():
    assert relevance(_di(), _di(tolerances=None)) == 900


def test_model_version_carried():
    assert default_model().version == PRECEDENT_MODEL_VERSION == "1.0.0"
