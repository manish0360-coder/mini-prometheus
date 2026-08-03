"""RM4 Commit 3 unit tests: Engineering Critique assembly (findings, assessment, identity, honesty).

Critiques are produced from situations assembled out of real RM1 episodes + RM3 precedent reports. Covers
the carried findings/assessment, deterministic content-hash identity (produced_at excluded), the case
reference, provenance, cautionary/supportive end-to-end, and that the internal situation never leaks.
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    Tolerances,
)
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.judgment import critic_model
from mini_prometheus.judgment.critic_model import Assessment, FindingKind
from mini_prometheus.judgment.engineering_critique import EngineeringCritique, critique
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
    req = _request()
    episode = runner.run_from_request(req, produced_at=FIXED_TIME, store_path=store_path).episode
    report = run_precedent(req, store_path=store_path, produced_at=FIXED_TIME)
    return assemble(episode, report)


def _not_manufacturable_situation(store_path):
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
    report = run_precedent(turn_req, store_path=store_path, produced_at=FIXED_TIME)
    return assemble(episode, report)


def test_carries_ordered_findings_and_assessment(store_path):
    situation = _not_manufacturable_situation(store_path)
    c = critique(situation)
    assert isinstance(c, EngineeringCritique)
    # the critique's assessment agrees with the model's, and findings match evaluate() as a set
    assert c.assessment is critic_model.assess(critic_model.evaluate(situation))
    assert set(c.findings) == set(critic_model.evaluate(situation))
    # deterministic total order (kind ascending)
    assert list(c.findings) == sorted(c.findings, key=lambda f: (f.kind.value, f.polarity.value, f.constituent, tuple(sorted(f.reason_codes)), f.detail))


def test_cautionary_end_to_end(store_path):
    c = critique(_not_manufacturable_situation(store_path))
    assert c.assessment is Assessment.CAUTIONARY
    kinds = {f.kind for f in c.findings}
    assert FindingKind.PRECEDENT_CONSISTENCY in kinds
    assert FindingKind.INTERNAL_VERDICT in kinds


def test_supportive_end_to_end(store_path):
    c = critique(_manufacturable_situation(store_path))
    assert c.assessment is Assessment.SUPPORTIVE


def test_content_hash_deterministic_and_excludes_produced_at(store_path):
    situation = _not_manufacturable_situation(store_path)
    a = critique(situation, produced_at="2026-07-23T00:00:00+00:00")
    b = critique(situation, produced_at="2031-01-01T00:00:00+00:00")
    assert a.content_hash == b.content_hash  # produced_at excluded from identity
    assert a.content_hash.startswith("sha256:")


def test_case_ref_ties_to_the_situation_design(store_path):
    situation = _manufacturable_situation(store_path)
    c = critique(situation)
    expected = h.content_hash(h.design_input_identity(situation.design_input))
    assert c.case_ref.content_hash == expected
    assert c.case_ref.id == situation.design_input.design_input_id


def test_provenance_sentinel_and_source(store_path):
    c = critique(_manufacturable_situation(store_path))
    assert c.provenance.capability_model_version == "0.0.0"  # sentinel
    assert c.provenance.rule_id == "engineering.judgment.critique"
    assert c.provenance.source_refs == [c.case_ref]


def test_model_version_recorded(store_path):
    c = critique(_manufacturable_situation(store_path))
    assert c.critic_model_version == critic_model.CRITIC_MODEL_VERSION == "1.0.0"


def test_critique_does_not_expose_the_internal_situation(store_path):
    c = critique(_manufacturable_situation(store_path))
    # the EngineeringSituation is consumed but never surfaced on the result
    for attr in ("situation", "engineering_situation", "design_input", "plan", "verdict", "precedent_report"):
        assert not hasattr(c, attr)
