"""ADR-0023 consistency gate for the shop-owner pilot demonstrator (``demo/pilot/``).

The page may only DISPLAY actual MP-S1 CLI output. This gate proves:
- every input and snapshot matches the SHA-256 recorded in MANIFEST.json;
- re-running the capture reproduces every snapshot byte for byte, so the screens cannot drift
  from MP-S1;
- every status and reason the page shows equals what the CLI printed and what it stored;
- the page itself contains no verdict logic and no verdict literals, and loads nothing from the
  network;
- every shop input is synthetic and every code shown has a plain-language label;
- no lead-time, cost or other unsupported prediction is presented.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PILOT = ROOT / "demo" / "pilot"
SNAPSHOTS = PILOT / "snapshots"
VERDICT_CODES = (
    "MANUFACTURABLE", "NOT_MANUFACTURABLE", "PLAN_INVALID", "INFRA_ERROR", "CAPABILITY_MISSING",
    "PRECEDENCE_VIOLATION", "RESOURCE_UNAVAILABLE", "TOLERANCE_UNSUPPORTED", "MATERIAL_UNSUPPORTED",
    "PLAN_MALFORMED",
)


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return json.loads((SNAPSHOTS / "MANIFEST.json").read_text(encoding="utf-8"))


def _data() -> dict:
    text = (SNAPSHOTS / "data.js").read_text(encoding="utf-8")
    prefix, suffix = "window.MP_PILOT_DATA = ", ";\n"
    assert text.startswith(prefix) and text.endswith(suffix)
    return json.loads(text[len(prefix):-len(suffix)])


def _strings(lang: str) -> dict[str, str]:
    text = (PILOT / "strings.js").read_text(encoding="utf-8")
    start = text.index(f"  {lang}: {{")
    end = text.index("  hi: {") if lang == "en" else text.rindex("};")
    pairs = re.findall(r'"([^"]+)":\s*"((?:[^"\\]|\\.)*)"', text[start:end])
    keys = [k for k, _ in pairs]
    assert len(keys) == len(set(keys)), f"duplicate keys in strings.js {lang}"
    return dict(pairs)


def _strings_en() -> dict[str, str]:
    return _strings("en")


def _capture_module():
    spec = importlib.util.spec_from_file_location("demo_pilot_capture", PILOT / "capture.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_manifest_hashes_match_every_file():
    m = _manifest()
    assert _sha(ROOT / m["shop"]["path"]) == m["shop"]["sha256"]
    assert _sha(PILOT / "capture.py") == m["generator_sha256"]
    assert _sha(SNAPSHOTS / "data.js") == m["data_js_sha256"]
    assert len(m["cases"]) == 4
    for case in m["cases"]:
        assert _sha(ROOT / case["job_path"]) == case["job_sha256"], case["id"]
        assert _sha(ROOT / case["stdout_path"]) == case["stdout_sha256"], case["id"]
        assert _sha(ROOT / case["plan_path"]) == case["plan_sha256"], case["id"]
        assert case["exit_code"] == 0
        assert case["command"] == (
            f"python -m mini_prometheus.orchestration.runner {case['job_path']} "
            f"--capability-model-file {m['shop']['path']}"
        )


def test_capture_reproduces_every_snapshot_byte_for_byte(tmp_path):
    committed = _manifest()
    fresh = _capture_module().capture(tmp_path, committed["mp_commit"])
    names = sorted(p.name for p in SNAPSHOTS.iterdir() if p.is_file())
    assert names == sorted(p.name for p in tmp_path.iterdir() if p.is_file())
    for name in names:
        if name == "MANIFEST.json":
            continue
        assert (tmp_path / name).read_bytes() == (SNAPSHOTS / name).read_bytes(), name
    strip = lambda m: {k: v for k, v in m.items() if k != "python"}  # noqa: E731
    assert strip(fresh) == strip(committed)


def test_displayed_verdicts_equal_the_captured_cli_output():
    data, manifest = _data(), _manifest()
    for shown, recorded in zip(data["cases"], manifest["cases"], strict=True):
        first = shown["stdout"].splitlines()[0]
        reasons = ", ".join(shown["reason_codes"])
        expected = f"{shown['status']} [{reasons}] plan {shown['plan_hash']}"
        assert first.startswith(expected), shown["id"]
        assert f" trace {shown['trace_hash']} -> " in first
        assert shown["shop_declaration_hash"] == data["shop"]["shop_declaration_hash"]
        stored = json.loads((ROOT / recorded["plan_path"]).read_text(encoding="utf-8"))
        verdict = {"status": shown["status"], "reason_codes": shown["reason_codes"]}
        assert stored["verdict"] == verdict
        assert stored["steps"] == shown["steps"]
        assert {k: shown[k] for k in recorded} == recorded


def test_the_four_example_outcomes_are_the_captured_ones():
    outcomes = {c["id"]: (c["status"], c["reason_codes"]) for c in _data()["cases"]}
    assert outcomes == {
        "bracket": ("MANUFACTURABLE", []),
        "turned_shaft": ("NOT_MANUFACTURABLE", ["CAPABILITY_MISSING"]),
        "brass_cover": ("NOT_MANUFACTURABLE", ["MATERIAL_UNSUPPORTED"]),
        "precision_plate": ("NOT_MANUFACTURABLE", ["TOLERANCE_UNSUPPORTED"]),
    }


def test_page_has_no_verdict_logic_and_no_network():
    page = (PILOT / "index.html").read_text(encoding="utf-8")
    for code in VERDICT_CODES:
        assert code not in page, f"index.html must not contain the verdict literal {code}"
    assert not re.search(r'(src|href)\s*=\s*"https?://', page), "the page must work offline"
    assert '<script src="snapshots/data.js"></script>' in page
    strings = (PILOT / "strings.js").read_text(encoding="utf-8")
    assert "function" not in strings and "=>" not in strings, "strings.js holds text only"


def test_every_code_and_term_shown_has_a_label():
    en, data = _strings_en(), _data()
    doc = data["shop"]["document"]
    for case in data["cases"]:
        assert f"status.{case['status']}" in en and f"tone.{case['status']}" in en
        for code in case["reason_codes"]:
            assert f"reason.{code}" in en
        assert f"case.{case['id']}" in en and f"stock.{case['request']['stock_form']}" in en
        for op in case["request"]["declared_operations"]:
            assert f"op.{op['op']}" in en
    for resource in doc["resources"]:
        for cap in resource["capabilities"]:
            assert f"cap.{cap}" in en
    for op in doc.get("unsupported_ops", []):
        assert f"op.{op}" in en
    for code in VERDICT_CODES[4:]:
        assert f"reason.{code}" in en
    # Every machine, material and operation target the screens name has a plain-language label.
    for resource in doc["resources"]:
        assert f"machine.{resource['resource_id']}" in en
    materials = list(doc["supported_materials"]) + [c["request"]["material"] for c in data["cases"]]
    for material in materials:
        assert f"material.{material.lower()}" in en
    for case in data["cases"]:
        for op in case["request"]["declared_operations"]:
            if op.get("target"):
                assert f"target.{op['target']}" in en


def test_hindi_and_english_hold_the_same_keys():
    en, hi = _strings("en"), _strings("hi")
    assert sorted(hi) == sorted(en)
    assert all(value.strip() for value in hi.values())
    for key in en:
        if key.startswith("tone."):
            assert hi[key] == en[key], "tone values are lamp colours, not text"
    page = (PILOT / "index.html").read_text(encoding="utf-8")
    assert '<script src="strings.js"></script>' in page


@pytest.mark.parametrize("path", sorted((PILOT / "inputs").glob("shop.*.json")))
def test_shop_inputs_are_synthetic_and_load(path):
    from mini_prometheus.orchestration.shop_model_file import read_shop_model

    assert json.loads(path.read_text(encoding="utf-8"))["evidence_class"] == "synthetic"
    assert read_shop_model(path).source.evidence_class == "synthetic"


def test_no_unsupported_prediction_is_presented():
    text = ((PILOT / "index.html").read_text(encoding="utf-8")
            + (PILOT / "strings.js").read_text(encoding="utf-8")).lower()
    assert "lead time" not in text and "lead_time" not in text
    en = _strings_en()
    for key, value in en.items():
        if re.search(r"\b(cost|price|delivery time|cycle time|geometry|velith)\b", value.lower()):
            assert key.startswith("limits."), (key, value)
