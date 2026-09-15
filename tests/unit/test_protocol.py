"""RM5 C2 unit tests: the frozen evaluation protocol (mapping, predicates, ceiling origin, claims)."""
from __future__ import annotations

from mini_prometheus.experiment import protocol
from mini_prometheus.judgment.critic_model import Assessment


def test_assessment_verdict_mapping():
    assert protocol.agrees(Assessment.SUPPORTIVE, "MANUFACTURABLE") is True
    assert protocol.agrees(Assessment.SUPPORTIVE, "NOT_MANUFACTURABLE") is False
    assert protocol.agrees(Assessment.CAUTIONARY, "NOT_MANUFACTURABLE") is True
    assert protocol.agrees(Assessment.CAUTIONARY, "PLAN_INVALID") is True
    assert protocol.agrees(Assessment.CAUTIONARY, "MANUFACTURABLE") is False


def test_neutral_abstains_excluded_from_agreement_but_not_correct():
    assert protocol.agrees(Assessment.NEUTRAL, "MANUFACTURABLE") is None  # excluded from agreement
    assert protocol.correct(Assessment.NEUTRAL, "MANUFACTURABLE") == 0  # abstain scores 0


def test_correct_is_one_only_on_true_agreement():
    assert protocol.correct(Assessment.SUPPORTIVE, "MANUFACTURABLE") == 1
    assert protocol.correct(Assessment.CAUTIONARY, "NOT_MANUFACTURABLE") == 1
    assert protocol.correct(Assessment.SUPPORTIVE, "NOT_MANUFACTURABLE") == 0


def test_false_alarm_is_cautionary_on_manufacturable_only():
    assert protocol.is_false_alarm(Assessment.CAUTIONARY, "MANUFACTURABLE") is True
    assert protocol.is_false_alarm(Assessment.CAUTIONARY, "NOT_MANUFACTURABLE") is False
    assert protocol.is_false_alarm(Assessment.SUPPORTIVE, "MANUFACTURABLE") is False


def test_false_alarm_ceiling_is_rm4_h1_zero():
    assert protocol.FALSE_ALARM_CEILING == 0
    assert "RM4 H1" in protocol.FALSE_ALARM_CEILING_ORIGIN


def test_compounding_fractions_are_the_frozen_quarters():
    assert protocol.COMPOUNDING_FRACTIONS == (0.0, 0.25, 0.5, 1.0)


def test_statement_of_claims_names_the_hard_boundary():
    soc = protocol.statement_of_claims()
    joined = " ".join(soc["cannot_claim"]).lower()
    assert "real-world manufacturing correctness" in soc["cannot_claim"]
    assert "cost" in joined and "dfm" in joined
    assert "beyond the fixed regime" in joined
