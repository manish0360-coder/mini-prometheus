"""RM9 x RM2 — availability is NOT part of the RM2 reuse key; RM2's existing re-derivation guard is the
protection. RM2 code is unchanged. The frozen expectations:

A. irrelevant availability  -> the same plan is re-derived -> reuse still succeeds;
B. availability changes the selected machine -> a different plan -> reuse fails closed;
C. the stored plan uses a machine that is now unavailable -> the re-derived plan differs (reuse fails
   closed) and verifying the stored plan now yields RESOURCE_UNAVAILABLE -> a stale result is never served.
"""
from __future__ import annotations

import pytest

from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.orchestration.reuse_runner import ExperienceConsistencyError, run_with_reuse

import support
from support import FIXED_TIME


def _request():
    return support.build_request(support.load_json("engineer_request_machined_bracket.json"))


def _twin() -> ProcessCapabilityModel:
    base = default_model()
    return ProcessCapabilityModel(
        version=base.version, op_capability=base.op_capability,
        resources={**base.resources, "mill02": frozenset({"cap.mill", "cap.drill"})},
        supported_materials=base.supported_materials,
    )


def _store_first(model, store):
    first = run_with_reuse(_request(), capability_model=model, produced_at=FIXED_TIME, store_path=str(store))
    assert not first.reused and first.status == "MANUFACTURABLE"
    return first


def test_A_irrelevant_availability_reuse_still_succeeds(tmp_path):
    store = tmp_path / "episodes.jsonl"
    first = _store_first(default_model(), store)
    again = run_with_reuse(_request(), capability_model=with_unavailable_resources(default_model(), ["lathe01"]),
                           produced_at=FIXED_TIME, store_path=str(store))
    assert again.reused and again.status == "MANUFACTURABLE"
    assert again.plan.content_hash == first.plan.content_hash


def test_B_changed_machine_selection_makes_reuse_fail_closed(tmp_path):
    store = tmp_path / "episodes.jsonl"
    _store_first(_twin(), store)                                          # stored plan uses mill01
    with pytest.raises(ExperienceConsistencyError):
        run_with_reuse(_request(), capability_model=with_unavailable_resources(_twin(), ["mill01"]),
                       produced_at=FIXED_TIME, store_path=str(store))


def test_C_stale_stored_plan_is_never_served(tmp_path):
    store = tmp_path / "episodes.jsonl"
    first = _store_first(default_model(), store)                          # stored plan uses mill01
    down = with_unavailable_resources(default_model(), ["mill01"])
    with pytest.raises(ExperienceConsistencyError):                       # re-derived plan differs
        run_with_reuse(_request(), capability_model=down, produced_at=FIXED_TIME, store_path=str(store))
    verdict = ManufacturabilityOracle().verify(first.plan, down)          # and the verdict would change
    assert verdict.status == "NOT_MANUFACTURABLE" and verdict.reason_codes == ["RESOURCE_UNAVAILABLE"]
