"""RM3-M4: the Engineering Precedent Composition — the thin, read-only entry point.

Composes the already-implemented RM3 modules into one deterministic end-to-end call:

    ManufacturingRequest
      -> DesignInput        (RM1 intake, read-only)
      -> RankedPrecedent[]  (RM3-M2 retriever, read-only corpus scan)
      -> PrecedentReport    (RM3-M3 reasoner, pure)

This is a NEW file. RM1's ``runner.py``, RM2's ``reuse_runner.py``, and every RM3 module
(``precedent_model``, ``retriever``, ``reasoner``) are byte-unchanged. The composition holds **no**
business logic of its own — no retrieval, no reasoning, no planning, no manufacturability verification,
no persistence, no adaptation, no caching, no ML, no embeddings, no vector DB, no Noetica, no
MiniFlyWire. It only wires the existing components and shares one ``produced_at`` and one model version
across the steps, so the report faithfully records the model that produced the ranking.

Read-only: intake validates and writes nothing; the retriever reads the corpus read-only; the reasoner
is pure. No episode is written. Determinism: identical request + identical corpus + identical model
version ⇒ identical ``PrecedentReport`` ``content_hash`` and ``report_id`` (``produced_at`` excluded
from identity).
"""
from __future__ import annotations

from mini_prometheus._contracts import ManufacturingRequest
from mini_prometheus._provenance import now_rfc3339
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.precedent import reasoner, retriever
from mini_prometheus.precedent.precedent_model import PRECEDENT_MODEL_VERSION, PrecedentModel

from contracts.python.manufacturing.precedent_report_schema import PrecedentReport


def run_precedent(
    request: ManufacturingRequest,
    *,
    store_path: str | None = None,
    model: PrecedentModel | None = None,
    top_k: int | None = None,
    relevance_threshold: int | None = None,
    produced_at: str | None = None,
) -> PrecedentReport:
    """Compose intake → retriever → reasoner into one deterministic, read-only PrecedentReport call.

    ``produced_at`` is resolved once and shared by intake and the reasoner (it is excluded from every
    identity view). The model version recorded on the report is the passed ``model``'s version, or the
    frozen default when ``model is None`` — matching what the retriever used to rank. ``top_k`` and
    ``relevance_threshold``, when given, are forwarded to the retriever / reasoner respectively;
    otherwise each component's own frozen default applies.
    """
    produced_at = produced_at or now_rfc3339()

    design_input = intake(request, produced_at=produced_at)
    ranked = retriever.retrieve(design_input, store_path=store_path, model=model, top_k=top_k)

    precedent_model_version = model.version if model is not None else PRECEDENT_MODEL_VERSION
    threshold = {} if relevance_threshold is None else {"relevance_threshold": relevance_threshold}
    return reasoner.reason(
        design_input,
        ranked,
        precedent_model_version=precedent_model_version,
        produced_at=produced_at,
        **threshold,
    )
