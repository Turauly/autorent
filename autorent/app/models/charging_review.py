from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ChargingReview(Base):
    __tablename__ = "charging_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    station_id = Column(Integer, ForeignKey("charging_stations.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(String, nullable=False, server_default=func.datetime("now"))
