"""MP-S1 loader, issue codes and the two identities (spec §3.1-§3.2.2; AC3, AC5, AC6; T3.x, T5.1, T6.2).

All fixtures are synthetic (``tests/fixtures/shop_models``).
"""

from __future__ import annotations

import ast
import copy
import itertools
import json
import pathlib
import random

import pytest

import mp_s1_support as s
from mini_prometheus._contracts import ProcessOp
from mini_prometheus.experience.episode_index import design_input_key
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import (
    constrained_model,
    default_model,
    with_unavailable_resources,
)
from mini_prometheus.orchestration.shop_model_file import parse_shop_model_text
from mini_prometheus.shop_declaration.shop_model import (
    InvalidShopModelError,
    ShopModelIssueCode,
    load_shop_model,
    shop_identities,
)

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "mini_prometheus"
FUNCTIONAL = (
    "version",
    "op_capability",
    "resources",
    "supported_materials",
    "capability_tolerance_mm",
    "ordering_constraints",
    "unavailable_resources",
)


def _functional(m):
    return {f: getattr(m, f) for f in FUNCTIONAL}


# --- loading and equivalence of the mirror fixtures ---------------------------------------------


def test_default_fixture_is_functionally_default_model():
    loaded = s.model("default_1.0.0")
    assert _functional(loaded) == _functional(default_model())
    assert loaded.source is not None and default_model().source is None


def test_constrained_fixture_is_functionally_constrained_model():
    assert _functional(s.model("constrained_1.1.0")) == _functional(constrained_model())


def test_r_star_fixture_is_functionally_the_rm5_regime_and_declares_its_gap():
    from mini_prometheus.experiment import corpus

    assert _functional(s.model("r_star_2.0.0")) == _functional(corpus.r_star())
    assert s.doc("r_star_2.0.0")["unsupported_capabilities"] == ["cap.lathe"]


def test_three_cell_fixture_loads_with_a_declared_unsupported_op():
    m = s.model("three_cell_synthetic")
    assert ProcessOp.turn not in m.op_capability and set(m.resources) >= {"mill01", "mill02"}


def test_availability_keeps_the_declaration():
    m = s.model("default_1.0.0")
    assert with_unavailable_resources(m, ["lathe01"]).source == m.source


# --- T5.1 typed fail-closed: one fixture per issue code -----------------------------------------


@pytest.mark.parametrize("code", list(ShopModelIssueCode))
def test_each_invalid_fixture_raises_exactly_its_issue_code(code):
    with pytest.raises(InvalidShopModelError) as err:
        load_shop_model(s.doc(f"invalid/{code.value}"))
    assert set(err.value.codes) == {code}, err.value.issues


def test_issue_lists_are_complete_sorted_and_deterministic():
    d = s.doc("default_1.0.0")
    d["supported_materials"].append("ALUMINUM")
    d["ordering_constraints"] = [["drill", "drill"], ["deburr", "inspect"], ["inspect", "deburr"]]
    d["resources"].append({"resource_id": "saw01", "capabilities": ["cap.saw"]})
    first = second = None
    with pytest.raises(InvalidShopModelError) as a:
        load_shop_model(d)
    with pytest.raises(InvalidShopModelError) as b:
        load_shop_model(copy.deepcopy(d))
    first, second = a.value.issues, b.value.issues
    assert first == second == tuple(sorted(first))
    assert {i.code for i in first} == {
        ShopModelIssueCode.DUPLICATE_MATERIAL,
        ShopModelIssueCode.PRECEDENCE_SELF_PAIR,
        ShopModelIssueCode.PRECEDENCE_CYCLE,
        ShopModelIssueCode.DUPLICATE_RESOURCE,
    }


@pytest.mark.parametrize(
    "text, fragment",
    [
        ('{"a": 1, "a": 2}', "duplicate key"),
        ('{"capability_tolerance_mm": {"cap.mill": NaN}}', "NaN"),
        ("not json", "invalid JSON"),
    ],
)
def test_strict_json_is_refused_before_loading(text, fragment):
    with pytest.raises(InvalidShopModelError) as err:
        parse_shop_model_text(text)
    assert err.value.codes == (ShopModelIssueCode.SCHEMA_VIOLATION,)
    assert fragment in err.value.issues[0].detail


