from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class CarPhoto(Base):
    __tablename__ = "car_photos"

    id = Column(Integer, primary_key=True, index=True)
    car_id = Column(Integer, ForeignKey("cars.id"), nullable=False, index=True)
    url = Column(String, nullable=False)

    car = relationship("Car", back_populates="photos")
