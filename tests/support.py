"""Shared test helpers (importable as ``support`` — ``tests`` is on the pytest pythonpath)."""
from __future__ import annotations

import json
import pathlib

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
FIXED_TIME = "2026-07-23T00:00:00+00:00"


def load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def build_request(raw: dict):
    from mini_prometheus._contracts import (
        DeclaredOperation,
        ManufacturingRequest,
        ProcessOp,
        StepArtifactRef,
        StockForm,
        Tolerances,
    )

    return ManufacturingRequest(
        schema_version=raw["schema_version"],
        request_id=raw["request_id"],
        material=raw["material"],
        material_code=raw.get("material_code"),
        stock_form=StockForm(raw["stock_form"]),
        declared_operations=[
            DeclaredOperation(op=ProcessOp(o["op"]), target=o.get("target"), params=o.get("params"))
            for o in raw["declared_operations"]
        ],
        quantity=raw["quantity"],
        tolerances=Tolerances(**raw["tolerances"]) if raw.get("tolerances") else None,
        step_artifact_ref=StepArtifactRef(**raw["step_artifact_ref"])
        if raw.get("step_artifact_ref")
        else None,
    )
