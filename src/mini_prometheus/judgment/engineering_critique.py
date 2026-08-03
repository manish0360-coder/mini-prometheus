"""RM4 Commit 3: Engineering Critique — the first implementation of Engineering Judgment.

Applies the deterministic ``critic_model`` (RM4 Commit 2) to the internal ``EngineeringSituation``
(RM4 Commit 1), orders the resulting findings by a deterministic total order, derives the summary
assessment, and assembles the advisory ``EngineeringCritique`` result — computing a reproducible
content-hash and provenance via the reused RM1 mechanisms.

Boundaries (RM4 spec §6/§8): no planning, no manufacturability verification, no retrieval, no
persistence, no ML; it reads the situation and returns an in-memory advisory object and writes nothing.
The ``content_hash`` is an **in-memory reproducibility fingerprint** (spec §4/§8 — identical inputs ⇒
identical critique), NOT an external, persisted, or published identity: nothing is written, no id is
minted, no other module depends on it, and the critique is not a contract. The internal
``EngineeringSituation`` is consumed but never exposed on the result.
"""
from __future__ import annotations

from dataclasses import dataclass

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import Provenance, Ref
from mini_prometheus._provenance import make_provenance, now_rfc3339
from mini_prometheus.judgment.critic_model import (
    Assessment,
    CriticFinding,
    CriticModel,
    assess,
    default_model,
    evaluate,
)
from mini_prometheus.judgment.engineering_situation import EngineeringSituation

CRITIQUE_VERSION = "1.0.0"
_RULE_ID = "engineering.judgment.critique"
# The frozen Provenance requires capability_model_version; this record is judgment content whose
# governing model is `critic_model_version`, so the field is the "not applicable" sentinel (as RM3 does).
_CAPABILITY_SENTINEL = "0.0.0"


@dataclass(frozen=True)
class EngineeringCritique:
    """The advisory output of Engineering Judgment (internal runtime object — not a contract).

    ``content_hash`` is an in-memory reproducibility fingerprint (identity view excludes ``provenance``,
    whose ``produced_at`` is volatile); the critique is never persisted or published.
    """

    critic_model_version: str
    case_ref: Ref
    findings: tuple[CriticFinding, ...]
    assessment: Assessment
    content_hash: str
    provenance: Provenance


def _order(findings: tuple[CriticFinding, ...]) -> tuple[CriticFinding, ...]:
    """Deterministic total order over findings (kind, polarity, constituent, reason codes, detail)."""
    return tuple(
        sorted(
            findings,
            key=lambda f: (
                f.kind.value,
                f.polarity.value,
                f.constituent,
                tuple(sorted(f.reason_codes)),
                f.detail,
            ),
        )
    )


def _case_ref(situation: EngineeringSituation) -> Ref:
    """Ref to the case's design (id + content hash) — reuses the design's existing identity; mints none."""
    di = situation.design_input
    return Ref(id=di.design_input_id, content_hash=h.content_hash(h.design_input_identity(di)))


def _critique_identity(
    case_ref: Ref,
    findings: tuple[CriticFinding, ...],
    assessment: Assessment,
    critic_model_version: str,
) -> dict:
    """The content-hash identity view. Excludes provenance (volatile) and content_hash (self)."""
    return {
        "critic_model_version": critic_model_version,
        "case_ref": h.to_contract_dict(case_ref),
        "findings": [
            {
                "kind": f.kind.value,
                "polarity": f.polarity.value,
                "constituent": f.constituent,
                "reason_codes": sorted(f.reason_codes),
                "detail": f.detail,
            }
            for f in findings
        ],
        "assessment": assessment.value,
    }


def critique(
    situation: EngineeringSituation,
    model: CriticModel | None = None,
    *,
    produced_at: str | None = None,
) -> EngineeringCritique:
    """Produce the advisory Engineering Critique for a situation (Engineering Judgment, first form).

    Pure and read-only: applies ``critic_model``, orders the findings, derives the assessment, and
    computes the reproducible ``content_hash`` + provenance. Determinism: identical situation + identical
    ``critic_model_version`` ⇒ identical ``content_hash`` (``produced_at``/provenance excluded).
    """
    model = model or default_model()
    produced_at = produced_at or now_rfc3339()

    findings = _order(evaluate(situation, model))
    assessment = assess(findings, model)
    case_ref = _case_ref(situation)

    identity = _critique_identity(case_ref, findings, assessment, model.version)
    content_hash = h.content_hash(identity)

    provenance = make_provenance(
        source_refs=[case_ref],
        rule_id=_RULE_ID,
        rule_version=CRITIQUE_VERSION,
        produced_at=produced_at,
        component="engineering-critic",
        component_version=CRITIQUE_VERSION,
        capability_model_version=_CAPABILITY_SENTINEL,
    )

    return EngineeringCritique(
        critic_model_version=model.version,
        case_ref=case_ref,
        findings=findings,
        assessment=assessment,
        content_hash=content_hash,
        provenance=provenance,
    )
