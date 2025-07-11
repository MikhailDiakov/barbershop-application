from datetime import date, time, timedelta

import pytest
import pytest_asyncio

from app.models.barberschedule import BarberSchedule


@pytest_asyncio.fixture
def barber_schedule_factory(db_session_with_rollback):
    async def create_schedule(
        barber_id: int = 1,
        schedule_date: date = date.today() + timedelta(days=1),
        start_time_: time = time(10, 0),
        end_time_: time = time(11, 0),
        is_active: bool = True,
    ) -> BarberSchedule:
        schedule = BarberSchedule(
            barber_id=barber_id,
            date=schedule_date,
            start_time=start_time_,
            end_time=end_time_,
            is_active=is_active,
        )
        db_session_with_rollback.add(schedule)
        await db_session_with_rollback.commit()
        await db_session_with_rollback.refresh(schedule)
        return schedule

    return create_schedule


schedule_create_payload = {
    "barber_id": 1,
    "date": (date.today() + timedelta(days=1)).isoformat(),
    "start_time": "10:00",
    "end_time": "11:00",
    "is_active": True,
}


@pytest.mark.asyncio
async def test_admin_can_list_all_schedules(admin_client, barber_schedule_factory):
    await barber_schedule_factory()
    response = await admin_client.get("/admin/barbers/schedules/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("id" in s and "barber_id" in s for s in data)


@pytest.mark.asyncio
async def test_admin_can_filter_schedules(admin_client, barber_schedule_factory):
    schedule = await barber_schedule_factory()
    url = f"/admin/barbers/schedules/?barber_id={schedule.barber_id}&start_date={schedule.date}&end_date={schedule.date}"
    response = await admin_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert any(s["id"] == schedule.id for s in data)


@pytest.mark.asyncio
async def test_admin_can_create_schedule(admin_client):
    response = await admin_client.post(
        "/admin/barbers/schedules/", json=schedule_create_payload
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "11:00"
    assert data["date"] == schedule_create_payload["date"]


@pytest.mark.asyncio
async def test_admin_cannot_create_schedule_in_past(admin_client):
    past_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {
        "barber_id": 1,
        "date": past_date,
        "start_time": "10:00",
        "end_time": "11:00",
        "is_active": True,
    }
    response = await admin_client.post("/admin/barbers/schedules/", json=payload)
    assert response.status_code == 400
    assert "Cannot create a schedule in the past" in response.text


@pytest.mark.asyncio
async def test_admin_cannot_create_overlapping_schedule(
    admin_client, barber_schedule_factory
):
    existing = await barber_schedule_factory()
    payload = {
        "barber_id": existing.barber_id,
        "date": existing.date.isoformat(),
        "start_time": "10:30",
        "end_time": "11:30",
        "is_active": True,
    }
    response = await admin_client.post("/admin/barbers/schedules/", json=payload)
    assert response.status_code == 400
    assert "overlaps" in response.text.lower()


@pytest.mark.asyncio
async def test_admin_can_update_schedule(admin_client, barber_schedule_factory):
    schedule = await barber_schedule_factory()
    payload = {
        "start_time": "12:00",
        "end_time": "13:00",
    }
    response = await admin_client.put(
        f"/admin/barbers/schedules/{schedule.id}", json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["start_time"] == "12:00"
    assert data["end_time"] == "13:00"
    assert data["id"] == schedule.id


@pytest.mark.asyncio
async def test_admin_update_nonexistent_schedule(admin_client):
    res = await admin_client.put(
        "/admin/barbers/schedules/9999", json=schedule_create_payload
    )
    assert res.status_code == 404
    assert "Schedule not found" in res.text


@pytest.mark.asyncio
async def test_admin_cannot_update_schedule_to_past(
    admin_client, barber_schedule_factory
):
    schedule = await barber_schedule_factory()
    yesterday = (date.today() - timedelta(days=2)).isoformat()
    payload = {
        "date": yesterday,
    }
    response = await admin_client.put(
        f"/admin/barbers/schedules/{schedule.id}", json=payload
    )
    assert response.status_code == 400
    assert "past" in response.text.lower()


@pytest.mark.asyncio
async def test_admin_update_schedule_with_overlap(
    barber_schedule_factory, admin_client
):
    _ = await barber_schedule_factory(
        start_time_=time(9, 0),
        end_time_=time(10, 0),
    )
    schedule2 = await barber_schedule_factory(
        start_time_=time(11, 0),
        end_time_=time(12, 0),
    )

    update_payload = {"start_time": "09:30", "end_time": "10:30"}
    res = await admin_client.put(
        f"/admin/barbers/schedules/{schedule2.id}",
        json=update_payload,
    )

    assert res.status_code == 400
    assert "overlap" in res.text.lower()


@pytest.mark.asyncio
async def test_admin_update_schedule_invalid_times(
    barber_schedule_factory, admin_client
):
    schedule = await barber_schedule_factory()

    update_payload = {"start_time": "14:00", "end_time": "13:00"}

    res = await admin_client.put(
        f"/admin/barbers/schedules/{schedule.id}",
        json=update_payload,
    )

    assert res.status_code == 400
    assert "end" in res.text.lower() or "start" in res.text.lower()


@pytest.mark.asyncio
async def test_admin_can_delete_schedule(
    admin_client, barber_schedule_factory, db_session_with_rollback
):
    schedule = await barber_schedule_factory()
    response = await admin_client.delete(f"/admin/barbers/schedules/{schedule.id}")
    assert response.status_code == 204

    deleted = await db_session_with_rollback.get(type(schedule), schedule.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_admin_delete_nonexistent_schedule(admin_client):
    res = await admin_client.delete("/admin/barbers/schedules/9999999")
    assert res.status_code == 404
    assert "Schedule not found" in res.text


@pytest.mark.asyncio
async def test_admin_cannot_delete_booked_schedule(
    admin_client, barber_schedule_factory
):
    schedule = await barber_schedule_factory(is_active=False)
    response = await admin_client.delete(f"/admin/barbers/schedules/{schedule.id}")
    assert response.status_code == 400
    assert "Cannot delete schedule" in response.text


@pytest.mark.asyncio
async def test_non_admin_cannot_access_schedule_endpoints(
    authorized_client, barber_client
):
    async def check_schedule_access_denied(client):
        res = await client.get("/admin/barbers/schedules/")
        assert res.status_code == 403

        res = await client.get(
            f"/admin/barbers/schedules/?barber_id=1&start_date={date.today()}&end_date={date.today()}"
        )
        assert res.status_code == 403

        payload = {
            "barber_id": 1,
            "date": (date.today() + timedelta(days=1)).isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "is_active": True,
        }
        res = await client.post("/admin/barbers/schedules/", json=payload)
        assert res.status_code == 403

        res = await client.put(
            "/admin/barbers/schedules/1",
            json={"start_time": "09:00", "end_time": "10:00"},
        )
        assert res.status_code == 403

        res = await client.delete("/admin/barbers/schedules/1")
        assert res.status_code == 403

    await check_schedule_access_denied(authorized_client)
    await check_schedule_access_denied(barber_client)
