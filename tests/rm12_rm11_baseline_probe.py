"""RM12 zero-diff probe — RM11 multi-job scheduling, fingerprinted against rm11-complete.

READ-ONLY: it computes a fingerprint, never writes one. The frozen golden
(``tests/fixtures/rm12_rm11_baseline_golden.json``) was generated ONCE by running this exact file
against the ``rm11-complete`` tree (commit ``40d6066``) in the project verifier image, and is frozen
by digest in ``tests/unit/test_rm12_no_downtime_zero_diff.py``. It uses only the RM11 API, so the
same scenarios run unchanged on RM12: with no downtime — and with downtime only on machines the job
set does not use — RM12 must reproduce every row byte for byte (rule, input identity, digest,
schedule, makespan, lower bound, refusals and CLI report).
"""

from __future__ import annotations

import copy
import hashlib
import json

import support
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    constrained_model,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_scheduling.model import schedule_view
from mini_prometheus.orchestration.schedule_runner import render, schedule_requests

FIXED_TIME = "2026-07-23T00:00:00+00:00"
ID_A = "aaaaaaaa-0000-4000-8000-000000000001"
ID_B = "bbbbbbbb-0000-4000-8000-000000000002"
ID_C = "cccccccc-0000-4000-8000-000000000003"


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _twin() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(
        version=base.version,
        op_capability=base.op_capability,
        resources={**base.resources, "mill02": frozenset({"cap.mill", "cap.drill"})},
        supported_materials=base.supported_materials,
    )


def _job(request_id, operations, material="Aluminum 6061"):
    declared = []
    for op, duration in operations:
        entry = {"op": op}
        if duration is not None:
            entry["params"] = {"duration_min": duration}
        declared.append(entry)
    return support.build_request(
        {
            "schema_version": "1.0.0",
            "request_id": request_id,
            "material": material,
            "stock_form": "block",
            "declared_operations": declared,
            "quantity": 1,
        }
    )


def _three():
    names = ("rm11_jobs/job_a.json", "rm11_jobs/job_b.json", "rm11_jobs/job_c.json")
    return [support.build_request(copy.deepcopy(support.load_json(n))) for n in names]


def _timed():
    return [support.build_request(support.load_json("engineer_request_with_durations.json"))]


def scenarios():
    shared = [_job(ID_A, [("cut_stock", 10)]), _job(ID_B, [("cut_stock", 10), ("face_mill", 100)])]
    swapped = [_job(ID_B, [("cut_stock", 10)]), _job(ID_A, [("cut_stock", 10), ("face_mill", 100)])]
    independent = [_job(ID_A, [("face_mill", 100)]), _job(ID_B, [("cut_stock", 5), ("deburr", 5)])]
    return [
        ("three_job", default_model(), _three()),
        ("three_job_reversed_input", default_model(), list(reversed(_three()))),
        ("shared_machine", default_model(), shared),
        ("shared_machine_swapped_ids", default_model(), swapped),
        ("independent_machines", default_model(), independent),
        ("one_job_rm10", default_model(), _timed()),
        ("three_job_twin", _twin(), _three()),
        ("three_job_twin_mill02_down", with_unavailable_resources(_twin(), ["mill02"]), _three()),
        ("three_job_twin_mill01_down", with_unavailable_resources(_twin(), ["mill01"]), _three()),
        ("three_job_constrained", constrained_model(), _three()),
        ("refused_missing_duration", default_model(), [*_three()[:2], _job(ID_C, [("cut_stock", None)])]),
        ("refused_lathe01_down", with_unavailable_resources(default_model(), ["lathe01"]), _three()),
        ("refused_duplicate", default_model(), [_job(ID_A, [("cut_stock", 10)]), _job(ID_A, [("drill", 5)])]),
    ]


def fingerprint(extra_kwargs=None) -> dict:
    """``extra_kwargs(case, model, requests)`` may add keyword arguments to ``schedule_requests``."""
    rows = []
    for case, model, requests in scenarios():
        kwargs = extra_kwargs(case, model, requests) if extra_kwargs else {}
        outcome = schedule_requests(requests, capability_model=model, produced_at=FIXED_TIME, **kwargs)
        schedule = outcome.schedule
        rows.append(
            {
                "case": case,
                "status": str(outcome.status),
                "refusals": [[str(r.reason), r.request_id, r.detail] for r in outcome.refusals],
                "view": schedule_view(schedule) if schedule else None,
                "schedule_input_identity": schedule.schedule_input_identity if schedule else None,
                "schedule_digest": schedule.schedule_digest if schedule else None,
                "machines": sorted({op.resource_id for op in schedule.operations}) if schedule else [],
                "cli": render(outcome),
            }
        )
    return {"n": len(rows), "digest": _sha(rows), "rows": rows}
