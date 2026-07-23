"""Internal facade over the generated contract bindings.

Single import surface for RM1 implementation. The bindings themselves are generated
(``contracts/python/**``, source of truth = ``contracts/schemas``); this module only
re-exports them under clean names — no logic, no redefinition (Law 6/14; repo-arch §13).

Requires the repository root on ``sys.path`` so ``contracts.python`` resolves as a package
(see ``tests/conftest.py`` / ``pyproject`` pythonpath).
"""
from __future__ import annotations

from contracts.python.common_schema import ProducedBy, Provenance, Ref
from contracts.python.consumed.noetica.verdict_schema import Verdict
from contracts.python.consumed.velith.engineering_result_schema import (
    DesignArtifact,
    EngineeringResult,
)
from contracts.python.manufacturing.design_input_schema import (
    DesignArtifactRef,
    DesignInput,
    DesignSource,
    DesignSourceKind,
    EngineeringVerificationStatus,
)
from contracts.python.manufacturing.manufacturability_schema import (
    ManufacturabilityReasonCode,
    ManufacturabilityVerdictStatus,
)
from contracts.python.manufacturing.manufacturing_episode_schema import (
    ManufacturingEpisode,
    Timing,
)
from contracts.python.manufacturing.manufacturing_request_schema import (
    DeclaredOperation,
    ManufacturingRequest,
    ProcessOp,
    StockForm,
    StepArtifactRef,
    Tolerances,
)
from contracts.python.manufacturing.manufacturing_task_schema import (
    ManufacturingTask,
    ProductIntent,
)
from contracts.python.manufacturing.production_plan_schema import (
    ProcessStep,
    ProductionPlan,
    ResourceAssignment,
)

__all__ = [
    "ProducedBy", "Provenance", "Ref",
    "Verdict",
    "EngineeringResult", "DesignArtifact",
    "DesignInput", "DesignSource", "DesignSourceKind", "DesignArtifactRef",
    "EngineeringVerificationStatus",
    "ManufacturabilityReasonCode", "ManufacturabilityVerdictStatus",
    "ManufacturingEpisode", "Timing",
    "ManufacturingRequest", "DeclaredOperation", "ProcessOp", "StockForm",
    "StepArtifactRef", "Tolerances",
    "ManufacturingTask", "ProductIntent",
    "ProductionPlan", "ProcessStep", "ResourceAssignment",
]
