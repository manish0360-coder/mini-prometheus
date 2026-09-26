"""ProcessCapabilityModel — internal manufacturing CONTENT (not a contract; package §6).

The minimal machined-part capability model RM1 plans and checks against. Versioned
(``version`` flows into plan/verdict/episode ``capability_model_version``). Deliberately small
(no premature abstraction); richer models are later milestones.

ECR (Engineering Constraint Reasoning) C1 adds two **additive, defaulted-empty** declarative fields —
``capability_tolerance_mm`` (sparse tolerance-feasibility data) and ``ordering_constraints`` (pairwise
operation precedence). Both are empty on ``default_model()``, which therefore preserves RM1–RM4 behavior
and hashes byte-for-byte (``version`` stays ``1.0.0``; only the ``version`` STRING flows into identity,
not the dataclass shape). The populated, opt-in ``constrained_model()`` (``1.1.0``) is for future ECR /
RM5 re-evaluation corpora; the frozen RM5 fixture is never touched by this milestone.

Scientific boundary: ``capability_tolerance_mm`` is a **deliberately coarse MP domain approximation**
(one scalar min-achievable tolerance per tolerance-bearing capability), NOT a universal manufacturing
law. Feature-level tolerance attribution, GD&T, geometry, fixturing, and empirical process capability
are out of scope.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from mini_prometheus._contracts import ProcessOp

MODEL_VERSION = "1.0.0"
# The opt-in ECR-enriched model version (declarative precedence + tolerance populated).
MODEL_VERSION_CONSTRAINED = "1.1.0"


@dataclass(frozen=True)
class ProcessCapabilityModel:
    version: str
    op_capability: dict[ProcessOp, str]          # op -> required capability id
    resources: dict[str, frozenset[str]]         # resource_id -> capabilities provided
    supported_materials: frozenset[str]          # matched case-insensitively
    # --- ECR C1: additive declarative constraint data (empty => no constraint; RM1–RM4-compatible) ---
    # Sparse: an entry exists ONLY for capabilities that ESTABLISH dimensional tolerance (shaping/
    # finishing). Absent capabilities (stock-cut, deburr, inspection) neither confer nor gate tolerance.
    capability_tolerance_mm: dict[str, float] = field(default_factory=dict)
    # Pairwise precedence relation: (before, after) means every `before`-step precedes every `after`-step
    # whenever both ops are present in a plan. Minimal & justified only; NOT a total order, NOT a DAG.
    ordering_constraints: frozenset[tuple[ProcessOp, ProcessOp]] = field(default_factory=frozenset)


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


def _seed_ordering_constraints() -> frozenset[tuple[ProcessOp, ProcessOp]]:
    """The two justified constraints ONLY: cut_stock precedes every other op; every other op precedes
    inspect. Nothing is asserted about deburr-vs-machining or inter-machining order (they stay free)."""
    others = [
        ProcessOp.face_mill, ProcessOp.drill, ProcessOp.pocket_mill, ProcessOp.turn, ProcessOp.deburr,
    ]
    pairs: set[tuple[ProcessOp, ProcessOp]] = set()
    for o in [*others, ProcessOp.inspect]:
        pairs.add((ProcessOp.cut_stock, o))          # cut_stock first
    for o in [ProcessOp.cut_stock, *others]:
        pairs.add((o, ProcessOp.inspect))            # inspect last
    return frozenset(pairs)


def constrained_model() -> ProcessCapabilityModel:
    """The opt-in ECR-enriched model (v1.1.0): full default capabilities PLUS declarative precedence and
    a sparse tolerance map. For future ECR / RM5-re-evaluation corpora only — NOT used by RM1–RM4.

    The tolerance values are explicit, deliberately coarse MP demo-domain data (a single min-achievable
    tolerance per tolerance-bearing shaping capability), NOT universal manufacturing truth. Only the
    material-removal capabilities that establish dimensional tolerance appear; stock-cut (``cap.saw``),
    deburr (``cap.bench``), and inspection (``cap.cmm``) are intentionally absent (they do not produce
    dimensional tolerance under this coarse model).
    """
    base = default_model()
    return ProcessCapabilityModel(
        version=MODEL_VERSION_CONSTRAINED,
        op_capability=base.op_capability,
        resources=base.resources,
        supported_materials=base.supported_materials,
        capability_tolerance_mm={
            "cap.lathe": 0.01,   # turning — finest in this demo model
            "cap.mill": 0.02,
            "cap.drill": 0.05,   # drilling — coarsest shaping op
        },
        ordering_constraints=_seed_ordering_constraints(),
    )


def min_tolerance_for_capability(model: ProcessCapabilityModel, capability: str) -> float | None:
    """The tightest tolerance (mm) a capability can hold, or ``None`` if it is not tolerance-bearing.

    ``None`` means the capability does not establish dimensional tolerance in this model (sparse map):
    it neither confers nor gates tolerance feasibility. Consumed by the ECR oracle tolerance check (C3).
    """
    return model.capability_tolerance_mm.get(capability)


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
