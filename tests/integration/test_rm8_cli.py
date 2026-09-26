"""RM8 C4 — the existing CLI with ``--capability-model {default,constrained}``.

default     : legacy RM1 behavior, unchanged. It performs NO tolerance or declared-precedence reasoning
              and does not read the request's ``tolerances`` (documented limitation, RM8 spec §8).
constrained : the RM8 ECR model (1.1.0); the request's tolerance reaches the planner and the oracle.
The default-mode outputs are additionally pinned byte-for-byte by the rm5-complete golden
(tests/unit/test_rm8_default_zero_diff.py, section ``cli_default``).
"""
from __future__ import annotations

import contextlib
import copy
import io
import json

import pytest

from mini_prometheus.orchestration import episode_store, runner

import support

BASE = support.load_json("engineer_request_machined_bracket.json")          # tolerance 0.1 mm
TIGHT_MISORDERED = copy.deepcopy(BASE)
TIGHT_MISORDERED["tolerances"] = {"general_tolerance_mm": 0.001}
TIGHT_MISORDERED["declared_operations"] = [BASE["declared_operations"][-1], *BASE["declared_operations"][:-1]]


def _cli(tmp_path, monkeypatch, raw, *flags):
    store = tmp_path / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(raw), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = runner._main([str(request_path), *flags])
    episode = json.loads(store.read_text(encoding="utf-8").splitlines()[-1])
    return code, out.getvalue(), episode


@pytest.mark.parametrize("flags", [(), ("--capability-model", "default")])
def test_default_mode_is_legacy_and_does_no_tolerance_reasoning(tmp_path, monkeypatch, flags):
    code, out, episode = _cli(tmp_path, monkeypatch, TIGHT_MISORDERED, *flags)
    # Inspect-first and 0.001 mm would both be rejected by ECR; the legacy default accepts them.
    assert code == 0 and out.startswith("MANUFACTURABLE")
    assert episode["verdict"]["status"] == "MANUFACTURABLE" and episode["verdict"]["reason_codes"] == []
    assert episode["verdict"]["produced_by"]["version"] == "1.0.0"
    assert episode["capability_model_version"] == "1.0.0"
    assert "tolerances" not in episode["design_input"]        # the documented default-mode limitation


def test_explicit_default_equals_implicit_default(tmp_path, monkeypatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _, _, implicit = _cli(tmp_path / "a", monkeypatch, BASE)
    _, _, explicit = _cli(tmp_path / "b", monkeypatch, BASE, "--capability-model", "default")
    assert implicit["content_hash"] == explicit["content_hash"]
    assert implicit["plan"]["content_hash"] == explicit["plan"]["content_hash"]


def test_constrained_mode_passes_tolerance_and_reasons(tmp_path, monkeypatch):
    code, out, episode = _cli(tmp_path, monkeypatch, TIGHT_MISORDERED, "--capability-model", "constrained")
    assert code == 0 and out.startswith("PLAN_INVALID")
    assert episode["verdict"]["reason_codes"] == ["PRECEDENCE_VIOLATION", "TOLERANCE_UNSUPPORTED"]
    assert episode["verdict"]["produced_by"]["version"] == "1.1.0"
    assert episode["capability_model_version"] == "1.1.0"
    assert episode["design_input"]["tolerances"] == {"general_tolerance_mm": 0.001}
    carried = [s for s in episode["plan"]["steps"] if "required_tolerance_mm" in s.get("params", {})]
    assert {s["op"] for s in carried} == {"face_mill", "drill"}
    assert episode["plan"]["provenance"]["rule_version"] == "1.1.0"


def test_constrained_mode_accepts_a_feasible_request(tmp_path, monkeypatch):
    code, out, episode = _cli(tmp_path, monkeypatch, BASE, "--capability-model", "constrained")
    assert code == 0 and out.startswith("MANUFACTURABLE")
    assert episode["verdict"]["reason_codes"] == [] and episode["verdict"]["produced_by"]["version"] == "1.1.0"


def test_unknown_capability_model_is_rejected(tmp_path, monkeypatch):
    with pytest.raises(SystemExit):
        _cli(tmp_path, monkeypatch, BASE, "--capability-model", "experimental")
