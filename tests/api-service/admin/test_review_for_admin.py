from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.models.review import Review


@pytest_asyncio.fixture
async def two_reviews(db_session_with_rollback):
    approved = Review(
        client_id=1,
        barber_id=1,
        rating=5,
        comment="Excellent service!",
        is_approved=True,
        created_at=datetime.utcnow(),
    )
    unapproved = Review(
        client_id=1,
        barber_id=1,
        rating=3,
        comment="Average experience.",
        is_approved=False,
        created_at=datetime.utcnow(),
    )
    db_session_with_rollback.add_all([approved, unapproved])
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(approved)
    await db_session_with_rollback.refresh(unapproved)
    return {"approved": approved, "unapproved": unapproved}


@pytest.mark.asyncio
async def test_admin_list_reviews(admin_client, two_reviews):
    res = await admin_client.get("/admin/reviews/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    ids_in_response = {r["id"] for r in data}
    assert two_reviews["approved"].id in ids_in_response
    assert two_reviews["unapproved"].id in ids_in_response
    assert len(data) >= 2


@pytest.mark.asyncio
@patch("app.services.admin.reviews.get_barber_rating", new_callable=AsyncMock)
@patch("app.services.admin.reviews.save_barber_rating", new_callable=AsyncMock)
async def test_admin_approve_review_success(
    mock_save_rating,
    mock_get_rating,
    admin_client,
    two_reviews,
):
    review = two_reviews["unapproved"]

    mock_get_rating.return_value = (4.0, 2)

    res = await admin_client.post(f"/admin/reviews/{review.id}/approve")

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == review.id
    assert data["is_approved"] is True

    mock_get_rating.assert_called_once_with(review.barber_id)
    mock_save_rating.assert_called_once()


@pytest.mark.asyncio
async def test_admin_approve_already_approved_review(admin_client, two_reviews):
    review = two_reviews["approved"]

    res = await admin_client.post(f"/admin/reviews/{review.id}/approve")

    assert res.status_code == 400
    assert "already approved" in res.text.lower()


@pytest.mark.asyncio
async def test_admin_approve_nonexistent_review(admin_client):
    res = await admin_client.post("/admin/reviews/999999/approve")

    assert res.status_code == 404
    assert "not found" in res.text.lower()


@pytest.mark.asyncio
@patch("app.services.admin.reviews.get_barber_rating", new_callable=AsyncMock)
@patch("app.services.admin.reviews.save_barber_rating", new_callable=AsyncMock)
async def test_admin_delete_approved_review(
    mock_save_rating,
    mock_get_rating,
    admin_client,
    two_reviews,
):
    review = two_reviews["approved"]
    mock_get_rating.return_value = (4.5, 3)

    res = await admin_client.delete(f"/admin/reviews/{review.id}")

    assert res.status_code == 200
    data = res.json()
    assert data["detail"] == "Review deleted"

    mock_get_rating.assert_called_once_with(review.barber_id)
    mock_save_rating.assert_called_once()


@pytest.mark.asyncio
async def test_admin_delete_unapproved_review(admin_client, two_reviews):
    review = two_reviews["unapproved"]

    res = await admin_client.delete(f"/admin/reviews/{review.id}")

    assert res.status_code == 200
    data = res.json()
    assert data["detail"] == "Review deleted"


@pytest.mark.asyncio
async def test_admin_delete_nonexistent_review(admin_client):
    res = await admin_client.delete("/admin/reviews/999999")

    assert res.status_code == 404
    assert "not found" in res.text.lower()
