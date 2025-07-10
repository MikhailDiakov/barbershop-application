from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_my_barber_profile(barber_client):
    res = await barber_client.get("/barber/me")
    assert res.status_code == 200
    data = res.json()
    assert "full_name" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_update_my_barber_profile(barber_client):
    update_payload = {"full_name": "Updated Barber Name"}
    res = await barber_client.put("/barber/me", json=update_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Updated Barber Name"


@patch("app.services.barber_service.upload_file_to_s3", new_callable=AsyncMock)
@patch("app.services.barber_service.delete_file_from_s3", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_upload_barber_avatar(
    mock_delete_file_from_s3, mock_upload_file_to_s3, barber_client
):
    mock_upload_file_to_s3.return_value = (
        "https://mock-bucket.s3.amazonaws.com/barbers/avatar.jpg"
    )
    mock_delete_file_from_s3.return_value = None

    files = {"file": ("avatar.jpg", b"fake image data", "image/jpeg")}
    res = await barber_client.post("/barber/avatar", files=files)

    assert res.status_code == 200, res.text
    data = res.json()
    assert "avatar_url" in data
    assert data["avatar_url"].startswith("https://mock-bucket")


@patch("app.services.barber_service.upload_file_to_s3", new_callable=AsyncMock)
@patch("app.services.barber_service.delete_file_from_s3", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_delete_barber_avatar(
    mock_delete_file_from_s3, mock_upload_file_to_s3, barber_client
):
    mock_upload_file_to_s3.return_value = (
        "https://mock-bucket.s3.amazonaws.com/barbers/avatar.jpg"
    )
    mock_delete_file_from_s3.return_value = None

    res = await barber_client.delete("/barber/avatar")
    assert res.status_code == 200
    assert res.json() == {"detail": "Avatar deleted"}
