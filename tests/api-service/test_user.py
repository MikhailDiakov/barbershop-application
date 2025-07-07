from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_get_my_profile(authorized_client):
    response = await authorized_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["phone"] == "+10000000003"


@pytest.mark.asyncio
async def test_update_my_profile_success_change_phone(authorized_client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "phone": "+1234567890",
            "old_password": "testuser1#",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1234567890"


@pytest.mark.asyncio
async def test_update_my_profile_fail_phone_already_in_use(authorized_client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "phone": "+10000000001",
            "old_password": "testuser1#",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Phone already in use"


@pytest.mark.asyncio
async def test_update_my_profile_fail_password_required_to_change_phone(
    authorized_client,
):
    response = await authorized_client.put(
        "/users/me/update", json={"phone": "+10000000003"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Password required to change phone"


@pytest.mark.asyncio
async def test_update_my_profile_fail_old_password_incorrect(authorized_client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "old_password": "wrongpassword",
            "new_password": "newPass123!",
            "confirm_password": "newPass123!",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Old password is incorrect"


@pytest.mark.asyncio
async def test_update_my_profile_success_change_password(authorized_client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "old_password": "testuser1#",
            "new_password": "newPass123!",
            "confirm_password": "newPass123!",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_my_profile_fail_passwords_mismatch(authorized_client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "old_password": "testuser1#",
            "new_password": "newPass123!",
            "confirm_password": "differentPass!",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@patch("app.services.user_service.send_sms_task.delay")
@patch("app.services.user_service.save_verification_code", new_callable=AsyncMock)
@patch("app.services.user_service.can_request_code", new_callable=AsyncMock)
async def test_password_reset_request_success(
    mock_can_request,
    mock_save_code,
    mock_send_sms,
    client,
):
    phone = "+10000000003"

    mock_can_request.return_value = True
    mock_save_code.return_value = None

    res = await client.post("/users/password-reset/request", json={"phone": phone})
    assert res.status_code == 200
    assert res.json() == {"detail": "Verification code sent"}

    mock_can_request.assert_awaited_once_with(phone)
    mock_send_sms.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.user_service.get_verification_code", new_callable=AsyncMock)
@patch("app.services.user_service.delete_verification_code", new_callable=AsyncMock)
async def test_password_reset_confirm_success_real(
    mock_delete_code,
    mock_get_code,
    client,
):
    phone = "+10000000003"
    username = "testuser"
    new_password = "NewTestPass123!"

    mock_get_code.return_value = "123456"
    mock_delete_code.return_value = None

    res = await client.post(
        "/users/password-reset/confirm",
        json={
            "phone": phone,
            "code": "123456",
            "new_password": new_password,
            "new_password_repeat": new_password,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["phone"] == phone
    assert data["username"] == username