def test_colon_in_a_resource_id_is_refused():
    d = s.doc("default_1.0.0")
    d["resources"][0]["resource_id"] = "bench:01"
    with pytest.raises(InvalidShopModelError) as err:
        load_shop_model(d)
    assert ShopModelIssueCode.SCHEMA_VIOLATION in err.value.codes


def test_an_impossible_calendar_date_is_refused():
    d = s.doc("default_1.0.0")
    d["declaration"]["declared_on"] = "2026-02-30"
    with pytest.raises(InvalidShopModelError) as err:
        load_shop_model(d)
    assert err.value.issues[0].path == "/declaration/declared_on"


# --- AC3 / T3.2: the §3.2.1 + §3.2.2 truth table, row by row, against the real loader ----------

BASE = s.doc("default_1.0.0")
C0, D0 = shop_identities(BASE)


def _reordered(value):
    if isinstance(value, dict):
        return {k: _reordered(value[k]) for k in reversed(list(value))}
    if isinstance(value, list):
        return [_reordered(v) for v in value]
    return value


def _with(mutator):
    d = copy.deepcopy(BASE)
    mutator(d)
    return d


def _list_order(d):
    d["resources"].reverse()
    d["resources"][1]["capabilities"].reverse()
    d["supported_materials"].reverse()


def _lathe_removed(d):
    d["resources"] = [r for r in d["resources"] if r["resource_id"] != "lathe01"]
    d["unsupported_capabilities"] = ["cap.lathe"]


TRUTH = [  # (row, document, content hash changes, declaration hash changes)
    ("1 key reordering", _reordered(BASE), False, False),
    ("2 whitespace only", json.loads(json.dumps(BASE, separators=(",", ":"))), False, False),
    ("3 list order", _with(_list_order), False, False),
    ("4 lathe removed, declared unsupported", _with(_lathe_removed), True, True),
    (
        "5 drill added to a second machine",
        _with(lambda d: d["resources"][4]["capabilities"].append("cap.drill")),
        True,
        True,
    ),
    ("6 material removed", s.doc("variants/material_removed"), True, True),
    (
        "7 tolerance added",
        _with(lambda d: d.update(capability_tolerance_mm={"cap.mill": 0.02})),
        True,
        True,
    ),
    ("8 precedence added", s.doc("variants/precedence_added"), True, True),
    ("9 evidence class", s.doc("variants/evidence_public_specification"), False, True),
    ("10 declarer", s.doc("variants/declarer_changed"), False, True),
    ("11 date", s.doc("variants/date_changed"), False, True),
    ("12 model_version label", s.doc("variants/model_version_changed"), False, False),
    ("12a display_name", s.doc("variants/display_name_changed"), False, False),
    ("13 notes", s.doc("variants/notes_changed"), False, False),
]


@pytest.mark.parametrize("row, document, content_changes, declaration_changes", TRUTH)
def test_truth_table_row(row, document, content_changes, declaration_changes):
    load_shop_model(document)  # every row is a valid declaration
    c, d = shop_identities(document)
    assert (c != C0, d != D0) == (content_changes, declaration_changes), row


def test_tolerance_spellings_are_one_value_and_a_new_value_is_not():
    t = {"cap.mill": 0.02}
    a = shop_identities(_with(lambda d: d.update(capability_tolerance_mm=t)))
    b = shop_identities(
        json.loads(
            json.dumps(_with(lambda d: d.update(capability_tolerance_mm=t))).replace(
                "0.02", "0.020"
            )
        )
    )
    c = shop_identities(_with(lambda d: d.update(capability_tolerance_mm={"cap.mill": 2e-2})))
    e = shop_identities(_with(lambda d: d.update(capability_tolerance_mm={"cap.mill": 0.01})))
    assert a == b == c and e[0] != a[0]


