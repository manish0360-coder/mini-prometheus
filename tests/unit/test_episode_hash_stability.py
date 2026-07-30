"""Hash-stability verification: ManufacturingEpisode.content_hash excludes design_input (RM1 1.1.0).

Proves that embedding `design_input` does not change the episode `content_hash` — i.e. an episode with
identical engineering content produces the same hash whether or not `design_input` is embedded. The
identity builder under test is `mini_prometheus._hashing.episode_identity` (a curated allow-list that
never references `design_input`). `schema_version` is held constant so the sole difference is
`design_input`, isolating the field whose exclusion is being verified.
"""
from __future__ import annotations

import dataclasses

from mini_prometheus import _hashing as h
from mini_prometheus.orchestration import runner

from support import FIXED_TIME


def test_content_hash_excludes_design_input(engineer_request, store_path):
    # A real new (schema_version 1.1.0) episode that embeds the full DesignInput.
    with_di = runner.run_from_request(
        engineer_request, produced_at=FIXED_TIME, store_path=store_path
    ).episode
    assert with_di.design_input is not None

    # The same episode with identical engineering content but WITHOUT the embedded design_input
    # (only design_input differs; schema_version and every other identity field are unchanged).
    without_di = dataclasses.replace(with_di, design_input=None)

    # episode_identity never references design_input, so the two must hash identically ...
    assert h.content_hash(h.episode_identity(with_di)) == h.content_hash(h.episode_identity(without_di))
    # ... and both equal the content_hash the emitter stored on the design_input-bearing episode.
    assert with_di.content_hash == h.content_hash(h.episode_identity(without_di))
