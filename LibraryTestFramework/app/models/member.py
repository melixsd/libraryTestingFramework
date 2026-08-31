"""Member model - library member"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.core.time import utc_now


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    join_date = Column(DateTime, default=utc_now)
    outstanding_fine = Column(Float, nullable=False, default=0.0)

    membership_type_id = Column(Integer, ForeignKey("membership_types.id"), nullable=False)
    membership_type = relationship("MembershipType", back_populates="members")

    borrow_records = relationship("BorrowRecord", back_populates="member")
    reservations = relationship("Reservation", back_populates="member")
