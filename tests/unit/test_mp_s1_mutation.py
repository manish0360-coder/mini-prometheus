"""MP-S1 anti-vacuity (T10.1): every required mutant must be caught by a NAMED gate.

Each mutant is an exact textual substitution in the REAL source (each anchor must occur exactly once),
executed as an isolated module. A gate returns True when the behaviour is correct. It must be True on
the real code and False under its mutant; a gate that raises under the mutant counts as caught.
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import json
import pathlib
import sys
import types

import mp_s1_support as s
import support
from mini_prometheus.experience import episode_index as real_index
from mini_prometheus.experience import episode_store_reader as real_reader
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_planning import planner as real_planner
from mini_prometheus.manufacturing_scheduling import checker as real_checker
from mini_prometheus.manufacturing_scheduling.model import IssueCode
from mini_prometheus.orchestration import episode_store
from mini_prometheus.orchestration import precedent_basis as real_basis
from mini_prometheus.orchestration import reuse_runner as real_reuse
from mini_prometheus.orchestration import runner as real_runner
from mini_prometheus.orchestration import verdict_trace as real_trace
from mini_prometheus.orchestration.schedule_runner import _request_from_json, schedule_requests
from mini_prometheus.shop_declaration import shop_model as real_shop
from mini_prometheus.shop_declaration.shop_model import capability_model_ref_for

T = "2026-11-06T00:00:00+00:00"


def mutate(module, *substitutions: tuple[str, str]) -> types.ModuleType:
    source = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    for old, new in substitutions:
        assert source.count(old) == 1, f"anchor not unique in {module.__name__}: {old!r}"
        source = source.replace(old, new)
    name = module.__name__ + "_mutant"
    mutant = types.ModuleType(name)
    mutant.__file__ = module.__file__
    sys.modules[name] = mutant  # dataclasses resolve their module through sys.modules
    exec(compile(source, module.__file__, "exec"), mutant.__dict__)
    return mutant


def caught(gate, *args) -> bool:
    try:
        return gate(*args) is False
    except Exception:
        return True


# --- gates ---------------------------------------------------------------------------------------


def gate_plan_carries_ref(planner):
    model = s.model("default_1.0.0")
    plan = planner.plan(intake(s.bracket(), produced_at=T), model, produced_at=T)[1]
    return plan.capability_model_ref == capability_model_ref_for(model)


def _reuse(tmp, run_with_reuse, base, variant):
    store = str(tmp / f"{variant}.jsonl")
    run_with_reuse(s.bracket(), capability_model=s.model(base), produced_at=T, store_path=store)
    return run_with_reuse(
        s.bracket(),
        capability_model=s.model(f"variants/{variant}"),
        produced_at=T,
        store_path=store,
    )


def gate_no_stale_material_reuse(tmp, run_with_reuse):
    second = _reuse(tmp, run_with_reuse, "default_1.0.0", "material_removed")
    return second.reused is False and second.status == "NOT_MANUFACTURABLE"


def gate_evidence_change_misses(tmp, run_with_reuse):
    return (
        _reuse(tmp, run_with_reuse, "default_1.0.0", "evidence_public_specification").reused
        is False
    )


def gate_runner_refuses_mismatch(tmp, run, monkeypatch):
    other = s.model("variants/declarer_changed")
    real = real_planner.plan
    monkeypatch.setattr(real_planner, "plan", lambda di, _m, **kw: real(di, other, **kw))
    try:
        run(
            intake(s.bracket(), produced_at=T),
            capability_model=s.model("default_1.0.0"),
            produced_at=T,
            store_path=str(tmp / "g2.jsonl"),
        )
    except real_shop.ShopIdentityMismatchError:
        return not (tmp / "g2.jsonl").exists()
    finally:
        monkeypatch.setattr(real_planner, "plan", real)
    return False


def gate_load_refuses_ref_edit(tmp, load):
    path = tmp / "g3.jsonl"
    real_runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=s.model("default_1.0.0"),
        produced_at=T,
        store_path=str(path),
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    data["plan"]["capability_model_ref"]["evidence_class"] = "shop_declared"
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    try:
        load(str(path))
    except Exception:
        return True
    return False


def gate_checker_flags_missing_schedule_ref(schedule_issues):
    model = s.model("default_1.0.0")
    jobs_json = [support.load_json(f"rm11_jobs/job_{n}.json") for n in ("a", "b", "c")]
    requests = [_request_from_json(raw, False) for raw in jobs_json]
    schedule = schedule_requests(requests, capability_model=model, produced_at=T).schedule
    from mini_prometheus.manufacturing_scheduling.model import SchedulingJob

    jobs = []
    for request in requests:
        task, plan = real_planner.plan(intake(request, produced_at=T), model, produced_at=T)
        jobs.append(SchedulingJob(request.request_id, task.task_id, plan))
    broken = dataclasses.replace(schedule, shop_model_ref=None)
    issues = schedule_issues(
        broken, jobs, model.version, shop_model_ref=capability_model_ref_for(model)
    )
    return any(i.code == IssueCode.METADATA_MISMATCH and "shop" in i.detail for i in issues)


def gate_cycle_refused(load_shop_model):
    try:
        load_shop_model(s.doc("invalid/PRECEDENCE_CYCLE"))
    except Exception as exc:
        return "PRECEDENCE_CYCLE" in str(exc)
    return False


def gate_cli_no_fallback(tmp, main, monkeypatch):
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", tmp / "cli.jsonl")
    request = tmp / "request.json"
    request.write_text(json.dumps(s.bracket_json()), encoding="utf-8")
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(
                [str(request), "--capability-model-file", str(s.INVALID / "PRECEDENCE_CYCLE.json")]
            )
        except SystemExit as exc:
            code = exc.code
    return code == 2 and not (tmp / "cli.jsonl").exists()


def gate_other_shop_is_not_evidence(tmp, annotate):
    path = str(tmp / "basis.jsonl")
    real_runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=s.model("three_cell_synthetic"),
        produced_at=T,
        store_path=path,
    )
    current = s.model("default_1.0.0")
    report, _ = real_basis.run_precedent_for_shop(
        s.bracket(), capability_model=current, store_path=path
    )
    annotation = annotate(report, real_reader.load(path), current)
    return [e.capability_evidence for e in annotation.entries] == [False]


def gate_trace_refuses_wrong_verdict(tmp, trace_run):
    model = s.model("default_1.0.0")
    result = real_runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=model,
        produced_at=T,
        store_path=str(tmp / "trace.jsonl"),
    )
    forged = dataclasses.replace(
        result, verdict=dataclasses.replace(result.verdict, status="PLAN_INVALID")
    )
    try:
        trace_run(forged, model)
    except Exception:
        return True
    return False


def gate_display_name_is_not_identity(shop_identities):
    return shop_identities(s.doc("default_1.0.0")) == shop_identities(
        s.doc("variants/display_name_changed")
    )


# --- the mutants ---------------------------------------------------------------------------------


def test_m01_plan_loses_its_ref():
    assert gate_plan_carries_ref(real_planner)
    mutant = mutate(
        real_planner,
        ("        capability_model_ref=shop_ref,\n", "        capability_model_ref=None,\n"),
    )
    assert caught(gate_plan_carries_ref, mutant)


_INDEX_DROP = (
    ("        ref.shop_declaration_hash if ref is not None else None,\n", "        None,\n"),
    (
        "        capability_model_version,\n        shop_declaration_hash,\n    )",
        "        capability_model_version,\n        None,\n    )",
    ),
)


def _reuse_with(index_mutant, reuse_subs=()):
    reuse = mutate(
        real_reuse, *reuse_subs
    )  # with no substitution: an isolated copy of the real module
    reuse.EpisodeIndex, reuse.design_input_key = (
        index_mutant.EpisodeIndex,
        index_mutant.design_input_key,
    )
    return reuse.run_with_reuse


def test_m02_reuse_key_drops_the_declaration_hash(tmp_path):
    assert gate_no_stale_material_reuse(tmp_path, real_reuse.run_with_reuse)
    (tmp_path / "m").mkdir()
    assert caught(
        gate_no_stale_material_reuse, tmp_path / "m", _reuse_with(mutate(real_index, *_INDEX_DROP))
    )


def test_m03_reuse_keys_on_the_content_hash(tmp_path):
    assert gate_evidence_change_misses(tmp_path, real_reuse.run_with_reuse)
    index = mutate(real_index, ("ref.shop_declaration_hash if ref", "ref.shop_content_hash if ref"))
    reuse = _reuse_with(
        index, (("model.source.shop_declaration_hash", "model.source.shop_content_hash"),)
    )
    (tmp_path / "m").mkdir()
    assert caught(gate_evidence_change_misses, tmp_path / "m", reuse)


def test_m04_runner_skips_g2(tmp_path, monkeypatch):
    assert gate_runner_refuses_mismatch(tmp_path, real_runner.run, monkeypatch)
    mutant = mutate(
        real_runner,
        (
            "        require_plan_shop_identity(plan, model)  # MP-S1 G2: before verification\n",
            "        pass\n",
        ),
    )
    (tmp_path / "m").mkdir()
    assert caught(gate_runner_refuses_mismatch, tmp_path / "m", mutant.run, monkeypatch)


def test_m05_reader_skips_g3(tmp_path):
    assert gate_load_refuses_ref_edit(tmp_path, real_reader.load)
    mutant = mutate(
        real_reader,
        ("        _verify_shop_identity(lineno, episode.plan)  # MP-S1 G3\n", "        pass\n"),
    )
    (tmp_path / "m").mkdir()
    assert caught(gate_load_refuses_ref_edit, tmp_path / "m", mutant.load)


def test_m06_checker_ignores_the_shop_ref():
    assert gate_checker_flags_missing_schedule_ref(real_checker.schedule_issues)
    mutant = mutate(
        real_checker, ("    if schedule.shop_model_ref != shop_model_ref:\n", "    if False:\n")
    )
    assert caught(gate_checker_flags_missing_schedule_ref, mutant.schedule_issues)


def test_m07_cycle_check_skipped():
    assert gate_cycle_refused(real_shop.load_shop_model)
    mutant = mutate(real_shop, ("    if _has_cycle(pairs):\n", "    if False:\n"))
    assert caught(gate_cycle_refused, mutant.load_shop_model)


def test_m08_cli_falls_back_to_the_default_model(tmp_path, monkeypatch):
    assert gate_cli_no_fallback(tmp_path, real_runner._main, monkeypatch)
    mutant = mutate(
        real_runner,
        ("            parser.exit(2, refusal_message(exc))\n", "            declared = None\n"),
    )
    (tmp_path / "m").mkdir()
    assert caught(gate_cli_no_fallback, tmp_path / "m", mutant._main, monkeypatch)


def test_m09_annotation_counts_other_shop_as_evidence(tmp_path):
    assert gate_other_shop_is_not_evidence(tmp_path, real_basis.annotate_precedent_basis)
    mutant = mutate(
        real_basis,
        ("basis == PrecedentBasis.SAME_DECLARATION)", "basis != PrecedentBasis.UNRESOLVED)"),
    )
    (tmp_path / "m").mkdir()
    assert caught(gate_other_shop_is_not_evidence, tmp_path / "m", mutant.annotate_precedent_basis)


def test_m10_trace_skips_the_consistency_check(tmp_path):
    assert gate_trace_refuses_wrong_verdict(tmp_path, real_trace.trace_run)
    mutant = mutate(
        real_trace,
        (
            "    if h.to_contract_dict(episode.verdict) != h.to_contract_dict(verdict):\n",
            "    if False:\n",
        ),
    )
    (tmp_path / "m").mkdir()
    assert caught(gate_trace_refuses_wrong_verdict, tmp_path / "m", mutant.trace_run)


def test_m11_display_name_leaks_into_the_declaration_hash():
    assert gate_display_name_is_not_identity(real_shop.shop_identities)
    mutant = mutate(
        real_shop,
        (
            '         "declaration": n["declaration"]}',
            '         "declaration": n["declaration"], "display_name": document.get("display_name")}',
        ),
    )
    assert caught(gate_display_name_is_not_identity, mutant.shop_identities)
