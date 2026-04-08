from sqlalchemy import Boolean, Column, Date, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Car(Base):
    __tablename__ = "cars"

    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    category = Column(String, default="econom", nullable=False)  # econom/budget/comfort/lux
    year = Column(Integer)
    transmission = Column(String, default="automatic")
    fuel_type = Column(String, default="petrol")
    seats = Column(Integer, default=5)
    has_ac = Column(Boolean, default=True)
    has_gps = Column(Boolean, default=False)
    has_bluetooth = Column(Boolean, default=False)
    is_electric = Column(Boolean, default=False, nullable=False)
    battery_capacity_kwh = Column(Float, nullable=True)
    range_km = Column(Integer, nullable=True)
    charge_port = Column(String, nullable=True)
    price_per_day = Column(Float, nullable=False)
    status = Column(String, default="available")
    main_image_url = Column(String, nullable=True)
    next_service_date = Column(Date, nullable=True)
    service_note = Column(Text, nullable=True)

    photos = relationship("CarPhoto", back_populates="car", cascade="all, delete-orphan")
