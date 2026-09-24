from app.utils.normalizers import (
    normalize_title,
    title_variants,
    transliterate_en_to_ru,
    transliterate_ru_to_en,
)


def test_normalize_basic():
    assert normalize_title("  Матрица: Перезагрузка! ") == "матрица перезагрузка"


def test_transliteration_ru_en():
    assert transliterate_ru_to_en("матрица") == "matritsa"


def test_transliteration_en_ru():
    assert "матр" in transliterate_en_to_ru("matrix")


def test_title_variants_include_translit():
    variants = title_variants("Матрица")
    assert any("matritsa" in v or "matrix" in v for v in variants)
