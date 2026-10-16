"""RM15 EC4-implement pre-run tests — NO arm execution, NO experimental outcome.

Two kinds of evidence:
  * ASSEMBLY tests drive the pure ``assemble_report`` with INJECTED synthetic ArmOutcomes (constructing an
    ArmOutcome does not run an arm), covering schema completeness, the paired b/c table + the c==0
    invariant, provenance correctness (constrained_model/rm15, never r_star/rm5), deterministic hashing,
    fail-closed gates, confounding flags, and the dropped reason-aligned metric.
  * FIXTURE tests use only load + frozen partition + frozen ``_classify_held_out`` + ``classify`` (no arms)
    to pin the RM15 checkpoint, determinism, status totality, and the primary subset size n=70.

Neither ``enriched_runner.run`` nor any arm (`cold_start`/`no_precedent`/`full_system`) is called.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from contracts.python.manufacturing.precedent_report_schema import PrecedentSignal

from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import enriched_corpus, enriched_runner, partition, protocol, runner
from mini_prometheus.experiment.arms import ArmOutcome
from mini_prometheus.judgment.critic_model import Assessment

_FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm15_corpus"
_CHECKPOINT = "sha256:11c039a96113aadeaba07a4078df04a6f4b25b94f3d1301a27db2123f09cb4d6"

SUP, CAU, NEU = Assessment.SUPPORTIVE, Assessment.CAUTIONARY, Assessment.NEUTRAL


def _oc(assessment: Assessment, signal: PrecedentSignal = PrecedentSignal.NONE, hsh: str = "h") -> ArmOutcome:
    return ArmOutcome(assessment=assessment, signal=signal, critique_content_hash=hsh)


def _compounding(statuses, arm3):
    # Four points reusing the same arm3 outcomes (assembly-only; composition is synthetic).
    return [
        enriched_runner.CompoundingInput(f, size, tuple(arm3), {"MANUFACTURABLE": size})
        for f, size in ((0.0, 0), (0.25, 5), (0.5, 10), (1.0, 20))
    ]


def _baseline_inputs():
    """A small, valid synthetic case set: Arm2 abstains on MANUFACTURABLE; adverse cases agree in all arms."""
    statuses = ["MANUFACTURABLE", "MANUFACTURABLE", "NOT_MANUFACTURABLE", "PLAN_INVALID", "NOT_MANUFACTURABLE"]
    labels = ["MANUFACTURABLE", "MANUFACTURABLE", "material", "precedence", "tolerance"]
    arm1 = [_oc(NEU), _oc(NEU), _oc(CAU), _oc(CAU), _oc(CAU)]
    arm2 = [_oc(NEU), _oc(NEU), _oc(CAU), _oc(CAU), _oc(CAU)]          # == arm1 (hashes equal)
    arm3 = [_oc(SUP, PrecedentSignal.SUPPORTING), _oc(CAU, PrecedentSignal.CAUTIONARY),
            _oc(CAU, PrecedentSignal.CAUTIONARY), _oc(CAU, PrecedentSignal.CAUTIONARY),
            _oc(CAU, PrecedentSignal.CAUTIONARY)]
    return dict(
        statuses=statuses, labels=labels, arm1=arm1, arm2=arm2, arm3=arm3,
        compounding=_compounding(statuses, arm3),
        excluded_duplicates=0, cross_partition_design_dups=0,
        checkpoint_computed=_CHECKPOINT, checkpoint_committed=_CHECKPOINT,
        partition_disjoint=True, partition_covering=True,
        n_total=960, n_experience=731, n_held_out=229, produced_at="2026-01-01T00:00:00+00:00",
    )


# ---- assembly tests (injected synthetic outcomes; no arms) -----------------------------------------

def test_schema_completeness_and_integer_rationals():
    r = enriched_runner.assemble_report(**_baseline_inputs())
    m = r["metrics"]
    for key in ("n_analogous_held_out", "primary_marginal_MANUFACTURABLE", "per_arm_oracle_agreement_status_class",
                "aggregate_marginal", "per_axis_diagnostics", "cautionary_false_alarm_rate_on_controls",
                "precedent_coverage", "arm1_arm2_validity_control", "excluded_duplicate_count",
                "compounding_curve", "reason_aligned_agreement"):
        assert key in m, key
    for pair in (m["aggregate_marginal"], m["cautionary_false_alarm_rate_on_controls"],
                 m["primary_marginal_MANUFACTURABLE"]["marginal"]):
        assert len(pair) == 2 and all(isinstance(x, int) for x in pair)
    assert "content_hash" in r and r["validity_passed"] is True
    assert set(r["validity_gates"]) == {
        "VG1_arm1_equals_arm2_exact", "VG2_both_verdict_classes_present",
        "VG3_no_cross_partition_exact_duplicates", "VG4_checkpoint_matches_committed",
        "VG5_analogous_set_nonempty", "VG6_partition_disjoint_and_covering",
        "RM15_primary_arm2_abstains_and_c_zero"}


def test_primary_paired_table_bc_and_c_zero_invariant():
    r = enriched_runner.assemble_report(**_baseline_inputs())
    p = r["metrics"]["primary_marginal_MANUFACTURABLE"]
    assert p["denominator"] == 2                       # two MANUFACTURABLE cases
    assert p["paired_table"] == {"b_arm3_corrects_arm2_errors": 1, "c_arm3_regressions": 0}
    assert p["marginal"] == [1, 2]                     # (b-c)/n
    assert p["arm2_structurally_abstains"] is True


def test_c_nonzero_is_a_validity_failure():
    inp = _baseline_inputs()
    # Make a MANUFACTURABLE case where Arm2 is (wrongly) correct and Arm3 wrong -> c=1.
    inp["arm2"] = [_oc(SUP), *inp["arm2"][1:]]        # arm2 correct on a MANUFACTURABLE case
    inp["arm3"] = [_oc(CAU), *inp["arm3"][1:]]        # arm3 wrong there
    r = enriched_runner.assemble_report(**inp)
    assert r["metrics"]["primary_marginal_MANUFACTURABLE"]["paired_table"]["c_arm3_regressions"] == 1
    assert r["validity_gates"]["RM15_primary_arm2_abstains_and_c_zero"] is False
    assert r["validity_passed"] is False


def test_arm2_correct_on_primary_is_fail_closed_even_with_c_zero():
    # Arm2 correct on a MANUFACTURABLE case while Arm3 is also correct -> c stays 0, but Arm2 did NOT
    # structurally abstain. The invariant must still make the report inadmissible.
    inp = _baseline_inputs()
    inp["arm2"] = [_oc(SUP), *inp["arm2"][1:]]   # arm2[0] correct on MANUFACTURABLE; arm3[0] is already SUP
    r = enriched_runner.assemble_report(**inp)
    p = r["metrics"]["primary_marginal_MANUFACTURABLE"]
    assert p["paired_table"]["c_arm3_regressions"] == 0          # c is zero ...
    assert p["arm2_structurally_abstains"] is False              # ... but Arm2 did NOT abstain
    assert r["validity_gates"]["RM15_primary_arm2_abstains_and_c_zero"] is False
    assert r["validity_passed"] is False


def test_compounding_length_mismatch_is_fail_closed():
    inp = _baseline_inputs()
    short = enriched_runner.CompoundingInput(0.5, 10, tuple(inp["arm3"][:2]), {"MANUFACTURABLE": 2})  # len 2 != 5
    inp["compounding"] = [*inp["compounding"][:1], short]
    with pytest.raises(ValueError):
        enriched_runner.assemble_report(**inp)


def test_provenance_is_rm15_never_rm5_or_rstar():
    r = enriched_runner.assemble_report(**_baseline_inputs())
    assert r["capability_regime"]["version"] == "1.1.0"
    assert r["fixture"] == "tests/fixtures/rm15_corpus/"
    blob = json.dumps({k: r[k] for k in ("capability_regime", "fixture", "metrics", "validity_gates",
                                         "hypothesis", "checkpoint_id")})
    assert "r_star" not in blob and "rm5_corpus" not in blob
    assert r["checkpoint_id"] == _CHECKPOINT


def test_content_hash_is_deterministic_and_excludes_volatile_provenance():
    a = enriched_runner.assemble_report(**_baseline_inputs())
    b = enriched_runner.assemble_report(**_baseline_inputs())
    assert a["content_hash"] == b["content_hash"]
    inp = _baseline_inputs(); inp["produced_at"] = "2099-12-31T23:59:59+00:00"
    assert enriched_runner.assemble_report(**inp)["content_hash"] == a["content_hash"]


def test_synthetic_gate_failure_makes_report_inadmissible():
    inp = _baseline_inputs(); inp["checkpoint_computed"] = "sha256:" + "0" * 64
    r = enriched_runner.assemble_report(**inp)
    assert r["validity_gates"]["VG4_checkpoint_matches_committed"] is False
    assert r["validity_passed"] is False


def test_per_axis_confounding_flags():
    d = enriched_runner.assemble_report(**_baseline_inputs())["metrics"]["per_axis_diagnostics"]
    assert d["material"]["similarity_confounded"] is True
    assert d["precedence"]["similarity_confounded"] is True
    assert d["tolerance"]["similarity_confounded"] is False


def test_reason_aligned_is_recorded_not_measured():
    ra = enriched_runner.assemble_report(**_baseline_inputs())["metrics"]["reason_aligned_agreement"]
    assert ra["measured"] is False and "dropped" in ra["reason"].lower()


# ---- fixture tests (load + frozen partition/classify only; NO arms) --------------------------------

def test_rm15_checkpoint_matches_frozen_value():
    episodes = load(_FIX / "episodes.jsonl")
    committed = json.loads((_FIX / "checkpoint.json").read_text(encoding="utf-8"))
    assert partition.checkpoint_id(partition.partition(episodes)) == _CHECKPOINT == committed["checkpoint_id"]


def test_rm15_fixture_and_partition_deterministic_disjoint_covering():
    a = load(_FIX / "episodes.jsonl")
    b = load(_FIX / "episodes.jsonl")
    assert [e.content_hash for e in a] == [e.content_hash for e in b] and len(a) == 960
    part = partition.partition(a)
    assert set(part.experience).isdisjoint(part.held_out)
    assert len(part.experience) + len(part.held_out) == len(a)


def test_all_rm15_statuses_map_through_frozen_protocol():
    statuses = {e.verdict.status for e in load(_FIX / "episodes.jsonl")}
    assert statuses <= ({protocol._MANUFACTURABLE} | set(protocol._ADVERSE))


def test_primary_subset_membership_is_70_via_frozen_classifier():
    episodes = load(_FIX / "episodes.jsonl")
    part = partition.partition(episodes)
    by = {e.content_hash: e for e in episodes}
    exp = [by[h] for h in part.experience]
    hel = [by[h] for h in part.held_out]
    analogous, _ = runner._classify_held_out(hel, exp)        # frozen held-out classifier; NO arms
    n_manu = sum(1 for c in analogous if protocol.is_manufacturable(c.episode.verdict.status))
    assert n_manu == 70


# ---- fail-closed gate tests (one minimal invalid condition each; injected synthetic; no arms) -------

def test_vg1_arm1_ne_arm2_is_fail_closed():
    inp = _baseline_inputs()
    inp["arm1"] = [_oc(NEU, hsh="DIFFERENT"), *inp["arm1"][1:]]   # arm1[0] hash != arm2[0]
    r = enriched_runner.assemble_report(**inp)
    assert r["validity_gates"]["VG1_arm1_equals_arm2_exact"] is False
    assert r["metrics"]["arm1_arm2_validity_control"]["mismatches"] == 1
    assert r["validity_passed"] is False


def test_vg2_single_class_is_fail_closed():
    inp = _baseline_inputs()
    inp["statuses"] = ["MANUFACTURABLE"] * 5                      # no adverse class present
    inp["labels"] = ["MANUFACTURABLE"] * 5
    inp["arm3"] = [_oc(SUP, PrecedentSignal.SUPPORTING)] * 5      # c stays 0 (arm2 abstains)
    r = enriched_runner.assemble_report(**inp)
    assert r["validity_gates"]["VG2_both_verdict_classes_present"] is False
    assert r["validity_passed"] is False


def test_vg3_cross_partition_duplicate_is_fail_closed():
    inp = _baseline_inputs()
    inp["cross_partition_design_dups"] = 1
    r = enriched_runner.assemble_report(**inp)
    assert r["validity_gates"]["VG3_no_cross_partition_exact_duplicates"] is False
    assert r["validity_passed"] is False


def test_vg5_empty_analogous_set_is_fail_closed():
    inp = dict(
        statuses=[], labels=[], arm1=[], arm2=[], arm3=[], compounding=[],
        excluded_duplicates=0, cross_partition_design_dups=0,
        checkpoint_computed=_CHECKPOINT, checkpoint_committed=_CHECKPOINT,
        partition_disjoint=True, partition_covering=True,
        n_total=960, n_experience=731, n_held_out=229, produced_at="2026-01-01T00:00:00+00:00",
    )
    r = enriched_runner.assemble_report(**inp)
    assert r["validity_gates"]["VG5_analogous_set_nonempty"] is False
    # n==0 also necessarily trips VG2 (both-classes); that is an inherent consequence, not a separate tweak.
    assert r["validity_passed"] is False


def test_vg6_partition_not_disjoint_is_fail_closed():
    inp = _baseline_inputs()
    inp["partition_disjoint"] = False
    r = enriched_runner.assemble_report(**inp)
    assert r["validity_gates"]["VG6_partition_disjoint_and_covering"] is False
    assert r["validity_passed"] is False


# ---- diagnostic VALUE assertions (controlled synthetic inputs; not experimental results) ------------

def _controlled_inputs():
    """Hand-computed case set (NOT an experiment): 3 MANUFACTURABLE + material/precedence/tolerance."""
    statuses = ["MANUFACTURABLE", "MANUFACTURABLE", "MANUFACTURABLE",
                "NOT_MANUFACTURABLE", "PLAN_INVALID", "NOT_MANUFACTURABLE"]
    labels = ["MANUFACTURABLE", "MANUFACTURABLE", "MANUFACTURABLE", "material", "precedence", "tolerance"]
    arm2 = [_oc(NEU), _oc(NEU), _oc(NEU), _oc(CAU), _oc(CAU), _oc(CAU)]
    arm1 = list(arm2)
    arm3 = [_oc(SUP, PrecedentSignal.SUPPORTING),   # manu: correct, covered
            _oc(CAU, PrecedentSignal.CAUTIONARY),   # manu: FALSE ALARM, covered
            _oc(NEU, PrecedentSignal.NONE),         # manu: wrong, NOT covered
            _oc(CAU, PrecedentSignal.CAUTIONARY),   # material: correct, covered
            _oc(CAU, PrecedentSignal.NONE),         # precedence: correct, NOT covered
            _oc(SUP, PrecedentSignal.CAUTIONARY)]   # tolerance: wrong, covered
    return dict(
        statuses=statuses, labels=labels, arm1=arm1, arm2=arm2, arm3=arm3,
        compounding=_compounding(statuses, arm3),
        excluded_duplicates=0, cross_partition_design_dups=0,
        checkpoint_computed=_CHECKPOINT, checkpoint_committed=_CHECKPOINT,
        partition_disjoint=True, partition_covering=True,
        n_total=960, n_experience=731, n_held_out=229, produced_at="2026-01-01T00:00:00+00:00",
    )


def test_diagnostic_values_false_alarm_coverage_per_axis():
    m = enriched_runner.assemble_report(**_controlled_inputs())["metrics"]
    assert m["primary_marginal_MANUFACTURABLE"]["paired_table"] == {
        "b_arm3_corrects_arm2_errors": 1, "c_arm3_regressions": 0}
    assert m["primary_marginal_MANUFACTURABLE"]["marginal"] == [1, 3]
    assert m["cautionary_false_alarm_rate_on_controls"] == [1, 3]
    assert m["precedent_coverage"]["manufacturable"] == [2, 3]
    assert m["precedent_coverage"]["not_manufacturable"] == [2, 3]
    assert m["per_axis_diagnostics"]["material"]["marginal"] == [0, 1]
    assert m["per_axis_diagnostics"]["precedence"]["marginal"] == [0, 1]
    assert m["per_axis_diagnostics"]["tolerance"]["marginal"] == [-1, 1]
    assert m["per_arm_oracle_agreement_status_class"]["arm2_no_precedent"] == [3, 6]
    # arm3 correct on: idx0 SUP/MANUFACTURABLE, idx3 CAU/NOT, idx4 CAU/PLAN_INVALID = 3 of 6.
    assert m["per_arm_oracle_agreement_status_class"]["arm3_full_system"] == [3, 6]
    assert m["aggregate_marginal"] == [0, 6]


# ---- arm-free compounding composition (real fixture + frozen _subsample) ----------------------------

def test_axis_composition_matches_classification_of_same_subset():
    import collections
    episodes = load(_FIX / "episodes.jsonl")
    part = partition.partition(episodes)
    by = {e.content_hash: e for e in episodes}
    experience = [by[h] for h in part.experience]
    for frac in protocol.COMPOUNDING_FRACTIONS:
        sub = runner._subsample(experience, frac)                 # frozen subsampler; NO arms
        expected = dict(collections.Counter(enriched_corpus.classify(e) for e in sub))
        assert enriched_runner._axis_composition(sub) == expected


# ---- hash sensitivity to a nonvolatile registered metric -------------------------------------------

def test_content_hash_changes_when_a_metric_changes():
    base = enriched_runner.assemble_report(**_baseline_inputs())
    inp = _baseline_inputs()
    inp["arm3"] = [_oc(NEU), *inp["arm3"][1:]]   # flips a MANUFACTURABLE case right->wrong (b: 1->0)
    changed = enriched_runner.assemble_report(**inp)
    assert changed["metrics"]["primary_marginal_MANUFACTURABLE"]["marginal"] == [0, 2]
    assert changed["content_hash"] != base["content_hash"]
