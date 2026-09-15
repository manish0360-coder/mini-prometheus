"""RM5 C5 reproducibility freeze: pin the measured experiment so it cannot silently drift.

The Director- and Gemini-accepted first measurement is a scientific observation of record. This test
freezes it: the runner's report ``content_hash`` (which covers every metric, gate, and the R* regime)
is pinned, so ANY change to the protocol, arms, runner, or the committed fixture that would alter the
result fails CI. The headline values the Director required preserved are additionally pinned as
human-readable regression sentinels. This is protection, not re-measurement — it must never be
"updated" to accommodate a changed result without an explicit, reviewed decision.
"""
from __future__ import annotations

import functools

from mini_prometheus.experiment import runner

# Frozen first-measurement identity (RM5 C4, accepted for commit as 2e1118f; Gemini-reviewed).
FROZEN_REPORT_CONTENT_HASH = "sha256:2b7c487294e7cd792155a832e2e5f2e73591721e71c2f2314bcf5534ef2b3574"


@functools.lru_cache(maxsize=1)
def _report():
    return runner.run(produced_at="2026-01-01T00:00:00+00:00")


def test_report_content_hash_is_frozen():
    assert _report()["content_hash"] == FROZEN_REPORT_CONTENT_HASH


def test_headline_results_preserved_exactly():
    m = _report()["metrics"]
    assert m["n_analogous_held_out"] == 121
    assert m["per_arm_oracle_agreement"]["arm1_cold_start"] == [76, 121]
    assert m["per_arm_oracle_agreement"]["arm2_no_precedent"] == [76, 121]
    assert m["per_arm_oracle_agreement"]["arm3_full_system"] == [118, 121]
    assert m["precedent_marginal_agreement"] == [42, 121]
    assert m["cautionary_false_alarm_rate_on_controls"] == [3, 45]  # the 3 false alarms stay
    assert m["precedent_coverage"]["manufacturable"] == [45, 45]
    assert m["precedent_coverage"]["not_manufacturable"] == [76, 76]
    assert m["excluded_duplicate_count"] == 0
    assert m["arm1_arm2_validity_control"] == {"equal_exact": True, "mismatches": 0}


def test_decoupling_and_compounding_preserved_exactly():
    r = _report()
    da = r["decoupling_audit"]
    assert da["not_class_marginal_zero_by_internal_verdict"] == [0, 76]  # internal-verdict cancels
    assert da["manufacturable_class_marginal"] == [42, 45]
    marginals = [pt["marginal_vs_arm2"][0] for pt in r["metrics"]["compounding_curve"]]
    assert marginals == [0, 39, 43, 42]  # non-monotone tail preserved (NOT forced monotonic)


def test_validity_gates_all_pass_but_hypotheses_reported_as_measured():
    r = _report()
    assert r["validity_passed"] is True
    # Hypothesis outcomes are recorded as measured; H2 and H4 remain NOT met (valid findings).
    assert r["hypothesis"]["H1_precedent_marginal_positive"]["met"] is True
    assert r["hypothesis"]["H2_zero_false_alarms_on_controls"]["met"] is False
    assert r["hypothesis"]["H3_coverage_nonzero_both_classes"]["met"] is True
    assert r["hypothesis"]["H4_compounding_non_decreasing"]["met"] is False
