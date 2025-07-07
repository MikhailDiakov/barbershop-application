import pytest


@pytest.mark.asyncio
async def test_create_review_success(authorized_client):
    review_res = await authorized_client.post(
        "/review/",
        json={
            "barber_id": 1,
            "rating": 5,
            "comment": "Great haircut!",
        },
    )
    assert review_res.status_code == 200
    review = review_res.json()
    assert review["barber_id"] == 1
    assert review["rating"] == 5
    assert review["comment"] == "Great haircut!"


@pytest.mark.asyncio
async def test_create_review_rating_too_low(authorized_client):
    review_res = await authorized_client.post(
        "/review/",
        json={
            "barber_id": 1,
            "rating": -1,
            "comment": "Bad rating",
        },
    )
    assert review_res.status_code == 422
    data = review_res.json()
    assert "rating" in data["detail"] or "rating" in str(data)


@pytest.mark.asyncio
async def test_create_review_nonexistent_barber(authorized_client):
    review_res = await authorized_client.post(
        "/review/",
        json={
            "barber_id": 9999,
            "rating": 4,
            "comment": "Who is this?",
        },
    )
    assert review_res.status_code == 404
    data = review_res.json()
    assert "barber" in data["detail"] or "not found" in str(data).lower()


@pytest.mark.asyncio
async def test_create_review_rating_too_high(authorized_client):
    review_res = await authorized_client.post(
        "/review/",
        json={
            "barber_id": 1,
            "rating": 6,
            "comment": "Too good!",
        },
    )
    assert review_res.status_code == 422
    data = review_res.json()
    assert "rating" in data["detail"] or "rating" in str(data)


@pytest.mark.asyncio
async def test_get_my_reviews(authorized_client):
    review_res = await authorized_client.post(
        "/review/",
        json={
            "barber_id": 1,
            "rating": 4,
            "comment": "Nice but could be better",
        },
    )
    assert review_res.status_code == 200

    res = await authorized_client.get("/review/my-reviews/")
    assert res.status_code == 200
    reviews = res.json()
    assert isinstance(reviews, list)
    assert any(r["comment"] == "Nice but could be better" for r in reviews)
