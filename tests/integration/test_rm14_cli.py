"""RM14 CLI: ``--setup MACHINE:PREV_OP:CURR_OP:MINUTES`` and ``--setup-default MACHINE:MINUTES``
declare cross-job changeovers for one run; invalid rules are usage errors (exit 2); an undeclared
transition the schedule needs is a NOT_SCHEDULED refusal; without them the report is exactly RM13's.

Three-job fixture (job_a/b/c.json) with saw01 default 2, mill01 default 6 and mill01
face_mill -> drill 3, hand-computed (earliest_start_v1, block start, request_id ties):
A cut [0,10) -> A face_mill [10,40) -> B changeover [10,12) + cut [12,17) -> B turn [17,37) ->
C changeover [17,19) + cut [19,27) -> A inspect [40,45) -> B changeover [40,43) + drill [43,53) ->
B inspect [53,58) -> C changeover [53,59) + pocket_mill [59,71) -> C deburr [71,77). Makespan 77,
lower bound 52 (mill01), gap 25.
"""

from __future__ import annotations

import contextlib
import io

import pytest

import rm11_support as s
import rm14_support as t
import support
from mini_prometheus.orchestration import schedule_runner
from rm11_support import ID_A, ID_B, ID_C
from rm14_support import R

FIXTURE_PATHS = [str(support.FIXTURES / name) for name in s.THREE_JOB_FILES]
FLAGS = [
    "--setup-default",
    "saw01:2",
    "--setup-default",
    "mill01:6",
    "--setup",
    "mill01:face_mill:drill:3",
]
RULES = [
    R("saw01", None, None, 2),
    R("mill01", None, None, 6),
    R("mill01", "face_mill", "drill", 3),
]


def _cli(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = schedule_runner._main(list(args))
    return code, out.getvalue().splitlines()


def test_cli_setup_schedule_and_report():
    code, lines = _cli(*FIXTURE_PATHS, *FLAGS)
    sched = t.run(s.three_job_requests(), RULES).schedule
    assert code == 0
    assert lines[0] == (
        "SCHEDULED: 3 jobs, 10 operations (rule earliest_start_v1_setup 1.0.0; NOT_OPTIMIZED; "
        "capability model 1.0.0)"
    )
    assert s.placements(sched) == [
        (ID_A, 0, "cut_stock", "saw01", 0, 10),
        (ID_A, 1, "face_mill", "mill01", 10, 40),
        (ID_B, 0, "cut_stock", "saw01", 12, 17),
        (ID_B, 1, "turn", "lathe01", 17, 37),
        (ID_C, 0, "cut_stock", "saw01", 19, 27),
        (ID_A, 2, "inspect", "cmm01", 40, 45),
        (ID_B, 2, "drill", "mill01", 43, 53),
        (ID_B, 3, "inspect", "cmm01", 53, 58),
        (ID_C, 1, "pocket_mill", "mill01", 59, 71),
        (ID_C, 2, "deburr", "bench01", 71, 77),
    ]
    assert (
        "setup rules: mill01 default 6 min; mill01 face_mill -> drill 3 min; saw01 default 2 min"
        in lines
    )
    assert [line for line in lines if line.startswith("changeover ")] == [
        f"changeover [10, 12) saw01 before {ID_B} step 0: cut_stock ({ID_A}) -> cut_stock, 2 min "
        "(machine_default)",
        f"changeover [17, 19) saw01 before {ID_C} step 0: cut_stock ({ID_B}) -> cut_stock, 2 min "
        "(machine_default)",
        f"changeover [40, 43) mill01 before {ID_B} step 2: face_mill ({ID_A}) -> drill, 3 min "
        "(transition)",
        f"changeover [53, 59) mill01 before {ID_C} step 1: drill ({ID_B}) -> pocket_mill, 6 min "
        "(machine_default)",
    ]
    assert "makespan: 77 min" in lines
    assert "lower bound: 52 min (busiest machine mill01)" in lines
    assert "gap to lower bound: 25 min" in lines
    assert lines[-2:] == [
        f"schedule input identity: {sched.schedule_input_identity}",
        f"schedule digest: {sched.schedule_digest}",
    ]


def test_cli_setup_with_downtime_and_the_opt_in_rule():
    code, lines = _cli(
        *FIXTURE_PATHS,
        *FLAGS,
        "--downtime",
        "mill01:20:45",
        "--rule",
        "earliest_start_v1_most_work_remaining",
    )
    assert code == 0
    assert "(rule earliest_start_v1_most_work_remaining_downtime_setup 1.0.0;" in lines[0]
    assert any(line.startswith("window-aware lower bound: ") for line in lines)


def test_cli_needed_undeclared_transition_is_a_refusal_not_an_error():
    # only mill01 face_mill -> drill declared: after A cut, A face_mill, B cut, B turn and C cut,
    # C's pocket_mill is evaluated after A's face_mill on mill01 -> needed, undeclared: refused
    code, lines = _cli(*FIXTURE_PATHS, "--setup", "mill01:face_mill:drill:3")
    assert code == 0
    assert lines == [
        "NOT_SCHEDULED: no schedule produced (all-or-nothing); 1 refusal(s)",
        "refusal UNSPECIFIED_SETUP_TRANSITION: mill01: cross-job changeover face_mill -> "
        "pocket_mill is not declared and mill01 has no declared default",
    ]


def test_cli_irrelevant_setup_is_the_rm13_report_byte_for_byte():
    assert _cli(*FIXTURE_PATHS) == _cli(*FIXTURE_PATHS, "--setup-default", "bench01:5")


@pytest.mark.parametrize(
    "args,message",
    [
        (["--setup", "mill01:drill:5"], "expected MACHINE:PREV_OP:CURR_OP:MINUTES"),
        (["--setup", "saw01:cut_stock:cut_stock:x"], "MINUTES must be integer minutes"),
        (["--setup", "mill01:turn:drill:5"], "mill01 cannot perform turn"),
        (["--setup", "mill01:ANY:ANY:5"], "unknown operation"),
        (["--setup-default", "saw01"], "expected MACHINE:MINUTES"),
        (["--setup-default", "saw01:-1"], "integer minutes >= 0"),
        (["--setup-default", "mill99:5"], "unknown machine id"),
        (["--setup-default", "saw01:1", "--setup-default", "saw01:2"], "declared twice"),
    ],
)
def test_cli_rejects_invalid_setup_rules(args, message, capsys):
    with pytest.raises(SystemExit) as exc:
        _cli(*FIXTURE_PATHS, *args)
    assert exc.value.code == 2
    assert message in capsys.readouterr().err
