import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post(
        "/users/register",
        json={
            "username": "testreguser",
            "phone": "+1234567890",
            "password": "testreguser1#",
            "confirm_password": "testreguser1#",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testreguser"
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
async def test_login_barber(client):
    response = await client.post(
        "/users/login",
        data={"username": "barberuser", "password": "barber123#"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()
    assert "access_token" in token
    assert token["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_admin(client):
    response = await client.post(
        "/users/login",
        data={"username": "admin", "password": "admin"},
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
