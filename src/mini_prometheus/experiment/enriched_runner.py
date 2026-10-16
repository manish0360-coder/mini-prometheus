"""RM15 EC4 — additive enriched-oracle measurement harness (composes the FROZEN RM5 machinery).

This module assembles the registered RM15 report for the enriched corpus (RM8 ``constrained_model()``)
WITHOUT modifying any frozen RM5 module. It reuses the frozen definitions by import:
- ``runner._classify_held_out`` (held-out analogous membership) and ``runner._subsample`` (compounding
  subsamples) — permitted private reuse;
- ``protocol`` (correct/agrees/is_false_alarm/is_manufacturable mapping, frozen); status-class agreement
  sums the frozen per-case ``protocol.correct`` (the same primitive ``runner._agreement_count`` sums);
- ``arms`` (the three arms — executed ONLY inside ``run``), ``partition`` (frozen), and
  ``enriched_corpus.classify`` (EC1 verdict-axis labels).

Separation of concerns (so pre-run tests never execute arms): ``run()`` is the ONLY function that
executes arms; ``assemble_report()`` is pure and builds the full report from already-computed per-case
outcomes, so it is fully testable with injected synthetic outcomes. Importing this module has no
measurement side effect; the ``__main__`` block (the measurement entry) runs only when executed as a
script and is NOT invoked by tests.

Dropped per RM15 governance: reason-aligned agreement (no defensible frozen RM4-finding -> oracle
reason-code mapping). It is reported as ``measured: false`` with the reason, never silently computed.

Scientific boundary (recorded in the report): on the primary MANUFACTURABLE subset Arm2 structurally
abstains (NEUTRAL) and is always non-correct, so ``c == 0`` by construction and ``(b-c)/n`` equals Arm3's
one-sample agreement rate against a STRUCTURALLY ABSTAINING baseline — NOT a conventional
paired-classifier improvement. Any ``c != 0`` is a validity failure. The enriched RM1/RM8 rules are
synthetic declared-model rules; this is not real-world manufacturing validation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from mini_prometheus import _hashing as h
from mini_prometheus._provenance import now_rfc3339
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import arms, enriched_corpus, partition, protocol, runner
from mini_prometheus.manufacturing_constraints.capability_model import constrained_model
from mini_prometheus.judgment.critic_model import CRITIC_MODEL_VERSION
from mini_prometheus.precedent.precedent_model import default_model as precedent_default_model

RM15_RUNNER_VERSION = "1.0.0"
RM15_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "rm15_corpus"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SINK = _REPO_ROOT / "artifacts" / "evaluation"
_RM15_FIXTURE_LABEL = "tests/fixtures/rm15_corpus/"

# Per the §B audit: tolerance/MANUFACTURABLE verdicts depend on model-only data RM3 cannot see;
# material and precedence depend on DesignInput features RM3 ranks on -> similarity-confounded.
_SIMILARITY_CONFOUNDED = {"material": True, "precedence": True, "tolerance": False}


def constrained_model_descriptor() -> dict:
    """Deterministic JSON descriptor of the RM15 regime (constrained_model()); NEVER r_star/rm5."""
    m = constrained_model()
    return {
        "version": m.version,
        "derivation": "constrained_model() (full default resources + declared precedence + tolerance)",
        "op_capability": {op.value: cap for op, cap in sorted(m.op_capability.items(), key=lambda kv: kv[0].value)},
        "resources": {rid: sorted(caps) for rid, caps in sorted(m.resources.items())},
        "supported_materials": sorted(m.supported_materials),
        "capability_tolerance_mm": {k: m.capability_tolerance_mm[k] for k in sorted(m.capability_tolerance_mm)},
        "ordering_constraints": sorted([before.value, after.value] for before, after in m.ordering_constraints),
        "unavailable_resources": sorted(m.unavailable_resources),
    }


def statement_of_claims() -> dict:
    """Frozen RM5 Statement of Claims PLUS the RM15 boundary additions (synthetic enriched rules)."""
    soc = dict(protocol.statement_of_claims())
    soc["rm15_scientific_boundary"] = [
        "The enriched RM1/RM8 oracle rules (declared precedence, scalar tolerance minimums) are SYNTHETIC "
        "declared-model rules — this is NOT real-world manufacturing validation.",
        "Precedence and material per-axis diagnostics are similarity-confounded (DesignInput features RM3 "
        "ranks on) and are NOT causal attribution of engineering judgment.",
        "On the primary MANUFACTURABLE subset the Arm2 baseline structurally abstains; the primary marginal "
        "is Arm3's one-sample agreement rate against an abstaining baseline, not a paired-classifier gain.",
        "No generalization beyond this fixed regime and this synthetic corpus is claimed.",
    ]
    return soc


# --- pure report assembly (NO arm execution; testable with injected synthetic outcomes) -------------

@dataclass(frozen=True)
class CompoundingInput:
    fraction: float
    experience_size: int
    sub_arm3: tuple[arms.ArmOutcome, ...]   # Arm3 outcome per analogous case at this N
    axis_composition: dict[str, int]        # verdict-axis composition of the experience subsample


def _agreement(outcomes: list[arms.ArmOutcome], statuses: list[str]) -> int:
    """Status-class agreement = sum of the FROZEN per-case ``protocol.correct`` (the primitive that
    ``runner._agreement_count`` itself sums)."""
    return sum(protocol.correct(o.assessment, s) for o, s in zip(outcomes, statuses))


def _axis_composition(episodes: list) -> dict[str, int]:
    """Verdict-axis composition = the ``enriched_corpus.classify`` distribution of an episode subset.

    Pure (no arms). Used by ``run`` for each compounding subsample AND directly testable against the
    same subset, so the sub_arm3<->composition correspondence can be verified without executing arms.
    """
    comp: dict[str, int] = {}
    for e in episodes:
        label = enriched_corpus.classify(e)
        comp[label] = comp.get(label, 0) + 1
    return comp


def assemble_report(
    *,
    statuses: list[str],                    # verdict.status per held-out analogous case
    labels: list[str],                      # enriched_corpus.classify per held-out analogous case
    arm1: list[arms.ArmOutcome],
    arm2: list[arms.ArmOutcome],
    arm3: list[arms.ArmOutcome],
    compounding: list[CompoundingInput],
    excluded_duplicates: int,
    cross_partition_design_dups: int,
    checkpoint_computed: str,
    checkpoint_committed: str,
    partition_disjoint: bool,
    partition_covering: bool,
    n_total: int,
    n_experience: int,
    n_held_out: int,
    produced_at: str | None = None,
) -> dict:
    """Build the registered RM15 report from already-computed outcomes. Pure; executes no arm."""
    n = len(statuses)
    assert len(labels) == len(arm1) == len(arm2) == len(arm3) == n

    a1, a2, a3 = (_agreement(arm, statuses) for arm in (arm1, arm2, arm3))
    manu_idx = [i for i in range(n) if protocol.is_manufacturable(statuses[i])]
    not_idx = [i for i in range(n) if i not in set(manu_idx)]

    # --- PRIMARY: paired Arm2/Arm3 table on the held-out analogous MANUFACTURABLE subset ------------
    b = c = 0
    for i in manu_idx:
        a2c = protocol.correct(arm2[i].assessment, statuses[i])
        a3c = protocol.correct(arm3[i].assessment, statuses[i])
        if a2c == 0 and a3c == 1:
            b += 1
        elif a2c == 1 and a3c == 0:
            c += 1
    n_manu = len(manu_idx)
    # Structural abstention: Arm2 must be NON-CORRECT on EVERY primary MANUFACTURABLE case. This is
    # strictly stronger than c==0 (Arm2 and Arm3 could both be correct, leaving c==0 without abstention).
    arm2_abstains_on_primary = all(
        protocol.correct(arm2[i].assessment, statuses[i]) == 0 for i in manu_idx)
    primary = {
        "subset": "held_out_analogous_MANUFACTURABLE",
        "denominator": n_manu,
        "paired_table": {"b_arm3_corrects_arm2_errors": b, "c_arm3_regressions": c},
        "marginal": [b - c, n_manu],
        "arm2_structurally_abstains": arm2_abstains_on_primary,
        "interpretation": (
            "Arm2 structurally abstains on this subset (NEUTRAL => non-correct), so c==0 by construction "
            "and (b-c)/n is Arm3's one-sample agreement rate against an abstaining baseline — NOT a "
            "conventional paired-classifier improvement."
        ),
    }

    # --- per-axis diagnostics (adverse single-cause axes; marginal expected ~0; confounded flags) ---
    per_axis = {}
    for axis in ("material", "precedence", "tolerance"):
        idx = [i for i in range(n) if labels[i] == axis]
        a2_ax = sum(protocol.correct(arm2[i].assessment, statuses[i]) for i in idx)
        a3_ax = sum(protocol.correct(arm3[i].assessment, statuses[i]) for i in idx)
        per_axis[axis] = {
            "marginal": [a3_ax - a2_ax, len(idx)],
            "similarity_confounded": _SIMILARITY_CONFOUNDED[axis],
            "note": "diagnostic only; not causal attribution" if _SIMILARITY_CONFOUNDED[axis] else "diagnostic",
        }

    false_alarms = sum(protocol.is_false_alarm(arm3[i].assessment, statuses[i]) for i in manu_idx)

    def _coverage(idx: list[int]) -> int:
        from contracts.python.manufacturing.precedent_report_schema import PrecedentSignal
        return sum(1 for i in idx if arm3[i].signal is not PrecedentSignal.NONE)

    arm1_eq_arm2 = all(o1.critique_content_hash == o2.critique_content_hash for o1, o2 in zip(arm1, arm2))
    arm1_arm2_mismatches = sum(
        o1.critique_content_hash != o2.critique_content_hash for o1, o2 in zip(arm1, arm2))

    # --- compounding curve (reuses frozen subsampling upstream) + per-N axis composition ------------
    curve = []
    curve_marginals: list[int] = []
    for pt in compounding:
        # Fail closed: a sub_arm3 shorter than the analogous set would let `zip` in `_agreement`
        # silently truncate, yielding a misleading numerator over the full denominator `n`.
        if len(pt.sub_arm3) != n:
            raise ValueError(
                f"compounding sub_arm3 length {len(pt.sub_arm3)} != analogous set size {n} "
                f"(fraction {pt.fraction}); refusing to emit a truncated agreement numerator")
        a3_sub = _agreement(list(pt.sub_arm3), statuses)
        curve_marginals.append(a3_sub - a2)
        curve.append({
            "fraction": [round(pt.fraction * 4), 4],
            "experience_size": pt.experience_size,
            "arm3_agreement": [a3_sub, n],
            "marginal_vs_arm2": [a3_sub - a2, n],
            "experience_axis_composition": {k: pt.axis_composition[k] for k in sorted(pt.axis_composition)},
        })

    # --- hard validity gates (admissibility) --------------------------------------------------------
    validity_gates = {
        "VG1_arm1_equals_arm2_exact": arm1_eq_arm2,
        "VG2_both_verdict_classes_present": len(manu_idx) > 0 and len(not_idx) > 0,
        "VG3_no_cross_partition_exact_duplicates": excluded_duplicates == 0 and cross_partition_design_dups == 0,
        "VG4_checkpoint_matches_committed": checkpoint_computed == checkpoint_committed,
        "VG5_analogous_set_nonempty": n > 0,
        "VG6_partition_disjoint_and_covering": partition_disjoint and partition_covering,
        # RM15 structural-admissibility invariant: the primary (b-c)/n is only interpretable as "Arm3 vs an
        # abstaining baseline" when BOTH hold — Arm2 is non-correct on every primary MANUFACTURABLE case
        # (structural abstention) AND the paired regression count c is zero. c==0 alone is insufficient.
        "RM15_primary_arm2_abstains_and_c_zero": arm2_abstains_on_primary and c == 0,
    }
    validity_passed = all(validity_gates.values())

    hypothesis = {
        "H1_precedent_marginal_positive_MANUFACTURABLE": {
            "criterion": "primary (b-c)/n > 0 on held-out analogous MANUFACTURABLE",
            "value": [b - c, n_manu],
            "met": (b - c) > 0,
        },
        "H2_zero_false_alarms_on_controls": {
            "criterion": f"cautionary false alarms on MANUFACTURABLE controls == {protocol.FALSE_ALARM_CEILING}",
            "origin": protocol.FALSE_ALARM_CEILING_ORIGIN,
            "value": [false_alarms, n_manu],
            "met": false_alarms == protocol.FALSE_ALARM_CEILING,
        },
        "H3_coverage_nonzero_both_classes": {
            "criterion": "precedent coverage > 0 for both verdict classes",
            "manufacturable": [_coverage(manu_idx), n_manu],
            "not_manufacturable": [_coverage(not_idx), len(not_idx)],
            "met": _coverage(manu_idx) > 0 and _coverage(not_idx) > 0,
        },
        "H4_compounding_non_decreasing": {
            "criterion": "marginal non-decreasing in experience size (flat/decreasing is valid NOT-SUPPORTED)",
            "marginals": curve_marginals,
            "met": all(y >= x for x, y in zip(curve_marginals, curve_marginals[1:])),
        },
    }

    metrics = {
        "n_analogous_held_out": n,
        "primary_marginal_MANUFACTURABLE": primary,
        "per_arm_oracle_agreement_status_class": {
            "arm1_cold_start": [a1, n], "arm2_no_precedent": [a2, n], "arm3_full_system": [a3, n],
        },
        "aggregate_marginal": [a3 - a2, n],
        "per_axis_diagnostics": per_axis,
        "cautionary_false_alarm_rate_on_controls": [false_alarms, n_manu],
        "precedent_coverage": {
            "manufacturable": [_coverage(manu_idx), n_manu],
            "not_manufacturable": [_coverage(not_idx), len(not_idx)],
        },
        "arm1_arm2_validity_control": {"equal_exact": arm1_eq_arm2, "mismatches": arm1_arm2_mismatches},
        "excluded_duplicate_count": excluded_duplicates,
        "compounding_curve": curve,
        "reason_aligned_agreement": {
            "measured": False,
            "reason": "dropped per RM15 governance: no defensible frozen RM4-finding -> oracle reason-code mapping",
        },
    }

    identity = {
        "evaluation_protocol_version": protocol.EVALUATION_PROTOCOL_VERSION,
        "rm15_runner_version": RM15_RUNNER_VERSION,
        "critic_model_version": CRITIC_MODEL_VERSION,
        "precedent_model_version": precedent_default_model().version,
        "enriched_generator_version": enriched_corpus.GENERATOR_VERSION,
        "checkpoint_id": checkpoint_computed,
        "capability_regime": constrained_model_descriptor(),
        "fixture": _RM15_FIXTURE_LABEL,
        "metrics": metrics,
        "validity_gates": validity_gates,
        "hypothesis": hypothesis,
    }
    report_content_hash = h.content_hash(identity)
    return {
        **identity,
        # Fields intentionally OUTSIDE the identity hash: content_hash (self), validity_passed (derived
        # from validity_gates), statement_of_claims (static boundary text), and provenance (produced_at
        # is volatile; the n_* counts are deterministic but kept with provenance by convention, mirroring
        # the frozen RM5 runner). Everything hash-relevant lives in `identity` above.
        "content_hash": report_content_hash,
        "validity_passed": validity_passed,
        "statement_of_claims": statement_of_claims(),
        "provenance": {
            "component": "rm15-enriched-runner",
            "component_version": RM15_RUNNER_VERSION,
            "produced_at": produced_at or now_rfc3339(),
            "fixture": _RM15_FIXTURE_LABEL,
            "n_total": n_total, "n_experience": n_experience, "n_held_out": n_held_out,
        },
    }


# --- the measurement (executes arms — ONLY here; NOT called by tests, NOT in this phase) ------------

def run(fixture_dir: str | Path | None = None, *, produced_at: str | None = None) -> dict:  # pragma: no cover
    """Execute the RM15 enriched measurement once. Runs the three frozen arms. Do not call in EC4-implement."""
    fx = Path(fixture_dir) if fixture_dir is not None else RM15_FIXTURE_DIR
    episodes = load(fx / "episodes.jsonl")
    committed = json.loads((fx / "checkpoint.json").read_text(encoding="utf-8"))
    part = partition.partition(episodes)
    by_hash = {e.content_hash: e for e in episodes}
    experience = [by_hash[hx] for hx in part.experience]
    held_out = [by_hash[hx] for hx in part.held_out]
    analogous, excluded_duplicates = runner._classify_held_out(held_out, experience)

    statuses = [c.episode.verdict.status for c in analogous]
    labels = [enriched_corpus.classify(c.episode) for c in analogous]
    arm1 = [arms.cold_start(c.episode) for c in analogous]
    arm2 = [arms.no_precedent(c.episode) for c in analogous]
    arm3 = [arms.full_system(c.episode, experience) for c in analogous]

    compounding: list[CompoundingInput] = []
    for frac in protocol.COMPOUNDING_FRACTIONS:
        sub = runner._subsample(experience, frac)
        sub_arm3 = tuple(arm3) if frac == 1.0 else tuple(arms.full_system(c.episode, sub) for c in analogous)
        compounding.append(CompoundingInput(frac, len(sub), sub_arm3, _axis_composition(sub)))

    exp_designs = {e.design_ref.content_hash for e in experience}
    held_designs = {e.design_ref.content_hash for e in held_out}
    return assemble_report(
        statuses=statuses, labels=labels, arm1=arm1, arm2=arm2, arm3=arm3, compounding=compounding,
        excluded_duplicates=excluded_duplicates,
        cross_partition_design_dups=len(exp_designs & held_designs),
        checkpoint_computed=partition.checkpoint_id(part), checkpoint_committed=committed["checkpoint_id"],
        partition_disjoint=set(part.experience).isdisjoint(part.held_out),
        partition_covering=len(part.experience) + len(part.held_out) == len(episodes),
        n_total=len(episodes), n_experience=len(experience), n_held_out=len(held_out),
        produced_at=produced_at,
    )


def write_report(report: dict, sink_dir: str | Path | None = None) -> Path:  # pragma: no cover
    sink = Path(sink_dir) if sink_dir is not None else _DEFAULT_SINK
    sink.mkdir(parents=True, exist_ok=True)
    out = sink / "rm15_report.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":  # pragma: no cover
    rep = run()
    path = write_report(rep)
    print(f"wrote {path} (content_hash={rep['content_hash']}, validity_passed={rep['validity_passed']})")
