"""MP-S1 AC2 (T2.1-T2.3): file-loaded mirrors reproduce the frozen RM8 golden, READ-ONLY.

The golden (``tests/fixtures/rm8_default_behavior_golden.json``, generated once from ``rm5-complete``)
holds 902 library rows = 451 requests x {``default`` 1.0.0, ``r_star`` 2.0.0}. For every row the
declared mirror fixture must give the same full verdict, and the plan, with its ``capability_model_ref``
removed and its schema_version reset, must re-hash to the golden plan and episode. The golden and its
probe are only read; their own digest pins (``test_rm8_default_zero_diff.py``) stay in force. No golden
exists for ``constrained_model()``, so that mirror is compared live.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json

import mp_s1_support as s
import support
from mini_prometheus import _hashing as h
from mini_prometheus.experiment import corpus
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import constrained_model
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration.episode_store import build_episode

FIXED_TIME = "2026-07-23T00:00:00+00:00"  # the probe's timestamp
GOLDEN = support.FIXTURES / "rm8_default_behavior_golden.json"


def _sha(obj) -> str:  # the probe's own digest function, byte for byte
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _requests():
    out = [
        (
            "engineer_fixture",
            support.build_request(support.load_json("engineer_request_machined_bracket.json")),
        )
    ]
    return out + [(f"rm5_{i:03d}", r) for i, r in enumerate(corpus._requests())]


def _stripped(plan):
    """The plan as the code model would have produced it: no ref, schema 1.0.0, re-hashed."""
    bare = dataclasses.replace(
        plan, capability_model_ref=None, schema_version="1.0.0", plan_id="", content_hash=""
    )
    digest = h.content_hash(h.plan_identity(bare))
    return dataclasses.replace(bare, content_hash=digest, plan_id=h.derive_uuid(digest))


def test_both_golden_models_are_reproduced_row_by_row_by_the_declared_mirrors():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["fingerprint"]["library"]["rows"]
    assert len(golden) == 902
    by_key = {(row["case"], row["model"]): row for row in golden}
    mirrors = {"default": s.model("default_1.0.0"), "r_star": s.model("r_star_2.0.0")}
    oracle = ManufacturabilityOracle()
    checked = 0
    for name, request in _requests():
        for model_name, model in mirrors.items():
            row = by_key[(name, model_name)]
            design_input = intake(request, produced_at=FIXED_TIME)
            task, plan = planner.plan(design_input, model, produced_at=FIXED_TIME)
            verdict = oracle.verify(plan, model)
            assert plan.capability_model_ref is not None and plan.schema_version == "1.1.0"
            assert h.to_contract_dict(verdict) == row["verdict"], (name, model_name)
            bare = _stripped(plan)
            assert bare.content_hash == row["plan_content_hash"], (name, model_name)
            assert _sha(h.to_contract_dict(bare)) == row["plan_full"], (name, model_name)
            episode = build_episode(
                task,
                design_input,
                bare,
                verdict,
                model.version,
                produced_at=FIXED_TIME,
                plan_ms=0.0,
                verify_ms=0.0,
            )
            assert episode.content_hash == row["episode_content_hash"], (name, model_name)
            assert _sha(h.to_contract_dict(episode)) == row["episode_full"], (name, model_name)
            checked += 1
    assert checked == 902


def test_constrained_mirror_matches_constrained_model_live():
    mirror, code = s.model("constrained_1.1.0"), constrained_model()
    oracle = ManufacturabilityOracle()
    count = 0
    for _name, request in _requests():
        di = intake(request, produced_at=FIXED_TIME)
        _, p_mirror = planner.plan(di, mirror, produced_at=FIXED_TIME)
        _, p_code = planner.plan(di, code, produced_at=FIXED_TIME)
        assert h.to_contract_dict(oracle.verify(p_mirror, mirror)) == h.to_contract_dict(
            oracle.verify(p_code, code)
        )
        assert _stripped(p_mirror).content_hash == p_code.content_hash
        count += 1
    assert count == 451
