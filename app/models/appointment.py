from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_name = Column(String, nullable=True)
    client_phone = Column(String)
    barber_id = Column(Integer, ForeignKey("barbers.id"))
    appointment_time = Column(DateTime, index=True)
    status = Column(String, default="scheduled")
    schedule_id = Column(Integer, ForeignKey("barber_schedules.id"), nullable=False)

    client = relationship(
        "User", foreign_keys=[client_id], back_populates="appointments_as_client"
    )
    barber = relationship(
        "Barber", foreign_keys=[barber_id], back_populates="appointments"
    )
    schedule = relationship("BarberSchedule", backref="appointments")
