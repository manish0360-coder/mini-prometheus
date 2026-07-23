"""Unit tests for the canonical-hash / identity mechanisms (contract package §1)."""
from __future__ import annotations

import uuid

from mini_prometheus import _hashing as h


def test_canonical_json_is_sorted_and_compact():
    assert h.canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_content_hash_is_deterministic_and_prefixed():
    a = h.content_hash({"x": 1})
    b = h.content_hash({"x": 1})
    assert a == b
    assert a.startswith("sha256:") and len(a) == len("sha256:") + 64


def test_derive_uuid_is_deterministic_and_valid():
    ch = h.content_hash({"x": 1})
    u1 = h.derive_uuid(ch)
    u2 = h.derive_uuid(ch)
    assert u1 == u2
    assert uuid.UUID(u1).version == 5  # uuid5(NS_MP, ...)


def test_ns_mp_is_frozen_value():
    assert str(h.NS_MP) == "4f5b56ae-3c77-4135-9f5c-1eef0ab1b252"
