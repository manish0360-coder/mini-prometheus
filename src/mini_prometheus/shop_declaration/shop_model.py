"""MP-S1 (ADR-0022): load a declared ``ShopCapabilityModel`` into the EXISTING ``ProcessCapabilityModel``.

Pure: a function of an already-parsed JSON document (file reading lives in ``orchestration/``). There
is no second model type (Law 13) and no default: a document that fails any check raises
``InvalidShopModelError`` with the complete, sorted list of issues. Callers must never fall back to
``default_model()``.

Two identities (spec §3.2), both via the existing ``_hashing.content_hash``:
- ``shop_content_hash``: the semantic capability basis (schema_version, resources, op_capability,
  unsupported_ops, unsupported_capabilities, supported_materials, capability_tolerance_mm,
  ordering_constraints), canonicalised;
- ``shop_declaration_hash``: that hash plus ``evidence_class`` and ``declaration``. It is the
  identity RM2 reuse keys on and that every binding check (G1-G5) compares.
``model_version`` (the contracted ``capability_model_version`` label, already part of the frozen RM1
plan identity), ``display_name`` and ``notes`` are in neither hash.

``evidence_class`` is copied verbatim; nothing derives or upgrades it. It records who asserted the
declaration, never that anyone verified it. Material compatibility is shop-wide (spec §4.1).
"""
from __future__ import annotations

import datetime
import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import jsonschema

from contracts.python.manufacturing.production_plan_schema import CapabilityModelRef
from contracts.python.manufacturing.shop_capability_model_schema import EvidenceClass
from mini_prometheus import _hashing as h
from mini_prometheus import _validate
from mini_prometheus._contracts import ProcessOp, ProductionPlan
from mini_prometheus.manufacturing_constraints.capability_model import (
    ProcessCapabilityModel,
    ShopModelSource,
)

SHOP_SCHEMA_ID = (
    "https://contracts.mini-prometheus.dev/v1/manufacturing/shop_capability_model.schema.json"
)
SUPPORTED_SCHEMA_VERSION = "1.0.0"
PLAN_SCHEMA_VERSION_WITH_REF = "1.1.0"
NOT_VERIFIED = "not independently verified"

SEMANTIC_FIELDS = (
    "schema_version",
    "resources",
    "op_capability",
    "unsupported_ops",
    "unsupported_capabilities",
    "supported_materials",
    "capability_tolerance_mm",
    "ordering_constraints",
)


class ShopModelIssueCode(StrEnum):
    """Why a shop declaration was refused (closed, internal; not a cross-layer contract)."""

    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    UNSUPPORTED_SCHEMA_VERSION = "UNSUPPORTED_SCHEMA_VERSION"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    DUPLICATE_MATERIAL = "DUPLICATE_MATERIAL"
    OP_UNDECLARED = "OP_UNDECLARED"
    OP_CONTRADICTORY = "OP_CONTRADICTORY"
    CAPABILITY_UNPROVIDED_UNDECLARED = "CAPABILITY_UNPROVIDED_UNDECLARED"
    CAPABILITY_CONTRADICTORY = "CAPABILITY_CONTRADICTORY"
    CAPABILITY_UNREFERENCED = "CAPABILITY_UNREFERENCED"
    TOLERANCE_INVALID = "TOLERANCE_INVALID"
    TOLERANCE_UNKNOWN_CAPABILITY = "TOLERANCE_UNKNOWN_CAPABILITY"
    PRECEDENCE_SELF_PAIR = "PRECEDENCE_SELF_PAIR"
    PRECEDENCE_DUPLICATE = "PRECEDENCE_DUPLICATE"
    PRECEDENCE_CYCLE = "PRECEDENCE_CYCLE"
    DECLARATION_SOURCES_MISSING = "DECLARATION_SOURCES_MISSING"


@dataclass(frozen=True, order=True)
class ShopModelIssue:
    path: str
    code: ShopModelIssueCode
    detail: str


