from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.database import Base


class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    charger_type = Column(String, nullable=False, default="DC")
    connector_types = Column(String, nullable=False, default="CCS2")
    slot_count = Column(Integer, nullable=False, default=2)
    power_kw = Column(Float, nullable=False, default=60)
    price_per_kwh = Column(Float, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    note = Column(Text, nullable=True)
