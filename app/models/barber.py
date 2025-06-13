from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Barber(Base):
    __tablename__ = "barbers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    user = relationship("User", back_populates="barber_profile")
    schedules = relationship(
        "BarberSchedule", back_populates="barber", cascade="all, delete-orphan"
    )

    appointments = relationship(
        "Appointment",
        foreign_keys="Appointment.barber_id",
        back_populates="barber",
        cascade="all, delete-orphan",
    )
