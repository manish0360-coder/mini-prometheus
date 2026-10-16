"""RM15 EC1 — deterministic ENRICHED corpus generator + materialized fixture (read-only over RM1–RM14).

Produces a fully deterministic corpus of ``ManufacturingEpisode``s under RM8's ``constrained_model()``
(declared precedence + tolerance feasibility; **no RM9 availability**) by enumerating a bounded design
space and running the **unchanged** RM1 pipeline (intake -> planner -> oracle). This is the fresh corpus
for the RM15 enriched-oracle compounding re-evaluation; it does NOT touch the frozen RM5 corpus, harness,
protocol, arms, runner, or any RM5 artifact, and it writes no episode store.

Verdicts now span four drivers, read empirically from the oracle's own ``reason_codes`` (the generator
hard-codes NO manufacturing rule — it classifies what the frozen oracle actually returned):
- MANUFACTURABLE (no reason);
- material-single  (only MATERIAL_UNSUPPORTED, NOT_MANUFACTURABLE);
- precedence-single (only PRECEDENCE_VIOLATION, PLAN_INVALID);
- tolerance-single (only TOLERANCE_UNSUPPORTED, NOT_MANUFACTURABLE);
- multi-cause      (more than one reason) — kept for the aggregate, excluded from per-axis attribution.

The frozen §9 adequacy gates are enforced fail-closed (``verify_guarantees`` raises with the EXACT
deficiency; the only permitted response is enlarging the design-space enumeration, blind to any
Arm2/Arm3 outcome — never weakening a gate). Partitioning reuses the frozen RM5 ``partition`` module.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturabilityVerdictStatus,
    ManufacturingEpisode,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.experiment.partition import HOLD_OUT_MODULO, Partition, checkpoint_id, partition
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import constrained_model
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration.episode_store import SCHEMA_VERSION as EPISODE_SCHEMA_VERSION
from mini_prometheus.orchestration.episode_store import build_episode
from mini_prometheus.precedent.precedent_model import default_model as precedent_default_model
from mini_prometheus.precedent.precedent_model import relevance

GENERATOR_VERSION = "1.0.0"
_FIXED_PRODUCED_AT = "2026-01-01T00:00:00+00:00"
_ANALOGOUS_MIN = 1
_IDENTICAL = 1000

_MANUFACTURABLE = ManufacturabilityVerdictStatus.MANUFACTURABLE.value

# Frozen §9 held-out-analogous adequacy gates (finite-corpus adequacy, NOT statistical power).
GATE_MANUFACTURABLE = 30
GATE_SINGLE_CAUSE_PER_AXIS = 10

# --- deterministic design space (fixed enumeration order) -------------------------------------------
# Supported materials carry a code; unsupported carry None (material-driven NOT).
_MATERIALS = [
    ("Aluminum 6061", "AL6061"),
    ("Steel 1018", "ST1018"),
    ("Brass 360", "BR360"),
    ("Titanium Grade 5", None),   # UNSUPPORTED
    ("Inconel 718", None),        # UNSUPPORTED
]
# Operation profiles. VALID = cut_stock first, inspect last. INVALID = same op multiset, broken order
# (so each INVALID is a controlled precedence near-miss of its VALID twin). Tolerance-bearing op sets
# the governing capability min: mill 0.02, drill 0.05, lathe(turn) 0.01; none => no tolerance check.
_OP_PROFILES = [
    ("V_mill",     [ProcessOp.cut_stock, ProcessOp.face_mill, ProcessOp.inspect]),
    ("V_drill",    [ProcessOp.cut_stock, ProcessOp.drill, ProcessOp.inspect]),
    ("V_turn",     [ProcessOp.cut_stock, ProcessOp.turn, ProcessOp.inspect]),
    ("V_millturn", [ProcessOp.cut_stock, ProcessOp.face_mill, ProcessOp.turn, ProcessOp.inspect]),
    ("V_none",     [ProcessOp.cut_stock, ProcessOp.deburr, ProcessOp.inspect]),
    ("I_mill",     [ProcessOp.face_mill, ProcessOp.cut_stock, ProcessOp.inspect]),   # cut_stock not first
    ("I_drill",    [ProcessOp.cut_stock, ProcessOp.inspect, ProcessOp.drill]),       # inspect not last
    ("I_turn",     [ProcessOp.turn, ProcessOp.cut_stock, ProcessOp.inspect]),        # cut_stock not first
]
_TOLERANCES = [0.1, 0.05, 0.02, 0.005]   # span feasible/infeasible across the capability minimums
_STOCK_FORMS = [StockForm.block, StockForm.bar, StockForm.plate]
_QUANTITIES = [10, 100]


def _requests() -> list[ManufacturingRequest]:
    """Deterministic enumeration of the enriched design space (fixed nested order)."""
    out: list[ManufacturingRequest] = []
    counter = 0
    for material, code in _MATERIALS:
        for _profile, ops in _OP_PROFILES:
            for tol in _TOLERANCES:
                for stock in _STOCK_FORMS:
                    for qty in _QUANTITIES:
                        counter += 1
                        out.append(
                            ManufacturingRequest(
                                schema_version="1.0.0",
                                request_id=f"00000000-0000-0000-0000-{counter:012d}",
                                material=material,
                                material_code=code,
                                stock_form=stock,
                                declared_operations=[DeclaredOperation(op=o) for o in ops],
                                quantity=qty,
                                tolerances=Tolerances(general_tolerance_mm=tol),
                            )
                        )
    return out


def generate() -> list[ManufacturingEpisode]:
    """Deterministically generate the enriched corpus under constrained_model() (frozen RM1 pipeline)."""
    model = constrained_model()
    oracle = ManufacturabilityOracle()
    episodes: list[ManufacturingEpisode] = []
    for request in _requests():
        design_input = intake(request, produced_at=_FIXED_PRODUCED_AT)
        task, production_plan = planner.plan(design_input, model, produced_at=_FIXED_PRODUCED_AT)
        verdict = oracle.verify(production_plan, model)
        episodes.append(
            build_episode(
                task, design_input, production_plan, verdict, model.version,
                produced_at=_FIXED_PRODUCED_AT, plan_ms=0.0, verify_ms=0.0,
            )
        )
    episodes.sort(key=lambda e: e.content_hash)
    return episodes


# --- empirical verdict-axis classification (reads the oracle's own reason_codes) --------------------

def classify(episode: ManufacturingEpisode) -> str:
    """The verdict driver read from the frozen oracle's output (no manufacturing rule re-implemented)."""
    if episode.verdict.status == _MANUFACTURABLE:
        return "MANUFACTURABLE"
    reasons = list(episode.verdict.reason_codes)
    if len(reasons) == 1:
        return {
            "MATERIAL_UNSUPPORTED": "material",
            "PRECEDENCE_VIOLATION": "precedence",
            "TOLERANCE_UNSUPPORTED": "tolerance",
        }.get(reasons[0], "other")
    return "multi"


