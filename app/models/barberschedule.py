from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Time
from sqlalchemy.orm import relationship

from app.db.base import Base


class BarberSchedule(Base):
    __tablename__ = "barber_schedules"

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey("barbers.id"))
    date = Column(Date, index=True)
    start_time = Column(Time)
    end_time = Column(Time)
    is_active = Column(Boolean, default=True)

    barber = relationship("Barber", back_populates="schedules")
