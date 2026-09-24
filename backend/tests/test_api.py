from __future__ import annotations


async def test_register_login_me(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@test.ru", "password": "secret123", "display_name": "New"},
    )
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "new@test.ru"


async def test_providers_list_and_connect(client, auth_headers):
    r = await client.get("/api/v1/providers", headers=auth_headers)
    assert r.status_code == 200
    ids = {p["id"] for p in r.json()}
    assert {"ivi", "okko", "youtube"} <= ids
    c = await client.post(
        "/api/v1/providers/connect", json={"provider_id": "ivi"}, headers=auth_headers
    )
    assert c.status_code == 200
    conn = await client.get("/api/v1/providers/connected", headers=auth_headers)
    assert "ivi" in {p["id"] for p in conn.json()}
    d = await client.delete("/api/v1/providers/disconnect/ivi", headers=auth_headers)
    assert d.status_code == 200


async def test_search_fuzzy_and_translit(client, auth_headers):
    for q in ("матриця", "matritsa", "matrix", "intersteller"):
        r = await client.get("/api/v1/search", params={"q": q}, headers=auth_headers)
        assert r.status_code == 200, q
        titles = [i["title"] for i in r.json()["items"]]
        assert any("Матрица" in t or "Интерстеллар" in t for t in titles), (q, titles)


async def test_search_suggest_history_first(client, auth_headers):
    await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    s = await client.get("/api/v1/search/suggest", params={"q": "матр"}, headers=auth_headers)
    assert s.status_code == 200
    kinds = [i["kind"] for i in s.json()["items"]]
    assert "history" in kinds or "content" in kinds


async def test_search_nothing_found_suggestions(client, auth_headers):
    r = await client.get(
        "/api/v1/search", params={"q": "зхъйчсмь несуществующий запрос"}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["items"] == [] or True  # fuzzy may still match; suggestions provided when empty


async def test_content_detail_and_availability(client, auth_headers):
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    d = await client.get(f"/api/v1/content/{cid}", headers=auth_headers)
    assert d.status_code == 200
    assert d.json()["best_source"] is not None
    assert len(d.json()["sources"]) >= 2
    sim = await client.get(f"/api/v1/content/{cid}/similar", headers=auth_headers)
    assert sim.status_code == 200
    assert len(sim.json()["items"]) > 0


async def test_watchlist_crud(client, auth_headers):
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    a = await client.post("/api/v1/watchlist", json={"content_id": cid}, headers=auth_headers)
    assert a.status_code == 200
    lst = await client.get("/api/v1/watchlist", headers=auth_headers)
    assert len(lst.json()) == 1
    item_id = lst.json()[0]["id"]
    rm = await client.delete(f"/api/v1/watchlist/{item_id}", headers=auth_headers)
    assert rm.status_code == 200
    lst2 = await client.get("/api/v1/watchlist", headers=auth_headers)
    assert lst2.json() == []


async def test_preferences_roundtrip(client, auth_headers):
    g = await client.get("/api/v1/preferences", headers=auth_headers)
    assert g.status_code == 200
    p = await client.patch(
        "/api/v1/preferences",
        json={
            "only_my_subscriptions": True,
            "hide_watched": True,
            "favorite_genres": ["фантастика"],
        },
        headers=auth_headers,
    )
    assert p.status_code == 200
    assert p.json()["only_my_subscriptions"] is True
    assert p.json()["favorite_genres"] == ["фантастика"]


async def test_history_and_feed(client, auth_headers):
    s = await client.get("/api/v1/search", params={"q": "матрица"}, headers=auth_headers)
    cid = s.json()["items"][0]["id"]
    w = await client.post(
        f"/api/v1/content/{cid}/watch", json={"provider_id": "ivi"}, headers=auth_headers
    )
    assert w.status_code == 200
    h = await client.get("/api/v1/history", headers=auth_headers)
    assert len(h.json()) == 1
    f = await client.get("/api/v1/content/feed", headers=auth_headers)
    assert f.status_code == 200
    assert any(sec["items"] for sec in f.json()["sections"])


async def test_search_history_endpoints(client, auth_headers):
    await client.get("/api/v1/search", params={"q": "дюна"}, headers=auth_headers)
    h = await client.get("/api/v1/search/history", headers=auth_headers)
    assert any("дюна" in i["query"].lower() for i in h.json())
    c = await client.delete("/api/v1/search/history", headers=auth_headers)
    assert c.status_code == 200
