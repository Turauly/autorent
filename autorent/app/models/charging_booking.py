from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ChargingBooking(Base):
    __tablename__ = "charging_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("charging_stations.id"), nullable=False, index=True)
    booking_date = Column(Date, nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)
    status = Column(String, nullable=False, default="booked")
    note = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
