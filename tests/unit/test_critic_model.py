"""RM4 Commit 2 unit tests: the deterministic judgment model (finding families + assessment).

Situations are assembled from real RM1 episodes + RM3 precedent reports (read-only), then scored by the
critic model. Covers each finding family, the summary assessment, determinism, and the evidence-grounding
rule (every finding traces to a situation constituent).
"""
from __future__ import annotations

import dataclasses

from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.judgment import critic_model
from mini_prometheus.judgment.critic_model import Assessment, FindingKind, FindingPolarity
from mini_prometheus.judgment.engineering_situation import assemble
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    default_model as capability_default_model,
)
from mini_prometheus.orchestration import runner
from mini_prometheus.orchestration.precedent_runner import run_precedent

from support import FIXED_TIME


def _request(**over) -> ManufacturingRequest:
    fields = dict(
        schema_version="1.0.0",
        request_id="11111111-1111-1111-1111-111111111111",
        material="Aluminum 6061",
        material_code="AL6061",
        stock_form=StockForm.block,
        declared_operations=[
            DeclaredOperation(op=ProcessOp.cut_stock),
            DeclaredOperation(op=ProcessOp.face_mill),
            DeclaredOperation(op=ProcessOp.drill),
            DeclaredOperation(op=ProcessOp.inspect),
        ],
        quantity=25,
        tolerances=Tolerances(general_tolerance_mm=0.1),
    )
    fields.update(over)
    return ManufacturingRequest(**fields)


def _turn_request() -> ManufacturingRequest:
    return ManufacturingRequest(
        schema_version="1.0.0",
        request_id="22222222-2222-2222-2222-222222222222",
        material="Aluminum 6061",
        stock_form=StockForm.bar,
        declared_operations=[DeclaredOperation(op=ProcessOp.turn)],
        quantity=1,
    )


def _manufacturable_situation(store_path):
    """A machined case whose own precedent (itself) is MANUFACTURABLE -> report signal SUPPORTING."""
    req = _request()
    episode = runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path).episode
    report = run_precedent(req, store_path=store_path, produced_at=FIXED_TIME)
    return assemble(episode, report)


def _not_manufacturable_situation(store_path):
    """A turned case rejected under a lathe-less model -> adverse verdict + CAUTIONARY precedent signal."""
    model_no_lathe = ProcessCapabilityModel(
        version="1.0.0",
        op_capability=capability_default_model().op_capability,
        resources={k: v for k, v in capability_default_model().resources.items() if k != "lathe01"},
        supported_materials=capability_default_model().supported_materials,
    )
    turn_req = _turn_request()
    episode = runner.run(
        intake(turn_req, produced_at=FIXED_TIME),
        capability_model=model_no_lathe,
        produced_at=FIXED_TIME,
        store_path=store_path,
    ).episode
    assert episode.verdict.status == "NOT_MANUFACTURABLE"
    report = run_precedent(turn_req, store_path=store_path, produced_at=FIXED_TIME)
    return assemble(episode, report)


def test_model_version_carried():
    assert critic_model.default_model().version == critic_model.CRITIC_MODEL_VERSION == "1.0.0"


def test_supportive_precedent_yields_supportive_assessment(store_path):
    findings = critic_model.evaluate(_manufacturable_situation(store_path))
    kinds = {(f.kind, f.polarity) for f in findings}
    assert (FindingKind.PRECEDENT_CONSISTENCY, FindingPolarity.SUPPORTIVE) in kinds
    assert not any(f.kind is FindingKind.INTERNAL_VERDICT for f in findings)  # verdict was MANUFACTURABLE
    assert critic_model.assess(findings) is Assessment.SUPPORTIVE


def test_cautionary_precedent_and_adverse_verdict(store_path):
    findings = critic_model.evaluate(_not_manufacturable_situation(store_path))
    precedent = next(f for f in findings if f.kind is FindingKind.PRECEDENT_CONSISTENCY)
    internal = next(f for f in findings if f.kind is FindingKind.INTERNAL_VERDICT)
    assert precedent.polarity is FindingPolarity.CAUTIONARY
    assert "CAPABILITY_MISSING" in precedent.reason_codes  # surfaced from the precedent's verdict
    assert internal.polarity is FindingPolarity.CAUTIONARY
    assert "CAPABILITY_MISSING" in internal.reason_codes  # surfaced from the case's own verdict
    assert critic_model.assess(findings) is Assessment.CAUTIONARY  # cautionary dominates


def test_intent_coverage_gap_is_flagged(store_path):
    situation = _manufacturable_situation(store_path)
    # inject a declared operation the plan does not realize
    di = dataclasses.replace(
        situation.design_input,
        declared_operations=[*situation.design_input.declared_operations, DeclaredOperation(op=ProcessOp.turn)],
    )
    gapped = dataclasses.replace(situation, design_input=di)
    findings = critic_model.evaluate(gapped)
    intent = next(f for f in findings if f.kind is FindingKind.INTENT_COVERAGE)
    assert intent.polarity is FindingPolarity.CAUTIONARY
    assert intent.constituent == "design_input"
    assert "turn" in intent.detail


def test_no_intent_gap_when_plan_covers_declared(store_path):
    findings = critic_model.evaluate(_manufacturable_situation(store_path))
    assert not any(f.kind is FindingKind.INTENT_COVERAGE for f in findings)


def test_neutral_when_no_findings(store_path, tmp_path):
    # MANUFACTURABLE verdict + empty precedent corpus (signal NONE) + plan covers intent -> zero findings
    req = _request()
    episode = runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path).episode
    report_none = run_precedent(req, store_path=str(tmp_path / "empty.jsonl"), produced_at=FIXED_TIME)
    situation = assemble(episode, report_none)
    assert report_none.signal_source_rank is None
    findings = critic_model.evaluate(situation)
    assert findings == ()
    assert critic_model.assess(findings) is Assessment.NEUTRAL


def test_evaluation_is_deterministic(store_path):
    situation = _not_manufacturable_situation(store_path)
    assert critic_model.evaluate(situation) == critic_model.evaluate(situation)


def test_every_finding_is_grounded_in_a_situation_constituent(store_path):
    situation = _not_manufacturable_situation(store_path)
    allowed = set(situation.constituents)
    for f in critic_model.evaluate(situation):
        assert f.constituent in allowed  # evidence-grounding rule