class InvalidShopModelError(ValueError):
    """A shop declaration was refused before planning. ``issues`` is complete and sorted."""

    def __init__(self, issues: list[ShopModelIssue]) -> None:
        self.issues: tuple[ShopModelIssue, ...] = tuple(sorted(issues))
        super().__init__(
            "invalid shop capability model: "
            + "; ".join(f"{i.code} at {i.path}: {i.detail}" for i in self.issues)
        )

    @property
    def codes(self) -> tuple[ShopModelIssueCode, ...]:
        return tuple(i.code for i in self.issues)


class ShopIdentityMismatchError(ValueError):
    """A plan's shop identity does not match the model it is being verified or used under."""


# --- loading ------------------------------------------------------------------------------------

def _schema_issues(document: object) -> list[ShopModelIssue]:
    registry = _validate._registry()  # documented private reuse of the frozen registry (D3)
    schema = registry.get_or_retrieve(SHOP_SCHEMA_ID).value.contents
    validator = jsonschema.Draft202012Validator(schema, registry=registry)
    return [
        ShopModelIssue(
            "/" + "/".join(str(p) for p in error.absolute_path),
            ShopModelIssueCode.SCHEMA_VIOLATION,
            error.message,
        )
        for error in validator.iter_errors(document)
    ]


def _has_cycle(pairs: set[tuple[str, str]]) -> bool:
    graph: dict[str, set[str]] = {}
    for before, after in pairs:
        graph.setdefault(before, set()).add(after)
    state: dict[str, int] = {}  # 1 = on the current path, 2 = done

    def visit(node: str) -> bool:
        state[node] = 1
        for nxt in sorted(graph.get(node, ())):
            if state.get(nxt) == 1 or (nxt not in state and visit(nxt)):
                return True
        state[node] = 2
        return False

    return any(node not in state and visit(node) for node in sorted(graph))


