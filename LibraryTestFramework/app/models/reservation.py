"""Reservation model - waiting queue for unavailable books"""
import enum
from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ReservationStatus(str, enum.Enum):
    WAITING = "WAITING"
    READY = "READY"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    reservation_date = Column(DateTime, nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.WAITING)
    expiry_date = Column(DateTime, nullable=True)

    book = relationship("Book", back_populates="reservations")
    member = relationship("Member", back_populates="reservations")
