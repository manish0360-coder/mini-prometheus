"""RM5 C4 — the deterministic compounding-validation runner + report.

Loads the committed frozen fixture (never regenerates during normal evaluation), verifies its
checkpoint provenance and leakage-safe partition, evaluates the three arms (C3) on the strictly
held-out **analogous** cases under the fixed regime R*, and computes the frozen primary metrics (C2):
per-arm oracle agreement, the precedent marginal agreement (Arm3-Arm2), the compounding curve over
deterministic experience subsamples, the cautionary false-alarm rate on MANUFACTURABLE controls, and
precedent coverage per verdict class. It records hard validity-gate results separately from the
(non-mutating) hypothesis-criterion evaluation, embeds the Statement of Claims, and writes a
content-addressed report to the isolated ``artifacts/evaluation/`` sink — never the episode store.

Read-only over RM1-RM4: it composes ``experiment.arms`` (which compose RM3 retrieval/reasoning + RM4
judgment) and reuses ``precedent_model.relevance`` to classify analogy. It owns no reasoning, no
scoring, no judgment, and no persistence beyond its own report file. All metrics are exact integer
rationals ``[numerator, denominator]``; the report ``content_hash`` excludes volatile provenance.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import ManufacturingEpisode
from mini_prometheus._provenance import now_rfc3339
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import arms, partition, protocol
from mini_prometheus.experiment.corpus import GENERATOR_VERSION, r_star_descriptor
from mini_prometheus.judgment.critic_model import CRITIC_MODEL_VERSION
from mini_prometheus.precedent.precedent_model import default_model as precedent_default_model
from mini_prometheus.precedent.precedent_model import relevance

from contracts.python.manufacturing.precedent_report_schema import PrecedentSignal

RUNNER_VERSION = "1.0.0"
_FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "rm5_corpus"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SINK = _REPO_ROOT / "artifacts" / "evaluation"


# --- analogy classification (reuses RM3 relevance; exact-duplicate exclusion) -----------------------

@dataclass(frozen=True)
class _AnalogousCase:
    episode: ManufacturingEpisode
    best_relevance: int  # best relevance vs any non-identical experience design


def _classify_held_out(
    held_out: list[ManufacturingEpisode], experience: list[ManufacturingEpisode]
) -> tuple[list[_AnalogousCase], int]:
    """Partition held-out into analogous cases (relevance in [MIN, IDENTICAL)) and count exact duplicates.

    Exact identity (relevance == IDENTICAL) is excluded from the analogous set and counted separately;
    by corpus construction there are no cross-partition exact design duplicates, so this stays 0.
    """
    pmodel = precedent_default_model()
    analogous: list[_AnalogousCase] = []
    excluded_duplicates = 0
    for hq in held_out:
        if hq.design_input is None:
            continue
        best = 0
        for ep in experience:
            if ep.design_input is None or ep.design_ref.content_hash == hq.design_ref.content_hash:
                continue  # exclude exact design identity from the analogy measure
            best = max(best, relevance(hq.design_input, ep.design_input, pmodel))
        if best >= protocol.IDENTICAL_RELEVANCE:
            excluded_duplicates += 1
        elif best >= protocol.ANALOGOUS_MIN_RELEVANCE:
            analogous.append(_AnalogousCase(episode=hq, best_relevance=best))
    return analogous, excluded_duplicates


# --- deterministic experience subsamples (content-hash prefix) --------------------------------------

def _subsample(experience: list[ManufacturingEpisode], fraction: float) -> list[ManufacturingEpisode]:
    """Deterministic prefix subsample of the content-hash-sorted experience corpus."""
    ordered = sorted(experience, key=lambda e: e.content_hash)
    return ordered[: int(len(ordered) * fraction)]


def _agreement_count(cases: list[_AnalogousCase], outcomes: list[arms.ArmOutcome]) -> int:
    return sum(protocol.correct(o.assessment, c.episode.verdict.status) for c, o in zip(cases, outcomes))


# --- the run ----------------------------------------------------------------------------------------

def run(fixture_dir: str | Path | None = None, *, produced_at: str | None = None) -> dict:
    """Execute the frozen compounding-validation experiment; return the full report dict.

    Deterministic: identical fixture + identical code ⇒ identical report ``content_hash``.
    """
    fx = Path(fixture_dir) if fixture_dir is not None else _FIXTURE
    episodes = load(fx / "episodes.jsonl")
    committed = json.loads((fx / "checkpoint.json").read_text(encoding="utf-8"))

    part = partition.partition(episodes)
    by_hash = {e.content_hash: e for e in episodes}
    experience = [by_hash[hx] for hx in part.experience]
    held_out = [by_hash[hx] for hx in part.held_out]

    checkpoint_id = partition.checkpoint_id(part)
    analogous, excluded_duplicates = _classify_held_out(held_out, experience)

    # --- arms over the analogous held-out set -------------------------------------------------------
    arm1 = [arms.cold_start(c.episode) for c in analogous]
    arm2 = [arms.no_precedent(c.episode) for c in analogous]
    arm3 = [arms.full_system(c.episode, experience) for c in analogous]

    n = len(analogous)
    a1, a2, a3 = (_agreement_count(analogous, arm) for arm in (arm1, arm2, arm3))

    # --- Arm1 == Arm2 validity control (exact critique-hash equality per case) ----------------------
    arm1_eq_arm2 = all(o1.critique_content_hash == o2.critique_content_hash for o1, o2 in zip(arm1, arm2))
    arm1_arm2_mismatches = sum(
        o1.critique_content_hash != o2.critique_content_hash for o1, o2 in zip(arm1, arm2)
    )

    # --- verdict-class denominators over the analogous set ------------------------------------------
    manu_idx = [i for i, c in enumerate(analogous) if protocol.is_manufacturable(c.episode.verdict.status)]
    _manu_set = set(manu_idx)
    not_idx = [i for i in range(n) if i not in _manu_set]

    # --- cautionary false alarms on MANUFACTURABLE controls (Arm3) ----------------------------------
    false_alarms = sum(
        protocol.is_false_alarm(arm3[i].assessment, analogous[i].episode.verdict.status) for i in manu_idx
    )

    # --- precedent coverage (Arm3 produced a non-NONE signal) per class -----------------------------
    def _coverage(idx: list[int]) -> int:
        return sum(1 for i in idx if arm3[i].signal is not PrecedentSignal.NONE)

    # --- compounding curve over deterministic experience subsamples ---------------------------------
    curve = []
    marginals: list[int] = []
    for frac in protocol.COMPOUNDING_FRACTIONS:
        sub = _subsample(experience, frac)
        sub_arm3 = arm3 if frac == 1.0 else [arms.full_system(c.episode, sub) for c in analogous]
        a3_sub = _agreement_count(analogous, sub_arm3)
        marginals.append(a3_sub - a2)
        curve.append(
            {
                "fraction": [round(frac * 4), 4],  # exact quarters: 0/4, 1/4, 2/4, 4/4
                "experience_size": len(sub),
                "arm3_agreement": [a3_sub, n],
                "marginal_vs_arm2": [a3_sub - a2, n],
            }
        )
    curve_non_decreasing = all(b >= a for a, b in zip(marginals, marginals[1:]))

    # --- hard validity gates (admissibility of the result; NOT the hypothesis) ----------------------
    validity_gates = {
        "VG1_arm1_equals_arm2_exact": arm1_eq_arm2,
        "VG2_both_verdict_classes_present": len(manu_idx) > 0 and len(not_idx) > 0,
        "VG3_no_cross_partition_exact_duplicates": excluded_duplicates == 0
        and set(e.design_ref.content_hash for e in experience).isdisjoint(
            e.design_ref.content_hash for e in held_out
        ),
        "VG4_checkpoint_matches_committed": checkpoint_id == committed["checkpoint_id"],
        "VG5_analogous_set_nonempty": n > 0,
        "VG6_partition_disjoint": set(part.experience).isdisjoint(set(part.held_out))
        and len(part.experience) + len(part.held_out) == len(episodes),
    }
    validity_passed = all(validity_gates.values())

    # --- hypothesis criteria (evaluated, reported, NEVER mutated; flat/negative is valid) -----------
    precedent_marginal = a3 - a2
    hypothesis = {
        "H1_precedent_marginal_positive": {
            "criterion": "Arm3 - Arm2 > 0",
            "value": [precedent_marginal, n],
            "met": precedent_marginal > 0,
        },
        "H2_zero_false_alarms_on_controls": {
            "criterion": f"cautionary false alarms on MANUFACTURABLE controls == {protocol.FALSE_ALARM_CEILING}",
            "origin": protocol.FALSE_ALARM_CEILING_ORIGIN,
            "value": [false_alarms, len(manu_idx)],
            "met": false_alarms == protocol.FALSE_ALARM_CEILING,
        },
        "H3_coverage_nonzero_both_classes": {
            "criterion": "precedent coverage > 0 for both verdict classes",
            "manufacturable": [_coverage(manu_idx), len(manu_idx)],
            "not_manufacturable": [_coverage(not_idx), len(not_idx)],
            "met": _coverage(manu_idx) > 0 and _coverage(not_idx) > 0,
        },
        "H4_compounding_non_decreasing": {
            "criterion": "marginal agreement non-decreasing in experience size",
            "marginals": marginals,
            "met": curve_non_decreasing,
            "note": "flat/decreasing is a VALID NOT-SUPPORTED outcome, not a failure",
        },
    }

    # --- metrics block (exact integer rationals [num, den]) -----------------------------------------
    metrics = {
        "n_analogous_held_out": n,
        "per_arm_oracle_agreement": {
            "arm1_cold_start": [a1, n],
            "arm2_no_precedent": [a2, n],
            "arm3_full_system": [a3, n],
        },
        "precedent_marginal_agreement": [precedent_marginal, n],
        "compounding_curve": curve,
        "cautionary_false_alarm_rate_on_controls": [false_alarms, len(manu_idx)],
        "precedent_coverage": {
            "manufacturable": [_coverage(manu_idx), len(manu_idx)],
            "not_manufacturable": [_coverage(not_idx), len(not_idx)],
        },
        "arm1_arm2_validity_control": {"equal_exact": arm1_eq_arm2, "mismatches": arm1_arm2_mismatches},
        "excluded_duplicate_count": excluded_duplicates,
    }

    # --- decoupling audit (why oracle agreement is non-tautological) --------------------------------
    decoupling_audit = {
        "not_class_marginal_zero_by_internal_verdict": [
            _agreement_count([analogous[i] for i in not_idx], [arm3[i] for i in not_idx])
            - _agreement_count([analogous[i] for i in not_idx], [arm2[i] for i in not_idx]),
            len(not_idx),
        ],
        "manufacturable_class_marginal": [
            _agreement_count([analogous[i] for i in manu_idx], [arm3[i] for i in manu_idx])
            - _agreement_count([analogous[i] for i in manu_idx], [arm2[i] for i in manu_idx]),
            len(manu_idx),
        ],
        "note": (
            "RM4's internal-verdict finding fires CAUTIONARY on adverse verdicts in ALL arms, so the "
            "NOT-class marginal cancels to 0; the precedent's measurable effect concentrates on "
            "MANUFACTURABLE held-out cases where internal-verdict is silent."
        ),
    }

    identity = {
        "evaluation_protocol_version": protocol.EVALUATION_PROTOCOL_VERSION,
        "runner_version": RUNNER_VERSION,
        "critic_model_version": CRITIC_MODEL_VERSION,
        "precedent_model_version": precedent_default_model().version,
        "generator_version": GENERATOR_VERSION,
        "checkpoint_id": checkpoint_id,
        "capability_regime": r_star_descriptor(),
        "metrics": metrics,
        "validity_gates": validity_gates,
        "hypothesis": hypothesis,
        "decoupling_audit": decoupling_audit,
    }
    report_content_hash = h.content_hash(identity)

    report = {
        **identity,
        "content_hash": report_content_hash,
        "validity_passed": validity_passed,
        "statement_of_claims": protocol.statement_of_claims(),
        "provenance": {
            "component": "rm5-compounding-runner",
            "component_version": RUNNER_VERSION,
            "produced_at": produced_at or now_rfc3339(),
            "fixture": "tests/fixtures/rm5_corpus/",
            "n_total": len(episodes),
            "n_experience": len(experience),
            "n_held_out": len(held_out),
        },
    }
    return report


def write_report(report: dict, sink_dir: str | Path | None = None) -> Path:
    """Write the report to the isolated evaluation sink (never the episode store). Returns the path."""
    sink = Path(sink_dir) if sink_dir is not None else _DEFAULT_SINK
    sink.mkdir(parents=True, exist_ok=True)
    out = sink / "rm5_compounding_report.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":  # pragma: no cover
    rep = run()
    path = write_report(rep)
    print(f"wrote {path} (content_hash={rep['content_hash']}, validity_passed={rep['validity_passed']})")
