from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text

from app.database import Base


class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, ForeignKey("rentals.id"), nullable=False, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("charging_stations.id"), nullable=False, index=True)
    charged_at = Column(Date, nullable=False)
    kwh_amount = Column(Float, nullable=False)
    price_per_kwh = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    battery_percent_start = Column(Integer, nullable=True)
    battery_percent_end = Column(Integer, nullable=True)
    payment_status = Column(String, nullable=False, default="paid")
    note = Column(Text, nullable=True)
