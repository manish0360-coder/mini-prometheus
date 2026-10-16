"""RM15 EC2 — compatibility of the FROZEN RM5 protocol with the enriched RM15 corpus.

Proves, read-only, that the frozen ``experiment/protocol.py`` already maps every verdict the RM15
enriched oracle produces — so the RM5 harness needs NO change for RM15. This test imports only the
protocol's pure mapping functions, the RM2 reader, and the RM4 ``Assessment`` enum; it does NOT import
``arms`` or ``runner`` and computes NO Arm1/Arm2/Arm3 outcome. It asserts the mapping semantics by
supplying assessments by hand, never by running judgment.

Enriched corpus verdict statuses (read from the committed fixture): MANUFACTURABLE, NOT_MANUFACTURABLE
(material/tolerance drivers), PLAN_INVALID (precedence driver). The frozen mapping domain is
{MANUFACTURABLE} ∪ {NOT_MANUFACTURABLE, PLAN_INVALID}, which must cover all three.
"""
from __future__ import annotations

import pathlib

from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import protocol
from mini_prometheus.judgment.critic_model import Assessment

_FIXTURE = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm15_corpus"
_STATUSES = {e.verdict.status for e in load(_FIXTURE / "episodes.jsonl")}
_MAPPING_DOMAIN = {protocol._MANUFACTURABLE} | set(protocol._ADVERSE)


def test_every_corpus_status_is_in_the_frozen_mapping_domain():
    # Totality: the frozen protocol maps every status the enriched oracle emits (no unmapped verdict).
    assert _STATUSES <= _MAPPING_DOMAIN, (_STATUSES - _MAPPING_DOMAIN)


def test_corpus_exercises_all_three_enriched_statuses():
    # The enriched corpus is richer than RM5: both adverse statuses are present, plus MANUFACTURABLE.
    assert _STATUSES == {"MANUFACTURABLE", "NOT_MANUFACTURABLE", "PLAN_INVALID"}


def test_manufacturable_mapping_semantics():
    s = "MANUFACTURABLE"
    assert protocol.is_manufacturable(s) is True
    assert protocol.agrees(Assessment.SUPPORTIVE, s) is True
    assert protocol.agrees(Assessment.CAUTIONARY, s) is False
    assert protocol.agrees(Assessment.NEUTRAL, s) is None        # abstain
    assert protocol.correct(Assessment.SUPPORTIVE, s) == 1
    assert protocol.is_false_alarm(Assessment.CAUTIONARY, s) is True  # cautionary on a MANUFACTURABLE control


def test_adverse_mapping_semantics_for_both_statuses():
    for s in ("NOT_MANUFACTURABLE", "PLAN_INVALID"):
        assert protocol.is_manufacturable(s) is False
        assert protocol.agrees(Assessment.CAUTIONARY, s) is True
        assert protocol.agrees(Assessment.SUPPORTIVE, s) is False
        assert protocol.agrees(Assessment.NEUTRAL, s) is None     # abstain
        assert protocol.correct(Assessment.CAUTIONARY, s) == 1
        assert protocol.is_false_alarm(Assessment.CAUTIONARY, s) is False  # not a control


def test_protocol_version_is_frozen():
    # Freeze sentinel: the enriched corpus must not have required any protocol change.
    assert protocol.EVALUATION_PROTOCOL_VERSION == "1.0.0"
