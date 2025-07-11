import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_admins(super_admin_client):
    res = await super_admin_client.get("/superadmin/admins")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    admin_ids = [admin["id"] for admin in data]
    assert any(role_id in [0, 1] for role_id in admin_ids)


@pytest.mark.asyncio
async def test_get_admin_by_id(super_admin_client):
    res = await super_admin_client.get("/superadmin/admins/2")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 2
    assert data["role_id"] == 1


@pytest.mark.asyncio
async def test_get_admin_by_id_not_found(super_admin_client):
    res = await super_admin_client.get("/superadmin/admins/999999")
    assert res.status_code == 404
    assert "admin not found" in res.text.lower()


@pytest.mark.asyncio
async def test_promote_to_admin(super_admin_client):
    res = await super_admin_client.post("/superadmin/users/4/promote")
    assert res.status_code == 200
    data = res.json()
    assert data["role_id"] == 1


@pytest.mark.asyncio
async def test_demote_from_admin(super_admin_client):
    res = await super_admin_client.post("/superadmin/users/2/demote")
    assert res.status_code == 200
    data = res.json()
    assert data["role_id"] == 3


@pytest.mark.asyncio
async def test_debug_error_route_zero_division(super_admin_client: AsyncClient):
    with pytest.raises(ZeroDivisionError):
        await super_admin_client.get("/superadmin/debug-error?error_type=zero_division")


@pytest.mark.asyncio
async def test_debug_error_route_runtime(super_admin_client: AsyncClient):
    with pytest.raises(RuntimeError, match="This is a test RuntimeError for Sentry."):
        await super_admin_client.get("/superadmin/debug-error?error_type=runtime")


@pytest.mark.asyncio
async def test_debug_error_route_http_403(super_admin_client: AsyncClient):
    res = await super_admin_client.get("/superadmin/debug-error?error_type=http_403")
    assert res.status_code == 403
    assert "access denied" in res.text.lower()


@pytest.mark.asyncio
async def test_debug_error_route_custom(super_admin_client: AsyncClient):
    with pytest.raises(Exception, match="Custom generic exception"):
        await super_admin_client.get("/superadmin/debug-error?error_type=custom")


@pytest.mark.asyncio
async def test_debug_error_route_unsupported_error(super_admin_client: AsyncClient):
    with pytest.raises(ValueError, match="Unsupported error type"):
        await super_admin_client.get("/superadmin/debug-error?error_type=unsupported")


@pytest.mark.asyncio
async def test_non_admin_cannot_access_superadmin_endpoints(
    authorized_client, barber_client, admin_client
):
    async def check_superadmin_access_denied(client):
        res = await client.get("/superadmin/admins")
        assert res.status_code == 403
        assert "access denied" in res.text.lower()

        res = await client.get("/superadmin/admins/2")
        assert res.status_code == 403
        assert "access denied" in res.text.lower()

        res = await client.post("/superadmin/users/4/promote")
        assert res.status_code == 403
        assert "access denied" in res.text.lower()

        res = await client.post("/superadmin/users/2/demote")
        assert res.status_code == 403
        assert "access denied" in res.text.lower()

        res = await client.get("/superadmin/debug-error?error_type=zero_division")
        assert res.status_code == 403
        assert "access denied" in res.text.lower()

    await check_superadmin_access_denied(authorized_client)
    await check_superadmin_access_denied(barber_client)
    await check_superadmin_access_denied(admin_client)
