# app/models/rental.py
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Rental(Base):
    __tablename__ = "rentals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    car_id = Column(Integer, ForeignKey("cars.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_price = Column(Float)
    status = Column(String, default="active")  # active / completed / canceled
    price_variant = Column(String, default="A", nullable=False)  # A/B pricing bucket

    # Relationships
    user = relationship("User")
    car = relationship("Car")
