"""RM5 C2 — frozen evaluation protocol (pure; smallest correct deterministic representation).

Fixes the assessment<->verdict agreement mapping, the per-case correctness/false-alarm predicates, the
analogous-case band, the compounding sub-sample fractions, the RM4-H1-grounded false-alarm ceiling, and
the mandatory Statement-of-Claims template. Pure: depends only on the RM4 ``Assessment`` enum + stdlib;
no RM1/RM3 mechanism, no I/O. All quantities are exact integers/rationals (no float identity hazard).
"""
from __future__ import annotations

from mini_prometheus.judgment.critic_model import Assessment

EVALUATION_PROTOCOL_VERSION = "1.0.0"

# "Analogous" (frozen checkpoint): RM3-relevant but not exact identity. relevance in [MIN, IDENTICAL).
ANALOGOUS_MIN_RELEVANCE = 1
IDENTICAL_RELEVANCE = 1000

# Deterministic compounding sub-sample fractions of the experience corpus.
COMPOUNDING_FRACTIONS = (0.0, 0.25, 0.5, 1.0)

# Cautionary false-alarm ceiling on MANUFACTURABLE controls. ORIGIN (labeled): RM4 H1 —
# "zero cautionary false alarms on controls" (specs/milestones/RM4-engineering-judgment.md §2;
# docs/design/RM4-engineering-package.md). Not an invented number.
FALSE_ALARM_CEILING = 0
FALSE_ALARM_CEILING_ORIGIN = "RM4 H1 (zero cautionary false alarms on controls)"

_MANUFACTURABLE = "MANUFACTURABLE"
_ADVERSE = frozenset({"NOT_MANUFACTURABLE", "PLAN_INVALID"})


def agrees(assessment: Assessment, verdict_status: str) -> bool | None:
    """Assessment<->verdict agreement. NEUTRAL abstains (None): excluded from agreement, kept for coverage."""
    if assessment is Assessment.NEUTRAL:
        return None
    if assessment is Assessment.SUPPORTIVE:
        return verdict_status == _MANUFACTURABLE
    return verdict_status in _ADVERSE  # CAUTIONARY


def correct(assessment: Assessment, verdict_status: str) -> int:
    """Paired per-case correctness on the common analogous set: agree -> 1; disagree or abstain -> 0.

    Using a common denominator (the analogous set) makes the paired Arm3-Arm2 contrast well-defined and
    non-degenerate; internal-verdict + intent-coverage are constant across arms and cancel per case.
    """
    return 1 if agrees(assessment, verdict_status) is True else 0


def is_false_alarm(assessment: Assessment, verdict_status: str) -> bool:
    """A precedent-driven false alarm: CAUTIONARY assessment on an oracle-MANUFACTURABLE case."""
    return assessment is Assessment.CAUTIONARY and verdict_status == _MANUFACTURABLE


def is_manufacturable(verdict_status: str) -> bool:
    return verdict_status == _MANUFACTURABLE


def statement_of_claims() -> dict:
    """The mandatory Statement of Claims (RM5 spec §8): what the report may and may NOT claim."""
    return {
        "oracle_agreement": (
            "Absolute per-arm agreement with the deterministic RM1 oracle. CAVEAT: inflated by the RM4 "
            "internal-verdict finding (a direct readout of the query's own verdict); not evidence of "
            "precedent value."
        ),
        "held_out_generalization": (
            "Precedent marginal agreement (Arm3 - Arm2) on analogous, non-identical held-out cases within "
            "the fixed regime R*. The internal-model generalization claim."
        ),
        "compounding_evidence": "The precedent-marginal-agreement curve vs experience-corpus size N.",
        "internal_model_causal": (
            "Precedent causes the marginal change ONLY within the oracle-internal, single-regime world, "
            "established by the Arm3-Arm2 ablation (arms differ only in the precedent input)."
        ),
        "cannot_claim": [
            "real-world manufacturing correctness",
            "real manufacturability improvement",
            "cost or quality improvement",
            "true DFM expertise",
            "superiority to human engineers",
            "that the deterministic oracle equals real manufacturability",
            "generalization beyond the fixed regime R*",
        ],
    }
