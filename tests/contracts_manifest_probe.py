"""MP-S1 contracts manifest probe (ADR-0022) — a file-by-file fingerprint of a ``contracts/`` tree.

READ-ONLY. This module only COMPUTES a manifest. The frozen manifest
(``tests/fixtures/contracts_0_4_0_manifest.json``) was generated ONCE by running this exact file on an
export of the ``rm14-complete`` tree (``git archive rm14-complete``), whose ``contracts/`` tree is the
0.4.0 suite unchanged since ``rm4-complete``. It is frozen by digest in
``tests/boundary/test_mp_s1_gates.py`` and never regenerated from the current tree.

Per file: sha256 of the LF-normalised bytes. For ``production_plan.schema.json`` also the canonical
JSON hash (sorted keys, compact), so an additive property can be checked structurally.

Usage (generation only): ``python -I tests/contracts_manifest_probe.py <tree-root>``
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

PLAN_SCHEMA = "contracts/schemas/manufacturing/production_plan.schema.json"


def lf_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def canonical_sha256(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest(root: pathlib.Path) -> dict[str, object]:
    files = sorted(
        p for p in (root / "contracts").rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    plan_schema = json.loads((root / PLAN_SCHEMA).read_text(encoding="utf-8"))
    return {
        "files": {p.relative_to(root).as_posix(): lf_sha256(p.read_bytes()) for p in files},
        "production_plan_schema_canonical_sha256": canonical_sha256(plan_schema),
    }


if __name__ == "__main__":  # pragma: no cover - one-time generation
    print(json.dumps(manifest(pathlib.Path(sys.argv[1])), indent=2, sort_keys=True))