def test_model_version_misses_reuse_only_through_the_frozen_key_component():
    di = intake(s.bracket(), produced_at="2026-07-23T00:00:00+00:00")
    base, label = load_shop_model(BASE), load_shop_model(s.doc("variants/model_version_changed"))
    assert base.source.shop_declaration_hash == label.source.shop_declaration_hash
    k_base = design_input_key(
        di, base.version, shop_declaration_hash=base.source.shop_declaration_hash
    )
    k_label = design_input_key(
        di, label.version, shop_declaration_hash=label.source.shop_declaration_hash
    )
    assert k_base != k_label and k_base[2] == k_label[2] and k_base[1] != k_label[1]


# --- T3.1 / T3.3 properties ---------------------------------------------------------------------


def test_permutations_never_change_either_hash():
    rng = random.Random(20261106)
    for _ in range(50):
        d = copy.deepcopy(BASE)
        rng.shuffle(d["resources"])
        for r in d["resources"]:
            rng.shuffle(r["capabilities"])
        rng.shuffle(d["supported_materials"])
        items = list(d["op_capability"].items())
        rng.shuffle(items)
        d["op_capability"] = dict(items)
        keys = list(d)
        rng.shuffle(keys)
        assert shop_identities({k: d[k] for k in keys}) == (C0, D0)


def _single_field_edits():
    yield "materials", _with(lambda d: d["supported_materials"].pop())
    yield "resource", _with(lambda d: d["resources"][4]["capabilities"].append("cap.drill"))
    yield "ordering", _with(lambda d: d.update(ordering_constraints=[["cut_stock", "inspect"]]))
    yield "tolerance", _with(lambda d: d.update(capability_tolerance_mm={"cap.lathe": 0.5}))
    yield "evidence", s.doc("variants/evidence_public_specification")
    yield "declarer", s.doc("variants/declarer_changed")
    yield (
        "sources",
        _with(
            lambda d: (
                d.update(evidence_class="public_specification"),
                d["declaration"].update(sources=["x", "y"]),
            )
        ),
    )
    for n in range(1, 6):
        yield (
            f"date+{n}",
            _with(lambda d, n=n: d["declaration"].update(declared_on=f"2026-12-0{n}")),
        )


def test_content_change_implies_declaration_change_and_key_tracks_the_declaration_hash():
    di = intake(s.bracket(), produced_at="2026-07-23T00:00:00+00:00")
    k0 = design_input_key(di, BASE["model_version"], shop_declaration_hash=D0)
    for name, d in _single_field_edits():
        c, dh = shop_identities(d)
        assert not (c != C0 and dh == D0), name
        k = design_input_key(di, d["model_version"], shop_declaration_hash=dh)
        assert (k != k0) == (dh != D0), name


def test_no_two_valid_declarations_in_the_fixtures_share_a_declaration_hash_unless_display_only():
    names = ["default_1.0.0", "constrained_1.1.0", "r_star_2.0.0", "three_cell_synthetic"] + [
        f"variants/{p.stem}" for p in sorted(s.VARIANTS.glob("*.json"))
    ]
    by_hash: dict[str, list[str]] = {}
    for name in names:
        by_hash.setdefault(shop_identities(s.doc(name))[1], []).append(name)
    shared = [group for group in by_hash.values() if len(group) > 1]
    display_only = {
        "default_1.0.0",
        "variants/display_name_changed",
        "variants/notes_changed",
        "variants/model_version_changed",
    }
    assert all(set(group) <= display_only for group in shared), shared


# --- AC6 / T6.2: the loader is the only writer of the shop identity; nothing upgrades evidence --


def test_only_the_loader_constructs_a_shop_model_source():
    writers = []
    for path in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ShopModelSource":
                writers.append(path.relative_to(SRC).as_posix())
    assert writers == ["shop_declaration/shop_model.py"], writers


def test_no_fixture_claims_real_shop_evidence():
    for path in itertools.chain(
        s.SHOP.glob("*.json"), s.VARIANTS.glob("*.json"), s.INVALID.glob("*.json")
    ):
        assert (
            json.loads(path.read_text(encoding="utf-8"))["evidence_class"] != "shop_declared"
        ), path.name


def test_evidence_class_is_copied_verbatim():
    for cls in ("synthetic", "public_specification", "shop_declared"):
        d = _with(
            lambda d, cls=cls: (
                d.update(evidence_class=cls),
                d["declaration"].update(sources=["cited"]),
            )
        )
        assert load_shop_model(d).source.evidence_class == cls
