"""RM14 boundaries (mirrored by the import-linter checker-independence contract):

- the checker never imports the setup-rule module (it re-reads the rules and re-derives relevance
  and every required changeover itself);
- setup rules stay internal, per-run scheduling input: no contract, schema or manufacturability
  reason code mentions a changeover or a setup rule, and no RM1-RM10 module reads them.
"""

from __future__ import annotations

import ast
import pathlib

from mini_prometheus._contracts import ManufacturabilityReasonCode

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "mini_prometheus"
ROOT = SRC.parents[1]
SCHEDULING = SRC / "manufacturing_scheduling"


def _imports(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names


def test_checker_does_not_import_the_setup_rule_module():
    imported = _imports(SCHEDULING / "checker.py")
    assert not any(".manufacturing_scheduling.changeover" in n for n in imported), sorted(imported)
    assert not any(
        n.endswith((".canonical_setup_rules", ".relevant_setup_rules", ".possible_transitions"))
        for n in imported
    )


def test_setup_rules_stay_internal():
    files = [
        p for p in (ROOT / "contracts").rglob("*") if p.is_file() and "__pycache__" not in p.parts
    ]
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore").lower()
        assert "changeover" not in text and "setup_rule" not in text, p
    assert not any("SETUP" in member.value for member in ManufacturabilityReasonCode)


def test_only_scheduling_modules_read_setup_rules():
    readers = sorted(
        str(p.relative_to(SRC)).replace("\\", "/")
        for p in SRC.rglob("*.py")
        if any("changeover" in n for n in _imports(p))
    )
    assert readers == [
        "manufacturing_scheduling/earliest_start.py",
        "manufacturing_scheduling/job_set.py",
        "orchestration/schedule_runner.py",
    ]
