"""RM12 downtime input: validation, canonicalization and relevance (ADR-0015).

Downtime is immutable input to ONE scheduling run: per KNOWN machine, finite half-open intervals
``[start_min, end_min)`` in integer minutes from schedule origin 0 (``0 <= start_min < end_min``).
The machine is available everywhere else, so the scheduling horizon stays unbounded and every
operation eventually fits. Nothing here is stored, updated or read from a live source: no calendar,
shift, maintenance policy, MES or factory state.

- ``canonical_downtime`` validates every interval (integer minutes — no bool, float, infinity or
  string — start >= 0, end > start), rejects unknown machine ids (never silently ignored), sorts
  each machine's intervals and merges overlapping AND touching ones: ``[60, 120) + [120, 180)`` ->
  ``[60, 180)``. The result is deterministic: machines in sorted order, intervals sorted, pairwise
  disjoint and non-touching; machines without intervals are omitted.
- ``relevant_downtime`` keeps only machines assigned to at least one operation of the job set;
  downtime elsewhere cannot affect the schedule, its identity or its digest.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import cast

from mini_prometheus.manufacturing_scheduling.model import (
    Downtime,
    DowntimeInterval,
    InvalidDowntimeError,
    SchedulingJob,
)

# machine id -> intervals, each a (start_min, end_min) pair or a DowntimeInterval
DowntimeInput = Mapping[str, Iterable[object]]


def _interval(machine: str, raw: object) -> DowntimeInterval:
    if isinstance(raw, DowntimeInterval):
        pair: tuple[object, ...] = (raw.start_min, raw.end_min)
    else:
        try:
            pair = tuple(cast(Iterable[object], raw))
        except TypeError:
            pair = ()
    if len(pair) != 2:
        raise InvalidDowntimeError(
            f"{machine}: downtime {raw!r} must be a (start_min, end_min) pair"
        )
    start, end = pair
    if (
        not isinstance(start, int)
        or isinstance(start, bool)
        or not isinstance(end, int)
        or isinstance(end, bool)
    ):
        raise InvalidDowntimeError(
            f"{machine}: downtime [{start!r}, {end!r}) must be finite integer minutes"
        )
    if start < 0:
        raise InvalidDowntimeError(f"{machine}: downtime [{start}, {end}) starts before 0")
    if end <= start:
        raise InvalidDowntimeError(f"{machine}: downtime [{start}, {end}) must end after it starts")
    return DowntimeInterval(start, end)


def canonical_downtime(
    downtime: DowntimeInput | None, known_resources: Iterable[str]
) -> dict[str, tuple[DowntimeInterval, ...]]:
    """Validated, sorted, merged (overlapping and touching) downtime per known machine."""
    if not downtime:
        return {}
    known = set(known_resources)
    unknown = sorted(str(machine) for machine in downtime if machine not in known)
    if unknown:
        raise InvalidDowntimeError("unknown machine id(s) in downtime: " + ", ".join(unknown))
    canonical: dict[str, tuple[DowntimeInterval, ...]] = {}
    for machine in sorted(downtime):
        try:
            given = list(downtime[machine])
        except TypeError:
            raise InvalidDowntimeError(f"{machine}: downtime must be a list of intervals") from None
        intervals = sorted(_interval(machine, raw) for raw in given)
        merged: list[DowntimeInterval] = []
        for interval in intervals:
            if merged and interval.start_min <= merged[-1].end_min:
                end = max(merged[-1].end_min, interval.end_min)
                merged[-1] = DowntimeInterval(merged[-1].start_min, end)
            else:
                merged.append(interval)
        if merged:
            canonical[machine] = tuple(merged)
    return canonical


def relevant_downtime(
    canonical: Mapping[str, tuple[DowntimeInterval, ...]], jobs: Sequence[SchedulingJob]
) -> Downtime:
    """Only the downtime of machines assigned to at least one operation of the job set."""
    used = {a.resource_id for job in jobs for a in job.plan.resource_assignments}
    return tuple(
        (machine, intervals) for machine, intervals in sorted(canonical.items()) if machine in used
    )
