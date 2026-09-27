"""RM13 CLI: ``--rule`` opts into earliest_start_v1_most_work_remaining; the default and the
RM11/RM12 reports are unchanged; an unknown rule is a usage error (exit 2)."""

from __future__ import annotations

import contextlib
import io

import pytest

import rm11_support as s
import support
from mini_prometheus.orchestration import schedule_runner
from mini_prometheus.orchestration.schedule_runner import schedule_requests
from rm11_support import FIXED_TIME

FIXTURE_PATHS = [str(support.FIXTURES / name) for name in s.THREE_JOB_FILES]


def _cli(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = schedule_runner._main(list(args))
    return code, out.getvalue().splitlines()


def test_cli_default_is_the_rm11_report_byte_for_byte():
    assert _cli(*FIXTURE_PATHS) == _cli(*FIXTURE_PATHS, "--rule", "earliest_start_v1")


def test_cli_opt_in_rule_reports_its_own_identity():
    code, lines = _cli(*FIXTURE_PATHS, "--rule", "earliest_start_v1_most_work_remaining")
    sched = schedule_requests(
        s.three_job_requests(), produced_at=FIXED_TIME, rule="earliest_start_v1_most_work_remaining"
    ).schedule
    assert code == 0
    assert lines[0] == (
        "SCHEDULED: 3 jobs, 10 operations (rule earliest_start_v1_most_work_remaining 1.0.0; "
        "NOT_OPTIMIZED; capability model 1.0.0)"
    )
    assert "makespan: 67 min" in lines
    assert lines[-2:] == [
        f"schedule input identity: {sched.schedule_input_identity}",
        f"schedule digest: {sched.schedule_digest}",
    ]


def test_cli_opt_in_rule_with_downtime():
    code, lines = _cli(
        *FIXTURE_PATHS,
        "--rule",
        "earliest_start_v1_most_work_remaining",
        "--downtime",
        "mill01:20:45",
    )
    assert code == 0 and "earliest_start_v1_most_work_remaining_downtime" in lines[0]
    assert (
        "makespan: 102 min" in lines
        and "window-aware lower bound: 77 min (binding: mill01)" in lines
    )


@pytest.mark.parametrize("rule", ["earliest_start_v1_downtime", "giffler_thompson", "optimal"])
def test_cli_rejects_unknown_rules(rule):
    with pytest.raises(SystemExit) as exc:
        _cli(*FIXTURE_PATHS, "--rule", rule)
    assert exc.value.code == 2
