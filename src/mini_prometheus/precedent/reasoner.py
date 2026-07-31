"""RM3-M3: Engineering Precedent Reasoning — the RM3 architectural identity.

From the deterministically ranked precedents produced by the RM3-M2 ``retriever`` (``RankedPrecedent``
— the sole hand-off), this module derives an advisory ``PrecedentSignal`` and assembles the
``PrecedentReport`` (with its ``PrecedentEntry[]``), computes the report ``content_hash`` and
deterministic ``report_id``, and populates provenance — exactly per the frozen RM3 contract package
(§2–§7). It is *domain reasoning content* (Law 3), the counterpart to the retriever's mechanism.

Strict boundaries (RM3 spec §6/§8; this milestone's requirements):
- consumes ``RankedPrecedent`` results only — it never retrieves, ranks, or re-scores (no retrieval
  logic; it imports only the ``RankedPrecedent`` hand-off type from the retriever, not its functions);
- no planning, no manufacturability verification, no adaptive learning, no plan mutation;
- read-only and pure: it builds and returns a report object and writes nothing (no persistence);
- no orchestration (composing intake → retrieve → reason is RM3-M4's ``precedent_runner``);
- no ML / embeddings / vector search; no Noetica / MiniFlyWire.

Honesty (Law 18, spec §8): the report carries **no** query-verdict field (structurally impossible to
assert a precedent's verdict as the query's own); each precedent is labeled *analogous* by its
relevance score and grounded by ``episode_ref.content_hash``.
"""
from __future__ import annotations

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import (
    DesignInput,
    EngineeringVerificationStatus,
    ManufacturabilityReasonCode,
    ManufacturabilityVerdictStatus,
    Ref,
)
from mini_prometheus._provenance import make_provenance, now_rfc3339
from mini_prometheus.precedent.precedent_model import PRECEDENT_MODEL_VERSION
from mini_prometheus.precedent.retriever import RankedPrecedent

from contracts.python.manufacturing.precedent_report_schema import (
    PrecedentEntry,
    PrecedentReport,
    PrecedentSignal,
)

REPORT_SCHEMA_VERSION = "1.0.0"
REASONER_VERSION = "1.0.0"
_RULE_ID = "precedent.reasoning"
# The frozen Provenance requires capability_model_version; this record is precedent reasoning, whose
# governing model is the top-level precedent_model_version — so the field is the "not applicable"
# sentinel per contract package §6.
_CAPABILITY_SENTINEL = "0.0.0"

# A precedent is signal-eligible ("strongly relevant") only if its per-mille relevance is at least this
# threshold. Default 1 = it must share at least one engineering feature (score 0 = shares nothing, so it
# is never signal-eligible). The numeric threshold conceptually belongs to precedent_model_version; the
# frozen RM3-M1 PrecedentModel does not yet carry it, so it is surfaced here as an overridable default
# (the same threshold/K gap flagged at RM3-M1/M2) — callers/models may raise it. It gates only signal
# derivation, never which precedents appear in the report.
DEFAULT_RELEVANCE_THRESHOLD = 1

# Only these verdicts are decisive manufacturability outcomes for signal derivation; PLAN_INVALID (and
# the never-persisted INFRA_ERROR) are not manufacturability outcomes and are not signal-eligible. This
# keeps contract §4 invariant 2 true by construction (a signal source is MANUFACTURABLE or NOT_MANUFACTURABLE).
_DECISIVE = {
    ManufacturabilityVerdictStatus.MANUFACTURABLE: PrecedentSignal.SUPPORTING,
    ManufacturabilityVerdictStatus.NOT_MANUFACTURABLE: PrecedentSignal.CAUTIONARY,
}


def _entry(rank: int, rp: RankedPrecedent) -> PrecedentEntry:
    """Build a PrecedentEntry exactly from a retrieved precedent (contract package §3)."""
    e = rp.episode
    return PrecedentEntry(
        rank=rank,
        episode_ref=Ref(id=e.episode_id, content_hash=e.content_hash),
        relevance_score=rp.relevance_score,
        verdict_status=ManufacturabilityVerdictStatus(e.verdict.status),
        reason_codes=[ManufacturabilityReasonCode(c) for c in e.verdict.reason_codes],
        precedent_verification_status=EngineeringVerificationStatus(e.engineering_verification_status),
    )


