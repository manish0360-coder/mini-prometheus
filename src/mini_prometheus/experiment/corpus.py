"""RM5 C0 — deterministic corpus generator + materialized frozen fixture.

Produces a fully deterministic corpus of ``ManufacturingEpisode``s by enumerating a bounded design
space and running the **unchanged** RM1 pipeline (intake -> planner -> oracle) under one fixed
capability regime R* = ``default_model()`` minus ``lathe01`` (frozen pre-registration). Episodes are
built with zeroed timing and a fixed ``produced_at`` so the materialized fixture is byte-deterministic.

The corpus deliberately yields both verdict classes within R* — op-driven NOT (any ``turn`` needs the
absent ``cap.lathe``) and material-driven NOT (unsupported materials) — plus **near-miss analogous
pairs** (designs differing only by one verdict-determining op, e.g. ``drill``<->``turn``), so RM3's
weighted structural similarity is not the oracle's decision function (RM5 spec §2c/§5).

Partitioning is **content-addressed** by ``design_ref.content_hash`` (deterministic bucket) with
design-level integrity; the frozen fixture (episodes + partition + checkpoint) is committed under
``tests/fixtures/rm5_corpus/``. This module is read-only w.r.t. RM1 and never writes the episode store;
``build_fixture`` writes only the committed fixture directory.
"""
from __future__ import annotations

import json
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
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.experiment.partition import HOLD_OUT_MODULO, Partition, checkpoint_id, partition
from mini_prometheus.orchestration.episode_store import SCHEMA_VERSION as EPISODE_SCHEMA_VERSION
from mini_prometheus.orchestration.episode_store import build_episode
from mini_prometheus.precedent.precedent_model import default_model as precedent_default_model
from mini_prometheus.precedent.precedent_model import relevance

GENERATOR_VERSION = "1.0.0"
# Fixed, timing-free timestamp so materialized episode bytes are deterministic (identity excludes it).
_FIXED_PRODUCED_AT = "2026-01-01T00:00:00+00:00"
# "Analogous" per the frozen definition: RM3-relevant but NOT exact identity (relevance in (0, 1000)).
_ANALOGOUS_MIN = 1  # strongly-relevant threshold reused from RM4 critic_model (DEFAULT_RELEVANCE_THRESHOLD)
_IDENTICAL = 1000

_MANUFACTURABLE = ManufacturabilityVerdictStatus.MANUFACTURABLE.value


def r_star():
    """The frozen primary capability regime R*: default_model() minus the lathe resource.

    Op-driven verdict diversity (any ``turn`` -> cap.lathe -> no resource -> NOT_MANUFACTURABLE) plus
    material-driven diversity. R* is a generator parameter (a ProcessCapabilityModel instance); it does
    NOT modify RM1's default_model and is NOT a contract.
    """
    base = default_model()
    # A distinct, valid-SemVer label for RM5's fixed regime (contract requires SemVer). The complete,
    # authoritative regime is recorded in r_star_descriptor() / checkpoint.json — the number is only a label.
    return type(base)(
        version="2.0.0",
        op_capability=base.op_capability,
        resources={rid: caps for rid, caps in base.resources.items() if rid != "lathe01"},
        supported_materials=base.supported_materials,
    )


def r_star_descriptor() -> dict:
    """A JSON-serializable descriptor of R* recorded in the checkpoint (auditability)."""
    m = r_star()
    return {
        "version": m.version,
        "derivation": "default_model() minus resource 'lathe01'",
        "op_capability": {op.value: cap for op, cap in sorted(m.op_capability.items(), key=lambda kv: kv[0].value)},
        "resources": {rid: sorted(caps) for rid, caps in sorted(m.resources.items())},
        "supported_materials": sorted(m.supported_materials),
    }


# --- deterministic design space (fixed enumeration order) -------------------------------------------

_MATERIALS = [
    ("Aluminum 6061", "AL6061"),   # supported
    ("Steel 1018", "ST1018"),      # supported
    ("Brass 360", "BR360"),        # supported
    ("Titanium Grade 5", None),    # UNSUPPORTED -> material-driven NOT
    ("Inconel 718", None),         # UNSUPPORTED -> material-driven NOT
]
_STOCK_FORMS = [StockForm.block, StockForm.bar, StockForm.plate]
# Each sequence starts cut_stock, ends inspect. Sequences differ by one middle op; the `*_TURN`
# variants swap a machining op for `turn` (needs the absent lathe) -> near-miss to their non-turn twin.
_OP_SEQUENCES = [
    ("mill_drill", [ProcessOp.cut_stock, ProcessOp.face_mill, ProcessOp.drill, ProcessOp.inspect]),
    ("mill_turn", [ProcessOp.cut_stock, ProcessOp.face_mill, ProcessOp.turn, ProcessOp.inspect]),
    ("drill_deburr", [ProcessOp.cut_stock, ProcessOp.drill, ProcessOp.deburr, ProcessOp.inspect]),
    ("turn_deburr", [ProcessOp.cut_stock, ProcessOp.turn, ProcessOp.deburr, ProcessOp.inspect]),
    ("pocket_drill", [ProcessOp.cut_stock, ProcessOp.pocket_mill, ProcessOp.drill, ProcessOp.inspect]),
]
_QUANTITIES = [10, 25, 100]
_TOLERANCES = [Tolerances(general_tolerance_mm=0.1), Tolerances(general_tolerance_mm=0.05)]


