from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone = Column(String, unique=True)
    role_id = Column(Integer, ForeignKey("roles.id"))

    role = relationship("Role", back_populates="users")

    schedules = relationship(
        "BarberSchedule", back_populates="barber", cascade="all, delete-orphan"
    )
    appointments_as_client = relationship(
        "Appointment",
        foreign_keys="Appointment.client_id",
        back_populates="client",
        cascade="all, delete-orphan",
    )
    appointments_as_barber = relationship(
        "Appointment",
        foreign_keys="Appointment.barber_id",
        back_populates="barber",
        cascade="all, delete-orphan",
    )
