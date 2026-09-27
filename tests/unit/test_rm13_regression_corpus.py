"""RM13_REGRESSION_CORPUS_01 — a synthetic algorithm-regression corpus (Director test 16).

"This is a synthetic algorithm-regression corpus. It is not representative evidence of factory
performance." It is NOT a production benchmark. The 135 instances were extracted once, unchanged,
from the RM12 adversarial audit; this test pins the fixture, its input and optimum digests,
RE-DERIVES every optimum with its own exhaustive search (so the ground truth is proven, not merely
pinned) and reproduces the frozen metrics of both rules through the production API.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import statistics
from fractions import Fraction

import rm11_support as s
import support
from mini_prometheus.orchestration.schedule_runner import schedule_requests

CORPUS_PATH = support.FIXTURES / "rm13_regression_corpus_01.json"
CORPUS_SHA256 = "cdafd164b785bfd717c2a51f08ea7ce1be46efd1510f42e1a7cd72895caff9a5"
INPUT_DIGEST = "d0d9927bd17ff180894622771f9a54fc5423acb288b4068bbde9d37b51e8182d"
OPTIMUM_DIGEST = "734f77185d98ab2e3f543bbdb6b25045eb379a0c562a6a5c0885ac08889ca741"
NOTE = (
    "This is a synthetic algorithm-regression corpus. "
    "It is not representative evidence of factory performance."
)
OP_MACHINE = {
    "cut_stock": "saw01",
    "face_mill": "mill01",
    "drill": "mill01",
    "pocket_mill": "mill01",
    "turn": "lathe01",
    "deburr": "bench01",
    "inspect": "cmm01",
}
BASELINE, MWKR = "earliest_start_v1", "earliest_start_v1_most_work_remaining"
EXPECTED = {
    BASELINE: {
        "optimal": 124,
        "contended_optimal": 42,
        "median_abs": 0,
        "max_abs": 32,
        "median_rel": Fraction(0),
        "max_rel": Fraction(32, 50),
        "misses": {
            7: 20,
            23: 3,
            32: 12,
            46: 9,
            56: 6,
            72: 3,
            76: 8,
            91: 10,
            101: 32,
            105: 18,
            115: 15,
        },
    },
    MWKR: {
        "optimal": 131,
        "contended_optimal": 49,
        "median_abs": 0,
        "max_abs": 32,
        "median_rel": Fraction(0),
        "max_rel": Fraction(32, 50),
        "misses": {72: 3, 91: 5, 101: 32, 130: 4},
    },
}


def _lf_sha256(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _digest(obj) -> str:
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode()).hexdigest()


def _corpus() -> dict:
    return json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


def _makespans(rule: str) -> dict[int, int]:
    spans = {}
    for case in _corpus()["cases"]:
        requests = [
            s.request(j["request_id"], [tuple(o) for o in j["operations"]]) for j in case["jobs"]
        ]
        outcome = schedule_requests(
            requests, produced_at=s.FIXED_TIME, downtime=case["downtime"], rule=rule
        )
        spans[case["case"]] = outcome.schedule.makespan_min
    return spans


def _brute_optimum(case: dict) -> int:
    """Exhaustive: min makespan over every dispatch sequence, minute-level earliest fit."""
    blocked = {
        m: {t for a, b in spans for t in range(a, b)} for m, spans in case["downtime"].items()
    }
    jobs = [[(OP_MACHINE[op], d) for op, d in j["operations"]] for j in case["jobs"]]
    tokens = [i for i, ops in enumerate(jobs) for _ in ops]
    best = None
    for sequence in set(itertools.permutations(tokens)):
        nxt, ready, free = [0] * len(jobs), [0] * len(jobs), {}
        for i in sequence:
            machine, duration = jobs[i][nxt[i]]
            start = max(ready[i], free.get(machine, 0))
            while any(t in blocked.get(machine, ()) for t in range(start, start + duration)):
                start += 1
            ready[i] = free[machine] = start + duration
            nxt[i] += 1
        best = max(ready) if best is None else min(best, max(ready))
    return best


def test_corpus_is_frozen_named_and_disclaimed():
    corpus = _corpus()
    assert _lf_sha256(CORPUS_PATH) == CORPUS_SHA256, "the frozen corpus was modified"
    assert corpus["name"] == "RM13_REGRESSION_CORPUS_01" and corpus["note"] == NOTE
    cases = corpus["cases"]
    assert [c["case"] for c in cases] == list(range(135))
    assert _digest([{k: c[k] for k in ("case", "jobs", "downtime")} for c in cases]) == INPUT_DIGEST
    assert (
        _digest([{k: c[k] for k in ("case", "optimum_makespan")} for c in cases]) == OPTIMUM_DIGEST
    )


def test_every_optimum_and_contention_flag_is_re_derived_independently():
    for case in _corpus()["cases"]:
        assert _brute_optimum(case) == case["optimum_makespan"], case["case"]
        machines = [{OP_MACHINE[op] for op, _d in j["operations"]} for j in case["jobs"]]
        shared = any(sum(m in used for used in machines) >= 2 for m in set().union(*machines))
        assert shared == case["contended"], case["case"]
    assert sum(c["contended"] for c in _corpus()["cases"]) == 53


def test_16_benchmark_metrics_reproduce_the_frozen_values():
    corpus = _corpus()
    optimum = {c["case"]: c["optimum_makespan"] for c in corpus["cases"]}
    contended = {c["case"] for c in corpus["cases"] if c["contended"]}
    spans = {rule: _makespans(rule) for rule in (BASELINE, MWKR)}
    for rule, expected in EXPECTED.items():
        gaps = {k: spans[rule][k] - optimum[k] for k in optimum}
        rels = [Fraction(g, optimum[k]) for k, g in gaps.items()]
        assert min(gaps.values()) >= 0, rule  # a schedule can never beat the exhaustive optimum
        measured = {
            "optimal": sum(g == 0 for g in gaps.values()),
            "contended_optimal": sum(gaps[k] == 0 for k in contended),
            "median_abs": statistics.median(gaps.values()),
            "max_abs": max(gaps.values()),
            "median_rel": statistics.median(rels),
            "max_rel": max(rels),
            "misses": {k: g for k, g in gaps.items() if g > 0},
        }
        assert measured == expected, rule
    base, new = spans[BASELINE], spans[MWKR]
    improved = sorted(k for k in optimum if new[k] < base[k])
    regressions = {k: (base[k], new[k]) for k in optimum if new[k] > base[k]}
    newly_optimal = sorted(k for k in optimum if new[k] == optimum[k] < base[k])
    failures = sorted(EXPECTED[BASELINE]["misses"])
    assert improved == [7, 23, 32, 46, 56, 76, 91, 105, 115]
    assert sum(new[k] == base[k] for k in optimum) == 125
    assert regressions == {130: (163, 167)}  # documented: baseline optimal, the new rule +4 min
    assert newly_optimal == [7, 23, 32, 46, 56, 76, 105, 115]  # 8 of the 11 failures repaired
    assert (base[91], new[91], optimum[91]) == (40, 35, 30)  # partially improved
    assert [k for k in failures if new[k] == base[k]] == [72, 101]  # unchanged
