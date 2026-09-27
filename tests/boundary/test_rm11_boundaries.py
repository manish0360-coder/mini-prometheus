"""RM11 boundaries (mirrored by import-linter contracts in pyproject.toml):

- the scheduling code imports only the standard library and mini_prometheus (no solver, no new
  dependency);
- the checker never imports the generator, the bound calculator or the job-set gate (independence);
- no RM1-RM10 module imports the scheduling package or its CLI (scheduling is strictly downstream of
  per-job planning, so plan identity / RM2 reuse can never depend on co-scheduled jobs, and RM3/RM4
  never read schedules);
- the scheduling package does not import orchestration, integrations or intake;
- contracts are unchanged: suite 0.4.0 and no schedule schema (no ProductionSchedule /
  ScheduleVerdict).
"""

from __future__ import annotations

import ast
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "mini_prometheus"
ROOT = SRC.parents[1]
SCHEDULING = SRC / "manufacturing_scheduling"
SCHEDULE_RUNNER = SRC / "orchestration" / "schedule_runner.py"
RM11_MODULES = [*sorted(SCHEDULING.glob("*.py")), SCHEDULE_RUNNER]


def _modules(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
    return names


def test_rm11_modules_add_no_dependency():
    allowed = set(sys.stdlib_module_names) | {"mini_prometheus", "__future__"}
    for path in RM11_MODULES:
        foreign = {name.split(".")[0] for name in _modules(path)} - allowed
        assert not foreign, f"{path.name} imports {sorted(foreign)}"


def test_checker_is_independent_of_what_it_checks():
    imported = _modules(SCHEDULING / "checker.py")
    for forbidden in ("earliest_start", "lower_bound", "job_set"):
        assert not any(forbidden in name for name in imported), (forbidden, sorted(imported))


def test_no_rm1_to_rm10_module_imports_scheduling():
    for path in SRC.rglob("*.py"):
        if path.is_relative_to(SCHEDULING) or path == SCHEDULE_RUNNER:
            continue
        for name in _modules(path):
            assert "manufacturing_scheduling" not in name and "schedule_runner" not in name, (
                path,
                name,
            )


def test_scheduling_package_does_not_import_orchestration_integrations_or_intake():
    forbidden = (
        "mini_prometheus.orchestration",
        "mini_prometheus.integrations",
        "mini_prometheus.intake",
    )
    for path in SCHEDULING.glob("*.py"):
        for name in _modules(path):
            assert not name.startswith(forbidden), (path.name, name)


def test_contracts_unchanged_and_no_schedule_schema():
    assert (ROOT / "contracts" / "VERSION").read_text(encoding="utf-8").strip() == "0.4.0"
    names = [p.name.lower() for p in (ROOT / "contracts").rglob("*") if p.is_file()]
    assert not any("schedul" in name for name in names), names
