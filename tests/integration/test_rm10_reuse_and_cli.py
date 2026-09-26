"""RM10 x RM2 reuse (Q, R) and the CLI (S, T). RM2 is unchanged: declared durations are part of the
design input, so they enter the reuse key through the existing parameter identity path."""
from __future__ import annotations

import contextlib
import copy
import io
import json

from mini_prometheus.manufacturing_constraints.oracle import SCHEDULE_START_PARAM
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import episode_store, runner
from mini_prometheus.orchestration.reuse_runner import run_with_reuse

import support
from support import FIXED_TIME

TIMED = support.load_json("engineer_request_with_durations.json")


def _request(raw):
    return support.build_request(raw)


def test_Q_reuse_with_same_durations_succeeds(tmp_path):
    store = str(tmp_path / "episodes.jsonl")
    first = run_with_reuse(_request(TIMED), produced_at=FIXED_TIME, store_path=store)
    again = run_with_reuse(_request(TIMED), produced_at=FIXED_TIME, store_path=store)
    assert not first.reused and again.reused
    assert again.plan.content_hash == first.plan.content_hash and planner.lead_time_min(again.plan) == 108


def test_R_changed_durations_do_not_reuse(tmp_path):
    store = str(tmp_path / "episodes.jsonl")
    run_with_reuse(_request(TIMED), produced_at=FIXED_TIME, store_path=store)
    changed = copy.deepcopy(TIMED)
    changed["declared_operations"][1]["params"]["duration_min"] = 40
    other = run_with_reuse(_request(changed), produced_at=FIXED_TIME, store_path=store)
    assert not other.reused                                  # a different key: a fresh, verified run
    assert planner.lead_time_min(other.plan) == 113


def _cli(tmp_path, monkeypatch, raw, *flags):
    store = tmp_path / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(raw), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = runner._main([str(request_path), *flags])
    episode = json.loads(store.read_text(encoding="utf-8").splitlines()[-1])
    return code, out.getvalue().splitlines(), episode


def test_S_cli_prints_lead_time_for_a_valid_timeline(tmp_path, monkeypatch):
    code, lines, episode = _cli(tmp_path, monkeypatch, TIMED)
    assert code == 0 and lines[0].startswith("MANUFACTURABLE")
    assert lines[1] == "lead time: 108 min (single-job serialized timeline)"
    assert episode["plan"]["steps"][-1]["params"]["schedule_lead_time_min"] == 108
    assert episode["plan"]["provenance"]["rule_version"] == "1.3.0"


def test_T_cli_reports_missing_prerequisites_without_a_fake_timeline(tmp_path, monkeypatch):
    raw = copy.deepcopy(TIMED)
    del raw["declared_operations"][2]["params"]
    code, lines, episode = _cli(tmp_path, monkeypatch, raw, "--unavailable-resource", "cmm01")
    assert lines[0].startswith("NOT_MANUFACTURABLE")                       # RM9 verdict preserved
    assert lines[1] == ("timeline not derived: step 2 (drill): duration_min missing; "
                        "step 5 (inspect): no machine assigned")
    assert all(SCHEDULE_START_PARAM not in s.get("params", {}) for s in episode["plan"]["steps"])
    assert episode["verdict"]["reason_codes"] == ["RESOURCE_UNAVAILABLE"]


def test_cli_without_durations_prints_only_the_rm9_line(tmp_path, monkeypatch):
    _code, lines, _episode = _cli(tmp_path, monkeypatch, support.load_json("engineer_request_machined_bracket.json"))
    assert len(lines) == 1 and lines[0].startswith("MANUFACTURABLE")
