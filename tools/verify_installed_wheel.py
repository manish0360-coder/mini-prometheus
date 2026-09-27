"""Packaging-integrity check (ADR-0014): the installed wheel must work outside the repository.

Builds the wheel from the repository, inspects its contents, installs it into a clean virtual
environment and, from a neutral working directory with no repository path on ``sys.path``:
- runs the RM10 single-job CLI on the engineer fixture (lead time 108 min);
- runs the RM10 CLI on a request that violates the frozen schema (schema validation must execute
  from the installed contracts tree and reject it);
- runs the RM11 scheduling CLI on the three-job fixture (makespan 68) and requires its schedule
  digest to equal the digest produced from the repository source.

Run from the repository root inside the Docker verifier (Python 3.11). Needs network access for
the isolated build backend and the runtime dependency. Exit code 0 = every check passed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "mini-prometheus-runtime"
FIXTURES = ROOT / "tests" / "fixtures"
JOBS = [FIXTURES / "rm11_jobs" / f"job_{name}.json" for name in ("b", "a", "c")]
failures: list[str] = []


def check(ok: bool, label: str) -> None:
    print(("PASS  " if ok else "FAIL  ") + label)
    if not ok:
        failures.append(label)


def run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kwargs)


def repo_files(folder: str) -> dict[str, bytes]:
    base = ROOT / folder
    return {
        p.relative_to(base).as_posix(): p.read_bytes()
        for p in base.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def wheel_files(wheel: zipfile.ZipFile, prefix: str) -> dict[str, bytes]:
    return {n[len(prefix) :]: wheel.read(n) for n in wheel.namelist() if n.startswith(prefix)}


def digest(stdout: str) -> str | None:
    lines = [line for line in stdout.splitlines() if line.startswith("schedule digest: ")]
    return lines[0] if lines else None


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        build = run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                str(ROOT),
                "--no-deps",
                "-q",
                "-w",
                str(tmp / "dist"),
            ]
        )
        wheels = sorted((tmp / "dist").glob("*.whl"))
        check(build.returncode == 0 and len(wheels) == 1, "the wheel builds")
        if failures:
            print(build.stderr)
            return 1

        with zipfile.ZipFile(wheels[0]) as wheel:
            names = wheel.namelist()
            check(
                wheel_files(wheel, f"{RUNTIME}/contracts/") == repo_files("contracts"),
                "the wheel carries the whole contracts tree, byte-identical",
            )
            check(
                wheel_files(wheel, f"{RUNTIME}/src/mini_prometheus/")
                == repo_files("src/mini_prometheus"),
                "the wheel carries every mini_prometheus source file, byte-identical",
            )
            pth = (
                wheel.read("mini_prometheus.pth").decode().split()
                if "mini_prometheus.pth" in names
                else []
            )
            check(
                pth == [f"{RUNTIME}/src", RUNTIME],
                "mini_prometheus.pth puts both roots on sys.path",
            )
            check(
                not any(n.startswith(("mini_prometheus/", "contracts/")) for n in names),
                "nothing is installed at the top level besides the runtime tree and the .pth",
            )

        venv.create(tmp / "venv", with_pip=True)
        python = str(tmp / "venv" / ("Scripts" if os.name == "nt" else "bin") / "python")
        install = run([python, "-m", "pip", "install", "-q", str(wheels[0])])
        check(install.returncode == 0, "the wheel installs into a clean virtual environment")
        neutral = tmp / "neutral"
        neutral.mkdir()
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}

        where = run(
            [
                python,
                "-c",
                "import mini_prometheus, contracts.python, mini_prometheus._validate as v;"
                "print(mini_prometheus.__file__); print(v._SCHEMAS); print(v._SCHEMAS.is_dir())",
            ],
            cwd=neutral,
            env=env,
        )
        located = where.stdout.splitlines()
        check(
            where.returncode == 0
            and len(located) == 3
            and RUNTIME in located[0]
            and str(ROOT) not in where.stdout
            and located[2] == "True",
            "the installed package and its contracts are imported (not the repository)",
        )

        rm10 = run(
            [
                python,
                "-m",
                "mini_prometheus.orchestration.runner",
                str(FIXTURES / "engineer_request_with_durations.json"),
            ],
            cwd=neutral,
            env=env,
        )
        check(
            rm10.returncode == 0
            and "lead time: 108 min (single-job serialized timeline)" in rm10.stdout,
            "RM10 CLI runs from the installed package",
        )

        bad = json.loads(
            (FIXTURES / "engineer_request_with_durations.json").read_text(encoding="utf-8")
        )
        bad["schema_version"] = "not-a-semver"
        (tmp / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
        rejected = run(
            [python, "-m", "mini_prometheus.orchestration.runner", str(tmp / "bad.json")],
            cwd=neutral,
            env=env,
        )
        check(
            rejected.returncode != 0
            and "manufacturing_request violates contract at ['schema_version']" in rejected.stderr,
            "schema validation executes through the RM10 CLI (invalid request rejected)",
        )

        rm11 = run(
            [python, "-m", "mini_prometheus.orchestration.schedule_runner", *map(str, JOBS)],
            cwd=neutral,
            env=env,
        )
        check(
            rm11.returncode == 0 and "makespan: 68 min" in rm11.stdout,
            "RM11 scheduling CLI runs from the installed package",
        )
        source_env = {**env, "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), str(ROOT)])}
        reference = run(
            [
                sys.executable,
                "-m",
                "mini_prometheus.orchestration.schedule_runner",
                *map(str, reversed(JOBS)),
            ],
            cwd=ROOT,
            env=source_env,
        )
        check(
            digest(rm11.stdout) is not None and digest(rm11.stdout) == digest(reference.stdout),
            "the installed RM11 schedule digest equals the repository-source digest",
        )
        check(list(neutral.iterdir()) == [], "nothing is written to the working directory")

    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
