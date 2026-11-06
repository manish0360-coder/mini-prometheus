"""MP-S1 (ADR-0022) evolved contract gate: the 0.4.0 contracts are intact, file by file.

Replaces the earlier "contracts/VERSION == 0.4.0" pins and the RM8 golden's whole-tree
``contracts_digest`` equality. Those encoded "this milestone added no contract and the contracts it
relied on are intact". This check proves that fact more precisely, against the frozen manifest generated
once from ``rm14-complete``:
- every 0.4.0 contracts file is byte-identical (LF-normalised), except the three named below;
- ``production_plan.schema.json`` equals its 0.4.0 form plus exactly the one optional
  ``capability_model_ref`` property and its ``CapabilityModelRef`` definition (structural check);
- its generated binding is guarded by the CI contract drift check (regenerated, never hand-edited);
- ``contracts/VERSION`` is a SemVer no older than 0.4.0;
- the only files added to the tree are the MP-S1 shop schema and its generated binding.
"""

from __future__ import annotations

import copy
import json
import pathlib

from contracts_manifest_probe import PLAN_SCHEMA, canonical_sha256, lf_sha256

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "contracts_0_4_0_manifest.json"
PLAN_BINDING = "contracts/python/manufacturing/production_plan_schema.py"
VERSION_FILE = "contracts/VERSION"
MP_S1_ADDED = {
    "contracts/schemas/manufacturing/shop_capability_model.schema.json",
    "contracts/python/manufacturing/shop_capability_model_schema.py",
}


def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _semver(text: str) -> tuple[int, int, int]:
    major, minor, patch = (int(part) for part in text.strip().split("."))
    return major, minor, patch


def assert_0_4_0_contracts_intact() -> None:
    frozen = manifest()
    files: dict[str, str] = frozen["files"]
    current = {
        p.relative_to(ROOT).as_posix(): p
        for p in (ROOT / "contracts").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    missing = sorted(set(files) - set(current))
    assert not missing, f"0.4.0 contracts files removed: {missing}"
    for rel, digest in files.items():
        if rel in (PLAN_SCHEMA, PLAN_BINDING, VERSION_FILE):
            continue
        assert (
            lf_sha256(current[rel].read_bytes()) == digest
        ), f"0.4.0 contracts file changed: {rel}"
    added = sorted(set(current) - set(files))
    assert set(added) <= MP_S1_ADDED, f"unexpected contracts files added: {added}"

    plan_schema = json.loads(current[PLAN_SCHEMA].read_text(encoding="utf-8"))
    reduced = copy.deepcopy(plan_schema)
    reduced["properties"].pop("capability_model_ref", None)
    reduced["$defs"].pop("CapabilityModelRef", None)
    assert (
        canonical_sha256(reduced) == frozen["production_plan_schema_canonical_sha256"]
    ), "production_plan.schema.json changed beyond the one additive MP-S1 property"
    assert "capability_model_ref" not in plan_schema["required"], "the MP-S1 ref must stay optional"

    version = current[VERSION_FILE].read_text(encoding="utf-8")
    assert _semver(version) >= _semver(frozen["suite_version"]), f"contracts/VERSION {version!r}"
