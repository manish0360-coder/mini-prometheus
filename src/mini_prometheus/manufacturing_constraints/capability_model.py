"""ProcessCapabilityModel — internal manufacturing CONTENT (not a contract; package §6).

The minimal machined-part capability model RM1 plans and checks against. Versioned
(``version`` flows into plan/verdict/episode ``capability_model_version``). Deliberately small
(no premature abstraction); richer models are later milestones.
"""
from __future__ import annotations

from dataclasses import dataclass

from mini_prometheus._contracts import ProcessOp

MODEL_VERSION = "1.0.0"


@dataclass(frozen=True)
class ProcessCapabilityModel:
    version: str
    op_capability: dict[ProcessOp, str]          # op -> required capability id
    resources: dict[str, frozenset[str]]         # resource_id -> capabilities provided
    supported_materials: frozenset[str]          # matched case-insensitively


def default_model() -> ProcessCapabilityModel:
    return ProcessCapabilityModel(
        version=MODEL_VERSION,
        op_capability={
            ProcessOp.cut_stock: "cap.saw",
            ProcessOp.face_mill: "cap.mill",
            ProcessOp.drill: "cap.drill",
            ProcessOp.pocket_mill: "cap.mill",
            ProcessOp.turn: "cap.lathe",
            ProcessOp.deburr: "cap.bench",
            ProcessOp.inspect: "cap.cmm",
        },
        resources={
            "mill01": frozenset({"cap.mill", "cap.drill"}),
            "lathe01": frozenset({"cap.lathe"}),
            "saw01": frozenset({"cap.saw"}),
            "bench01": frozenset({"cap.bench"}),
            "cmm01": frozenset({"cap.cmm"}),
        },
        supported_materials=frozenset(
            {"aluminum", "aluminum 6061", "steel", "steel 1018", "brass", "brass 360"}
        ),
    )


def capability_for_op(model: ProcessCapabilityModel, op: ProcessOp) -> str:
    """Required capability id for an op; a non-empty sentinel if the op is unmodeled."""
    return model.op_capability.get(op, f"UNSUPPORTED_OP:{op.value}")


def resource_for_capability(model: ProcessCapabilityModel, capability: str) -> str | None:
    """First resource (deterministic order) providing the capability, else None."""
    for resource_id in sorted(model.resources):
        if capability in model.resources[resource_id]:
            return resource_id
    return None


def material_supported(model: ProcessCapabilityModel, material: str) -> bool:
    return material.strip().lower() in {m.lower() for m in model.supported_materials}
