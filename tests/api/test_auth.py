import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/users/register",
        json={
            "username": "testuser",
            "phone": "+1234567890",
            "password": "testuser1#",
            "confirm_password": "testuser1#",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["phone"] == "+1234567890"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_error",
    [
        (
            {
                "username": "u",
                "phone": "+1234567890",
                "password": "pass123#",
                "confirm_password": "pass123#",
            },
            "Username must be between 3 and 50 characters",
        ),
        (
            {
                "username": "user",
                "phone": "12345",
                "password": "pass123#",
                "confirm_password": "pass123#",
            },
            "Phone must be 10-15 digits",
        ),
        (
            {
                "username": "user",
                "phone": "+1234567890",
                "password": "pass",
                "confirm_password": "pass",
            },
            "Password must be at least 6 characters",
        ),
        (
            {
                "username": "user",
                "phone": "+1234567890",
                "password": "pass123#",
                "confirm_password": "pass124#",
            },
            "Passwords do not match",
        ),
    ],
)
async def test_register_invalid_input(client, payload, expected_error):
    response = await client.post("/users/register", json=payload)
    assert response.status_code == 422
    assert expected_error in response.text


@pytest.mark.asyncio
async def test_login_user(client):
    response = await client.post(
        "/users/login",
        data={"username": "testuser", "password": "testuser1#"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data, expected_status, expected_detail",
    [
        (
            {"username": "wronguser", "password": "testuser1#"},
            401,
            "Invalid credentials",
        ),
        (
            {"username": "testuser", "password": "wrongpassword"},
            401,
            "Invalid credentials",
        ),
        ({"username": "testuser"}, 422, None),
        ({}, 422, None),
    ],
)
async def test_login_invalid_cases(client, data, expected_status, expected_detail):
    response = await client.post(
        "/users/login",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == expected_status
    if expected_detail:
        assert response.json()["detail"] == expected_detail


@pytest.mark.asyncio
async def test_get_my_profile(authorized_client):
    response = await authorized_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["phone"] == "+1234567890"


@pytest.mark.asyncio
async def test_update_my_profile_success_change_phone(authorized_client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "phone": "+12345678901",
            "old_password": "testuser1#",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+12345678901"


@pytest.mark.asyncio
async def test_update_my_profile_fail_phone_already_in_use(authorized_client, client):
    register_response = await client.post(
        "/users/register",
        json={
            "username": "user999",
            "phone": "+9999999999",
            "password": "somepassword123#",
            "confirm_password": "somepassword123#",
        },
    )
    assert register_response.status_code == 201

    response = await authorized_client.put(
        "/users/me/update",
        json={
            "phone": "+9999999999",
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
        "/users/me/update", json={"phone": "+12345678901"}
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
async def test_update_my_profile_success_change_password(authorized_client, client):
    response = await authorized_client.put(
        "/users/me/update",
        json={
            "old_password": "testuser1#",
            "new_password": "newPass123!",
            "confirm_password": "newPass123!",
        },
    )
    assert response.status_code == 200
    login_response = await client.post(
        "/users/login",
        data={"username": "testuser", "password": "newPass123!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    client.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})

    response_revert = await client.put(
        "/users/me/update",
        json={
            "old_password": "newPass123!",
            "new_password": "testuser1#",
            "confirm_password": "testuser1#",
        },
    )
    assert response_revert.status_code == 200


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