# --- §9 adequacy gates (fail-closed; report exact deficiency, never weaken) --------------------------

@dataclass(frozen=True)
class GuaranteeReport:
    n_total: int
    n_experience: int
    n_held_out: int
    held_out_analogous: int
    held_out_non_analogous: int
    class_counts_held_out_analogous: dict[str, int]
    near_miss_material: int
    near_miss_precedence: int
    near_miss_tolerance: int
    cross_partition_exact_duplicates: int


def _by_hash(episodes: list[ManufacturingEpisode]) -> dict[str, ManufacturingEpisode]:
    return {e.content_hash: e for e in episodes}


def _best_relevance_to_experience(
    query: ManufacturingEpisode, experience: list[ManufacturingEpisode]
) -> int:
    pmodel = precedent_default_model()
    best = 0
    if query.design_input is None:
        return 0
    for ep in experience:
        if ep.design_input is None or ep.design_ref.content_hash == query.design_ref.content_hash:
            continue  # exclude exact design identity
        best = max(best, relevance(query.design_input, ep.design_input, pmodel))
    return best


def _ops_tuple(e: ManufacturingEpisode) -> tuple[str, ...]:
    di = e.design_input
    assert di is not None
    return tuple(o.op.value for o in di.declared_operations)


def _tol(e: ManufacturingEpisode) -> float | None:
    di = e.design_input
    assert di is not None
    return di.tolerances.general_tolerance_mm if di.tolerances is not None else None


def _near_miss_counts(episodes: list[ManufacturingEpisode]) -> tuple[int, int, int]:
    """Controlled near-miss pairs per axis: two designs identical except the one axis-feature, whose
    verdicts flip along that axis (MANUFACTURABLE vs the axis's single-cause verdict)."""
    cls = {e.content_hash: classify(e) for e in episodes}
    valid = [e for e in episodes if e.design_input is not None]

    # material: same (ops, tol, stock, qty), differ in material -> MANUFACTURABLE vs material-single
    mat: dict[tuple, set[str]] = defaultdict(set)
    for e in valid:
        di = e.design_input
        assert di is not None
        mkey = (_ops_tuple(e), _tol(e), di.stock_form.value, di.quantity)
        if cls[e.content_hash] in ("MANUFACTURABLE", "material"):
            mat[mkey].add(cls[e.content_hash])
    near_material = sum(1 for v in mat.values() if {"MANUFACTURABLE", "material"} <= v)

    # precedence: same (material, op MULTISET, tol, stock, qty), differ in op ORDER -> MANUF vs precedence
    prec: dict[tuple, set[str]] = defaultdict(set)
    for e in valid:
        di = e.design_input
        assert di is not None
        pkey = (di.material, tuple(sorted(_ops_tuple(e))), _tol(e), di.stock_form.value, di.quantity)
        if cls[e.content_hash] in ("MANUFACTURABLE", "precedence"):
            prec[pkey].add(cls[e.content_hash])
    near_precedence = sum(1 for v in prec.values() if {"MANUFACTURABLE", "precedence"} <= v)

    # tolerance: same (material, ops, stock, qty), differ in tolerance -> MANUFACTURABLE vs tolerance
    tol: dict[tuple, set[str]] = defaultdict(set)
    for e in valid:
        di = e.design_input
        assert di is not None
        tkey = (di.material, _ops_tuple(e), di.stock_form.value, di.quantity)
        if cls[e.content_hash] in ("MANUFACTURABLE", "tolerance"):
            tol[tkey].add(cls[e.content_hash])
    near_tolerance = sum(1 for v in tol.values() if {"MANUFACTURABLE", "tolerance"} <= v)

    return near_material, near_precedence, near_tolerance