def _requests() -> list[ManufacturingRequest]:
    """Deterministic enumeration of the design space (fixed nested order)."""
    out: list[ManufacturingRequest] = []
    counter = 0
    for material, code in _MATERIALS:
        for stock in _STOCK_FORMS:
            for _seq_name, ops in _OP_SEQUENCES:
                for qty in _QUANTITIES:
                    for tol in _TOLERANCES:
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
                                tolerances=tol,
                            )
                        )
    return out


def generate() -> list[ManufacturingEpisode]:
    """Deterministically generate the corpus episodes under R* (RM1 pipeline, zeroed timing)."""
    model = r_star()
    oracle = ManufacturabilityOracle()
    episodes: list[ManufacturingEpisode] = []
    for request in _requests():
        design_input = intake(request, produced_at=_FIXED_PRODUCED_AT)
        task, production_plan = planner.plan(design_input, model, produced_at=_FIXED_PRODUCED_AT)
        verdict = oracle.verify(production_plan, model)
        episode = build_episode(
            task, design_input, production_plan, verdict, model.version,
            produced_at=_FIXED_PRODUCED_AT, plan_ms=0.0, verify_ms=0.0,
        )
        episodes.append(episode)
    # deterministic order by content_hash (stable, timing-independent)
    episodes.sort(key=lambda e: e.content_hash)
    return episodes


# --- U2 guarantee verification (fail-closed; do not weaken) ------------------------------------------

@dataclass(frozen=True)
class GuaranteeReport:
    n_total: int
    n_experience: int
    n_held_out: int
    manufacturable: int
    not_manufacturable: int
    analogous_manufacturable_held_out: int
    analogous_not_manufacturable_held_out: int
    near_miss_pairs: int
    cross_partition_exact_duplicates: int


def _by_hash(episodes: list[ManufacturingEpisode]) -> dict[str, ManufacturingEpisode]:
    return {e.content_hash: e for e in episodes}


def verify_guarantees(episodes: list[ManufacturingEpisode], part: Partition) -> GuaranteeReport:
    """Assert the frozen U2 corpus guarantees. Raises ValueError on any deficiency (never weakens)."""
    by_hash = _by_hash(episodes)
    exp = [by_hash[hx] for hx in part.experience]
    hel = [by_hash[hx] for hx in part.held_out]
    pmodel = precedent_default_model()

    # (d) no exact cross-partition design duplicates
    exp_designs = {e.design_ref.content_hash for e in exp}
    hel_designs = {e.design_ref.content_hash for e in hel}
    cross_dups = len(exp_designs & hel_designs)

    # (a/b) analogous (non-identical) held-out cases per verdict class that have an experience precedent
    analog_manu = 0
    analog_not = 0
    for hq in hel:
        if hq.design_input is None:
            continue
        best = 0
        for ep in exp:
            if ep.design_input is None:
                continue
            if ep.design_ref.content_hash == hq.design_ref.content_hash:
                continue  # exact identity excluded from "analogous"
            r = relevance(hq.design_input, ep.design_input, pmodel)
            best = max(best, r)
        if _ANALOGOUS_MIN <= best < _IDENTICAL:
            if hq.verdict.status == _MANUFACTURABLE:
                analog_manu += 1
            else:
                analog_not += 1

    # (c) near-miss pairs: two designs, high relevance (<1000), DIFFERENT oracle verdict
    near_miss = 0
    for i in range(len(episodes)):
        ei = episodes[i]
        if ei.design_input is None:
            continue
        for ej in episodes[i + 1:]:
            if ej.design_input is None:
                continue
            if ei.verdict.status == ej.verdict.status:
                continue
            r = relevance(ei.design_input, ej.design_input, pmodel)
            if _ANALOGOUS_MIN <= r < _IDENTICAL and r >= 700:  # "near": share most features
                near_miss += 1

    manu = sum(1 for e in episodes if e.verdict.status == _MANUFACTURABLE)
    report = GuaranteeReport(
        n_total=len(episodes),
        n_experience=len(exp),
        n_held_out=len(hel),
        manufacturable=manu,
        not_manufacturable=len(episodes) - manu,
        analogous_manufacturable_held_out=analog_manu,
        analogous_not_manufacturable_held_out=analog_not,
        near_miss_pairs=near_miss,
        cross_partition_exact_duplicates=cross_dups,
    )
    problems = []
    if cross_dups != 0:
        problems.append(f"exact cross-partition duplicates: {cross_dups} (must be 0)")
    if analog_manu < 1:
        problems.append("no analogous non-identical MANUFACTURABLE held-out case with an experience precedent")
    if analog_not < 1:
        problems.append("no analogous non-identical NOT_MANUFACTURABLE held-out case with an experience precedent")
    if near_miss < 1:
        problems.append("no near-miss analogous pair with differing verdicts")
    if problems:
        raise ValueError("RM5 corpus guarantee deficiency (do not weaken criteria): " + "; ".join(problems))
    return report


# --- materialization (writes only the committed fixture dir; never the episode store) ---------------

def build_fixture(dest_dir: str | Path) -> GuaranteeReport:
    """Materialize the frozen fixture (episodes.jsonl, partition.json, checkpoint.json) deterministically."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    episodes = generate()
    part = partition(episodes)
    report = verify_guarantees(episodes, part)

    lines = [h.canonical_json(h.to_contract_dict(e)) for e in episodes]  # already sorted by content_hash
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
                "analogous_definition": {"min_relevance": _ANALOGOUS_MIN, "exclude_relevance": _IDENTICAL},
                "capability_regime": r_star_descriptor(),
                "precedent_model_version": precedent_default_model().version,
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
