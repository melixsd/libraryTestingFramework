"""MembershipType model - membership level (Student, Regular, Premium, etc.)"""
from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class MembershipType(Base):
    __tablename__ = "membership_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    max_books = Column(Integer, nullable=False, default=3)
    loan_period_days = Column(Integer, nullable=False, default=14)
    max_renewals = Column(Integer, nullable=False, default=1)
    can_reserve = Column(Boolean, default=True)
    daily_fine_rate = Column(Float, nullable=False, default=0.5)

    members = relationship("Member", back_populates="membership_type")
