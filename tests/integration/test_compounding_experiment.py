"""RM5 C4 integration test: the compounding runner over the committed frozen fixture.

Asserts IMPLEMENTATION correctness and PROTOCOL/validity integrity only — never the scientific
hypothesis outcome (a flat/negative Arm3-Arm2 or a non-zero false-alarm count is a VALID result and
must not be gated by a test).
"""
from __future__ import annotations

import functools

from mini_prometheus.experiment import runner


@functools.lru_cache(maxsize=1)
def _report():
    return runner.run(produced_at="2026-01-01T00:00:00+00:00")


def test_run_is_deterministic():
    a = runner.run(produced_at="2026-01-01T00:00:00+00:00")
    b = runner.run(produced_at="2026-01-01T00:00:00+00:00")
    assert a["content_hash"] == b["content_hash"]


def test_all_hard_validity_gates_pass():
    rep = _report()
    assert rep["validity_passed"] is True, rep["validity_gates"]
    vg = rep["validity_gates"]
    assert vg["VG1_arm1_equals_arm2_exact"] is True
    assert vg["VG2_both_verdict_classes_present"] is True
    assert vg["VG3_no_cross_partition_exact_duplicates"] is True
    assert vg["VG4_checkpoint_matches_committed"] is True
    assert vg["VG6_partition_disjoint"] is True


def test_no_leakage_excluded_duplicates_zero():
    assert _report()["metrics"]["excluded_duplicate_count"] == 0


def test_compounding_curve_starts_at_zero_marginal_and_reports_four_points():
    curve = _report()["metrics"]["compounding_curve"]
    assert len(curve) == 4
    assert curve[0]["experience_size"] == 0
    assert curve[0]["marginal_vs_arm2"][0] == 0  # N=0 => Arm3 collapses to NONE => marginal 0


def test_denominators_present_for_both_verdict_classes():
    cov = _report()["metrics"]["precedent_coverage"]
    assert cov["manufacturable"][1] > 0 and cov["not_manufacturable"][1] > 0  # both denominators reported


def test_arm1_equals_arm2_no_mismatches():
    ctrl = _report()["metrics"]["arm1_arm2_validity_control"]
    assert ctrl["equal_exact"] is True and ctrl["mismatches"] == 0


def test_report_writes_to_isolated_sink(tmp_path):
    out = runner.write_report(_report(), tmp_path / "evaluation")
    assert out.exists() and out.name == "rm5_compounding_report.json"
