"""RM3-M1: the deterministic, versioned engineering relevance model (domain content).

Scores how *relevant* one manufacturing design is to another, over the **frozen feature set** only
(material, stock form, ordered declared-operation sequence, quantity, tolerances; geometry excluded —
RM3 spec §5). Relevance is a per-mille **integer in [0, 1000]** (1000 = identical), computed with
**integer arithmetic only** so identical inputs always yield an identical integer (no floating-point
identity instability, RM3-M1 requirement). Pure and deterministic: no I/O, persistence, retrieval,
reasoning, report generation, ML, embeddings, or randomness.
"""
from __future__ import annotations

from dataclasses import dataclass

from mini_prometheus._contracts import DesignInput

PRECEDENT_MODEL_VERSION = "1.0.0"


@dataclass(frozen=True)
class PrecedentModel:
    """A versioned set of fixed feature weights. Weights sum to 1000 so identical designs score 1000."""

    version: str
    weight_material: int
    weight_stock_form: int
    weight_operations: int
    weight_quantity: int
    weight_tolerances: int


def default_model() -> PrecedentModel:
    """The frozen v1.0.0 model. Weights sum to exactly 1000 (material+stock+ops+quantity+tolerances)."""
    return PrecedentModel(
        version=PRECEDENT_MODEL_VERSION,
        weight_material=300,
        weight_stock_form=150,
        weight_operations=350,
        weight_quantity=100,
        weight_tolerances=100,
    )


def relevance(query: DesignInput, precedent: DesignInput, model: PrecedentModel | None = None) -> int:
    """Deterministic per-mille relevance in [0, 1000]; 1000 iff every frozen feature matches."""
    m = model or default_model()
    total = (
        _material_component(query, precedent, m.weight_material)
        + _stock_form_component(query, precedent, m.weight_stock_form)
        + _operations_component(query, precedent, m.weight_operations)
        + _quantity_component(query, precedent, m.weight_quantity)
        + _tolerances_component(query, precedent, m.weight_tolerances)
    )
    return max(0, min(1000, total))


# --- deterministic, integer-only feature components -------------------------------------------------

def _norm(text: str) -> str:
    return text.strip().lower()


def _material_component(q: DesignInput, p: DesignInput, w: int) -> int:
    if _norm(q.material) == _norm(p.material):
        return w
    if q.material_code and p.material_code and _norm(q.material_code) == _norm(p.material_code):
        return w
    return 0


def _stock_form_component(q: DesignInput, p: DesignInput, w: int) -> int:
    return w if q.stock_form == p.stock_form else 0


def _lcs_length(a: list, b: list) -> int:
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]


def _operations_component(q: DesignInput, p: DesignInput, w: int) -> int:
    qa = [op.op for op in q.declared_operations]
    pb = [op.op for op in p.declared_operations]
    longest = max(len(qa), len(pb))
    if longest == 0:
        return w
    return w * _lcs_length(qa, pb) // longest


def _quantity_component(q: DesignInput, p: DesignInput, w: int) -> int:
    if q.quantity == p.quantity:
        return w
    return w * min(q.quantity, p.quantity) // max(q.quantity, p.quantity)


def _tolerances_component(q: DesignInput, p: DesignInput, w: int) -> int:
    qt, pt = q.tolerances, p.tolerances
    if qt is None and pt is None:
        return w
    if qt is None or pt is None:
        return 0
    # micrometers as integers: deterministic for identical inputs; no float in the arithmetic path.
    a = round(qt.general_tolerance_mm * 1000)
    b = round(pt.general_tolerance_mm * 1000)
    if a == b:
        return w
    return w * min(a, b) // max(a, b)