def _semantic_issues(doc: dict[str, Any]) -> list[ShopModelIssue]:
    code = ShopModelIssueCode
    issues: list[ShopModelIssue] = []

    def add(path: str, c: ShopModelIssueCode, detail: str) -> None:
        issues.append(ShopModelIssue(path, c, detail))

    if doc["schema_version"] != SUPPORTED_SCHEMA_VERSION:
        add("/schema_version", code.UNSUPPORTED_SCHEMA_VERSION,
            f"{doc['schema_version']!r}; supported: {SUPPORTED_SCHEMA_VERSION}")
    declared_on = doc["declaration"]["declared_on"]
    try:
        datetime.date.fromisoformat(declared_on)
    except ValueError:
        add("/declaration/declared_on", code.SCHEMA_VIOLATION, f"{declared_on!r} is not a calendar date")
    if doc["evidence_class"] == EvidenceClass.public_specification.value and not doc[
        "declaration"
    ].get("sources"):
        add("/declaration/sources", code.DECLARATION_SOURCES_MISSING,
            "public_specification requires at least one cited source")

    seen: dict[str, int] = {}
    provided: set[str] = set()
    for i, resource in enumerate(doc["resources"]):
        rid = resource["resource_id"]
        if rid in seen:
            add(f"/resources/{i}/resource_id", code.DUPLICATE_RESOURCE,
                f"{rid!r} already declared at /resources/{seen[rid]}")
        else:
            seen[rid] = i
        provided.update(resource["capabilities"])

    materials: dict[str, int] = {}
    for i, material in enumerate(doc["supported_materials"]):
        key = material.lower()
        if key in materials:
            add(f"/supported_materials/{i}", code.DUPLICATE_MATERIAL,
                f"{material!r} duplicates /supported_materials/{materials[key]} (case-insensitive)")
        else:
            materials[key] = i

    op_capability: dict[str, str] = doc["op_capability"]
    unsupported_ops = set(doc.get("unsupported_ops", []))
    for op in ProcessOp:
        mapped, declared = op.value in op_capability, op.value in unsupported_ops
        if mapped and declared:
            add(f"/op_capability/{op.value}", code.OP_CONTRADICTORY,
                f"{op.value} is both mapped and in unsupported_ops")
        elif not mapped and not declared:
            add(f"/op_capability/{op.value}", code.OP_UNDECLARED,
                f"{op.value} is neither mapped nor in unsupported_ops")

    mapped_caps = set(op_capability.values())
    unsupported_caps = set(doc.get("unsupported_capabilities", []))
    for cap in sorted(mapped_caps):
        if cap in provided and cap in unsupported_caps:
            add("/unsupported_capabilities", code.CAPABILITY_CONTRADICTORY,
                f"{cap} is provided by a resource and declared unsupported")
        elif cap not in provided and cap not in unsupported_caps:
            add("/op_capability", code.CAPABILITY_UNPROVIDED_UNDECLARED,
                f"{cap} has no providing resource and is not in unsupported_capabilities")
    for i, resource in enumerate(doc["resources"]):
        for cap in sorted(set(resource["capabilities"]) - mapped_caps):
            add(f"/resources/{i}/capabilities", code.CAPABILITY_UNREFERENCED,
                f"{cap} on {resource['resource_id']} is not mapped from any op")
    for cap in sorted(unsupported_caps - mapped_caps):
        add("/unsupported_capabilities", code.CAPABILITY_UNREFERENCED,
            f"{cap} is declared unsupported but not mapped from any op")

    for cap, value in sorted(doc.get("capability_tolerance_mm", {}).items()):
        if cap not in mapped_caps:
            add(f"/capability_tolerance_mm/{cap}", code.TOLERANCE_UNKNOWN_CAPABILITY,
                f"{cap} is not mapped from any op")
        if not math.isfinite(value) or value <= 0:
            add(f"/capability_tolerance_mm/{cap}", code.TOLERANCE_INVALID,
                f"{value!r} must be a finite number > 0")

    pairs: set[tuple[str, str]] = set()
    for i, (before, after) in enumerate(doc.get("ordering_constraints", [])):
        if before == after:
            add(f"/ordering_constraints/{i}", code.PRECEDENCE_SELF_PAIR, f"{before} before itself")
        elif (before, after) in pairs:
            add(f"/ordering_constraints/{i}", code.PRECEDENCE_DUPLICATE, f"{before} before {after}")
        else:
            pairs.add((before, after))
    if _has_cycle(pairs):
        add("/ordering_constraints", code.PRECEDENCE_CYCLE,
            "the declared precedence pairs contain a cycle")
    return issues


def _normalised(doc: dict[str, Any]) -> dict[str, Any]:
    """Canonical form: every order-insensitive list sorted, capability lists de-duplicated,
    tolerances as floats (so 0.02, 0.020 and 2e-2 are one value)."""
    declaration = doc["declaration"]
    return {
        "schema_version": doc["schema_version"],
        "model_version": doc["model_version"],
        "evidence_class": doc["evidence_class"],
        "declaration": {
            "declared_by": declaration["declared_by"],
            "declared_on": declaration["declared_on"],
            "sources": sorted(declaration.get("sources", [])),
        },
        "resources": [
            {"resource_id": r["resource_id"], "capabilities": sorted(set(r["capabilities"]))}
            for r in sorted(doc["resources"], key=lambda r: r["resource_id"])
        ],
        "op_capability": dict(sorted(doc["op_capability"].items())),
        "unsupported_ops": sorted(doc.get("unsupported_ops", [])),
        "unsupported_capabilities": sorted(doc.get("unsupported_capabilities", [])),
        "supported_materials": sorted(doc["supported_materials"]),
        "capability_tolerance_mm": {
            k: float(v) for k, v in sorted(doc.get("capability_tolerance_mm", {}).items())
        },
        "ordering_constraints": sorted([a, b] for a, b in doc.get("ordering_constraints", [])),
    }


