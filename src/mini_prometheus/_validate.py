"""Runtime schema validation against the frozen JSON Schema contracts.

Verification-first (Principle 1): contract instances are validated at MP boundaries — a
ManufacturingRequest on intake, a ManufacturingEpisode before it is emitted. The schemas in
``contracts/schemas`` are the source of truth; a cross-file ``$ref`` registry resolves them.
"""
from __future__ import annotations

import functools
import json
import pathlib
from typing import Any

import jsonschema
from referencing import Registry, Resource

_REPO = pathlib.Path(__file__).resolve().parents[2]
_SCHEMAS = _REPO / "contracts" / "schemas"
_BASE = "https://contracts.mini-prometheus.dev/v1/"

SCHEMA_ID = {
    "manufacturing_request": _BASE + "manufacturing/manufacturing_request.schema.json",
    "design_input": _BASE + "manufacturing/design_input.schema.json",
    "manufacturing_task": _BASE + "manufacturing/manufacturing_task.schema.json",
    "production_plan": _BASE + "manufacturing/production_plan.schema.json",
    "manufacturing_episode": _BASE + "manufacturing/manufacturing_episode.schema.json",
}


class ContractValidationError(ValueError):
    """Raised when an instance violates its frozen schema."""


@functools.lru_cache(maxsize=1)
def _registry() -> Registry:
    resources = []
    for path in _SCHEMAS.rglob("*.schema.json"):
        doc = json.loads(path.read_text(encoding="utf-8"))
        resources.append((doc["$id"], Resource.from_contents(doc)))
    return Registry().with_resources(resources)


def validate(name: str, instance: dict[str, Any]) -> None:
    """Validate ``instance`` against the named frozen schema; raise on failure."""
    reg = _registry()
    schema = reg.get_or_retrieve(SCHEMA_ID[name]).value.contents
    validator = jsonschema.Draft202012Validator(schema, registry=reg)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        first = errors[0]
        raise ContractValidationError(
            f"{name} violates contract at {list(first.path)}: {first.message}"
        )
