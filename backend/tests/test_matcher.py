from app.db.models import Content, ContentType
from app.providers.base import ProviderItem
from app.services import matcher_service


def _content(**kw):
    base = dict(
        title="Матрица",
        original_title="The Matrix",
        year=1999,
        content_type=ContentType.movie,
        tmdb_id=603,
    )
    base.update(kw)
    return Content(**base)


def test_match_by_tmdb():
    c = _content()
    item = ProviderItem(external_id="x", title="Something else", tmdb_id=603)
    assert matcher_service.match_item(item, [c]) is c


def test_match_fuzzy_typo():
    c = _content()
    item = ProviderItem(external_id="x", title="Матриця", year=1999)
    assert matcher_service.match_item(item, [c]) is c


def test_match_translit():
    c = _content()
    item = ProviderItem(external_id="x", title="Matritsa", year=1999)
    assert matcher_service.match_item(item, [c]) is c


def test_no_match_year_far():
    c = _content()
    # year penalty may still match on exact title; different title must not
    item2 = ProviderItem(external_id="x", title="Совершенно другое", year=1980)
    assert matcher_service.match_item(item2, [c]) is None


def test_fuzzy_score_typo_high():
    assert matcher_service.fuzzy_score("матриця", "Матрица") >= 85
    assert matcher_service.fuzzy_score("intersteller", "Interstellar") >= 80


def test_gated_fuzzy_score():
    from app.services.matcher_service import gated_fuzzy_score

    # true matches pass
    assert gated_fuzzy_score("матриця", "Матрица") >= 68
    assert gated_fuzzy_score("matritsa", "Матрица") >= 68
    assert gated_fuzzy_score("intersteller", "Interstellar") >= 68
    assert gated_fuzzy_score("гари поттер", "Гарри Поттер и философский камень") >= 68
    # junk fails
    assert gated_fuzzy_score("матр", "Игра в кальмара") == 0
    assert gated_fuzzy_score("матр", "Триггер") == 0
    assert gated_fuzzy_score("matrix", "Смешарики") == 0
    assert gated_fuzzy_score("зхъйчсмь несуществующий", "Триггер") == 0
