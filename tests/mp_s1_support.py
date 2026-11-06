"""Shared MP-S1 test helpers (importable as ``mp_s1_support``). All shop fixtures are SYNTHETIC."""

from __future__ import annotations

import copy
import json
import pathlib

import support

SHOP = pathlib.Path(__file__).parent / "fixtures" / "shop_models"
VARIANTS = SHOP / "variants"
INVALID = SHOP / "invalid"


def doc(name: str) -> dict:
    """A shop fixture document, e.g. ``doc("default_1.0.0")`` or ``doc("variants/material_removed")``."""
    return json.loads((SHOP / f"{name}.json").read_text(encoding="utf-8"))


def model(name: str):
    from mini_prometheus.shop_declaration.shop_model import load_shop_model

    return load_shop_model(doc(name))


def edited(name: str, **changes) -> dict:
    d = copy.deepcopy(doc(name))
    d.update(changes)
    return d


def bracket():
    """The RM1 engineer request (Aluminum 6061; cut_stock, face_mill, drill x2, deburr, inspect; 0.1 mm)."""
    return support.build_request(support.load_json("engineer_request_machined_bracket.json"))


def bracket_json() -> dict:
    return support.load_json("engineer_request_machined_bracket.json")
