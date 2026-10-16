"""RM15 EC3 — pre-measurement harness binding smoke test (NO arm execution, NO scoring).

Establishes that the frozen RM5 harness is READY to consume the committed RM15 fixture, without running
the experiment. Two kinds of evidence, both execution-free:

RUNTIME (pre-arm path only):
  * deterministic fixture selection — the committed RM15 fixture loads reproducibly (RM2 reader);
  * deterministic harness configuration — partition + checkpoint_id reproduce the committed value
    (frozen ``partition`` module, pure; no arms); experience/held-out disjoint and covering.

STATIC WIRING (AST of the frozen ``runner.run`` source — parsed, never executed):
  * the fixture argument ``fixture_dir`` flows into the corpus-loading path: ``fx`` is assigned from
    ``fixture_dir`` and ``load(fx / "episodes.jsonl")`` is the load call site;
  * the runner contains the three arm call sites ``arms.cold_start`` / ``arms.no_precedent`` /
    ``arms.full_system``.

It deliberately does NOT call ``runner.run()`` (which, from the load call onward, executes the three
arms and computes agreement, false alarms, coverage and the compounding curve) and does NOT invoke any
arm. No Arm1/Arm2/Arm3 outcome or experiment metric is computed, materialized, printed, logged, compared
or reported here. That is EC4, separately gated. No production code is needed: the frozen
``runner.run(fixture_dir=...)`` parameter is the binding point.
"""
from __future__ import annotations

import ast
import inspect
import json
import pathlib
import textwrap

from mini_prometheus.experience.episode_store_reader import load
from mini_prometheus.experiment import partition, runner

RM15_FIXTURE_DIR = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "rm15_corpus"
_COMMITTED_CHECKPOINT = "sha256:11c039a96113aadeaba07a4078df04a6f4b25b94f3d1301a27db2123f09cb4d6"


def _run_ast() -> ast.FunctionDef:
    """The parsed AST of the FROZEN ``runner.run`` source (static inspection; never executed)."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(runner.run)))
    fn = tree.body[0]
    assert isinstance(fn, ast.FunctionDef) and fn.name == "run"
    return fn


# ---- (1) configured fixture path resolves to the committed RM15 corpus -----------------------------

def test_rm15_fixture_path_resolves_to_committed_corpus():
    assert RM15_FIXTURE_DIR.is_dir()
    assert RM15_FIXTURE_DIR.name == "rm15_corpus"
    assert RM15_FIXTURE_DIR.parent.name == "fixtures"
    for name in ("episodes.jsonl", "partition.json", "checkpoint.json"):
        assert (RM15_FIXTURE_DIR / name).is_file()


# ---- (2,3) static wiring via AST of the frozen runner.run ------------------------------------------

def test_fixture_dir_flows_into_corpus_load_call_site():
    fn = _run_ast()
    # fixture_dir is an actual parameter
    assert "fixture_dir" in {a.arg for a in fn.args.args}
    # `fx` is assigned from an expression that references `fixture_dir`
    fx_from_fixture_dir = any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "fx" for t in node.targets)
        and any(isinstance(n, ast.Name) and n.id == "fixture_dir" for n in ast.walk(node.value))
        for node in ast.walk(fn)
    )
    assert fx_from_fixture_dir, "runner.run does not derive `fx` from `fixture_dir`"
    # the corpus load call site is `load(fx / "episodes.jsonl")`
    load_binds_fx = False
    for node in ast.walk(fn):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "load" and node.args):
            arg = node.args[0]
            if (isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Div)
                    and isinstance(arg.left, ast.Name) and arg.left.id == "fx"
                    and isinstance(arg.right, ast.Constant) and arg.right.value == "episodes.jsonl"):
                load_binds_fx = True
    assert load_binds_fx, 'runner.run does not load `fx / "episodes.jsonl"`'


def test_runner_contains_the_three_arm_call_sites():
    fn = _run_ast()
    arm_calls = {
        node.func.attr
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name) and node.func.value.id == "arms"
    }
    assert {"cold_start", "no_precedent", "full_system"} <= arm_calls, arm_calls


# ---- (5) deterministic fixture + partition/checkpoint (pre-arm, no scoring) -------------------------

def test_rm15_fixture_selection_is_deterministic():
    a = load(RM15_FIXTURE_DIR / "episodes.jsonl")
    b = load(RM15_FIXTURE_DIR / "episodes.jsonl")
    assert [e.content_hash for e in a] == [e.content_hash for e in b]
    assert len(a) == 960


def test_rm15_partition_and_checkpoint_are_deterministic():
    episodes = load(RM15_FIXTURE_DIR / "episodes.jsonl")
    part = partition.partition(episodes)
    cp = partition.checkpoint_id(part)
    committed = json.loads((RM15_FIXTURE_DIR / "checkpoint.json").read_text(encoding="utf-8"))
    assert cp == _COMMITTED_CHECKPOINT == committed["checkpoint_id"]
    assert len(part.experience) + len(part.held_out) == len(episodes)
    assert set(part.experience).isdisjoint(part.held_out)
