from datetime import date, time

import pytest

from app.models.barberschedule import BarberSchedule
from app.utils.time_correction import check_time_overlap


def test_trim_time():
    from datetime import time

    from app.utils.time_correction import trim_time

    assert trim_time(time(12, 34, 56)) == time(12, 34)
    assert trim_time(time(0, 0, 0)) == time(0, 0)
    assert trim_time(time(23, 59, 59)) == time(23, 59)


@pytest.mark.asyncio
async def test_check_time_overlap_no_overlap(db_session_with_rollback):
    schedule = BarberSchedule(
        barber_id=1,
        date=date(2025, 7, 10),
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    db_session_with_rollback.add(schedule)
    await db_session_with_rollback.commit()

    result = await check_time_overlap(
        db_session_with_rollback,
        barber_id=1,
        date_=date(2025, 7, 10),
        start_time=time(11, 0),
        end_time=time(12, 0),
    )
    assert result is False


@pytest.mark.asyncio
async def test_check_time_overlap_with_overlap(db_session_with_rollback):
    schedule = BarberSchedule(
        barber_id=1,
        date=date(2025, 7, 10),
        start_time=time(10, 0),
        end_time=time(11, 0),
    )
    db_session_with_rollback.add(schedule)
    await db_session_with_rollback.commit()

    result = await check_time_overlap(
        db_session_with_rollback,
        barber_id=1,
        date_=date(2025, 7, 10),
        start_time=time(10, 30),
        end_time=time(11, 30),
    )
    assert result is True
