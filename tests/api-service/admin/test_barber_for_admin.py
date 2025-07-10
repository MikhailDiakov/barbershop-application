from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_admin_can_list_barbers(admin_client):
    response = await admin_client.get("/admin/barbers/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("id" in b and "full_name" in b for b in data)


@pytest.mark.asyncio
async def test_admin_can_get_barber(admin_client):
    barber_id = 1
    response = await admin_client.get(f"/admin/barbers/{barber_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == barber_id
    assert "full_name" in data


@pytest.mark.asyncio
async def test_admin_cannot_get_barber(admin_client):
    barber_id = 999
    response = await admin_client.get(f"/admin/barbers/{barber_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_create_barber(admin_client):
    payload = {
        "username": "newbarber",
        "phone": "+12345678999",
        "password": "newbarber1#",
        "full_name": "New Barber",
    }
    response = await admin_client.post("/admin/barbers/create", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["full_name"] == payload["full_name"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_error",
    [
        (
            {
                "username": "u",
                "phone": "+1234567890",
                "password": "pass123#",
                "full_name": "Valid Name",
            },
            "username must be between 3 and 50 characters",
        ),
        (
            {
                "username": "validuser",
                "phone": "12345",
                "password": "pass123#",
                "full_name": "Valid Name",
            },
            "phone must be 10-15 digits",
        ),
        (
            {
                "username": "validuser",
                "phone": "+1234567890",
                "password": "pass",
                "full_name": "Valid Name",
            },
            "password must be at least 6 characters",
        ),
        (
            {
                "username": "barberuser",
                "phone": "+12345678999",
                "password": "somepass1#",
                "full_name": "Duplicate Username",
            },
            "already exists",
        ),
        (
            {
                "username": "uniquebarber",
                "phone": "+10000000002",
                "password": "somepass2#",
                "full_name": "Duplicate Phone",
            },
            "already exists",
        ),
    ],
)
async def test_admin_create_barber_validation_errors(
    admin_client, payload, expected_error
):
    response = await admin_client.post("/admin/barbers/create", json=payload)
    assert response.status_code == 422 or response.status_code == 400
    assert expected_error.lower() in response.text.lower()


@pytest.mark.asyncio
async def test_admin_can_update_barber(admin_client):
    barber_id = 1
    payload = {"full_name": "Updated Name"}

    response = await admin_client.put(f"/admin/barbers/{barber_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_admin_update_barber_validation_errors(admin_client):
    barber_id = 1
    payload = {"full_name": ""}

    response = await admin_client.put(f"/admin/barbers/{barber_id}", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_can_delete_barber(admin_client, db_session_with_rollback):
    from app.models import Barber

    barber_id = 1
    response = await admin_client.delete(f"/admin/barbers/{barber_id}")
    assert response.status_code == 204

    deleted_barber = await db_session_with_rollback.get(Barber, barber_id)
    assert deleted_barber is None


@pytest.mark.asyncio
async def test_admin_cannot_delete_barber(admin_client):
    barber_id = 999
    response = await admin_client.delete(f"/admin/barbers/{barber_id}")
    assert response.status_code == 404


@patch("app.services.admin.barbers.upload_file_to_s3", new_callable=AsyncMock)
@patch("app.services.admin.barbers.delete_file_from_s3", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_admin_can_upload_barber_avatar(
    mock_delete_file_from_s3,
    mock_upload_file_to_s3,
    admin_client,
):
    barber_id = 1

    mock_upload_file_to_s3.return_value = (
        "https://mock-bucket.s3.amazonaws.com/barbers/avatar.jpg"
    )
    mock_delete_file_from_s3.return_value = None

    files = {"file": ("avatar.jpg", b"fake image data", "image/jpeg")}
    res = await admin_client.post(f"/admin/barbers/{barber_id}/avatar", files=files)

    assert res.status_code == 200, res.text
    data = res.json()
    assert data["avatar_url"].startswith("https://mock-bucket")


@patch("app.services.admin.barbers.upload_file_to_s3", new_callable=AsyncMock)
@patch("app.services.admin.barbers.delete_file_from_s3", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_admin_can_delete_barber_avatar(
    mock_delete_file_from_s3,
    mock_upload_file_to_s3,
    admin_client,
):
    mock_upload_file_to_s3.return_value = (
        "https://mock-bucket.s3.amazonaws.com/barbers/avatar.jpg"
    )
    mock_delete_file_from_s3.return_value = None

    barber_id = 1

    res = await admin_client.delete(f"/admin/barbers/{barber_id}/avatar")

    assert res.status_code == 204


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_barber_endpoints(
    authorized_client, barber_client
):
    async def check_non_admin_access(client):
        barber_id = 1
        payload = {"full_name": "New Name"}

        res_list = await client.get("/admin/barbers/")
        assert res_list.status_code == 403
        assert (
            res_list.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_get = await client.get(f"/admin/barbers/{barber_id}")
        assert res_get.status_code == 403
        assert (
            res_get.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_create = await client.post(
            "/admin/barbers/create",
            json={
                "username": "newbarber",
                "phone": "+12345678999",
                "password": "newbarber1#",
                "full_name": "New Barber",
            },
        )
        assert res_create.status_code == 403
        assert (
            res_create.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_update = await client.put(f"/admin/barbers/{barber_id}", json=payload)
        assert res_update.status_code == 403
        assert (
            res_update.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_delete = await client.delete(f"/admin/barbers/{barber_id}")
        assert res_delete.status_code == 403
        assert (
            res_delete.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        files = {"file": ("avatar.jpg", b"fake image data", "image/jpeg")}
        res_upload_avatar = await client.post(
            f"/admin/barbers/{barber_id}/avatar", files=files
        )
        assert res_upload_avatar.status_code == 403
        assert (
            res_upload_avatar.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_delete_avatar = await client.delete(f"/admin/barbers/{barber_id}/avatar")
        assert res_delete_avatar.status_code == 403
        assert (
            res_delete_avatar.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

    await check_non_admin_access(authorized_client)
    await check_non_admin_access(barber_client)
