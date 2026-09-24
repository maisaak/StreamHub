from __future__ import annotations

import re
import unicodedata

STOP_WORDS_RU = {
    "фильм",
    "сериал",
    "смотреть",
    "онлайн",
    "hd",
    "4k",
    "the",
    "a",
    "an",
    "кино",
    "видео",
    "часть",
    "сезон",
    "серия",
}

_RU_TO_EN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}

_EN_TO_RU = {
    "yo": "ё",
    "zh": "ж",
    "ch": "ч",
    "sh": "ш",
    "shch": "щ",
    "yu": "ю",
    "ya": "я",
    "kh": "х",
    "ts": "ц",
    "a": "а",
    "b": "б",
    "v": "в",
    "g": "г",
    "d": "д",
    "e": "е",
    "z": "з",
    "i": "и",
    "y": "й",
    "k": "к",
    "l": "л",
    "m": "м",
    "n": "н",
    "o": "о",
    "p": "п",
    "r": "р",
    "s": "с",
    "t": "т",
    "u": "у",
    "f": "ф",
    "h": "х",
    "c": "к",
    "w": "в",
    "x": "кс",
    "q": "к",
    "j": "дж",
}

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def transliterate_ru_to_en(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(_RU_TO_EN.get(ch, ch))
    return "".join(out)


def transliterate_en_to_ru(text: str) -> str:
    s = text.lower()
    # multi-char first
    for en in ("shch", "yo", "zh", "ch", "sh", "yu", "ya", "kh", "ts"):
        s = s.replace(en, _EN_TO_RU[en])
    return "".join(_EN_TO_RU.get(c, c) for c in s)


def normalize_title(title: str, remove_stopwords: bool = True) -> str:
    """Lowercase, strip accents/punct, collapse spaces, drop stop-words."""
    s = strip_accents(title.lower())
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    if remove_stopwords:
        tokens = [t for t in s.split(" ") if t and t not in STOP_WORDS_RU]
        s = " ".join(tokens)
    return s


def title_variants(title: str) -> list[str]:
    """Original + transliterations, normalized — for fuzzy matching."""
    base = normalize_title(title)
    variants = {base}
    ru_en = normalize_title(transliterate_ru_to_en(title))
    en_ru = normalize_title(transliterate_en_to_ru(title))
    variants.add(ru_en)
    variants.add(en_ru)
    # also single-word compact form helps with "matritsa" vs "матрица"
    variants.add(base.replace(" ", ""))
    return [v for v in variants if v]
