"""Match provider items to catalog content.

Order: TMDB ID → fuzzy title (rapidfuzz ≥ 85) + year ±1 → normalized equality.
"""

from __future__ import annotations

from rapidfuzz import fuzz

from app.db.models import Content
from app.providers.base import ProviderItem
from app.utils.normalizers import normalize_title, title_variants

FUZZY_THRESHOLD = 85


def _best_fuzzy(query_variants: list[str], target_variants: list[str]) -> int:
    best = 0
    for q in query_variants:
        for t in target_variants:
            if not q or not t:
                continue
            s = max(fuzz.WRatio(q, t), fuzz.ratio(q, t))
            if s > best:
                best = int(s)
    return best


def score_item_against_content(item: ProviderItem, content: Content) -> tuple[bool, int]:
    # 1. TMDB direct
    if item.tmdb_id and content.tmdb_id and item.tmdb_id == content.tmdb_id:
        return True, 100
    q_vars = title_variants(item.title) + title_variants(item.original_title or "")
    c_vars = title_variants(content.title) + title_variants(content.original_title or "")
    score = _best_fuzzy(q_vars, c_vars)
    # year check ±1
    if item.year and content.year and abs(item.year - content.year) > 1:
        score -= 30
    # normalized equality shortcut
    if normalize_title(item.title) and normalize_title(item.title) == normalize_title(
        content.title
    ):
        score = max(score, 95)
    return score >= FUZZY_THRESHOLD, score


def match_item(item: ProviderItem, candidates: list[Content]) -> Content | None:
    best: Content | None = None
    best_score = 0
    for c in candidates:
        ok, score = score_item_against_content(item, c)
        if ok and score > best_score:
            best, best_score = c, score
    return best


def fuzzy_score(a: str, b: str) -> int:
    """Symmetric fuzzy score over transliteration variants (0-100)."""
    return _best_fuzzy(title_variants(a), title_variants(b))


def gated_fuzzy_score(a: str, b: str) -> int:
    """Search-grade score: WRatio gated by token_set_ratio.

    WRatio alone is too generous on short queries ('матр' vs 'Триггер' = 60).
    True matches (typos, translits) score W>=68 AND token_set>=55; junk fails
    at least one. Returns 0 when the gate fails.
    """
    qv, tv = title_variants(a), title_variants(b)
    best_w = 0
    best_ts = 0
    for q in qv:
        for t in tv:
            if not q or not t:
                continue
            w = max(fuzz.WRatio(q, t), fuzz.ratio(q, t))
            ts = fuzz.token_set_ratio(q, t)
            best_w = max(best_w, int(w))
            best_ts = max(best_ts, int(ts))
    if best_w >= 68 and best_ts >= 55:
        return best_w
    return 0
