"""Noetica `Verifier` protocol — CONSUMED interface (Law 15).

Pinned by RM1 (see contracts/schemas/consumed/noetica/verifier.protocol.md) until the real Noetica
contract publishes. MP owns the concrete oracle that implements it; MP must not alter the signature.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from mini_prometheus._contracts import ProductionPlan, Verdict
from mini_prometheus.manufacturing_constraints.capability_model import ProcessCapabilityModel


@runtime_checkable
class Verifier(Protocol):
    def verify(self, plan: ProductionPlan, capability_model: ProcessCapabilityModel) -> Verdict:
        """Deterministic, pure (spec §9): same inputs -> same Verdict."""
        ...