def _derive_signal(
    entries: list[PrecedentEntry], relevance_threshold: int
) -> tuple[PrecedentSignal, int | None]:
    """Deterministically derive (signal, signal_source_rank) from the ranked entries.

    The nearest (lowest-rank) strongly-relevant precedent with a decisive verdict sets the signal:
    MANUFACTURABLE → SUPPORTING, NOT_MANUFACTURABLE → CAUTIONARY. If none qualifies (empty, all below
    threshold, or none decisive) → NONE / null (contract package §2, §4 invariants 2 & 4).
    """
    for e in entries:  # entries are already in rank order (0..n-1), relevance descending
        if e.relevance_score >= relevance_threshold and e.verdict_status in _DECISIVE:
            return _DECISIVE[e.verdict_status], e.rank
    return PrecedentSignal.NONE, None


def _query_ref(query: DesignInput) -> Ref:
    """Ref to the query DesignInput (id + content_hash of its identity view) — ties report to the query."""
    return Ref(id=query.design_input_id, content_hash=h.content_hash(h.design_input_identity(query)))


def _report_identity(
    query_ref: Ref,
    entries: list[PrecedentEntry],
    signal: PrecedentSignal,
    signal_source_rank: int | None,
    precedent_model_version: str,
) -> dict:
    """The content_hash identity view (contract package §4): excludes report_id, content_hash, provenance."""
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "query_design_input_ref": h.to_contract_dict(query_ref),
        "precedents": [
            {
                "rank": e.rank,
                "episode_ref": h.to_contract_dict(e.episode_ref),
                "relevance_score": e.relevance_score,
                "verdict_status": h.to_contract_dict(e.verdict_status),
                "reason_codes": sorted(h.to_contract_dict(c) for c in e.reason_codes),
                "precedent_verification_status": h.to_contract_dict(e.precedent_verification_status),
            }
            for e in entries
        ],
        "signal": h.to_contract_dict(signal),
        "signal_source_rank": signal_source_rank,
        "precedent_model_version": precedent_model_version,
    }


def reason(
    query: DesignInput,
    ranked: list[RankedPrecedent],
    *,
    precedent_model_version: str = PRECEDENT_MODEL_VERSION,
    relevance_threshold: int = DEFAULT_RELEVANCE_THRESHOLD,
    produced_at: str | None = None,
) -> PrecedentReport:
    """Assemble the advisory PrecedentReport from ranked precedents (Engineering Precedent Reasoning).

    Pure and read-only: derives the signal, builds entries, computes the content-hash identity and the
    deterministic ``report_id``, and populates provenance. Determinism: identical query + identical
    ranked precedents + identical ``precedent_model_version`` ⇒ identical ``content_hash`` and
    ``report_id`` (``produced_at``/provenance excluded from identity).
    """
    produced_at = produced_at or now_rfc3339()
    query_ref = _query_ref(query)
    entries = [_entry(rank, rp) for rank, rp in enumerate(ranked)]
    signal, signal_source_rank = _derive_signal(entries, relevance_threshold)

    identity = _report_identity(query_ref, entries, signal, signal_source_rank, precedent_model_version)
    report_content_hash = h.content_hash(identity)
    report_id = h.derive_uuid(report_content_hash)

    provenance = make_provenance(
        source_refs=[query_ref, *[e.episode_ref for e in entries]],
        rule_id=_RULE_ID,
        rule_version=REASONER_VERSION,
        produced_at=produced_at,
        component="precedent-reasoner",
        component_version=REASONER_VERSION,
        capability_model_version=_CAPABILITY_SENTINEL,
    )

    return PrecedentReport(
        schema_version=REPORT_SCHEMA_VERSION,
        report_id=report_id,
        query_design_input_ref=query_ref,
        precedents=entries,
        signal=signal,
        signal_source_rank=signal_source_rank,
        precedent_model_version=precedent_model_version,
        content_hash=report_content_hash,
        provenance=provenance,
    )
