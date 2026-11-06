"""MP-S1 (ADR-0022): read a ShopCapabilityModel JSON file for the CLIs (file I/O lives in orchestration).

Strict JSON: duplicate object keys and the non-standard constants NaN / Infinity are refused, so one
file text has exactly one meaning. Every refusal is an ``InvalidShopModelError`` (an unreadable path
raises ``OSError``). There is no fallback to a built-in model.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mini_prometheus.manufacturing_constraints.capability_model import ProcessCapabilityModel
from mini_prometheus.shop_declaration.shop_model import (
    InvalidShopModelError,
    ShopModelIssue,
    ShopModelIssueCode,
    load_shop_model,
)


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-standard JSON constant {name}")


def parse_shop_model_text(text: str) -> ProcessCapabilityModel:
    try:
        document = json.loads(
            text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant
        )
    except ValueError as exc:  # json.JSONDecodeError is a ValueError
        raise InvalidShopModelError(
            [ShopModelIssue("/", ShopModelIssueCode.SCHEMA_VIOLATION, f"invalid JSON: {exc}")]
        ) from exc
    return load_shop_model(document)


def read_shop_model(path: str | Path) -> ProcessCapabilityModel:
    return parse_shop_model_text(Path(path).read_text(encoding="utf-8"))


def refusal_message(exc: InvalidShopModelError) -> str:
    """Every issue on its own line: code, JSON path, detail (CLI exit 2)."""
    lines = [f"error: shop capability model refused ({len(exc.issues)} issue(s)); nothing was run"]
    lines += [f"  {i.code} {i.path}: {i.detail}" for i in exc.issues]
    return "\n".join(lines) + "\n"
