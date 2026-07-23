"""Canonical serialization, content-hash identity, deterministic ids, provenance.

Implements the frozen contract-package rules (contracts/RM1-contract-package.md §1.1–§1.4):
canonical JSON, ``content_hash = sha256(canonical_json(identity_view))``, deterministic ids
via ``uuid5(NS_MP, content_hash)``, and identity views that exclude volatile fields.

These are internal MP *mechanisms* (not contracts). NS_MP is the frozen namespace UUID.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import uuid
from enum import Enum
from typing import Any

# Frozen permanent namespace (contract package, CAP-0001 / ADR-0004).
NS_MP = uuid.UUID("4f5b56ae-3c77-4135-9f5c-1eef0ab1b252")


def to_contract_dict(obj: Any) -> Any:
    """Recursively convert a binding dataclass to its contract JSON dict.

    Enums -> their string value; ``None`` optionals dropped; nested dataclasses/lists recursed.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, Any] = {}
        for f in dataclasses.fields(obj):
            v = getattr(obj, f.name)
            if v is None:
                continue
            out[f.name] = to_contract_dict(v)
        return out
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [to_contract_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_contract_dict(v) for k, v in obj.items() if v is not None}
    return obj


def canonical_json(value: Any) -> str:
    """RM1 canonical JSON (contract package §1.1): sorted keys, compact, UTF-8."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(identity_view: Any) -> str:
    digest = hashlib.sha256(canonical_json(identity_view).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def derive_uuid(hash_str: str) -> str:
    """Deterministic id = uuid5(NS_MP, content_hash) (contract package §1.2)."""
    return str(uuid.uuid5(NS_MP, hash_str))


def _strip(d: dict[str, Any], exclude: set[str]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if k not in exclude}


# --- Identity views (contract package §3.x; volatile fields excluded) -------------------

def request_identity(request: Any) -> dict[str, Any]:
    return _strip(to_contract_dict(request), {"request_id", "metadata"})


def design_input_identity(design_input: Any) -> dict[str, Any]:
    d = _strip(to_contract_dict(design_input), {"design_input_id", "provenance"})
    if "design_artifact_ref" in d:  # opaque: only its content_hash is identity
        d["design_artifact_ref"] = {"content_hash": d["design_artifact_ref"]["content_hash"]}
    return d


def task_identity(task: Any) -> dict[str, Any]:
    return _strip(to_contract_dict(task), {"task_id"})


def plan_identity(plan: Any) -> dict[str, Any]:
    return _strip(to_contract_dict(plan), {"plan_id", "content_hash", "provenance"})


def episode_identity(episode: Any) -> dict[str, Any]:
    # Curated identity per contract package §3.6: task identity + plan.content_hash +
    # verdict(status + sorted reason_codes) + refs/versions. Embedding the full plan/task would
    # leak their volatile provenance timestamps; the package deliberately uses plan.content_hash.
    return {
        "schema_version": episode.schema_version,
        "task": task_identity(episode.task),
        "design_ref": to_contract_dict(episode.design_ref),
        "engineering_verification_status": to_contract_dict(episode.engineering_verification_status),
        "plan_content_hash": episode.plan.content_hash,
        "verdict": {
            "status": episode.verdict.status,
            "reason_codes": sorted(episode.verdict.reason_codes),
        },
        "capability_model_version": episode.capability_model_version,
    }
