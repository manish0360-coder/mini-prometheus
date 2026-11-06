"""MP-S1 AC4 (T4.1-T4.10) and G4 (T7.10, T7.11): no stale verdict is ever reused.

This is the owner's primary acceptance requirement. Protocol per variant V of ``default_1.0.0.json``:
run 1 = ``run_with_reuse`` under the base file (stores an episode); run 2 = ``run_with_reuse`` under V on
the SAME store; reference = ``runner.run`` under V on a FRESH store. Run 2 must equal the reference.
It must be a miss (``reused=False``) whenever the shop content, its evidence basis or the contracted
label changed, and a hit only for display-only metadata. All fixtures are synthetic.
"""

from __future__ import annotations

import dataclasses

import pytest

import mp_s1_support as s
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.reuse_runner import run_with_reuse
from mini_prometheus.shop_declaration.shop_model import capability_model_ref_for

T = "2026-11-06T00:00:00+00:00"

# (variant, expected run-2 status, expected reason codes or None for "same as run 1", reused)
MATRIX = [
    ("material_removed", "NOT_MANUFACTURABLE", ["MATERIAL_UNSUPPORTED"], False),
    ("tolerance_added", "NOT_MANUFACTURABLE", ["TOLERANCE_UNSUPPORTED"], False),
    ("capability_unsupported", "NOT_MANUFACTURABLE", ["CAPABILITY_MISSING"], False),
    ("precedence_added", "PLAN_INVALID", ["PRECEDENCE_VIOLATION"], False),
    ("evidence_public_specification", "MANUFACTURABLE", [], False),
    ("declarer_changed", "MANUFACTURABLE", [], False),
    ("date_changed", "MANUFACTURABLE", [], False),
    ("model_version_changed", "MANUFACTURABLE", [], False),
    ("display_name_changed", "MANUFACTURABLE", [], True),
    ("notes_changed", "MANUFACTURABLE", [], True),
]


@pytest.mark.parametrize("variant, status, reasons, reused", MATRIX)
def test_run_two_equals_a_fresh_run_under_the_variant(tmp_path, variant, status, reasons, reused):
    base, changed = s.model("default_1.0.0"), s.model(f"variants/{variant}")
    store = str(tmp_path / "shared.jsonl")
    first = run_with_reuse(s.bracket(), capability_model=base, produced_at=T, store_path=store)
    assert first.status == "MANUFACTURABLE" and first.reused is False
    second = run_with_reuse(s.bracket(), capability_model=changed, produced_at=T, store_path=store)
    reference = runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=changed,
        produced_at=T,
        store_path=str(tmp_path / "fresh.jsonl"),
    )
    assert second.reused is reused, variant
    assert (
        (second.status, second.verdict.reason_codes)
        == (status, reasons)
        == (reference.status, reference.verdict.reason_codes)
    ), variant
    # the plan that is exposed always carries the shop identity of the model in force (G4)
    assert second.plan.capability_model_ref == capability_model_ref_for(changed)


def test_the_reproduced_stale_verdict_bug_is_fixed():
    """§1.3, verbatim: same label 1.0.0, aluminium removed. Before MP-S1 reuse returned MANUFACTURABLE."""
    base, changed = s.model("default_1.0.0"), s.model("variants/material_removed")
    assert base.version == changed.version == "1.0.0"
    import os
    import tempfile

    store = os.path.join(tempfile.mkdtemp(), "episodes.jsonl")
    run_with_reuse(s.bracket(), capability_model=base, produced_at=T, store_path=store)
    again = run_with_reuse(s.bracket(), capability_model=changed, produced_at=T, store_path=store)
    assert (again.status, again.verdict.reason_codes, again.reused) == (
        "NOT_MANUFACTURABLE",
        ["MATERIAL_UNSUPPORTED"],
        False,
    )


def test_legacy_label_only_identity_for_code_models_is_pinned_unchanged(tmp_path):
    """T4.9 (scope honesty): code-level models with equal labels and no declaration keep RM2's
    label-only identity, so the stale hit is still possible for them. MP-S1 does not change
    code-model reuse; declared shops are the supported path."""
    a = default_model()
    b = dataclasses.replace(
        a,
        supported_materials=frozenset(
            m for m in a.supported_materials if not m.startswith("aluminum")
        ),
    )
    store = str(tmp_path / "legacy.jsonl")
    run_with_reuse(s.bracket(), capability_model=a, produced_at=T, store_path=store)
    legacy = run_with_reuse(s.bracket(), capability_model=b, produced_at=T, store_path=store)
    assert legacy.reused is True and legacy.status == "MANUFACTURABLE"


def test_a_store_mixing_two_declarations_serves_each_its_own(tmp_path):
    """T7.10: same design, same label, two declarations; each run reuses only its own episode."""
    a, b = s.model("default_1.0.0"), s.model("variants/declarer_changed")
    store = str(tmp_path / "mixed.jsonl")
    ra = run_with_reuse(s.bracket(), capability_model=a, produced_at=T, store_path=store)
    rb = run_with_reuse(s.bracket(), capability_model=b, produced_at=T, store_path=store)
    assert not ra.reused and not rb.reused and ra.episode.content_hash != rb.episode.content_hash
    ha = run_with_reuse(s.bracket(), capability_model=a, produced_at=T, store_path=store)
    hb = run_with_reuse(s.bracket(), capability_model=b, produced_at=T, store_path=store)
    assert ha.reused and hb.reused
    assert ha.source_episode.content_hash == ra.episode.content_hash
    assert hb.source_episode.content_hash == rb.episode.content_hash
    assert ha.plan.capability_model_ref == capability_model_ref_for(a)  # T7.11
    assert hb.plan.capability_model_ref == capability_model_ref_for(b)
