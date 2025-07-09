import pytest

from app.models.enums import RoleEnum


@pytest.mark.asyncio
async def test_admin_can_list_users(admin_client):
    response = await admin_client.get("/admin/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


@pytest.mark.asyncio
async def test_admin_can_get_user(admin_client):
    user_id = 4
    response = await admin_client.get(f"/admin/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert "username" in data


@pytest.mark.asyncio
async def test_admin_cannot_get_user(admin_client):
    user_id = 999
    response = await admin_client.get(f"/admin/users/{user_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_can_update_user(admin_client):
    user_id = 4
    new_phone = "+19999999999"
    response = await admin_client.put(
        f"/admin/users/{user_id}",
        json={"phone": new_phone},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == new_phone


@pytest.mark.asyncio
async def test_admin_can_update_username_phone_password(admin_client):
    user_id = 4
    new_username = "new_user_name"
    new_phone = "+18888888888"
    new_password = "new_secure_password_123"

    response = await admin_client.put(
        f"/admin/users/{user_id}",
        json={
            "username": new_username,
            "phone": new_phone,
            "password": new_password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == new_username
    assert data["phone"] == new_phone


@pytest.mark.asyncio
async def test_admin_cannot_set_existing_username(admin_client):
    target_user_id = 4

    response = await admin_client.put(
        f"/admin/users/{target_user_id}",
        json={"username": "admin"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


@pytest.mark.asyncio
async def test_admin_cannot_set_existing_phone(admin_client):
    target_user_id = 4

    response = await admin_client.put(
        f"/admin/users/{target_user_id}",
        json={"phone": "+10000000000"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Phone number already exists"


@pytest.mark.asyncio
async def test_admin_cannot_update_admin_user(admin_client):
    admin_user_id = 1
    response = await admin_client.put(
        f"/admin/users/{admin_user_id}",
        json={"phone": "+18888888888"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_delete_user(admin_client):
    user_id = 4
    response = await admin_client.delete(f"/admin/users/{user_id}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_cannot_delete_user(admin_client):
    user_id = 999
    response = await admin_client.delete(f"/admin/users/{user_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_cannot_delete_admin_user(admin_client):
    admin_user_id = 1
    response = await admin_client.delete(f"/admin/users/{admin_user_id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_promote_user_to_barber(admin_client):
    user_id = 4
    response = await admin_client.post(
        f"/admin/users/{user_id}/promote-to-barber",
        json={"full_name": "Barber Test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role_id"] == RoleEnum.BARBER.value


@pytest.mark.asyncio
async def test_admin_cannot_promote_already_barber(admin_client):
    user_id = 3
    response = await admin_client.post(
        f"/admin/users/{user_id}/promote-to-barber",
        json={"full_name": "Barber Duplicate"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_cannot_promote_admin_to_barber(admin_client):
    admin_user_id = 1
    response = await admin_client.post(
        f"/admin/users/{admin_user_id}/promote-to-barber",
        json={"full_name": "Barber Duplicate"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_endpoints(
    authorized_client, barber_client
):
    async def check_non_admin_access(client):
        user_id = 4

        res_list = await client.get("/admin/users/")
        assert res_list.status_code == 403
        assert (
            res_list.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_get = await client.get(f"/admin/users/{user_id}")
        assert res_get.status_code == 403
        assert (
            res_get.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_update = await client.put(
            f"/admin/users/{user_id}", json={"phone": "+12345678999"}
        )
        assert res_update.status_code == 403
        assert (
            res_update.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

        res_delete = await client.delete(f"/admin/users/{user_id}")
        assert res_delete.status_code == 403
        assert (
            res_delete.json()["detail"]
            == "Access denied: only admins can perform this action"
        )

    await check_non_admin_access(authorized_client)
    await check_non_admin_access(barber_client)
