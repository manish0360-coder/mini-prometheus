"""RM10 zero-diff gate (O) — requests that declare no duration behave byte-identically to rm9-complete.

Complements the RM8 golden (default model and R*, generated from rm5-complete): this golden covers the
RM8 ECR and RM9 availability paths. It was generated ONCE from rm9-complete by
tests/rm10_rm9_baseline_probe.py and is frozen here by digest, together with the probe's digest. This test
only READS it; nothing regenerates it from the current implementation.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import rm10_rm9_baseline_probe as probe
import support

GOLDEN_PATH = support.FIXTURES / "rm10_rm9_baseline_golden.json"
GOLDEN_SHA256 = "ad29d84678e76f6a275876da16a90df44d6337bd84525be19290597c17eb7646"
PROBE_SHA256 = "966a9e1106374207fd21260d41902e7b9392d553f595490ea0c7c3903ac5ab2f"
RM9_COMPLETE = "6ca4d225c24eaedd222d520685471ad45e3783d7"


def _lf_sha256(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_golden_is_the_frozen_rm9_complete_baseline():
    assert _lf_sha256(GOLDEN_PATH) == GOLDEN_SHA256, "the frozen golden was modified"
    assert _golden()["generated_from"] == {"tag": "rm9-complete", "commit": RM9_COMPLETE}


def test_probe_is_the_one_that_generated_the_golden():
    assert _lf_sha256(probe.__file__) == PROBE_SHA256 == _golden()["probe_sha256"], "the probe was modified"


def test_no_duration_requests_are_byte_identical_to_rm9():
    expected, actual = _golden()["fingerprint"], probe.fingerprint()
    for exp, act in zip(expected["rows"], actual["rows"], strict=True):
        assert act == exp, f"{exp['case']}: behavior differs from rm9-complete: expected {exp}, got {act}"
    assert actual == expected
