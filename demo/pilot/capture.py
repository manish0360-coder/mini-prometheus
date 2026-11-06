#!/usr/bin/env python3
"""Capture REAL Mini Prometheus MP-S1 CLI output for the shop-owner pilot demonstrator (ADR-0023).

Orchestration only: it contains no manufacturing logic. For each synthetic job it calls the shipped
single-job CLI entry point,

    python -m mini_prometheus.orchestration.runner <job.json> --capability-model-file <shop.json>

in-process (``runner._main``), with the episode store redirected to a temporary file so that nothing
is written to the repository. It records:
- the CLI's stdout verbatim, with only the temporary store path redacted;
- the plan steps and verdict copied from the episode the CLI stored;
- SHA-256 of every input and output;
- the exact command.

The page (``index.html``) only displays ``snapshots/data.js``. It never computes a verdict.
``tests/boundary/test_demo_pilot.py`` re-runs this script and requires the committed snapshots to be
reproduced byte for byte.

Usage (from the repository root, Python 3.11, as in the Docker verifier):
    python demo/pilot/capture.py --commit <mini-prometheus commit the snapshots are captured at>
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PILOT = pathlib.Path("demo/pilot")
SHOP = PILOT / "inputs" / "shop.example_workshop.json"
CASES = (  # (case id, synthetic job file) in display order
    ("bracket", PILOT / "inputs" / "job_bracket.json"),
    ("turned_shaft", PILOT / "inputs" / "job_turned_shaft.json"),
    ("brass_cover", PILOT / "inputs" / "job_brass_cover.json"),
    ("precision_plate", PILOT / "inputs" / "job_precision_plate.json"),
)
REDACTED_STORE = "<temporary episode store>"
HASH = r"sha256:[0-9a-f]{64}"
TRACE = re.compile(
    rf"^(?P<status>[A-Z_]+) \[(?P<reasons>[^\]]*)\] plan (?P<plan>{HASH}) "
    rf"episode (?P<episode>{HASH}) "
    rf"shop model .* (?P<declaration>{HASH}) \(.*\) trace (?P<trace>{HASH}) -> (?P<path>.+)$"
)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dump(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def command_for(job: pathlib.Path) -> str:
    return (
        f"python -m mini_prometheus.orchestration.runner {job.as_posix()} "
        f"--capability-model-file {SHOP.as_posix()}"
    )


def run_case(job: pathlib.Path) -> tuple[int, str, dict]:
    """Run the shipped CLI once; return (exit code, redacted stdout, stored episode)."""
    from mini_prometheus.orchestration import episode_store, runner

    with tempfile.TemporaryDirectory() as tmp:
        store = pathlib.Path(tmp) / "episodes.jsonl"
        original = episode_store.DEFAULT_STORE
        episode_store.DEFAULT_STORE = store
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                code = runner._main([str(ROOT / job), "--capability-model-file", str(ROOT / SHOP)])
        finally:
            episode_store.DEFAULT_STORE = original
        lines = store.read_text(encoding="utf-8").splitlines() if store.exists() else []
        episode = json.loads(lines[-1]) if lines else {}
        return code, out.getvalue().replace(str(store), REDACTED_STORE), episode


def steps_from(episode: dict) -> list[dict]:
    """Copy the plan steps and machine assignments exactly as the CLI stored them."""
    plan = episode.get("plan", {})
    assigned = {a["step_index"]: a["resource_id"] for a in plan.get("resource_assignments", [])}
    return [
        {
            "index": s["index"],
            "op": s["op"],
            "required_capability": s["required_capability"],
            "resource_id": assigned.get(s["index"]),
        }
        for s in plan.get("steps", [])
    ]


def capture(out_dir: pathlib.Path, commit: str) -> dict:
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from mini_prometheus.orchestration.shop_model_file import read_shop_model

    out_dir.mkdir(parents=True, exist_ok=True)
    shop_model = read_shop_model(ROOT / SHOP)  # the real MP-S1 loader; it refuses invalid files
    assert shop_model.source is not None
    shop = {
        "path": SHOP.as_posix(),
        "sha256": sha256_file(ROOT / SHOP),
        "document": json.loads((ROOT / SHOP).read_text(encoding="utf-8")),
        "shop_content_hash": shop_model.source.shop_content_hash,
        "shop_declaration_hash": shop_model.source.shop_declaration_hash,
        "evidence_class": shop_model.source.evidence_class,
    }
    cases, manifest_cases = [], []
    for case_id, job in CASES:
        code, stdout, episode = run_case(job)
        match = TRACE.match(stdout.splitlines()[0]) if stdout else None
        if code != 0 or match is None:
            raise SystemExit(f"capture failed for {case_id}: exit {code}, stdout {stdout!r}")
        stdout_name, plan_name = f"case.{case_id}.stdout.txt", f"case.{case_id}.plan.json"
        plan_record = {
            "plan_content_hash": episode["plan"]["content_hash"],
            "steps": steps_from(episode),
            "verdict": {
                "status": episode["verdict"]["status"],
                "reason_codes": episode["verdict"]["reason_codes"],
            },
        }
        (out_dir / stdout_name).write_text(stdout, encoding="utf-8", newline="\n")
        (out_dir / plan_name).write_text(dump(plan_record), encoding="utf-8", newline="\n")
        reasons = [r for r in match["reasons"].split(", ") if r]
        record = {
            "id": case_id,
            "job_path": job.as_posix(),
            "job_sha256": sha256_file(ROOT / job),
            "command": command_for(job),
            "exit_code": code,
            "stdout_path": (PILOT / "snapshots" / stdout_name).as_posix(),
            "stdout_sha256": sha256_text(stdout),
            "plan_path": (PILOT / "snapshots" / plan_name).as_posix(),
            "plan_sha256": sha256_text(dump(plan_record)),
            "status": match["status"],
            "reason_codes": reasons,
            "plan_hash": match["plan"],
            "episode_hash": match["episode"],
            "shop_declaration_hash": match["declaration"],
            "trace_hash": match["trace"],
        }
        manifest_cases.append(record)
        cases.append({
            **record,
            "request": json.loads((ROOT / job).read_text(encoding="utf-8")),
            "stdout": stdout,
            "steps": plan_record["steps"],
        })
    meta = {
        "adr": "ADR-0023",
        "generator": "demo/pilot/capture.py",
        "mp_commit": commit,
        "evidence": "synthetic example data; verdicts are actual MP-S1 CLI output on it",
    }
    payload = dump({"meta": meta, "shop": shop, "cases": cases})[:-1]
    data_js = "window.MP_PILOT_DATA = " + payload + ";\n"
    (out_dir / "data.js").write_text(data_js, encoding="utf-8", newline="\n")
    manifest = {
        **meta,
        "generator_sha256": sha256_file(ROOT / PILOT / "capture.py"),
        "python": ".".join(map(str, sys.version_info[:3])),
        "episode_store": "redirected to a temporary file per case; path redacted as "
        + REDACTED_STORE,
        "shop": {k: v for k, v in shop.items() if k != "document"},
        "cases": manifest_cases,
        "data_js_sha256": sha256_text(data_js),
    }
    (out_dir / "MANIFEST.json").write_text(dump(manifest), encoding="utf-8", newline="\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture real MP-S1 CLI output for demo/pilot")
    parser.add_argument("--commit", required=True, help="mini-prometheus commit being captured")
    parser.add_argument("--out", default=str(ROOT / PILOT / "snapshots"), help="output directory")
    args = parser.parse_args()
    manifest = capture(pathlib.Path(args.out), args.commit)
    for case in manifest["cases"]:
        print(f"{case['id']}: {case['status']} {case['reason_codes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
