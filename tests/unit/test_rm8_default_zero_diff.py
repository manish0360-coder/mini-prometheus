"""RM8 behavioral zero-diff gate — the default model must behave byte-identically to rm5-complete.

This replaces, for exactly the four files RM8 modifies, the CI byte-freeze of the RM1/RM2 core (ADR-0010):
what is protected is the BEHAVIOR (plans, verdicts, episodes and their hashes), not the source bytes.

The golden (tests/fixtures/rm8_default_behavior_golden.json) was generated ONCE from rm5-complete by
tests/rm8_behavior_probe.py and is frozen here by digest. This test only READS it; nothing in the suite
regenerates it from the current implementation. Any change to the golden, to the probe, or to the
default-model behavior fails this test.
"""
from __future__ import annotations

import hashlib
import json

import rm8_behavior_probe as probe
import support

GOLDEN_PATH = support.FIXTURES / "rm8_default_behavior_golden.json"
GOLDEN_SHA256 = "f36c5d4be10da83d8669c5036ecf36d607e699b3129e9075f14426ac606ffa02"
PROBE_SHA256 = "47a218c63e25060617a43d393163f9aedffafc7d960071dbdda495dd0f38bb4c"
RM5_COMPLETE = "96eb81f25c8a89d6a33a064c3c1e18c48b9d260f"


def _lf_sha256(path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _golden() -> dict:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def test_golden_is_the_frozen_rm5_complete_baseline():
    assert _lf_sha256(GOLDEN_PATH) == GOLDEN_SHA256, "the frozen golden was modified"
    golden = _golden()
    assert golden["generated_from"] == {"tag": "rm5-complete", "commit": RM5_COMPLETE}
    fp = golden["fingerprint"]
    assert fp["library"]["n"] == 902 and fp["cli_default"]["n"] == 2


def test_probe_is_the_one_that_generated_the_golden():
    import pathlib
    probe_path = pathlib.Path(probe.__file__)
    assert _lf_sha256(probe_path) == PROBE_SHA256 == _golden()["probe_sha256"], "the probe was modified"


def test_default_model_behavior_is_byte_identical_to_rm5_complete():
    expected = _golden()["fingerprint"]
    actual = probe.fingerprint()
    assert actual["contracts_digest"] == expected["contracts_digest"], "contracts/ changed"
    for section in ("library", "cli_default"):
        exp_rows, act_rows = expected[section]["rows"], actual[section]["rows"]
        assert len(act_rows) == len(exp_rows), f"{section}: case count changed"
        first = next((i for i, (a, b) in enumerate(zip(act_rows, exp_rows)) if a != b), None)
        assert first is None, (f"{section}: default-model behavior differs from rm5-complete at case "
                               f"{exp_rows[first]['case']}: expected {exp_rows[first]}, got {act_rows[first]}")
        assert actual[section]["digest"] == expected[section]["digest"]
    assert actual == expected
