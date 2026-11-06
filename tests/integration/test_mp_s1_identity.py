"""MP-S1 AC5 (CLI part), AC6 (wording), AC7 and the verdict trace (T5.2, T5.3, T6.1, T7.x, T12.x).

No artifact may silently lose or mismatch its shop identity: plans (G1), the runner (G2), the stored
episode (G3), reuse (G4, see test_mp_s1_reuse.py) and schedules (G5). Every exposed verdict is traceable
to its shop declaration, plan, episode (when one exists) and evidence class. All fixtures are synthetic.
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import json

import pytest

import mp_s1_support as s
import support
from mini_prometheus import _hashing as h
from mini_prometheus.experience.episode_store_reader import EpisodeIntegrityError, load
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints import capability_model as cm
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.manufacturing_scheduling.checker import schedule_issues
from mini_prometheus.manufacturing_scheduling.model import IssueCode, SchedulingJob
from mini_prometheus.orchestration import episode_store, runner, schedule_runner
from mini_prometheus.orchestration.reuse_runner import run_with_reuse
from mini_prometheus.orchestration.schedule_runner import schedule_requests
from mini_prometheus.orchestration.verdict_trace import (
    TraceRecord,
    VerdictTraceError,
    trace_job,
    trace_run,
)
from mini_prometheus.shop_declaration.shop_model import (
    ShopIdentityMismatchError,
    capability_model_ref_for,
)

T = "2026-11-06T00:00:00+00:00"
JOBS = [support.FIXTURES / "rm11_jobs" / f"job_{n}.json" for n in ("a", "b", "c")]


def _run(tmp_path, model, request=None):
    return runner.run(
        intake(request or s.bracket(), produced_at=T),
        capability_model=model,
        produced_at=T,
        store_path=str(tmp_path / "episodes.jsonl"),
    )


# --- positive cases -----------------------------------------------------------------------------


def test_plan_episode_and_verdict_carry_the_declared_identity(tmp_path):
    model = s.model("three_cell_synthetic")
    result = _run(tmp_path, model)
    ref = capability_model_ref_for(model)
    assert ref is not None and result.plan.capability_model_ref == ref  # G1
    assert (ref.shop_content_hash, ref.shop_declaration_hash, str(ref.evidence_class)) == (
        model.source.shop_content_hash,
        model.source.shop_declaration_hash,
        "synthetic",
    )
    [stored] = load(str(tmp_path / "episodes.jsonl"))  # G3 runs inside load()
    assert (
        stored.plan.capability_model_ref == ref
        and stored.content_hash == result.episode.content_hash
    )
    assert h.content_hash(h.plan_identity(stored.plan)) == stored.plan.content_hash
    fresh = ManufacturabilityOracle().verify(stored.plan, model)  # T7.3
    assert h.to_contract_dict(fresh) == h.to_contract_dict(stored.verdict)


def test_declared_gaps_give_capability_missing(tmp_path):
    raw = s.bracket_json()
    raw["declared_operations"] = raw["declared_operations"][:1] + [{"op": "turn"}]
    turn = support.build_request(raw)
    result = _run(tmp_path, s.model("three_cell_synthetic"), turn)  # turn in unsupported_ops
    assert (result.status, result.verdict.reason_codes) == (
        "NOT_MANUFACTURABLE",
        ["CAPABILITY_MISSING"],
    )
    result = _run(tmp_path, s.model("r_star_2.0.0"), turn)  # cap.lathe in unsupported_capabilities
    assert (result.status, result.verdict.reason_codes) == (
        "NOT_MANUFACTURABLE",
        ["CAPABILITY_MISSING"],
    )


def test_code_models_are_untouched():
    plan = planner.plan(intake(s.bracket(), produced_at=T), cm.default_model(), produced_at=T)[1]
    assert plan.capability_model_ref is None and plan.schema_version == "1.0.0"
    assert "capability_model_ref" not in h.to_contract_dict(plan)


# --- G3: stored identity cannot be lost or edited silently ---------------------------------------


def _stored_line(tmp_path):
    _run(tmp_path, s.model("default_1.0.0"))
    path = tmp_path / "episodes.jsonl"
    return path, json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def _rewrite(path, data):
    path.write_text(json.dumps(data) + "\n", encoding="utf-8")


@pytest.mark.parametrize(
    "edit",
    [
        lambda p: p.pop("capability_model_ref"),  # T7.5 loss
        lambda p: p["capability_model_ref"].update(
            shop_declaration_hash="sha256:" + "0" * 64
        ),  # T7.6
        lambda p: p["capability_model_ref"].update(shop_content_hash="sha256:" + "1" * 64),
        lambda p: p["capability_model_ref"].update(evidence_class="shop_declared"),
        lambda p: p.update(schema_version="1.0.0"),  # T7.7
    ],
)
def test_stored_shop_identity_edits_fail_loudly(tmp_path, edit):
    path, data = _stored_line(tmp_path)
    edit(data["plan"])
    _rewrite(path, data)
    with pytest.raises(EpisodeIntegrityError):
        load(str(path))


def test_a_legacy_plan_claiming_schema_1_1_0_without_a_ref_fails(tmp_path):
    path = tmp_path / "episodes.jsonl"
    runner.run(intake(s.bracket(), produced_at=T), produced_at=T, store_path=str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    data["plan"]["schema_version"] = "1.1.0"
    _rewrite(path, data)
    with pytest.raises(EpisodeIntegrityError):
        load(str(path))


# --- G2: a plan/model mismatch is never verified, logged or swallowed ----------------------------


def test_runner_refuses_a_plan_model_mismatch(tmp_path, monkeypatch):
    model, other = s.model("default_1.0.0"), s.model("variants/declarer_changed")
    real_plan = planner.plan
    monkeypatch.setattr(planner, "plan", lambda di, _m, **kw: real_plan(di, other, **kw))
    with pytest.raises(ShopIdentityMismatchError):
        _run(tmp_path, model)
    assert not (tmp_path / "episodes.jsonl").exists()


# --- G5: schedules ------------------------------------------------------------------------------


def _requests():
    return [
        schedule_runner._request_from_json(support.load_json(f"rm11_jobs/{p.name}"), False)
        for p in JOBS
    ]


def test_schedule_carries_the_declared_identity_and_checks_clean():
    model = s.model("default_1.0.0")
    outcome = schedule_requests(_requests(), capability_model=model, produced_at=T)
    schedule = outcome.schedule
    assert schedule is not None and schedule.shop_model_ref == capability_model_ref_for(model)
    other = schedule_requests(
        _requests(), capability_model=s.model("variants/declarer_changed"), produced_at=T
    ).schedule
    assert other.schedule_input_identity != schedule.schedule_input_identity
    assert other.makespan_min == schedule.makespan_min


def _jobs(model):
    jobs = []
    for request in _requests():
        task, plan = planner.plan(intake(request, produced_at=T), model, produced_at=T)
        jobs.append(SchedulingJob(request.request_id, task.task_id, plan))
    return jobs


@pytest.mark.parametrize("case", ["schedule_ref_missing", "job_ref_different", "mixed"])
def test_checker_refuses_any_shop_identity_mismatch(case):
    model, other = s.model("default_1.0.0"), s.model("variants/declarer_changed")
    ref = capability_model_ref_for(model)
    schedule = schedule_requests(_requests(), capability_model=model, produced_at=T).schedule
    jobs = _jobs(model)
    if case == "schedule_ref_missing":
        schedule = dataclasses.replace(schedule, shop_model_ref=None)
    elif case == "job_ref_different":
        jobs[0] = SchedulingJob(jobs[0].request_id, jobs[0].task_id, _jobs(other)[0].plan)
    else:
        jobs[1] = SchedulingJob(
            jobs[1].request_id, jobs[1].task_id, _jobs(cm.default_model())[1].plan
        )
    issues = schedule_issues(schedule, jobs, model.version, shop_model_ref=ref)
    assert IssueCode.METADATA_MISMATCH in {i.code for i in issues}, case


# --- §3.8 verdict trace (T12.x) -----------------------------------------------------------------


def test_trace_of_a_fresh_run_links_every_artifact_and_is_stable(tmp_path):
    model = s.model("default_1.0.0")
    result = _run(tmp_path, model)
    trace = trace_run(result, model)
    assert trace.record == TraceRecord.EPISODE
    assert trace.plan_ref.content_hash == result.plan.content_hash
    assert trace.episode_ref.content_hash == result.episode.content_hash
    assert (
        trace.shop_ref == capability_model_ref_for(model)
        and str(trace.shop_ref.evidence_class) == "synthetic"
    )
    other = tmp_path / "again"
    other.mkdir()
    assert trace_run(_run(other, model), model).trace_hash == trace.trace_hash


def test_trace_of_reuse_hit_and_miss(tmp_path):
    model = s.model("default_1.0.0")
    store = str(tmp_path / "episodes.jsonl")
    miss = run_with_reuse(s.bracket(), capability_model=model, produced_at=T, store_path=store)
    hit = run_with_reuse(s.bracket(), capability_model=model, produced_at=T, store_path=store)
    assert hit.reused and trace_run(miss, model).trace_hash == trace_run(hit, model).trace_hash


def test_trace_of_an_infra_error_names_the_attempted_shop(tmp_path):
    model = s.model("default_1.0.0")

    class Broken:
        def verify(self, plan, capability_model):
            raise RuntimeError("verifier down")

    result = runner.run(
        intake(s.bracket(), produced_at=T),
        capability_model=model,
        oracle=Broken(),
        produced_at=T,
        store_path=str(tmp_path / "e.jsonl"),
    )
    trace = trace_run(result, model)
    assert result.status == "INFRA_ERROR" and trace.record == TraceRecord.NONE_INFRA_ERROR
    assert trace.plan_ref is None and trace.episode_ref is None
    assert trace.shop_ref == capability_model_ref_for(model)


def test_trace_of_a_scheduling_job_has_no_episode_by_design():
    model = s.model("default_1.0.0")
    plan = _jobs(model)[0].plan
    verdict = ManufacturabilityOracle().verify(plan, model)
    trace = trace_job(plan, verdict, model)
    assert trace.record == TraceRecord.SCHEDULE_READ_ONLY and trace.episode_ref is None
    with pytest.raises(VerdictTraceError):
        trace_job(plan, verdict, s.model("variants/declarer_changed"))


def test_scheduling_refusals_carry_the_trace_for_declared_shops():
    raw = support.load_json("rm11_jobs/job_a.json")
    raw["material"] = "titanium"
    outcome = schedule_requests(
        [schedule_runner._request_from_json(raw, False)],
        capability_model=s.model("default_1.0.0"),
        produced_at=T,
    )
    [refusal] = [r for r in outcome.refusals if str(r.reason) == "JOB_NOT_MANUFACTURABLE"]
    assert (
        "shop sha256:" in refusal.detail and "no episode: scheduling is read-only" in refusal.detail
    )
    legacy = schedule_requests([schedule_runner._request_from_json(raw, False)], produced_at=T)
    assert all("shop sha256:" not in r.detail for r in legacy.refusals)


@pytest.mark.parametrize("break_it", ["verdict", "plan", "model", "source"])
def test_trace_refuses_inconsistent_artifacts(tmp_path, break_it):
    model = s.model("default_1.0.0")
    store = str(tmp_path / "episodes.jsonl")
    run_with_reuse(s.bracket(), capability_model=model, produced_at=T, store_path=store)
    result = run_with_reuse(s.bracket(), capability_model=model, produced_at=T, store_path=store)
    if break_it == "verdict":
        result = dataclasses.replace(
            result, verdict=dataclasses.replace(result.verdict, status="PLAN_INVALID")
        )
    elif break_it == "plan":
        result = dataclasses.replace(
            result, plan=dataclasses.replace(result.plan, content_hash="sha256:" + "2" * 64)
        )
    elif break_it == "source":
        result = dataclasses.replace(
            result,
            source_episode=dataclasses.replace(
                result.source_episode, content_hash="sha256:" + "3" * 64
            ),
        )
    target = s.model("variants/declarer_changed") if break_it == "model" else model
    with pytest.raises(VerdictTraceError):
        trace_run(result, target)


# --- CLIs (T5.2, T6.1, T12.6) -------------------------------------------------------------------


def _cli(main, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def test_runner_cli_prints_a_trace_line_for_a_declared_shop(tmp_path, monkeypatch):
    store = tmp_path / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    request = tmp_path / "request.json"
    request.write_text(json.dumps(s.bracket_json()), encoding="utf-8")
    code, out, _ = _cli(
        runner._main, [str(request), "--capability-model-file", str(s.SHOP / "default_1.0.0.json")]
    )
    line = out.splitlines()[0]
    assert code == 0 and line.startswith("MANUFACTURABLE [] plan sha256:")
    assert '"RM1 default model (synthetic mirror)"' in line and "(synthetic, declared by" in line
    assert "not independently verified" in line and " trace sha256:" in line
    assert "verified" not in line.replace("not independently verified", "")
    assert "validated" not in out


def test_runner_cli_without_the_flag_is_unchanged(tmp_path, monkeypatch):
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", tmp_path / "episodes.jsonl")
    request = tmp_path / "request.json"
    request.write_text(json.dumps(s.bracket_json()), encoding="utf-8")
    code, out, _ = _cli(runner._main, [str(request)])
    assert code == 0 and out == f"MANUFACTURABLE episode -> {tmp_path / 'episodes.jsonl'}\n"


@pytest.mark.parametrize("main_name", ["runner", "schedule_runner"])
def test_cli_invalid_shop_file_exits_2_writes_nothing_and_never_falls_back(
    tmp_path, monkeypatch, main_name
):
    store = tmp_path / "episodes.jsonl"
    monkeypatch.setattr(episode_store, "DEFAULT_STORE", store)
    calls = []
    monkeypatch.setattr(cm, "default_model", lambda: calls.append("default") or None)
    module = runner if main_name == "runner" else schedule_runner
    monkeypatch.setattr(module, "default_model", lambda: calls.append("default") or None)
    request = tmp_path / "request.json"
    request.write_text(json.dumps(s.bracket_json()), encoding="utf-8")
    bad = s.INVALID / "PRECEDENCE_CYCLE.json"
    code, out, err = _cli(module._main, [str(request), "--capability-model-file", str(bad)])
    assert code == 2 and out == "" and "PRECEDENCE_CYCLE /ordering_constraints" in err
    assert not store.exists() and calls == []
    code, _, err = _cli(
        module._main, [str(request), "--capability-model-file", str(tmp_path / "nope.json")]
    )
    assert code == 2 and "cannot read shop capability model" in err and calls == []


def test_cli_flags_are_mutually_exclusive(tmp_path):
    code, _, err = _cli(
        runner._main,
        ["r.json", "--capability-model", "constrained", "--capability-model-file", "x.json"],
    )
    assert code == 2 and "not allowed with" in err


def test_schedule_cli_prints_the_shop_line(tmp_path):
    code, out, _ = _cli(
        schedule_runner._main,
        [*map(str, JOBS), "--capability-model-file", str(s.SHOP / "default_1.0.0.json")],
    )
    assert code == 0 and out.splitlines()[-1].startswith('shop model "RM1 default model')
    assert out.splitlines()[-1].endswith("not independently verified)")
    code, legacy, _ = _cli(schedule_runner._main, [*map(str, JOBS)])
    assert code == 0 and "shop model" not in legacy
    assert out.startswith("SCHEDULED:") and legacy.startswith("SCHEDULED:")
