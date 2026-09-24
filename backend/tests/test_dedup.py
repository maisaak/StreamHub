from app.db.models import Content, ContentType
from app.providers.base import ProviderItem
from app.services.aggregator_service import _merge_provider_items


def test_merge_dedups_same_title():
    c = Content(
        title="Матрица",
        original_title="The Matrix",
        year=1999,
        content_type=ContentType.movie,
        tmdb_id=603,
    )
    items = {
        "ivi": [ProviderItem(external_id="1", title="Матрица", year=1999, tmdb_id=603)],
        "okko": [ProviderItem(external_id="2", title="Матриця", year=1999)],
    }
    matched, unmatched = _merge_provider_items([c], items)
    assert matched == [c]
    assert unmatched == []
