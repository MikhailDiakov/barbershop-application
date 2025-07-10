from datetime import datetime

import pytest

from app.models import Review


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
async def test_get_my_reviews_with_direct_db_insert(
    authorized_client, db_session_with_rollback
):
    client_id = 4
    barber_id = 1

    review = Review(
        client_id=client_id,
        barber_id=barber_id,
        rating=4,
        comment="Nice but could be better",
        is_approved=True,
        created_at=datetime.utcnow(),
    )
    db_session_with_rollback.add(review)
    await db_session_with_rollback.commit()

    response = await authorized_client.get("/review/my-reviews/")
    assert response.status_code == 200

    reviews = response.json()
    assert isinstance(reviews, list)
    assert any(r["comment"] == "Nice but could be better" for r in reviews)
