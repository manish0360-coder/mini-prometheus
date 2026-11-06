"""MP-S1 (spec §3.7 guarantee 2, ADR-0022): label cross-shop precedent as non-authoritative.

RM3 retrieval and RM4 judgment are byte-frozen and rank precedent regardless of the shop it was judged
under. This module does not filter them. It ANNOTATES a ``PrecedentReport``: each entry is resolved
against the store by ``episode_ref.content_hash`` (fail closed: an unmatched ref is UNRESOLVED, never
assumed) and its plan's shop identity is compared with the current declared shop. Only a precedent
judged under the exact same shop declaration may count as advisory capability evidence for this
shop; every other basis is non-authoritative. The frozen ``PrecedentReport`` and its hash are not
modified; the annotation is a separate internal object (not a contract, not persisted).

Precedent never reaches a manufacturability verdict at all: the verdict paths cannot import
``precedent`` / ``judgment`` (an import-linter contract, guarantee 1).
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from contracts.python.manufacturing.precedent_report_schema import PrecedentReport
from mini_prometheus._contracts import ManufacturingEpisode, ManufacturingRequest, Ref
from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.manufacturing_constraints.capability_model import ProcessCapabilityModel
from mini_prometheus.orchestration.precedent_runner import run_precedent
from mini_prometheus.shop_declaration.shop_model import capability_model_ref_for

NON_AUTHORITATIVE_NOTE = (
    "Precedent judged under a different, unknown or unresolved shop declaration is not evidence of "
    "capability in the current shop."
)


class PrecedentBasis(StrEnum):
    SAME_DECLARATION = "SAME_DECLARATION"
    SAME_CONTENT_OTHER_DECLARATION = "SAME_CONTENT_OTHER_DECLARATION"
    OTHER_SHOP = "OTHER_SHOP"
    UNKNOWN_BASIS = "UNKNOWN_BASIS"
    UNRESOLVED = "UNRESOLVED"


class SignalAuthority(StrEnum):
    SAME_DECLARATION_ADVISORY = "SAME_DECLARATION_ADVISORY"
    NON_AUTHORITATIVE_CROSS_BASIS = "NON_AUTHORITATIVE_CROSS_BASIS"


@dataclass(frozen=True)
class EntryBasis:
    rank: int
    episode_ref: Ref
    basis: PrecedentBasis
    capability_evidence: bool  # True only for SAME_DECLARATION (and even then advisory)


@dataclass(frozen=True)
class PrecedentBasisAnnotation:
    report_content_hash: str
    entries: tuple[EntryBasis, ...]
    signal: str
    signal_authority: SignalAuthority
    note: str


def annotate_precedent_basis(
    report: PrecedentReport,
    episodes: Iterable[ManufacturingEpisode],
    current_model: ProcessCapabilityModel,
) -> PrecedentBasisAnnotation:
    by_hash = {episode.content_hash: episode for episode in episodes}
    current = capability_model_ref_for(current_model)
    entries: list[EntryBasis] = []
    for entry in report.precedents:
        episode = by_hash.get(entry.episode_ref.content_hash)
        if episode is None:
            basis = PrecedentBasis.UNRESOLVED
        else:
            prior = episode.plan.capability_model_ref
            if current is None or prior is None:
                basis = PrecedentBasis.UNKNOWN_BASIS
            elif prior.shop_declaration_hash == current.shop_declaration_hash:
                basis = PrecedentBasis.SAME_DECLARATION
            elif prior.shop_content_hash == current.shop_content_hash:
                basis = PrecedentBasis.SAME_CONTENT_OTHER_DECLARATION
            else:
                basis = PrecedentBasis.OTHER_SHOP
        entries.append(
            EntryBasis(entry.rank, entry.episode_ref, basis, basis == PrecedentBasis.SAME_DECLARATION)
        )
    # Conservative report-level rule (spec §3.7): one non-same-declaration entry is enough to mark
    # the signal non-authoritative. It deliberately does not re-derive which entry drove the signal
    # (that would duplicate RM3's reasoner, Law 13).
    authority = (
        SignalAuthority.SAME_DECLARATION_ADVISORY
        if all(e.basis == PrecedentBasis.SAME_DECLARATION for e in entries)
        else SignalAuthority.NON_AUTHORITATIVE_CROSS_BASIS
    )
    return PrecedentBasisAnnotation(
        report_content_hash=report.content_hash,
        entries=tuple(entries),
        signal=str(report.signal),
        signal_authority=authority,
        note=NON_AUTHORITATIVE_NOTE,
    )


def run_precedent_for_shop(
    request: ManufacturingRequest,
    *,
    capability_model: ProcessCapabilityModel,
    store_path: str | None = None,
    **precedent_options: Any,
) -> tuple[PrecedentReport, PrecedentBasisAnnotation]:
    """The documented entry point for precedent under a declared shop: the UNCHANGED RM3
    ``run_precedent`` followed by the basis annotation over the same store."""
    report = run_precedent(request, store_path=store_path, **precedent_options)
    return report, annotate_precedent_basis(report, load(store_path), capability_model)
