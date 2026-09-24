from __future__ import annotations

import uuid

from app.providers import all_providers, get_provider
from app.services.ranking_service import QUALITY_ORDER


async def test_all_providers_details_availability():
    for p in all_providers():
        assert get_provider(p.provider_id) is p
        items = await p.search("матрица")
        assert isinstance(items, list)
        if items:
            d = await p.get_details(items[0].external_id)
            assert d is not None
            a = await p.get_availability(items[0].external_id)
            assert a is not None and a.available
        assert await p.get_details("no-such-id") is None
        assert await p.get_availability("no-such-id") is None
        assert p.build_deep_link("abc") is not None
        assert p.build_url("abc").endswith("/watch/abc")


async def test_health_and_shortlink(client, auth_headers):
    h = await client.get("/health")
    assert h.json() == {"status": "ok"}
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    sh = await client.post(f"/api/v1/content/{cid}/share", headers=auth_headers)
    assert sh.status_code == 200
    slug = sh.json()["slug"]
    r = await client.get(f"/s/{slug}", follow_redirects=False)
    assert r.status_code == 302
    r2 = await client.get("/s/doesnotexist")
    assert r2.status_code == 200  # JSON fallback message


async def test_search_filters(client, auth_headers):
    # only_my with connected provider
    await client.post(
        "/api/v1/providers/connect", json={"provider_id": "ivi"}, headers=auth_headers
    )
    r = await client.get(
        "/api/v1/search", params={"q": "матрица", "only_my": True}, headers=auth_headers
    )
    assert r.status_code == 200
    assert all("ivi" in i["providers"] for i in r.json()["items"])
    # free only
    r = await client.get(
        "/api/v1/search", params={"q": "космос", "free": True}, headers=auth_headers
    )
    assert r.status_code == 200
    assert all(i["free"] for i in r.json()["items"])
    # quality + genres + rating + year + type
    r = await client.get(
        "/api/v1/search",
        params={
            "q": "матрица",
            "quality": "4K",
            "genres": "фантастика",
            "min_rating": 8,
            "year": 1999,
            "type": "movie",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1
    # cache hit path (second identical call)
    r2 = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    assert r2.status_code == 200


async def test_search_anon_and_empty(client):
    r = await client.get("/api/v1/search", params={"q": "матрица"})
    assert r.status_code == 200
    r = await client.get("/api/v1/search", params={"q": ""})
    assert r.status_code == 200
    # invalid token -> treated as anon
    r = await client.get(
        "/api/v1/search", params={"q": "матрица"}, headers={"Authorization": "Bearer garbage"}
    )
    assert r.status_code == 200
    r = await client.get("/api/v1/search/suggest", params={"q": ""})
    assert r.json() == {"items": []}


async def test_content_errors(client, auth_headers):
    fake = str(uuid.uuid4())
    assert (await client.get(f"/api/v1/content/{fake}", headers=auth_headers)).status_code == 404
    assert (await client.get(f"/api/v1/content/{fake}/availability")).status_code == 404
    assert (
        await client.post(
            f"/api/v1/content/{fake}/mark-watched", json={"watched": True}, headers=auth_headers
        )
    ).status_code == 404
    assert (
        await client.post(f"/api/v1/content/{fake}/watch", json={}, headers=auth_headers)
    ).status_code == 404
    assert (
        await client.post(f"/api/v1/content/{fake}/share", headers=auth_headers)
    ).status_code == 404
    # invalid uuid content in watchlist
    r = await client.post(
        "/api/v1/watchlist", json={"content_id": "not-a-uuid"}, headers=auth_headers
    )
    assert r.status_code == 404
    r = await client.post("/api/v1/watchlist", json={"content_id": fake}, headers=auth_headers)
    assert r.status_code == 404
    # similar for missing -> empty
    from sqlalchemy.ext.asyncio import AsyncSession  # noqa

    s = await client.get(f"/api/v1/content/{fake}/similar")
    assert s.json() == {"items": []}


async def test_mark_watched_upsert(client, auth_headers):
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    for _ in range(2):
        r = await client.post(
            f"/api/v1/content/{cid}/mark-watched",
            json={"provider_id": "ivi", "watched": True},
            headers=auth_headers,
        )
        assert r.status_code == 200
    h = await client.get("/api/v1/history", headers=auth_headers)
    assert h.json()[0]["watched"] is True
    # watch again without watched flag keeps watched=True
    await client.post(
        f"/api/v1/content/{cid}/watch", json={"provider_id": "ivi"}, headers=auth_headers
    )
    # history clear
    c = await client.delete("/api/v1/history", headers=auth_headers)
    assert c.status_code == 200
    h = await client.get("/api/v1/history", headers=auth_headers)
    assert h.json() == []


async def test_auth_edge_cases(client, auth_headers):
    # duplicate register
    r = await client.post(
        "/api/v1/auth/register", json={"email": "dup@test.ru", "password": "secret123"}
    )
    assert r.status_code == 200
    r = await client.post(
        "/api/v1/auth/register", json={"email": "dup@test.ru", "password": "secret123"}
    )
    assert r.status_code == 409
    # short password
    r = await client.post("/api/v1/auth/register", json={"email": "x@test.ru", "password": "123"})
    assert r.status_code == 401
    # wrong login
    r = await client.post("/api/v1/auth/login", json={"email": "dup@test.ru", "password": "wrong"})
    assert r.status_code == 401
    # refresh invalid
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "bad"})
    assert r.status_code == 401
    # refresh unknown user
    from app.core.security import create_refresh_token

    r = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": create_refresh_token(str(uuid.uuid4()))}
    )
    assert r.status_code == 401
    # patch me
    r = await client.patch(
        "/api/v1/auth/me",
        json={
            "display_name": "Neo",
            "onboarding_completed": True,
            "preferred_theme": "dark",
            "preferred_language": "en",
        },
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["display_name"] == "Neo"
    # me without token
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


async def test_providers_edge(client, auth_headers):
    r = await client.post(
        "/api/v1/providers/connect", json={"provider_id": "nope"}, headers=auth_headers
    )
    assert r.status_code == 404
    # connect twice is idempotent
    await client.post(
        "/api/v1/providers/connect", json={"provider_id": "ivi"}, headers=auth_headers
    )
    await client.post(
        "/api/v1/providers/connect", json={"provider_id": "ivi"}, headers=auth_headers
    )
    c = await client.get("/api/v1/providers/connected", headers=auth_headers)
    assert len([p for p in c.json() if p["id"] == "ivi"]) == 1


async def test_watchlist_remove_by_content(client, auth_headers):
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    await client.post("/api/v1/watchlist", json={"content_id": cid}, headers=auth_headers)
    await client.post(
        "/api/v1/watchlist", json={"content_id": cid}, headers=auth_headers
    )  # idempotent
    r = await client.delete(f"/api/v1/watchlist/by-content/{cid}", headers=auth_headers)
    assert r.status_code == 200
    assert (await client.get("/api/v1/watchlist", headers=auth_headers)).json() == []


async def test_prefs_invalid_quality_ignored(client, auth_headers):
    r = await client.patch(
        "/api/v1/preferences", json={"preferred_quality": "8K"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["preferred_quality"] == "any"


async def test_feed_anon_and_popular(client):
    f = await client.get("/api/v1/content/feed")
    assert f.status_code == 200
    assert len(f.json()["sections"]) >= 2  # popular + recommended, no continue/mine
    p = await client.get("/api/v1/content/popular")
    assert len(p.json()) > 0


async def test_recommendations_hide_watched(client, auth_headers, db_session):
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    await client.post(
        f"/api/v1/content/{cid}/mark-watched", json={"watched": True}, headers=auth_headers
    )
    await client.patch(
        "/api/v1/preferences",
        json={"hide_watched": True, "favorite_genres": ["фантастика"]},
        headers=auth_headers,
    )
    me = await client.get("/api/v1/auth/me", headers=auth_headers)
    uid = uuid.UUID(me.json()["id"])
    from app.services import recommendation_service

    rec = await recommendation_service.recommend(db_session, uid)
    assert all(str(c.id) != cid for c in rec)
    cw = await recommendation_service.continue_watching(db_session, uid)
    assert all(str(c.id) != cid for c in cw)  # watched=True excluded
    n = await recommendation_service.popular(db_session, exclude={uuid.UUID(cid)})
    assert all(str(c.id) != cid for c in n)
    from app.services.history_service import search_count

    assert await search_count(db_session, uid) >= 1


async def test_worker_tasks(db_session):
    from app.worker.tasks import check_new_releases, prune_histories, refresh_catalog

    assert refresh_catalog() is not None
    assert check_new_releases() == {"checked": True}
    assert "pruned" in prune_histories()


async def test_quality_order_unknown():
    assert QUALITY_ORDER.get("8K", 1) == 1


async def test_partial_flag_on_provider_failure(client, auth_headers, monkeypatch):

    async def boom(self, query, year=None):
        raise RuntimeError("provider down")

    import app.providers.ivi as ivi_mod

    monkeypatch.setattr(ivi_mod.IviProvider, "search", boom)
    r = await client.get(
        "/api/v1/search", params={"q": "уникальныйзапрос12345"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["partial"] is True
    assert "ivi" in r.json()["failed_providers"]
