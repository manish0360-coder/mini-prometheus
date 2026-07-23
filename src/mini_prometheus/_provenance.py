"""Provenance construction helper (Law 18). Internal mechanism; not a contract."""
from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from mini_prometheus._contracts import ProducedBy, Provenance, Ref

DEFAULT_CAPABILITY_MODEL_VERSION = "1.0.0"


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_provenance(
    *,
    source_refs: Iterable[Ref],
    rule_id: str,
    rule_version: str,
    produced_at: str,
    component: str,
    component_version: str,
    capability_model_version: str = DEFAULT_CAPABILITY_MODEL_VERSION,
) -> Provenance:
    return Provenance(
        source_refs=list(source_refs),
        rule_id=rule_id,
        rule_version=rule_version,
        capability_model_version=capability_model_version,
        produced_by=ProducedBy(component=component, version=component_version),
        produced_at=produced_at,
    )
