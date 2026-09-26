"""RM10 zero-diff probe — the RM8/RM9 (no-duration) paths, fingerprinted against rm9-complete.

READ-ONLY: it computes a fingerprint, never writes one. The frozen golden
(``tests/fixtures/rm10_rm9_baseline_golden.json``) was generated ONCE by running this exact file against the
``rm9-complete`` tree (commit ``6ca4d22``) in the project verifier image, and is frozen by digest in
``tests/unit/test_rm10_no_duration_zero_diff.py``. It complements the RM8 golden (default model and R*) by
covering the constrained (RM8 ECR) and availability (RM9) paths for requests that declare no duration.
"""
from __future__ import annotations

import copy
import hashlib
import json

import support
from mini_prometheus import _hashing as h
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    constrained_model,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner

FIXED_TIME = "2026-07-23T00:00:00+00:00"


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _twin() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(version=base.version, op_capability=base.op_capability,
                                  resources={**base.resources, "mill02": frozenset({"cap.mill", "cap.drill"})},
                                  supported_materials=base.supported_materials)


def _no_lathe() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(version=base.version, op_capability=base.op_capability,
                                  resources={k: v for k, v in base.resources.items() if k != "lathe01"},
                                  supported_materials=base.supported_materials)


def _request(ops=None, tolerance=None):
    raw = copy.deepcopy(support.load_json("engineer_request_machined_bracket.json"))
    if ops is not None:
        raw["declared_operations"] = [{"op": o} for o in ops]
    if tolerance is not None:
        raw["tolerances"] = {"general_tolerance_mm": tolerance}
    return support.build_request(raw)


def scenarios():
    misordered = ["face_mill", "cut_stock", "drill", "inspect"]
    return [
        ("default", default_model(), _request()),
        ("constrained", constrained_model(), _request()),
        ("constrained_tight_misordered", constrained_model(), _request(misordered, 0.001)),
        ("constrained_tolerance_0_03", constrained_model(), _request(tolerance=0.03)),
        ("avail_mill01_down", with_unavailable_resources(default_model(), ["mill01"]), _request()),
        ("avail_lathe01_down_irrelevant", with_unavailable_resources(default_model(), ["lathe01"]), _request()),
        ("avail_mill01_cmm01_down", with_unavailable_resources(default_model(), ["mill01", "cmm01"]), _request()),
        ("avail_twin_reroute", with_unavailable_resources(_twin(), ["mill01"]), _request()),
        ("avail_twin_mill02_down", with_unavailable_resources(_twin(), ["mill02"]), _request()),
        ("avail_no_lathe_turn", with_unavailable_resources(_no_lathe(), ["mill01"]), _request(["turn"])),
        ("avail_constrained_combined", with_unavailable_resources(constrained_model(), ["mill01"]),
         _request(misordered, 0.001)),
    ]


def fingerprint() -> dict:
    oracle = ManufacturabilityOracle()
    rows = []
    for name, model, request in scenarios():
        design_input = intake(request, produced_at=FIXED_TIME)
        _task, plan = planner.plan(design_input, model, produced_at=FIXED_TIME)
        verdict = oracle.verify(plan, model)
        rows.append({"case": name, "plan_content_hash": plan.content_hash,
                     "plan_full": _sha(h.to_contract_dict(plan)), "verdict": h.to_contract_dict(verdict)})
    return {"n": len(rows), "digest": _sha(rows), "rows": rows}
