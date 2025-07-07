from datetime import date, time, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.barberschedule import BarberSchedule


@pytest.mark.asyncio
@patch("app.services.appointment_service.send_sms_task.delay")
@patch("app.services.appointment_service.send_sms_task.apply_async")
async def test_create_appointment_success_authorized_client(
    mock_remind_sms,
    mock_send_sms,
    db_session_with_rollback,
    authorized_client,
):
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

    res = await authorized_client.post(
        "/appointments/",
        json={
            "barber_id": 1,
            "schedule_id": schedule.id,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["barber_id"] == 1
    assert data["schedule_id"] == schedule.id

    mock_send_sms.assert_called_once()
    mock_remind_sms.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.appointment_service.send_sms_task.delay")
@patch("app.services.appointment_service.send_sms_task.apply_async")
async def test_create_appointment_success_anonymous_client(
    mock_remind_sms,
    mock_send_sms,
    db_session_with_rollback,
    client,
):
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

    res = await client.post(
        "/appointments/",
        json={
            "barber_id": 1,
            "schedule_id": schedule.id,
            "client_name": "anonymous",
            "client_phone": "+99999999999",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["barber_id"] == 1
    assert data["schedule_id"] == schedule.id

    mock_send_sms.assert_called_once()
    mock_remind_sms.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.appointment_service.send_sms_task.delay")
@patch("app.services.appointment_service.send_sms_task.apply_async")
async def test_create_appointment_fail_anonymous_missing_name_phone(
    mock_remind_sms,
    mock_send_sms,
    db_session_with_rollback,
    client,
):
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

    res = await client.post(
        "/appointments/",
        json={
            "barber_id": 1,
            "schedule_id": schedule.id,
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"] == "Name and phone required for anonymous booking"

    mock_send_sms.assert_not_called()
    mock_remind_sms.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.appointment_service.send_sms_task.delay", new_callable=AsyncMock)
@patch(
    "app.services.appointment_service.send_sms_task.apply_async", new_callable=AsyncMock
)
async def test_get_my_appointments(
    mock_apply_async,
    mock_delay,
    db_session_with_rollback,
    authorized_client,
):
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

    res_create = await authorized_client.post(
        "/appointments/",
        json={"barber_id": 1, "schedule_id": schedule.id},
    )
    assert res_create.status_code == 200

    res = await authorized_client.get("/appointments/my")
    assert res.status_code == 200
    appointments = res.json()
    assert isinstance(appointments, list)
    assert any(a["schedule_id"] == schedule.id for a in appointments)


@pytest.mark.asyncio
@patch("app.services.appointment_service.get_rating_for_barber", new_callable=AsyncMock)
async def test_get_barbers(mock_get_rating, client):
    mock_get_rating.return_value = (4.5, 10)
    res = await client.get("/appointments/barbers")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert "avg_rating" in data[0]
    assert data[0]["reviews_count"] == 10


@pytest.mark.asyncio
@patch("app.services.appointment_service.get_rating_for_barber", new_callable=AsyncMock)
async def test_get_barber_detail(mock_get_rating, client):
    mock_get_rating.return_value = (5.0, 3)
    res = await client.get("/appointments/barbers/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert "reviews" in data


@pytest.mark.asyncio
@patch("app.services.appointment_service.get_rating_for_barber", new_callable=AsyncMock)
async def test_get_available_slots(mock_get_rating, db_session_with_rollback, client):
    mock_get_rating.return_value = (4.2, 8)

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

    res = await client.get("/appointments/available-slots")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert "schedules" in data[0]
    assert len(data[0]["schedules"]) >= 1
    assert "schedules" in data[0]
    assert len(data[0]["schedules"]) >= 1
