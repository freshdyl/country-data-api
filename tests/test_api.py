def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["data_source"] == "sample"
    assert body["country_count"] > 0


def test_list_defaults(client):
    body = client.get("/countries").json()
    assert body["limit"] == 25
    assert body["offset"] == 0
    assert body["total"] == len(body["items"])
    names = [c["name"] for c in body["items"]]
    assert names == sorted(names, key=str.casefold)


def test_list_filter_sort_paginate(client):
    body = client.get(
        "/countries",
        params={"region": "Europe", "sort_by": "population", "order": "desc", "limit": 2},
    ).json()
    assert body["total"] == 4
    assert [c["name"] for c in body["items"]] == ["Germany", "France"]

    page2 = client.get(
        "/countries",
        params={
            "region": "Europe",
            "sort_by": "population",
            "order": "desc",
            "limit": 2,
            "offset": 2,
        },
    ).json()
    assert [c["name"] for c in page2["items"]] == ["Italy", "Switzerland"]


def test_list_by_currency_and_language(client):
    eur = client.get("/countries", params={"currency": "EUR"}).json()
    assert eur["total"] == 3
    french = client.get("/countries", params={"language": "French"}).json()
    assert {c["code3"] for c in french["items"]} == {"CAN", "FRA", "CHE"}


def test_invalid_query_params_return_422(client):
    assert client.get("/countries", params={"limit": 0}).status_code == 422
    assert client.get("/countries", params={"limit": 101}).status_code == 422
    assert client.get("/countries", params={"offset": -1}).status_code == 422
    assert client.get("/countries", params={"sort_by": "nonsense"}).status_code == 422
    assert client.get("/countries", params={"min_population": -1}).status_code == 422


def test_min_greater_than_max_returns_422(client):
    response = client.get("/countries", params={"min_population": 10, "max_population": 5})
    assert response.status_code == 422
    assert "min_population" in response.json()["detail"]


def test_search(client):
    results = client.get("/countries/search", params={"q": "ghana"}).json()
    assert results[0]["name"] == "Ghana"
    assert client.get("/countries/search", params={"q": "zzzzzz"}).json() == []


def test_search_requires_min_length(client):
    assert client.get("/countries/search", params={"q": "a"}).status_code == 422
    assert client.get("/countries/search").status_code == 422


def test_get_country_by_either_code(client):
    assert client.get("/countries/CA").json()["name"] == "Canada"
    assert client.get("/countries/can").json()["code2"] == "CA"


def test_get_country_not_found(client):
    response = client.get("/countries/XX")
    assert response.status_code == 404
    assert "XX" in response.json()["detail"]


def test_search_route_not_shadowed_by_code_route(client):
    # /countries/search must hit the search endpoint, not be read as code="search"
    assert client.get("/countries/search", params={"q": "japan"}).status_code == 200


def test_regions(client):
    regions = client.get("/regions").json()
    assert "Europe" in regions
    assert regions == sorted(regions)


def test_stats_global_and_regional(client):
    overall = client.get("/stats").json()
    assert overall["region"] is None
    assert overall["most_populous"][0]["name"] == "India"

    europe = client.get("/stats", params={"region": "europe"}).json()
    assert europe["country_count"] == 4


def test_stats_unknown_region_is_404(client):
    assert client.get("/stats", params={"region": "Atlantis"}).status_code == 404
