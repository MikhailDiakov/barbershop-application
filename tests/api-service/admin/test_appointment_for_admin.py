from datetime import date, datetime, time, timedelta
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.appointment import Appointment
from app.models.barberschedule import BarberSchedule


@pytest_asyncio.fixture
async def barber_schedule(db_session_with_rollback):
    schedule = BarberSchedule(
        barber_id=1,
        date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        is_active=True,
    )
    db_session_with_rollback.add(schedule)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(schedule)
    return schedule


@pytest_asyncio.fixture
async def appointment(db_session_with_rollback, barber_schedule):
    appointment_dt = datetime.combine(barber_schedule.date, barber_schedule.start_time)
    appointment = Appointment(
        client_name="John Doe",
        client_phone="+123456789",
        barber_id=barber_schedule.barber_id,
        appointment_time=appointment_dt,
        status="scheduled",
        schedule_id=barber_schedule.id,
    )
    db_session_with_rollback.add(appointment)
    barber_schedule.is_active = False
    db_session_with_rollback.add(barber_schedule)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(appointment)
    return appointment


@pytest.mark.asyncio
async def test_admin_get_appointments_basic(admin_client, appointment):
    res = await admin_client.get("/admin/appointments/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(a["id"] == appointment.id for a in data)


@pytest.mark.asyncio
async def test_admin_get_appointments_upcoming_false(
    admin_client, db_session_with_rollback, barber_schedule
):
    past_time = datetime.utcnow() - timedelta(days=2)
    appointment = Appointment(
        client_name="Past Client",
        client_phone="+123456789",
        barber_id=barber_schedule.barber_id,
        appointment_time=past_time,
        status="scheduled",
        schedule_id=barber_schedule.id,
    )
    db_session_with_rollback.add(appointment)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(appointment)

    res = await admin_client.get("/admin/appointments/?upcoming_only=false")
    assert res.status_code == 200
    data = res.json()
    assert any(a["id"] == appointment.id for a in data)


@pytest.mark.asyncio
async def test_admin_get_appointments_pagination(
    admin_client, db_session_with_rollback, barber_schedule
):
    for i in range(3):
        appointment_dt = datetime.combine(
            barber_schedule.date + timedelta(days=i), barber_schedule.start_time
        )
        appt = Appointment(
            client_name=f"Client {i}",
            client_phone=f"+12345678{i}",
            barber_id=barber_schedule.barber_id,
            appointment_time=appointment_dt,
            status="scheduled",
            schedule_id=barber_schedule.id,
        )
        db_session_with_rollback.add(appt)
    await db_session_with_rollback.commit()

    res = await admin_client.get("/admin/appointments/?limit=2&skip=0")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_admin_get_appointments_empty(admin_client):
    res = await admin_client.get("/admin/appointments/")
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.asyncio
@patch("app.services.admin.appointment.send_sms_task.delay")
@patch("app.services.admin.appointment.send_sms_task.apply_async")
async def test_admin_create_appointment_success(
    mock_apply_async,
    mock_delay,
    admin_client,
    barber_schedule,
):
    payload = {
        "barber_id": barber_schedule.barber_id,
        "schedule_id": barber_schedule.id,
        "client_name": "AdminTest",
        "client_phone": "+11111111111",
    }
    res = await admin_client.post("/admin/appointments/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["barber_id"] == barber_schedule.barber_id
    assert data["client_name"] == "AdminTest"

    mock_delay.assert_called_once()
    mock_apply_async.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.admin.appointment.send_sms_task.delay")
@patch("app.services.admin.appointment.send_sms_task.apply_async")
async def test_admin_create_appointment_missing_data(
    mock_apply_async,
    mock_delay,
    admin_client,
    barber_schedule,
):
    payload = {
        "barber_id": barber_schedule.barber_id,
        "schedule_id": barber_schedule.id,
    }
    res = await admin_client.post("/admin/appointments/", json=payload)
    assert res.status_code == 400
    assert "name and phone" in res.text.lower()

    mock_delay.assert_not_called()
    mock_apply_async.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.admin.appointment.send_sms_task.delay")
@patch("app.services.admin.appointment.send_sms_task.apply_async")
async def test_admin_create_appointment_on_inactive_schedule(
    mock_apply_async,
    mock_delay,
    admin_client,
    barber_schedule,
    db_session_with_rollback,
):
    barber_schedule.is_active = False
    db_session_with_rollback.add(barber_schedule)
    await db_session_with_rollback.commit()

    payload = {
        "barber_id": barber_schedule.barber_id,
        "schedule_id": barber_schedule.id,
        "client_name": "AdminFail",
        "client_phone": "+11111111111",
    }
    res = await admin_client.post("/admin/appointments/", json=payload)
    assert res.status_code == 400
    assert "not available" in res.text.lower()


@pytest.mark.asyncio
async def test_admin_can_delete_appointment(admin_client, appointment):
    res = await admin_client.delete(f"/admin/appointments/{appointment.id}")
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_admin_delete_nonexistent_appointment(admin_client):
    res = await admin_client.delete("/admin/appointments/999999")
    assert res.status_code == 404
    assert "not found" in res.text.lower()


@pytest.mark.asyncio
async def test_admin_delete_appointment_missing_schedule(
    admin_client, appointment, db_session_with_rollback
):
    await db_session_with_rollback.delete(appointment)
    await db_session_with_rollback.commit()

    result = await db_session_with_rollback.execute(
        select(BarberSchedule).where(BarberSchedule.id == appointment.schedule_id)
    )
    schedule = result.scalar_one_or_none()
    assert schedule is not None

    await db_session_with_rollback.delete(schedule)
    await db_session_with_rollback.commit()

    res = await admin_client.delete(f"/admin/appointments/{appointment.id}")
    assert res.status_code == 404
    assert "appointment not found" in res.text.lower()


@pytest.mark.asyncio
async def test_non_admin_cannot_access_appointment_admin_routes(
    authorized_client, barber_client, appointment, barber_schedule
):
    async def check(client):
        res = await client.get("/admin/appointments/")
        assert res.status_code == 403
        assert "only admins" in res.json()["detail"].lower()

        payload = {
            "barber_id": barber_schedule.barber_id,
            "schedule_id": barber_schedule.id,
            "client_name": "Blocked User",
            "client_phone": "+0000000000",
        }
        res = await client.post("/admin/appointments/", json=payload)
        assert res.status_code == 403
        assert "only admins" in res.json()["detail"].lower()

        res = await client.delete(f"/admin/appointments/{appointment.id}")
        assert res.status_code == 403
        assert "only admins" in res.json()["detail"].lower()

    await check(authorized_client)
    await check(barber_client)
