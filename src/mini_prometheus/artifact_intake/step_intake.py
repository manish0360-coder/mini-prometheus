"""Real STEP-file intake: bytes on disk -> a byte-grounded, opaque ``StepArtifactRef`` (RDAI-1 C1).

Fail-closed and deterministic. The ``content_hash`` is computed over the RAW bytes (encoding-independent);
only the *structural* check requires UTF-8-decodable text (documented RDAI-1 assumption — NOT full STEP
parsing). No geometry, entities, topology, or manufacturability are examined.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

from mini_prometheus import _hashing as h
from mini_prometheus._contracts import StepArtifactRef

_STEP_MEDIA_TYPE: Literal["model/step"] = "model/step"
_ISO_START = "ISO-10303-21;"
_ISO_END = "END-ISO-10303-21;"


class UnsupportedArtifactError(ValueError):
    """The artifact is not an ingestible ISO-10303-21 container (fail-closed; no partial result)."""


def _structural_container_check(text: str) -> None:
    """Basic ISO-10303-21 CONTAINER validation: the six container markers must all be present in the
    strict order ``ISO-10303-21;`` < ``HEADER;`` < first ``ENDSEC;`` < ``DATA;`` < second ``ENDSEC;`` <
    ``END-ISO-10303-21;``.

    This verifies the file is a structurally sound STEP container only. It does NOT validate HEADER/DATA
    entity grammar, the STEP schema, geometry, topology, or manufacturability.
    """
    stripped = text.strip()
    if not stripped.startswith(_ISO_START) or not stripped.endswith(_ISO_END):
        raise UnsupportedArtifactError("not an ISO-10303-21 container")
    i_start = text.find(_ISO_START)
    i_header = text.find("HEADER;")
    i_endsec1 = text.find("ENDSEC;")                                   # first ENDSEC (closes HEADER)
    i_data = text.find("DATA;")
    i_endsec2 = text.find("ENDSEC;", i_data + 1) if i_data != -1 else -1  # second ENDSEC (closes DATA)
    i_end = text.rfind(_ISO_END)
    order = [i_start, i_header, i_endsec1, i_data, i_endsec2, i_end]
    # All present (>= 0), strictly increasing (distinct + non-decreasing) => correct container ordering.
    if any(i < 0 for i in order) or len(set(order)) != len(order) or order != sorted(order):
        raise UnsupportedArtifactError("malformed STEP container structure")


def ingest(path: str | Path) -> StepArtifactRef:
    """Ingest a real STEP file into a byte-grounded opaque ``StepArtifactRef``.

    Raises ``UnsupportedArtifactError`` (fail-closed) on an unreadable/empty file, non-UTF-8 text,
    disallowed control characters, or a structurally invalid ISO-10303-21 container. On success returns
    ``StepArtifactRef(media_type="model/step", id=uuid5(NS_MP, content_hash), content_hash=sha256(bytes))``.
    """
    p = Path(path)
    try:
        raw = p.read_bytes()
    except OSError as exc:
        raise UnsupportedArtifactError(f"unreadable: {exc}") from exc
    if not raw:
        raise UnsupportedArtifactError("empty")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnsupportedArtifactError("invalid text encoding") from exc
    if any(ord(ch) < 0x20 and ch not in "\t\r\n" for ch in text):
        raise UnsupportedArtifactError("illegal control characters")
    _structural_container_check(text)

    content_hash = "sha256:" + hashlib.sha256(raw).hexdigest()
    return StepArtifactRef(
        media_type=_STEP_MEDIA_TYPE,
        id=h.derive_uuid(content_hash),
        content_hash=content_hash,
    )
