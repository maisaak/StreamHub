from app.services.ranking_service import RankInput, best_source_index, rank_sources


def test_ranking_order():
    sources = [
        RankInput(
            "a", connected=False, is_subscription=False, price=299, quality="HD"
        ),  # 6 rent not connected
        RankInput("b", connected=True, is_subscription=True, price=None, quality="HD"),  # 2
        RankInput("c", connected=False, is_subscription=False, price=None, quality="HD"),  # 5 free
        RankInput("d", connected=True, is_subscription=True, price=None, quality="4K"),  # 1 best
        RankInput("e", connected=False, is_subscription=True, price=None, quality="4K"),  # 3
        RankInput("f", connected=True, is_subscription=False, price=199, quality="HD"),  # 4
    ]
    order = rank_sources(sources)
    ranked = [sources[i].provider_id for i in order]
    assert ranked == ["d", "b", "e", "f", "c", "a"]
    assert best_source_index(sources) == 3


def test_best_none_empty():
    assert best_source_index([]) is None