def verify_guarantees(episodes: list[ManufacturingEpisode], part: Partition) -> GuaranteeReport:
    """Assert the frozen §9 adequacy gates on the HELD-OUT analogous set. Raise with the exact
    deficiency on any failure (never weaken a gate)."""
    by_hash = _by_hash(episodes)
    exp = [by_hash[hx] for hx in part.experience]
    hel = [by_hash[hx] for hx in part.held_out]

    exp_designs = {e.design_ref.content_hash for e in exp}
    hel_designs = {e.design_ref.content_hash for e in hel}
    cross_dups = len(exp_designs & hel_designs)

    analogous: list[ManufacturingEpisode] = []
    non_analogous = 0
    for hq in hel:
        best = _best_relevance_to_experience(hq, exp)
        if _ANALOGOUS_MIN <= best < _IDENTICAL:
            analogous.append(hq)
        else:
            non_analogous += 1

    counts: dict[str, int] = defaultdict(int)
    for e in analogous:
        counts[classify(e)] += 1

    nm_mat, nm_prec, nm_tol = _near_miss_counts(episodes)

    report = GuaranteeReport(
        n_total=len(episodes),
        n_experience=len(exp),
        n_held_out=len(hel),
        held_out_analogous=len(analogous),
        held_out_non_analogous=non_analogous,
        class_counts_held_out_analogous=dict(counts),
        near_miss_material=nm_mat,
        near_miss_precedence=nm_prec,
        near_miss_tolerance=nm_tol,
        cross_partition_exact_duplicates=cross_dups,
    )

    problems: list[str] = []
    if cross_dups != 0:
        problems.append(f"cross-partition exact design duplicates: {cross_dups} (must be 0)")
    if counts["MANUFACTURABLE"] < GATE_MANUFACTURABLE:
        problems.append(
            f"held-out analogous MANUFACTURABLE: {counts['MANUFACTURABLE']} (need >= {GATE_MANUFACTURABLE})")
    for axis in ("material", "precedence", "tolerance"):
        if counts[axis] < GATE_SINGLE_CAUSE_PER_AXIS:
            problems.append(
                f"held-out analogous single-cause {axis}: {counts[axis]} (need >= {GATE_SINGLE_CAUSE_PER_AXIS})")
    if nm_mat < 1:
        problems.append("no controlled material near-miss pair")
    if nm_prec < 1:
        problems.append("no controlled precedence near-miss pair")
    if nm_tol < 1:
        problems.append("no controlled tolerance near-miss pair")
    if problems:
        raise ValueError("RM15 enriched-corpus adequacy deficiency (do NOT weaken gates): " + "; ".join(problems))
    return report


def build_fixture(dest_dir: str | Path) -> GuaranteeReport:
    """Materialize the RM15 fixture (episodes.jsonl, partition.json, checkpoint.json) deterministically."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    episodes = generate()
    part = partition(episodes)
    report = verify_guarantees(episodes, part)

    lines = [h.canonical_json(h.to_contract_dict(e)) for e in episodes]
    (dest / "episodes.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (dest / "partition.json").write_text(
        json.dumps({"experience": list(part.experience), "held_out": list(part.held_out)}, indent=2) + "\n",
        encoding="utf-8",
    )
    (dest / "checkpoint.json").write_text(
        json.dumps(
            {
                "checkpoint_id": checkpoint_id(part),
                "generator_version": GENERATOR_VERSION,
                "episode_schema_version": EPISODE_SCHEMA_VERSION,
                "fixed_produced_at": _FIXED_PRODUCED_AT,
                "hold_out_modulo": HOLD_OUT_MODULO,
                "capability_model_version": constrained_model().version,
                "precedent_model_version": precedent_default_model().version,
                "analogous_definition": {"min_relevance": _ANALOGOUS_MIN, "exclude_relevance": _IDENTICAL},
                "adequacy_gates": {
                    "manufacturable": GATE_MANUFACTURABLE,
                    "single_cause_per_axis": GATE_SINGLE_CAUSE_PER_AXIS,
                },
                "n_total": report.n_total,
                "n_experience": report.n_experience,
                "n_held_out": report.n_held_out,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report
