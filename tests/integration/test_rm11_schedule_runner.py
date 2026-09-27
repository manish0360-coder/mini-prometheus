"""RM11 composition and CLI: per-job plans are exactly the standalone RM1-RM10 plans, scheduling
writes nothing (Director test 20), a schedule that fails the checker is never returned, and the
dedicated CLI reports the schedule, the lower-bound certificate and both identities without
depending on argument order. runner.py is untouched."""

from __future__ import annotations

import contextlib
import dataclasses
import io
import json

import pytest

import rm11_support as s
import support
from mini_prometheus.manufacturing_scheduling import earliest_start, job_set
from mini_prometheus.manufacturing_scheduling.model import ScheduleIntegrityError, schedule_digest
from mini_prometheus.orchestration import episode_store, schedule_runner
from mini_prometheus.orchestration.runner import run_from_request
from rm11_support import ID_A, ID_B, ID_C
from support import FIXED_TIME

FIXTURE_PATHS = [str(support.FIXTURES / name) for name in s.THREE_JOB_FILES]


def _cli(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = schedule_runner._main(list(args))
    return code, out.getvalue().splitlines()


def _corrupt_generator(jobs, version):
    sched = earliest_start.earliest_start_v1(jobs, version)
    ops = list(sched.operations)
    ops[-1] = dataclasses.replace(
        ops[-1], start_min=ops[-1].start_min - 1, end_min=ops[-1].end_min - 1
    )
    bad = dataclasses.replace(sched, operations=tuple(ops))
    return dataclasses.replace(bad, schedule_digest=schedule_digest(bad))


def test_plan_in_a_schedule_is_the_standalone_plan(tmp_path):
    sched = s.schedule(s.three_job_requests()).schedule
    standalone = {
        r.request_id: run_from_request(
            r, produced_at=FIXED_TIME, store_path=str(tmp_path / "e.jsonl")
        )
        for r in s.three_job_requests()
    }
    assert {j.request_id: j.plan_content_hash for j in sched.jobs} == {
        rid: result.plan.content_hash for rid, result in standalone.items()
    }


def test_20_no_files_episodes_or_state_written(tmp_path, monkeypatch):
    store = tmp_path / "store" / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    outcome = s.schedule(s.three_job_requests())
    code, _lines = _cli(*FIXTURE_PATHS)
    refused = s.schedule([s.request(ID_A, [("cut_stock", None)])])
    assert outcome.schedule is not None and code == 0 and refused.schedule is None
    assert not store.exists() and list(workdir.iterdir()) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cwd"]


def test_a_schedule_failing_the_checker_is_never_returned(monkeypatch):
    monkeypatch.setattr(job_set, "earliest_start_v1", _corrupt_generator)
    with pytest.raises(
        ScheduleIntegrityError, match="JOB_ORDER_VIOLATION|MACHINE_OVERLAP|COMPLETION_MISMATCH"
    ):
        s.schedule(s.three_job_requests())


def test_cli_reports_the_schedule_certificate_and_identities():
    code, lines = _cli(*FIXTURE_PATHS)
    sched = s.schedule(s.three_job_requests()).schedule
    assert code == 0
    assert lines[0] == (
        "SCHEDULED: 3 jobs, 10 operations (rule earliest_start_v1 1.0.0; NOT_OPTIMIZED; "
        "capability model 1.0.0)"
    )
    rows = [line.split() for line in lines[2:12]]
    assert [
        (r[3], int(r[4]), r[5], r[2], int(r[0]), int(r[1])) for r in rows
    ] == s.THREE_JOB_SCHEDULE
    assert lines[12:15] == [
        f"job {ID_A}: completion 45 min",
        f"job {ID_B}: completion 55 min",
        f"job {ID_C}: completion 68 min",
    ]
    assert lines[15:18] == [
        "makespan: 68 min",
        "lower bound: 52 min (busiest machine mill01)",
        "gap to lower bound: 16 min",
    ]
    assert lines[18] == "model assumptions: " + "; ".join(sched.model_assumptions)
    assert lines[19:] == [
        f"schedule input identity: {sched.schedule_input_identity}",
        f"schedule digest: {sched.schedule_digest}",
    ]


def test_cli_output_does_not_depend_on_argument_order():
    assert _cli(*FIXTURE_PATHS) == _cli(*reversed(FIXTURE_PATHS))


def test_cli_states_provable_optimality_only_when_the_bound_is_met(tmp_path):
    paths = []
    for raw in (
        s.raw_job(ID_A, [("face_mill", 100)]),
        s.raw_job(ID_B, [("cut_stock", 5), ("deburr", 5)]),
    ):
        path = tmp_path / f"{raw['request_id']}.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        paths.append(str(path))
    _code, lines = _cli(*paths)
    assert "lower bound: 100 min (longest job " + ID_A + "; busiest machine mill01)" in lines
    assert (
        "gap to lower bound: 0 min "
        "(makespan equals the lower bound: PROVABLY OPTIMAL under the RM11 model)"
    ) in lines
    _code, gap_lines = _cli(*FIXTURE_PATHS)
    assert not any("OPTIMAL" in line for line in gap_lines if line.startswith("gap"))


def test_cli_refuses_the_whole_set(tmp_path):
    raw = s.raw_job(ID_C, [("cut_stock", 8), ("deburr", None)])
    path = tmp_path / "c.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    code, lines = _cli(*FIXTURE_PATHS[:2], str(path))
    assert code == 0
    assert lines == [
        "NOT_SCHEDULED: no schedule produced (all-or-nothing); 1 refusal(s)",
        f"refusal JOB_TIMELINE_MISSING {ID_C}: step 1 (deburr): duration_min missing",
    ]


def test_cli_availability_applies_to_every_job():
    code, lines = _cli(*FIXTURE_PATHS, "--unavailable-resource", "lathe01")
    assert code == 0 and lines[0].startswith("NOT_SCHEDULED")
    assert lines[1:] == [
        f"refusal JOB_NOT_MANUFACTURABLE {ID_B}: NOT_MANUFACTURABLE [RESOURCE_UNAVAILABLE] "
        "(RESOURCE_UNAVAILABLE: lathe01)",
        f"refusal JOB_OPERATION_UNASSIGNED {ID_B}: no machine assigned: step 1 (turn)",
        f"refusal JOB_TIMELINE_MISSING {ID_B}: step 1 (turn): no machine assigned",
    ]


def test_cli_rejects_an_unknown_resource():
    with pytest.raises(SystemExit) as exc:
        _cli(*FIXTURE_PATHS, "--unavailable-resource", "mill99")
    assert exc.value.code == 2


def test_cli_integrity_error_returns_1_and_prints_no_schedule(monkeypatch):
    monkeypatch.setattr(job_set, "earliest_start_v1", _corrupt_generator)
    code, lines = _cli(*FIXTURE_PATHS)
    assert (
        code == 1
        and len(lines) == 1
        and lines[0].startswith("SCHEDULE_INTEGRITY_ERROR (no schedule returned)")
    )
