"""RM12 CLI: ``--downtime MACHINE:START:END`` on the dedicated scheduling entry point.

The report adds RM12 lines only when relevant downtime exists; downtime on unused machines leaves
the RM11 report byte-identical; invalid downtime is a usage error (exit 2) before any planning;
scheduling with downtime writes nothing (Director test AC).
"""

from __future__ import annotations

import contextlib
import io
import json

import pytest

import rm11_support as s
import support
from mini_prometheus.orchestration import episode_store, schedule_runner
from mini_prometheus.orchestration.schedule_runner import schedule_requests
from rm11_support import FIXED_TIME, ID_A, ID_B, ID_C

FIXTURE_PATHS = [str(support.FIXTURES / name) for name in s.THREE_JOB_FILES]


def _cli(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = schedule_runner._main(list(args))
    return code, out.getvalue().splitlines()


def _write(tmp_path, raws):
    paths = []
    for raw in raws:
        path = tmp_path / f"{raw['request_id']}.json"
        path.write_text(json.dumps(raw), encoding="utf-8")
        paths.append(str(path))
    return paths


def test_cli_reports_downtime_the_retained_and_window_aware_bounds_and_identities():
    code, lines = _cli(*FIXTURE_PATHS, "--downtime", "mill01:30:45", "--downtime", "mill01:20:30")
    sched = schedule_requests(
        s.three_job_requests(), produced_at=FIXED_TIME, downtime={"mill01": [(20, 45)]}
    ).schedule
    assert code == 0
    assert lines[0] == (
        "SCHEDULED: 3 jobs, 10 operations (rule earliest_start_v1_downtime 1.0.0; NOT_OPTIMIZED; "
        "capability model 1.0.0)"
    )
    rows = [line.split() for line in lines[2:12]]
    assert [(r[3], int(r[4]), int(r[0]), int(r[1])) for r in rows][4] == (ID_A, 1, 45, 75)
    assert lines[12:15] == [
        f"job {ID_A}: completion 80 min",
        f"job {ID_B}: completion 90 min",
        f"job {ID_C}: completion 103 min",
    ]
    assert lines[15:20] == [
        "downtime: mill01 [20, 45)",
        "makespan: 103 min",
        "lower bound: 52 min (busiest machine mill01)",
        "window-aware lower bound: 77 min (binding: mill01)",
        "gap to lower bound: 26 min",
    ]
    assert lines[20] == "model assumptions: " + "; ".join(sched.model_assumptions)
    assert lines[21:] == [
        f"schedule input identity: {sched.schedule_input_identity}",
        f"schedule digest: {sched.schedule_digest}",
    ]


def test_cli_states_provable_optimality_under_the_rm12_model_only_when_the_gap_is_zero(tmp_path):
    raws = [
        s.raw_job(ID_A, [("face_mill", 100)]),
        s.raw_job(ID_B, [("cut_stock", 5), ("deburr", 5)]),
    ]
    _code, lines = _cli(
        *_write(tmp_path, raws), "--downtime", "mill01:0:10", "--downtime", "saw01:0:3"
    )
    assert "window-aware lower bound: 110 min (binding: mill01)" in lines
    assert (
        "gap to lower bound: 0 min "
        "(makespan equals the window-aware lower bound: PROVABLY OPTIMAL under the RM12 model)"
    ) in lines


def test_cli_downtime_on_unused_machines_leaves_the_rm11_report_byte_identical(tmp_path):
    raws = [
        s.raw_job(ID_A, [("cut_stock", 10)]),
        s.raw_job(ID_B, [("cut_stock", 10), ("face_mill", 100)]),
    ]
    paths = _write(tmp_path, raws)
    plain = _cli(*paths)
    with_unused = _cli(*paths, "--downtime", "lathe01:0:500", "--downtime", "cmm01:10:20")
    assert with_unused == plain and not any(line.startswith("downtime") for line in plain[1])


def test_cli_output_does_not_depend_on_file_or_downtime_order():
    first = _cli(*FIXTURE_PATHS, "--downtime", "mill01:20:45", "--downtime", "saw01:12:14")
    second = _cli(
        *reversed(FIXTURE_PATHS), "--downtime", "saw01:12:14", "--downtime", "mill01:20:45"
    )
    assert first == second and first[0] == 0


@pytest.mark.parametrize(
    "value",
    [
        "mill99:0:10",
        "mill01:5:5",
        "mill01:10:5",
        "mill01:-1:5",
        "mill01:2.5:5",
        "mill01:0:inf",
        "mill01:10",
        "mill01:a:b",
    ],
)
def test_cli_rejects_invalid_downtime_as_a_usage_error(value):
    with pytest.raises(SystemExit) as exc:
        _cli(*FIXTURE_PATHS, "--downtime", value)
    assert exc.value.code == 2


def test_AC_scheduling_with_downtime_writes_nothing(tmp_path, monkeypatch):
    store = tmp_path / "store" / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    workdir = tmp_path / "cwd"
    workdir.mkdir()
    monkeypatch.chdir(workdir)
    code, _lines = _cli(*FIXTURE_PATHS, "--downtime", "mill01:20:45")
    outcome = schedule_requests(s.three_job_requests(), downtime={"mill01": [(20, 45)]})
    assert code == 0 and outcome.schedule is not None
    assert not store.exists() and list(workdir.iterdir()) == []
    assert sorted(p.name for p in tmp_path.iterdir()) == ["cwd"]
