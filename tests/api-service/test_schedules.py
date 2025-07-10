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
    "date": (date.today() + timedelta(days=1)).isoformat(),
    "start_time": "10:00",
    "end_time": "11:00",
}


@pytest.mark.asyncio
async def test_barber_can_create_schedule(barber_client):
    res = await barber_client.post("/barber/schedules/", json=schedule_create_payload)
    assert res.status_code == 200, res.text

    data = res.json()
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "11:00"
    assert data["date"] == schedule_create_payload["date"]


@pytest.mark.asyncio
async def test_barber_cannot_create_schedule_in_past(barber_client):
    past_date = (date.today() - timedelta(days=1)).isoformat()
    payload = {"date": past_date, "start_time": "10:00", "end_time": "11:00"}
    res = await barber_client.post("/barber/schedules/", json=payload)
    assert res.status_code == 400
    assert "Cannot create a schedule in the past" in res.text


@pytest.mark.asyncio
async def test_barber_cannot_create_overlapping_schedule(barber_client):
    payload = {
        "date": (date.today() + timedelta(days=1)).isoformat(),
        "start_time": "09:00",
        "end_time": "10:00",
    }
    res1 = await barber_client.post("/barber/schedules/", json=payload)
    assert res1.status_code == 200

    overlap_payload = {
        "date": payload["date"],
        "start_time": "09:30",
        "end_time": "10:30",
    }
    res2 = await barber_client.post("/barber/schedules/", json=overlap_payload)
    assert res2.status_code == 400
    assert "overlaps" in res2.text.lower()


@pytest.mark.asyncio
async def test_barber_can_get_own_schedules_as_unit(
    barber_schedule_factory, barber_client
):
    barber_schedule = await barber_schedule_factory()
    res = await barber_client.get("/barber/schedules/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(
        s["id"] == barber_schedule.id
        and date.fromisoformat(s["date"]) == barber_schedule.date
        and time.fromisoformat(s["start_time"]) == barber_schedule.start_time
        and time.fromisoformat(s["end_time"]) == barber_schedule.end_time
        for s in data
    )


@pytest.mark.asyncio
async def test_barber_can_update_schedule_unit(barber_schedule_factory, barber_client):
    barber_schedule = await barber_schedule_factory()
    update_payload = {
        "start_time": "12:00",
        "end_time": "13:00",
    }

    update_res = await barber_client.put(
        f"/barber/schedules/{barber_schedule.id}", json=update_payload
    )
    assert update_res.status_code == 200, update_res.text
    data = update_res.json()
    assert data["start_time"] == "12:00"
    assert data["end_time"] == "13:00"
    assert data["id"] == barber_schedule.id


@pytest.mark.asyncio
async def test_update_nonexistent_schedule(barber_client):
    update_payload = {
        "start_time": "12:00",
        "end_time": "13:00",
    }
    res = await barber_client.put("/barber/schedules/9999", json=update_payload)
    assert res.status_code == 404
    assert "Schedule not found" in res.text


@pytest.mark.asyncio
async def test_update_schedule_to_past_unit(barber_client, barber_schedule_factory):
    barber_schedule = await barber_schedule_factory()
    past_date = (date.today() - timedelta(days=2)).isoformat()
    update_payload = {"date": past_date, "start_time": "01:00", "end_time": "02:00"}

    update_res = await barber_client.put(
        f"/barber/schedules/{barber_schedule.id}",
        json=update_payload,
    )
    assert update_res.status_code == 400
    assert "past" in update_res.text.lower()


@pytest.mark.asyncio
async def test_update_schedule_with_overlap(barber_schedule_factory, barber_client):
    _ = await barber_schedule_factory(
        start_time_=time(9, 0),
        end_time_=time(10, 0),
    )
    schedule2 = await barber_schedule_factory(
        start_time_=time(11, 0),
        end_time_=time(12, 0),
    )

    update_payload = {"start_time": "09:30", "end_time": "10:30"}
    res = await barber_client.put(
        f"/barber/schedules/{schedule2.id}",
        json=update_payload,
    )

    assert res.status_code == 400
    assert "overlap" in res.text.lower()


@pytest.mark.asyncio
async def test_update_schedule_invalid_times(barber_schedule_factory, barber_client):
    schedule = await barber_schedule_factory()

    update_payload = {"start_time": "14:00", "end_time": "13:00"}

    res = await barber_client.put(
        f"/barber/schedules/{schedule.id}",
        json=update_payload,
    )

    assert res.status_code == 400
    assert "end" in res.text.lower() or "start" in res.text.lower()


@pytest.mark.asyncio
async def test_barber_can_delete_schedule(
    barber_schedule_factory, barber_client, db_session_with_rollback
):
    schedule = await barber_schedule_factory()

    res_delete = await barber_client.delete(f"/barber/schedules/{schedule.id}")
    assert res_delete.status_code == 200
    assert res_delete.json()["detail"] == "Schedule deleted"

    deleted = await db_session_with_rollback.get(type(schedule), schedule.id)
    assert deleted is None


@pytest.mark.asyncio
async def test_delete_nonexistent_schedule(barber_client):
    res = await barber_client.delete("/barber/schedules/9999999")
    assert res.status_code == 404
    assert "Schedule not found" in res.text


@pytest.mark.asyncio
async def test_delete_booked_schedule(barber_client, barber_schedule_factory):
    schedule = await barber_schedule_factory(is_active=False)

    res_delete = await barber_client.delete(f"/barber/schedules/{schedule.id}")
    assert res_delete.status_code == 400
    assert "Cannot delete schedule" in res_delete.text


@pytest.mark.asyncio
async def test_user_cannot_access_schedule_endpoints(authorized_client):
    res_create = await authorized_client.post(
        "/barber/schedules/", json=schedule_create_payload
    )
    assert res_create.status_code == 403
    assert (
        res_create.json()["detail"]
        == "Access denied: only barbers can perform this action"
    )

    res_get = await authorized_client.get("/barber/schedules/")
    assert res_get.status_code == 403
    assert (
        res_get.json()["detail"]
        == "Access denied: only barbers can perform this action"
    )

    res_update = await authorized_client.put(
        "/barber/schedules/1", json={"start_time": "14:00"}
    )
    assert res_update.status_code == 403
    assert (
        res_update.json()["detail"]
        == "Access denied: only barbers can perform this action"
    )
    res_delete = await authorized_client.delete("/barber/schedules/1")
    assert res_delete.status_code == 403
    assert (
        res_delete.json()["detail"]
        == "Access denied: only barbers can perform this action"
    )
