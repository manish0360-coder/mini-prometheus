"""RM9 C4 — the existing CLI with a repeatable ``--unavailable-resource ID``.

Without the flag the invocation is exactly RM8's (default mode is additionally pinned byte-for-byte by
the rm5-complete golden). With it, the availability snapshot is explicit and deterministic; unknown ids
are rejected before planning and nothing is written.
"""
from __future__ import annotations

import contextlib
import io
import json

import pytest

from mini_prometheus.orchestration import episode_store, runner

import support

BASE = support.load_json("engineer_request_machined_bracket.json")


def _cli(tmp_path, monkeypatch, *flags):
    store = tmp_path / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(BASE), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = runner._main([str(request_path), *flags])
    episode = json.loads(store.read_text(encoding="utf-8").splitlines()[-1]) if store.exists() else None
    return code, out.getvalue(), episode


def test_unavailable_only_capable_machine(tmp_path, monkeypatch):
    code, out, episode = _cli(tmp_path, monkeypatch, "--unavailable-resource", "mill01")
    assert code == 0 and out.startswith("NOT_MANUFACTURABLE")
    assert episode["verdict"]["reason_codes"] == ["RESOURCE_UNAVAILABLE"]
    assert episode["verdict"]["detail"] == "RESOURCE_UNAVAILABLE: mill01"
    assert episode["verdict"]["produced_by"]["version"] == "1.2.0"
    assert episode["capability_model_version"] == "1.0.0"                   # model version unchanged


def test_flag_is_repeatable(tmp_path, monkeypatch):
    _, _, episode = _cli(tmp_path, monkeypatch, "--unavailable-resource", "mill01", "--unavailable-resource", "cmm01")
    assert episode["verdict"]["detail"] == "RESOURCE_UNAVAILABLE: cmm01, mill01"


def test_irrelevant_availability_with_constrained_model_changes_nothing(tmp_path, monkeypatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    _, _, plain = _cli(tmp_path / "a", monkeypatch, "--capability-model", "constrained")
    _, _, with_flag = _cli(tmp_path / "b", monkeypatch, "--capability-model", "constrained",
                           "--unavailable-resource", "lathe01")
    assert with_flag["plan"]["content_hash"] == plain["plan"]["content_hash"]
    assert with_flag["content_hash"] == plain["content_hash"]
    assert with_flag["verdict"] == plain["verdict"]                            # 1.1.0, no detail


def test_unknown_resource_is_rejected_before_planning(tmp_path, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _cli(tmp_path, monkeypatch, "--unavailable-resource", "mill99")
    assert exc.value.code == 2
    assert not (tmp_path / "episodes.jsonl").exists()
