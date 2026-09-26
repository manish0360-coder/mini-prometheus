"""RM8 behavioral zero-diff probe — a fingerprint of the default-model manufacturing behavior.

READ-ONLY. This module only COMPUTES a fingerprint; it never writes one. The frozen golden
(``tests/fixtures/rm8_default_behavior_golden.json``) was generated ONCE by running this exact file
against the ``rm5-complete`` tree (commit ``96eb81f``) inside the project verifier image, and is frozen
by digest in ``tests/unit/test_rm8_default_zero_diff.py``. The golden is never regenerated from the
current implementation: the zero-diff test only reads it and compares.

What is fingerprinted (all time-independent):
- the library path ``intake -> plan -> verify -> build_episode`` (fixed timestamps) for the engineer
  fixture plus every RM5 generator request, under ``default_model()`` and the RM5 regime R*: the FULL
  serialized plan, the full verdict, the full episode, and their content hashes;
- the legacy CLI (``runner._main``) on two request JSONs, one with a tolerance far tighter than any
  machine and a declared order that ECR would reject: under the default model both must stay exactly as
  RM1 left them (the legacy CLI does not read ``tolerances``);
- a digest of the whole ``contracts/`` tree (schemas, generated bindings, VERSION).
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib
import tempfile

import support
from mini_prometheus import _hashing as h
from mini_prometheus.experiment import corpus
from mini_prometheus.intake.request_intake import intake
from mini_prometheus.manufacturing_constraints.capability_model import default_model
from mini_prometheus.manufacturing_constraints.oracle import ManufacturabilityOracle
from mini_prometheus.manufacturing_planning import planner
from mini_prometheus.orchestration import episode_store, runner
from mini_prometheus.orchestration.episode_store import build_episode

FIXED_TIME = "2026-07-23T00:00:00+00:00"
ROOT = pathlib.Path(__file__).resolve().parents[1]


def _sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _library_rows() -> list[dict]:
    requests = [("engineer_fixture",
                 support.build_request(support.load_json("engineer_request_machined_bracket.json")))]
    requests += [(f"rm5_{i:03d}", r) for i, r in enumerate(corpus._requests())]
    models = [("default", default_model()), ("r_star", corpus.r_star())]
    oracle = ManufacturabilityOracle()
    rows = []
    for name, request in requests:
        for model_name, model in models:
            design_input = intake(request, produced_at=FIXED_TIME)
            task, plan = planner.plan(design_input, model, produced_at=FIXED_TIME)
            verdict = oracle.verify(plan, model)
            episode = build_episode(task, design_input, plan, verdict, model.version,
                                    produced_at=FIXED_TIME, plan_ms=0.0, verify_ms=0.0)
            rows.append({
                "case": name, "model": model_name,
                "plan_content_hash": plan.content_hash, "plan_full": _sha(h.to_contract_dict(plan)),
                "verdict": h.to_contract_dict(verdict),
                "episode_content_hash": episode.content_hash,
                "episode_full": _sha(h.to_contract_dict(episode)),
            })
    return rows


def _cli_inputs() -> list[tuple[str, dict]]:
    base = support.load_json("engineer_request_machined_bracket.json")
    tight_and_misordered = json.loads(json.dumps(base))
    tight_and_misordered["tolerances"] = {"general_tolerance_mm": 0.001}
    ops = tight_and_misordered["declared_operations"]
    tight_and_misordered["declared_operations"] = [ops[-1], *ops[:-1]]      # inspect first
    return [("engineer_fixture", base), ("tight_and_misordered", tight_and_misordered)]


def _cli_rows() -> list[dict]:
    rows = []
    saved = episode_store.DEFAULT_STORE
    with tempfile.TemporaryDirectory() as tmp:
        try:
            for name, raw in _cli_inputs():
                store = pathlib.Path(tmp) / f"{name}.jsonl"
                episode_store.DEFAULT_STORE = store
                request_path = pathlib.Path(tmp) / f"{name}.json"
                request_path.write_text(json.dumps(raw), encoding="utf-8")
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = runner._main([str(request_path)])
                episode = json.loads(store.read_text(encoding="utf-8").splitlines()[-1])
                rows.append({
                    "case": name, "exit_code": code, "stdout_status": out.getvalue().split(" ")[0],
                    "episode_content_hash": episode["content_hash"],
                    "plan_content_hash": episode["plan"]["content_hash"],
                    "verdict": episode["verdict"],
                })
        finally:
            episode_store.DEFAULT_STORE = saved
    return rows


def _contracts_digest() -> str:
    files = sorted(p for p in (ROOT / "contracts").rglob("*")
                   if p.is_file() and "__pycache__" not in p.parts)
    crlf, lf = b"\r\n", b"\n"                       # LF-normalized: identical on any checkout
    lines = []
    for p in files:
        digest = hashlib.sha256(p.read_bytes().replace(crlf, lf)).hexdigest()
        lines.append(f"{digest}  {p.relative_to(ROOT).as_posix()}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def fingerprint() -> dict:
    library = _library_rows()
    cli = _cli_rows()
    return {
        "library": {"n": len(library), "digest": _sha(library), "rows": library},
        "cli_default": {"n": len(cli), "digest": _sha(cli), "rows": cli},
        "contracts_digest": _contracts_digest(),
    }
