"""BorrowRecord model - borrowing record for each physical copy"""
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    copy_id = Column(Integer, ForeignKey("book_copies.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    borrow_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    returned = Column(Boolean, default=False)
    renewed_count = Column(Integer, default=0)
    fine_amount = Column(Float, default=0.0)

    copy = relationship("BookCopy", back_populates="borrow_records")
    member = relationship("Member", back_populates="borrow_records")
