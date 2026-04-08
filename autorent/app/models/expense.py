from sqlalchemy import Column, Date, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False, default="operations")
    expense_date = Column(Date, nullable=False, server_default=func.current_date())
    note = Column(Text, nullable=True)
