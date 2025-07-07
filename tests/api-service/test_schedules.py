from datetime import date, time, timedelta

import pytest

from app.models.barberschedule import BarberSchedule

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
async def test_barber_can_get_own_schedules(barber_client):
    create_res = await barber_client.post(
        "/barber/schedules/", json=schedule_create_payload
    )
    assert create_res.status_code == 200, create_res.text

    res = await barber_client.get("/barber/schedules/")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "start_time" in data[0]
    assert "end_time" in data[0]
    assert "date" in data[0]


@pytest.mark.asyncio
async def test_barber_can_update_schedule(barber_client):
    create_res = await barber_client.post(
        "/barber/schedules/", json=schedule_create_payload
    )
    assert create_res.status_code == 200, create_res.text
    schedule_id = create_res.json()["id"]

    update_payload = {
        "start_time": "12:00",
        "end_time": "13:00",
    }
    update_res = await barber_client.put(
        f"/barber/schedules/{schedule_id}", json=update_payload
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["start_time"] == "12:00"
    assert data["end_time"] == "13:00"


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
async def test_update_schedule_to_past(barber_client):
    future_date = (date.today() + timedelta(days=1)).isoformat()
    valid_payload = {"date": future_date, "start_time": "10:00", "end_time": "11:00"}
    create_res = await barber_client.post("/barber/schedules/", json=valid_payload)
    assert create_res.status_code == 200
    schedule_id = create_res.json()["id"]

    past_date = (date.today() - timedelta(days=2)).isoformat()
    update_payload = {"date": past_date, "start_time": "01:00", "end_time": "02:00"}

    update_res = await barber_client.put(
        f"/barber/schedules/{schedule_id}",
        json=update_payload,
    )
    assert update_res.status_code == 400
    assert "past" in update_res.text.lower()


@pytest.mark.asyncio
async def test_update_schedule_with_overlap(barber_client):
    future_date = (date.today() + timedelta(days=1)).isoformat()
    payload1 = {"date": future_date, "start_time": "09:00", "end_time": "10:00"}
    payload2 = {"date": future_date, "start_time": "11:00", "end_time": "12:00"}

    res1 = await barber_client.post("/barber/schedules/", json=payload1)
    res2 = await barber_client.post("/barber/schedules/", json=payload2)
    assert res1.status_code == 200
    assert res2.status_code == 200

    second_id = res2.json()["id"]

    update_payload = {"start_time": "09:30", "end_time": "10:30"}
    res = await barber_client.put(f"/barber/schedules/{second_id}", json=update_payload)
    assert res.status_code == 400
    assert "overlaps" in res.text.lower()


@pytest.mark.asyncio
async def test_update_schedule_invalid_times(barber_client):
    future_date = (date.today() + timedelta(days=1)).isoformat()
    valid_payload = {"date": future_date, "start_time": "10:00", "end_time": "11:00"}
    res = await barber_client.post("/barber/schedules/", json=valid_payload)
    assert res.status_code == 200
    schedule_id = res.json()["id"]

    update_payload = {"start_time": "14:00", "end_time": "13:00"}
    res = await barber_client.put(
        f"/barber/schedules/{schedule_id}", json=update_payload
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_barber_can_delete_schedule(barber_client):
    create_res = await barber_client.post(
        "/barber/schedules/", json=schedule_create_payload
    )
    assert create_res.status_code == 200, create_res.text
    schedule_id = create_res.json()["id"]

    res_delete = await barber_client.delete(f"/barber/schedules/{schedule_id}")
    assert res_delete.status_code == 200
    assert res_delete.json()["detail"] == "Schedule deleted"

    res_check = await barber_client.get("/barber/schedules/")
    assert all(s["id"] != schedule_id for s in res_check.json())


@pytest.mark.asyncio
async def test_delete_nonexistent_schedule(barber_client):
    res = await barber_client.delete("/barber/schedules/9999999")
    assert res.status_code == 404
    assert "Schedule not found" in res.text


@pytest.mark.asyncio
async def test_delete_booked_schedule(barber_client, db_session_with_rollback):
    schedule = BarberSchedule(
        barber_id=1,
        date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(11, 0),
        is_active=False,
    )
    db_session_with_rollback.add(schedule)
    await db_session_with_rollback.commit()
    await db_session_with_rollback.refresh(schedule)

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
