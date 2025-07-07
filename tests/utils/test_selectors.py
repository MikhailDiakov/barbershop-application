from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barber import Barber
from app.models.barberschedule import BarberSchedule
from app.models.user import User
from app.utils.selectors.schedule import (
    get_barbers_with_schedules,
    select_all_schedules_flat,
)


@pytest.mark.asyncio
async def test_get_barbers_with_schedules_filters_out_past_schedules(
    db_session_with_rollback: AsyncSession,
):
    now = datetime.utcnow()
    today = now.date()
    current_time = now.time()

    user1 = User(
        username="user1", phone="+10000000004", hashed_password="fakehash", role_id=2
    )
    user2 = User(
        username="user2", phone="+10000000005", hashed_password="fakehash", role_id=2
    )
    db_session_with_rollback.add_all([user1, user2])
    await db_session_with_rollback.flush()

    barber = Barber(user_id=user1.id, full_name="Test Barber 1", id=2)
    past_schedule = BarberSchedule(
        barber_id=1,
        date=today,
        start_time=(datetime.combine(today, current_time) - timedelta(hours=2)).time(),
        end_time=(datetime.combine(today, current_time) - timedelta(hours=1)).time(),
        is_active=True,
    )

    barber2 = Barber(user_id=user2.id, full_name="Test Barber 2", id=3)
    future_schedule = BarberSchedule(
        barber_id=2,
        date=today,
        start_time=(datetime.combine(today, current_time) + timedelta(hours=1)).time(),
        end_time=(datetime.combine(today, current_time) + timedelta(hours=2)).time(),
        is_active=True,
    )

    db_session_with_rollback.add_all(
        [user1, user2, barber, barber2, past_schedule, future_schedule]
    )
    await db_session_with_rollback.commit()

    result = await get_barbers_with_schedules(db_session_with_rollback)
    assert len(result) == 3
    assert result[1].id == 2
    assert len(result[1].schedules) == 1


@pytest.mark.asyncio
async def test_select_all_schedules_flat_upcoming_only(
    db_session_with_rollback: AsyncSession,
):
    now = datetime.utcnow()
    today = now.date()
    current_time = now.time()

    past_schedule = BarberSchedule(
        barber_id=1,
        date=today,
        start_time=(datetime.combine(today, current_time) - timedelta(hours=3)).time(),
        end_time=(datetime.combine(today, current_time) - timedelta(hours=2)).time(),
        is_active=True,
    )

    future_schedule = BarberSchedule(
        barber_id=1,
        date=today,
        start_time=(datetime.combine(today, current_time) + timedelta(hours=1)).time(),
        end_time=(datetime.combine(today, current_time) + timedelta(hours=2)).time(),
        is_active=True,
    )

    inactive_schedule = BarberSchedule(
        barber_id=1,
        date=today,
        start_time=(datetime.combine(today, current_time) + timedelta(hours=3)).time(),
        end_time=(datetime.combine(today, current_time) + timedelta(hours=4)).time(),
        is_active=False,
    )

    db_session_with_rollback.add_all(
        [past_schedule, future_schedule, inactive_schedule]
    )
    await db_session_with_rollback.commit()

    schedules = await select_all_schedules_flat(
        db_session_with_rollback, upcoming_only=True
    )
    assert future_schedule in schedules
    assert past_schedule not in schedules
    assert inactive_schedule not in schedules


@pytest.mark.asyncio
async def test_select_all_schedules_flat_with_barber_id_and_date_filters(
    db_session_with_rollback: AsyncSession,
):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    schedule1 = BarberSchedule(
        barber_id=1,
        date=today,
        start_time=time(10, 0),
        end_time=time(11, 0),
        is_active=True,
    )
    schedule2 = BarberSchedule(
        barber_id=2,
        date=tomorrow,
        start_time=time(12, 0),
        end_time=time(13, 0),
        is_active=True,
    )
    schedule3 = BarberSchedule(
        barber_id=1,
        date=tomorrow,
        start_time=time(14, 0),
        end_time=time(15, 0),
        is_active=True,
    )

    db_session_with_rollback.add_all([schedule1, schedule2, schedule3])
    await db_session_with_rollback.commit()

    filtered_schedules = await select_all_schedules_flat(
        db_session_with_rollback,
        upcoming_only=False,
        barber_id=1,
        start_date=today,
        end_date=tomorrow,
    )

    assert schedule1 in filtered_schedules
    assert schedule3 in filtered_schedules
    assert schedule2 not in filtered_schedules