def shop_identities(document: dict[str, Any]) -> tuple[str, str]:
    """``(shop_content_hash, shop_declaration_hash)`` of a VALID document (call after loading)."""
    n = _normalised(document)
    content = h.content_hash({k: n[k] for k in SEMANTIC_FIELDS})
    declaration = h.content_hash(
        {"shop_content_hash": content, "evidence_class": n["evidence_class"],
         "declaration": n["declaration"]}
    )
    return content, declaration


def load_shop_model(document: object) -> ProcessCapabilityModel:
    """Validate, check, canonicalise and load a parsed ``ShopCapabilityModel`` document."""
    issues = _schema_issues(document)
    if issues:  # the semantic rules assume a schema-valid shape
        raise InvalidShopModelError(issues)
    assert isinstance(document, dict)
    issues = _semantic_issues(document)
    if issues:
        raise InvalidShopModelError(issues)
    n = _normalised(document)
    content, declaration = shop_identities(document)
    return ProcessCapabilityModel(
        version=n["model_version"],
        op_capability={ProcessOp(op): cap for op, cap in n["op_capability"].items()},
        resources={r["resource_id"]: frozenset(r["capabilities"]) for r in n["resources"]},
        supported_materials=frozenset(n["supported_materials"]),
        capability_tolerance_mm=dict(n["capability_tolerance_mm"]),
        ordering_constraints=frozenset(
            (ProcessOp(a), ProcessOp(b)) for a, b in n["ordering_constraints"]
        ),
        source=ShopModelSource(
            shop_content_hash=content,
            shop_declaration_hash=declaration,
            evidence_class=n["evidence_class"],
            declared_by=n["declaration"]["declared_by"],
            declared_on=n["declaration"]["declared_on"],
            display_name=document.get("display_name"),
        ),
    )


# --- binding (G1/G2/G5 share this one definition) -----------------------------------------------

def capability_model_ref_for(model: ProcessCapabilityModel) -> CapabilityModelRef | None:
    """The plan-level shop reference of a model: None for the built-in code models."""
    if model.source is None:
        return None
    return CapabilityModelRef(
        shop_content_hash=model.source.shop_content_hash,
        shop_declaration_hash=model.source.shop_declaration_hash,
        evidence_class=EvidenceClass(model.source.evidence_class),
    )


def shop_declaration_hash_of(model: ProcessCapabilityModel) -> str | None:
    return model.source.shop_declaration_hash if model.source is not None else None


def require_plan_shop_identity(plan: ProductionPlan, model: ProcessCapabilityModel) -> None:
    """G2: the plan must carry exactly the model's shop identity (or none, for a code model), and
    its schema_version must agree with the ref's presence. Raises ``ShopIdentityMismatchError``."""
    expected = capability_model_ref_for(model)
    if plan.capability_model_ref != expected:
        raise ShopIdentityMismatchError(
            f"plan {plan.content_hash} carries shop identity {plan.capability_model_ref!r}; "
            f"the capability model in force has {expected!r}"
        )
    if (plan.capability_model_ref is not None) != (
        plan.schema_version == PLAN_SCHEMA_VERSION_WITH_REF
    ):
        raise ShopIdentityMismatchError(
            f"plan schema_version {plan.schema_version} is inconsistent with its shop reference"
        )


def shop_identity_line(model: ProcessCapabilityModel) -> str:
    """The one presentation of a declared shop (spec §3.4). Never says verified or validated."""
    s = model.source
    if s is None:
        return "shop model: built-in code model (label-only identity)"
    name = f' "{s.display_name}"' if s.display_name else ""
    return (
        f"shop model{name} {s.shop_declaration_hash} ({s.evidence_class}, declared by "
        f"{s.declared_by} on {s.declared_on}; {NOT_VERIFIED})"
    )
