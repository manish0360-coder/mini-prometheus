"""RM12 zero-diff gate (A, K) — without relevant downtime RM12 is byte-identical to rm11-complete.

The golden was generated ONCE from rm11-complete by tests/rm12_rm11_baseline_probe.py and is frozen
here by digest, together with the probe's digest. This test only READS it; nothing regenerates it
from the current implementation. Every row pins the rule id/version, schedule_input_identity,
schedule_digest, the whole schedule view (placements, makespan, lower bound, gap), the refusals and
the CLI report.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import rm12_rm11_baseline_probe as probe
import support

GOLDEN_PATH = support.FIXTURES / "rm12_rm11_baseline_golden.json"
GOLDEN_SHA256 = "eaf3ed1b4737b96992759a41470504377d1d51d03fd4be6c2bb6647e55b67b0e"
PROBE_SHA256 = "b964d5cf23abbdf661eb1609a813ac71561a5af94190bda9221351b7c48d7e37"
RM11_COMPLETE = "40d6066fbcbb6a9834a0db6bf5d12e9cd4b1b24a"


def _lf_sha256(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _assert_rows_equal(expected: dict, actual: dict) -> None:
    for exp, act in zip(expected["rows"], actual["rows"], strict=True):
        assert act == exp, f"{exp['case']}: differs from rm11-complete"
    assert actual == expected


def test_golden_is_the_frozen_rm11_complete_baseline():
    assert _lf_sha256(GOLDEN_PATH) == GOLDEN_SHA256, "the frozen golden was modified"
    assert _golden()["generated_from"] == {"tag": "rm11-complete", "commit": RM11_COMPLETE}


def test_probe_is_the_one_that_generated_the_golden():
    assert _lf_sha256(probe.__file__) == PROBE_SHA256 == _golden()["probe_sha256"]


def test_A_no_downtime_is_byte_identical_to_rm11():
    _assert_rows_equal(_golden()["fingerprint"], probe.fingerprint())


def test_K_downtime_on_unused_machines_is_byte_identical_to_rm11():
    machines = {row["case"]: set(row["machines"]) for row in _golden()["fingerprint"]["rows"]}
    received = []

    def irrelevant(case, model, requests):
        unused = sorted(set(model.resources) - machines[case])
        if not unused:
            return {}
        received.append(case)
        # overlapping, touching and unsorted on purpose: still irrelevant after canonicalization
        spans = [(500, 900), (0, 60), (60, 120), (100, 200)]
        return {"downtime": {machine: spans for machine in unused}}

    _assert_rows_equal(_golden()["fingerprint"], probe.fingerprint(irrelevant))
    scheduled_with_downtime = [c for c in received if not c.startswith("refused")]
    assert len(scheduled_with_downtime) >= 6, received  # non-vacuous: real schedules received it
