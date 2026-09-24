"""Rank sources per spec §4:

1. connected + subscription + max quality
2. connected + subscription
3. not connected + subscription (needs subscription)
4. connected + rent (with price)
5. free source
6. not connected + rent
"""

from __future__ import annotations

from dataclasses import dataclass

QUALITY_ORDER = {"SD": 0, "HD": 1, "4K": 2}


@dataclass
class RankInput:
    provider_id: str
    connected: bool
    is_subscription: bool
    price: float | None
    quality: str


def rank_key(s: RankInput) -> tuple[int, int, float]:
    q = QUALITY_ORDER.get(s.quality, 1)
    free = s.price is None and not s.is_subscription
    if s.connected and s.is_subscription:
        return (0, -q, 0.0)
    if not s.connected and s.is_subscription:
        return (2, -q, 0.0)
    if s.connected and s.price is not None:
        return (3, -q, s.price)
    if free:
        # Free sources: connected-free (youtube/rutube connected) still rank 4,
        # prefer higher quality.
        return (4, -q, 0.0)
    if s.price is not None:
        return (5, -q, s.price)
    return (6, -q, 0.0)


def rank_sources(sources: list[RankInput]) -> list[int]:
    """Return indices of sources sorted best-first."""
    return sorted(range(len(sources)), key=lambda i: rank_key(sources[i]))


def best_source_index(sources: list[RankInput]) -> int | None:
    if not sources:
        return None
    return rank_sources(sources)[0]
