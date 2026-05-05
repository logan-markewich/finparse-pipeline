async def test_create_review_extraction_not_found(client):
    response = await client.post(
        "/reviews/",
        json={"extraction_ids": [999]},
    )
    assert response.status_code == 404


async def test_list_reviews_empty(client):
    response = await client.get("/reviews/")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_review_not_found(client):
    response = await client.get("/reviews/999")
    assert response.status_code == 404
